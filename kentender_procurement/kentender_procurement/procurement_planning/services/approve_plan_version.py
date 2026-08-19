# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Approve Plan Version — Gate 05: In review + recommend + Ready → atomic lock."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.mvp1_constants import (
	ALLOC_DRAFT,
	ALLOC_EFFECTIVE,
	DECISION_APPROVED,
	ITEM_ACTIVE,
	VALIDATION_READY,
	VERSION_APPROVABLE_STATUSES,
	VERSION_APPROVED,
	VERSION_SUPERSEDED,
)
from kentender_procurement.procurement_planning.services._invariants import (
	assert_version_concurrency,
	new_concurrency_token,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	APPROVE_PLAN_ROLES,
	CAP_PLAN_APPROVE,
	CAP_PLAN_RETURN,
	actor_planning_roles,
	assert_planning_scope,
)
from kentender_procurement.procurement_planning.services.planning_tasks import (
	authorize_planning_task,
	idempotent_decision,
	transition_planning_task,
)
from kentender_procurement.procurement_planning.services.validate_plan import validate_plan
from kentender_procurement.procurement_planning.services.remove_plan_item import (
	apply_proposed_removals_on_approval,
	assert_no_handoff_for_proposed_removals,
)
from kentender_procurement.procurement_planning.services.need_allocations import activate_need_allocations


