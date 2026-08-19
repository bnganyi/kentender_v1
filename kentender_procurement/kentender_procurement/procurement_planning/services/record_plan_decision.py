# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-010 — Record professional recommend / return on an In-review Plan Version."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.mvp1_constants import (
	DECISION_RECOMMENDED,
	DECISION_RETURNED,
	DOCTYPE_DECISION,
	VALIDATION_READY,
	VERSION_IN_REVIEW,
	VERSION_RETURNED,
)
from kentender_procurement.procurement_planning.services._invariants import (
	assert_version_concurrency,
	new_concurrency_token,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	CAP_PLAN_APPROVE,
	CAP_PLAN_RECOMMEND,
	CAP_PLAN_RETURN,
	ROLE_ACCOUNTING_OFFICER,
	ROLE_AUTHORITY,
	ROLE_DESIGNATED_APPROVER,
	ROLE_REVIEWER,
	actor_planning_roles,
	assert_planning_scope,
)
from kentender_procurement.procurement_planning.services.planning_tasks import (
	authorize_planning_task,
	create_governed_planning_task,
	task_owner,
	transition_planning_task,
)
from kentender_procurement.procurement_planning.services.validate_plan import validate_plan

ACTION_RECOMMEND = "recommend"
ACTION_RETURN = "return"


def record_plan_decision(
	*,
	version: str,
	decision: str,
	comment: str | None = None,
	concurrency_token: str | None = None,
	task: str | None = None,
	expected_task_token: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	action = cstr(decision).strip().lower()
	if action not in (ACTION_RECOMMEND, ACTION_RETURN):
		return {
			"ok": False,
			"errors": {"form": "Decision must be recommend or return."},
		}

	actor = (user or frappe.session.user or "").strip()

	version_name = cstr(version).strip()
	if not version_name or not frappe.db.exists("Procurement Plan Version", version_name):
		return {"ok": False, "errors": {"form": "Plan Version not found"}}

	ver = frappe.get_doc("Procurement Plan Version", version_name)
	task_id = cstr(task or ver.review_task_id).strip()
	capability = CAP_PLAN_RECOMMEND if action == ACTION_RECOMMEND else CAP_PLAN_RETURN
	authorize_planning_task(
		task_id=task_id, actor=actor, capability=capability,
		subject_type="Procurement Plan Version", subject_id=version_name,
	)
	if not expected_task_token:
		frappe.throw(frappe._("Reload this task before recording a decision."), title="PLN_TASK_STALE")
	plan = frappe.get_doc("Procurement Plan", ver.plan)
	try:
		assert_planning_scope(
			procuring_entity=cstr(plan.procuring_entity).strip(),
			org_unit=None,
			user=actor,
			require_write=True,
		)
	except frappe.PermissionError:
		return {"ok": False, "errors": {"form": "Not permitted for this organisational scope"}}

	if cstr(ver.status) != VERSION_IN_REVIEW:
		return {
			"ok": False,
			"errors": {"form": "Decisions can only be recorded while the version is In review."},
		}

	try:
		assert_version_concurrency(version_name, concurrency_token)
	except frappe.ValidationError as exc:
		return {"ok": False, "errors": {"form": str(exc) or "Concurrency conflict"}}

	note = cstr(comment or "").strip()
	errors: dict[str, str] = {}
	if action == ACTION_RETURN and not note:
		errors["decision_comment"] = "A comment is required when returning the Plan."

	if action == ACTION_RECOMMEND:
		validation = validate_plan(plan=plan.name, user=actor)
		if cstr(validation.get("status")) != VALIDATION_READY:
			errors["form"] = "Validation must be Ready before recommending approval."

	if errors:
		return {"ok": False, "errors": errors}

	now = now_datetime()
	token = new_concurrency_token()
	decision_label = DECISION_RECOMMENDED if action == ACTION_RECOMMEND else DECISION_RETURNED
	decision_type = "Recommendation" if action == ACTION_RECOMMEND else "Return"
	stage = "Professional review" if action == ACTION_RECOMMEND else "Return from review"

	terminal_task = transition_planning_task(
		task_id=task_id, actor=actor, capability=capability,
		target_state="Returned" if action == ACTION_RETURN else "Completed",
		expected_token=cstr(expected_task_token),
	)
	if action == ACTION_RETURN:
		frappe.db.set_value(
			"Procurement Plan Version",
			version_name,
			{
				"status": VERSION_RETURNED,
				"open_version_slot": plan.name,
				"concurrency_token": token,
			},
			update_modified=True,
		)
	else:
		approval_task, approval_iteration = create_governed_planning_task(
			prefix="PLN-APR", record=ver, id_field="review_task_id", iteration_field="review_task_iteration",
			task_type=CAP_PLAN_APPROVE, subject_type="Procurement Plan Version", subject_id=version_name,
			procuring_entity=cstr(plan.procuring_entity), financial_year=cstr(plan.financial_year),
			predecessor_task_id=task_id, idempotency_key=f"planning:approval:{version_name}:{task_id}", actor=actor,
		)
		frappe.db.set_value(
			"Procurement Plan Version",
			version_name,
			{
				"concurrency_token": token,
				"review_task_id": approval_task.name,
				"review_task_iteration": approval_iteration,
				"review_task_assignee": task_owner(approval_task),
				"review_task_state": "Open",
				"review_task_predecessor": task_id,
				"review_task_token": approval_task.concurrency_token,
			},
			update_modified=True,
		)

	frappe.get_doc(
		{
			"doctype": DOCTYPE_DECISION,
			"plan_version": version_name,
			"decision_type": decision_type,
			"decision_stage": stage,
			"actor": actor,
			"actor_role": _actor_role(actor, action),
			"decision": decision_label,
			"reason": note or ("Recommended for approval" if action == ACTION_RECOMMEND else ""),
			"decided_at": now,
			"task_id": task_id,
			"task_iteration": int(ver.review_task_iteration or 1),
		}
	).insert(ignore_permissions=True)

	frappe.db.commit()
	if action == ACTION_RETURN:
		from kentender_procurement.procurement_planning.services.planning_notification_service import (
			notify_plan_returned,
		)

		notify_plan_returned(plan=plan, version_name=version_name, actor=actor)
	status = VERSION_RETURNED if action == ACTION_RETURN else VERSION_IN_REVIEW
	return {
		"ok": True,
		"plan": plan.name,
		"version": version_name,
		"decision": decision_label,
		"status": status,
		"concurrency_token": token,
		"actor": actor,
		"decided_at": str(now),
		"task": cstr(approval_task.name) if action == ACTION_RECOMMEND else task_id,
		"task_token": cstr(approval_task.concurrency_token) if action == ACTION_RECOMMEND else cstr(terminal_task.concurrency_token),
	}


def has_recommendation(*, version: str) -> bool:
	return bool(
		frappe.db.exists(
			DOCTYPE_DECISION,
			{"plan_version": version, "decision": DECISION_RECOMMENDED},
		)
	)


def _actor_role(user: str, action: str) -> str:
	roles = actor_planning_roles(user)
	order = (
		(ROLE_REVIEWER, ROLE_AUTHORITY)
		if action == ACTION_RECOMMEND
		else (
			ROLE_DESIGNATED_APPROVER,
			ROLE_ACCOUNTING_OFFICER,
			ROLE_AUTHORITY,
			ROLE_REVIEWER,
		)
	)
	for role in order:
		if role in roles:
			return role
	return ROLE_REVIEWER