def approve_plan_version(
	*,
	task: str | None = None,
	version: str | None = None,
	expected_token: str | None = None,
	idempotency_key: str | None = None,
	concurrency_token: str | None = None,
	reason: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	actor = (user or frappe.session.user or "").strip()
	task_id = cstr(task).strip()
	if not task_id:
		frappe.throw(_("A current review task is required."), frappe.PermissionError, title="PLN_TASK_REQUIRED")
	workflow_task = authorize_planning_task(
		task_id=task_id, actor=actor, capability=CAP_PLAN_APPROVE,
		subject_type="Procurement Plan Version",
	)
	version_name = cstr(workflow_task.subject_id)
	replay = idempotent_decision(idempotency_key)
	if replay:
		return replay

	ver = frappe.get_doc("Procurement Plan Version", version_name)
	if cstr(ver.review_task_id) != task_id:
		frappe.throw(_("Task not found."), frappe.PermissionError, title="PLN_TASK_NOT_FOUND")
	if ver.status not in VERSION_APPROVABLE_STATUSES:
		frappe.throw(
			_("Only an In review version can be approved."),
			title="PLN_VERSION_NOT_APPROVABLE",
		)

	plan = frappe.get_doc("Procurement Plan", ver.plan)
	assert_planning_scope(
		procuring_entity=cstr(plan.procuring_entity).strip(),
		org_unit=None,
		user=actor,
		require_write=True,
	)
	if plan.lifecycle_state != "Open":
		frappe.throw(_("Plan is not Open."), title="PLN_PLAN_NOT_OPEN")

	validation = validate_plan(plan=plan.name, user=actor)
	if cstr(validation.get("status")) != VALIDATION_READY:
		frappe.throw(
			_("Validation must be Ready before approval."),
			title="PLN_VALIDATION_NOT_READY",
		)

	from kentender_procurement.procurement_planning.services.plan_item_finance import (
		finance_not_confirmed_error,
	)

	finance_err = finance_not_confirmed_error(plan=plan.name, version=ver.name)
	if finance_err:
		frappe.throw(
			_(finance_err["form"]),
			title="PLN_FINANCE_NOT_CONFIRMED",
		)

	assert_no_handoff_for_proposed_removals(version=ver.name)
	prior_actions = []
	for decision in frappe.get_all("Plan Decision", filters={"plan_version": ver.name}, fields=["actor", "decision"]):
		capability = {
			"Recommended approval": "plan.recommend",
			"Submitted for review": "plan.submit",
		}.get(cstr(decision.decision))
		if capability:
			prior_actions.append({"user": cstr(decision.actor), "capability": capability})
	completed_task = transition_planning_task(
		task_id=task_id, actor=actor, capability=CAP_PLAN_APPROVE,
		target_state="Completed", expected_token=cstr(expected_token), prior_actions=prior_actions,
	)

	now = now_datetime()
	prior = cstr(plan.current_approved_version or "").strip()

	# Supersede prior approved
	if prior and prior != ver.name:
		prior_status = frappe.db.get_value("Procurement Plan Version", prior, "status")
		if prior_status == VERSION_APPROVED:
			frappe.db.set_value(
				"Procurement Plan Version",
				prior,
				{
					"status": VERSION_SUPERSEDED,
					"open_version_slot": None,
					"superseded_at": now,
					"concurrency_token": new_concurrency_token(),
				},
				update_modified=True,
			)

	# Flip Draft allocations proposed in this version → Effective once
	draft_allocs = frappe.get_all(
		"Plan Demand Allocation",
		filters={
			"proposed_in_version": ver.name,
			"status": ALLOC_DRAFT,
		},
		pluck="name",
	)
	for alloc_name in draft_allocs:
		alloc = frappe.get_doc("Plan Demand Allocation", alloc_name)
		if alloc.effective_from_version:
			frappe.throw(
				_("Allocation was already made effective."),
				title="PLN_ALLOC_ALREADY_EFFECTIVE",
			)
		alloc.status = ALLOC_EFFECTIVE
		alloc.effective_from_version = ver.name
		alloc.effective_at = now
		alloc.save(ignore_permissions=True)
		_write_planning_consumption(alloc)
	need_allocs = activate_need_allocations(version=ver.name)

	# Activate items that have item versions on this plan version (skip proposed removals)
	item_versions = frappe.get_all(
		"Procurement Plan Item Version",
		filters={"plan_version": ver.name},
		fields=["name", "plan_item", "proposed_removal"],
	)
	for iv in item_versions:
		if int(iv.proposed_removal or 0):
			continue
		frappe.db.set_value(
			"Procurement Plan Item",
			iv.plan_item,
			{
				"baseline_state": ITEM_ACTIVE,
				"current_approved_item_version": iv.name,
				"draft_item_version": None,
			},
			update_modified=False,
		)

	apply_proposed_removals_on_approval(version=ver.name, actor=actor)

	frappe.db.set_value(
		"Procurement Plan Version",
		ver.name,
		{
			"status": VERSION_APPROVED,
			"open_version_slot": None,
			"validation_projection": VALIDATION_READY,
			"effective_at": now,
			"approved_by": actor,
			"approved_at": now,
			"concurrency_token": new_concurrency_token(),
			"review_task_state": "Approved" if task_id else ver.review_task_state,
			"review_task_token": cstr(completed_task.concurrency_token),
		},
		update_modified=True,
	)

	frappe.db.set_value(
		"Procurement Plan",
		plan.name,
		{
			"current_approved_version": ver.name,
			"open_draft_version": None,
		},
		update_modified=False,
	)

	frappe.get_doc(
		{
			"doctype": "Plan Decision",
			"plan_version": ver.name,
			"decision_type": "Approval",
			"decision_stage": "Plan Version Approval",
			"actor": actor,
			"actor_role": _primary_planning_role(actor),
			"decision": DECISION_APPROVED,
			"reason": cstr(reason or "Approved"),
			"decided_at": now,
			"task_id": task_id or None,
			"task_iteration": int(ver.review_task_iteration or 0) or None,
			"command_idempotency_key": cstr(idempotency_key) or None,
		}
	).insert(ignore_permissions=True)

	return {
		"ok": True,
		"plan": plan.name,
		"version": ver.name,
		"version_code": ver.version_code,
		"status": VERSION_APPROVED,
		"allocations_effective": len(draft_allocs) + len(need_allocs),
		"need_allocations_effective": len(need_allocs),
		"superseded_version": prior or None,
		"approved_by": actor,
		"approved_at": str(now),
		"route": f"/app/procurement-plan-approved?plan={plan.name}",
	}


def return_plan_version(*, task: str, expected_token: str | None, reason: str | None, idempotency_key: str | None, user: str | None = None) -> dict[str, Any]:
	actor = (user or frappe.session.user or "").strip()
	note = cstr(reason).strip()
	if not note:
		return {"ok": False, "errors": {"reason": "A return reason is required."}}
	task_id = cstr(task).strip()
	workflow_task = authorize_planning_task(
		task_id=task_id, actor=actor, capability=CAP_PLAN_RETURN,
		subject_type="Procurement Plan Version",
	)
	version_name = cstr(workflow_task.subject_id)
	ver = frappe.get_doc("Procurement Plan Version", version_name)
	if cstr(ver.review_task_id) != task_id:
		frappe.throw(_("Task not found."), frappe.PermissionError, title="PLN_TASK_NOT_FOUND")
	replay = idempotent_decision(idempotency_key)
	if replay:
		return replay
	plan = frappe.get_doc("Procurement Plan", ver.plan)
	assert_planning_scope(procuring_entity=plan.procuring_entity, org_unit=None, user=actor, require_write=True)
	returned_task = transition_planning_task(
		task_id=task_id, actor=actor, capability=CAP_PLAN_RETURN,
		target_state="Returned", expected_token=cstr(expected_token),
	)
	now = now_datetime()
	frappe.db.set_value("Procurement Plan Version", ver.name, {"status": "Returned", "review_task_state": "Returned", "review_task_token": cstr(returned_task.concurrency_token), "concurrency_token": new_concurrency_token()}, update_modified=True)
	frappe.get_doc({"doctype": "Plan Decision", "plan_version": ver.name, "decision_type": "Professional review", "decision_stage": "Professional decision", "actor": actor, "actor_role": _primary_planning_role(actor), "decision": "Returned", "reason": note, "decided_at": now, "task_id": task_id, "task_iteration": int(ver.review_task_iteration or 1), "command_idempotency_key": cstr(idempotency_key)}).insert(ignore_permissions=True)
	return {"ok": True, "plan": plan.name, "version": ver.name, "status": "Returned", "route": f"/app/procurement-plan-builder?plan={plan.name}"}


def _primary_planning_role(user: str) -> str:
	roles = actor_planning_roles(user)
	for role in (
		"Designated Approver",
		"Accounting Officer",
		"Planning Authority",
	):
		if role in roles and role in APPROVE_PLAN_ROLES:
			return role
	return "Designated Approver"


def _write_planning_consumption(alloc) -> None:
	"""Create Planning Consumption for Effective allocation (Demands bridge)."""
	if not frappe.db.exists("DocType", "Planning Consumption"):
		return
	existing = frappe.db.exists(
		"Planning Consumption",
		{
			"demand": alloc.demand,
			"demand_item": alloc.demand_item,
			"plan_item_code": frappe.db.get_value(
				"Procurement Plan Item", alloc.plan_item, "plan_item_code"
			),
		},
	)
	plan_item_code = frappe.db.get_value(
		"Procurement Plan Item", alloc.plan_item, "plan_item_code"
	)
	values = {
		"demand": alloc.demand,
		"demand_item": alloc.demand_item,
		"plan_item_code": plan_item_code,
		"consumed_amount": alloc.allocated_amount,
		"consumed_quantity": alloc.allocated_quantity,
		"currency": alloc.currency,
		"consumed_by": frappe.session.user,
		"consumed_at": now_datetime(),
	}
	if existing:
		frappe.db.set_value("Planning Consumption", existing, values, update_modified=False)
	else:
		frappe.get_doc({"doctype": "Planning Consumption", **values}).insert(
			ignore_permissions=True
		)

	# Update Demand planning_usage when consumption exists
	if frappe.db.has_column("Demand", "planning_usage"):
		frappe.db.set_value(
			"Demand",
			alloc.demand,
			"planning_usage",
			"Fully planned",
			update_modified=False,
		)
