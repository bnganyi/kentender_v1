# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-009 — Submit Draft/Returned Plan Version for professional review."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.mvp1_constants import (
	DECISION_SUBMITTED_FOR_REVIEW,
	DOCTYPE_DECISION,
	DOCTYPE_ITEM,
	ITEM_ACTIVE,
	ITEM_PROPOSED,
	VALIDATION_READY,
	VERSION_IN_REVIEW,
	VERSION_SUBMITTABLE_FOR_REVIEW,
)
from kentender_procurement.procurement_planning.services._invariants import (
	assert_version_concurrency,
	new_concurrency_token,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	assert_can_submit_for_review,
	assert_planning_scope,
)
from kentender_procurement.procurement_planning.services.validate_plan import validate_plan
from kentender_procurement.procurement_planning.services.remove_plan_item import (
	draft_has_effective_changes,
)


def submit_plan_for_review(
	*,
	plan: str,
	expected_token: str | None = None,
	idempotency_key: str | None = None,
	concurrency_token: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	actor = assert_can_submit_for_review(user)
	plan_name = cstr(plan).strip()
	if not plan_name or not frappe.db.exists("Procurement Plan", plan_name):
		return {"ok": False, "errors": {"form": "Procurement Plan not found"}}

	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	try:
		assert_planning_scope(
			procuring_entity=cstr(plan_doc.procuring_entity).strip(),
			org_unit=None,
			user=actor,
			require_write=True,
		)
	except frappe.PermissionError:
		return {"ok": False, "errors": {"form": "Not permitted for this organisational scope"}}

	if cstr(plan_doc.lifecycle_state) != "Open":
		return {"ok": False, "errors": {"form": "Plan is not Open."}}

	version_name = cstr(plan_doc.open_draft_version or "").strip()
	if not version_name:
		return {
			"ok": False,
			"errors": {"form": "Open a Draft or Returned revision before submitting for review."},
		}

	ver = frappe.get_doc("Procurement Plan Version", version_name)
	if cstr(ver.status) not in VERSION_SUBMITTABLE_FOR_REVIEW:
		return {
			"ok": False,
			"errors": {
				"form": f"Only Draft or Returned versions can be submitted for review (now {ver.status})."
			},
		}

	key = cstr(idempotency_key).strip()
	if not key:
		return {"ok": False, "errors": {"form": "An idempotency key is required."}}
	existing = frappe.db.get_value("Plan Decision", {"command_idempotency_key": key}, "name")
	if existing:
		return {"ok": True, "idempotent": True, "decision": existing, "version": version_name, "task": cstr(ver.review_task_id)}
	try:
		assert_version_concurrency(version_name, expected_token or concurrency_token)
	except frappe.ValidationError as exc:
		return {"ok": False, "errors": {"form": str(exc) or "Concurrency conflict"}}

	from kentender_procurement.procurement_planning.services.plan_builder_successor import (
		planner_update_reason,
	)

	if cstr(plan_doc.current_approved_version or "").strip() and not planner_update_reason(
		ver.version_reason
	):
		return {
			"ok": False,
			"errors": {
				"update_reason": "Enter a reason for this update after Plan approval before submitting for review."
			},
		}

	validation = validate_plan(plan=plan_name, user=actor)
	if cstr(validation.get("status")) != VALIDATION_READY:
		return {
			"ok": False,
			"errors": {
				"form": "Resolve validation issues until the plan is Ready before submitting for review."
			},
		}

	item_count = frappe.db.count(
		DOCTYPE_ITEM,
		{
			"plan": plan_name,
			"baseline_state": ["in", [ITEM_PROPOSED, ITEM_ACTIVE]],
		},
	)
	if not item_count:
		return {
			"ok": False,
			"errors": {"form": "Add at least one Plan Item before submitting for review."},
		}

	if cstr(plan_doc.current_approved_version or "").strip() and not draft_has_effective_changes(
		plan=plan_name, version=version_name
	):
		return {
			"ok": False,
			"errors": {"form": "No changes remain on this update. Cancel the update or add a change before submitting."},
		}

	# C02: no Departmental Submission / contribution prerequisite.
	from kentender_procurement.procurement_planning.services.plan_item_finance import (
		finance_not_confirmed_error,
	)

	finance_err = finance_not_confirmed_error(plan=plan_name, version=version_name)
	if finance_err:
		return {"ok": False, "errors": finance_err}

	now = now_datetime()
	token = new_concurrency_token()
	from kentender_procurement.procurement_planning.services.planning_tasks import next_task_identity, resolve_single_assignee
	assignee = resolve_single_assignee(role="Designated Approver", procuring_entity=cstr(plan_doc.procuring_entity))
	predecessor = cstr(getattr(ver, "review_task_id", ""))
	task_id, iteration, task_token = next_task_identity(prefix="PLN-REV", record=ver, id_field="review_task_id", iteration_field="review_task_iteration")
	frappe.db.set_value(
		"Procurement Plan Version",
		version_name,
		{
			"status": VERSION_IN_REVIEW,
			"open_version_slot": plan_doc.name,
			"validation_projection": VALIDATION_READY,
			"concurrency_token": token,
			"review_task_id": task_id,
			"review_task_iteration": iteration,
			"review_task_assignee": assignee,
			"review_task_state": "Open",
			"review_task_predecessor": predecessor or None,
			"review_task_token": task_token,
			"submitted_by": actor,
			"submitted_at": now,
		},
		update_modified=True,
	)

	frappe.get_doc(
		{
			"doctype": DOCTYPE_DECISION,
			"plan_version": version_name,
			"decision_type": "Submission",
			"decision_stage": "Submit for review",
			"actor": actor,
			"actor_role": "Procurement Planner",
			"decision": DECISION_SUBMITTED_FOR_REVIEW,
			"reason": "Submitted for professional review",
			"decided_at": now,
			"task_id": task_id,
			"task_iteration": iteration,
			"command_idempotency_key": key,
		}
	).insert(ignore_permissions=True)

	frappe.db.commit()
	from kentender_procurement.procurement_planning.services.planning_notification_service import (
		notify_plan_submitted,
	)

	notify_plan_submitted(plan=plan_doc, version_name=version_name, actor=actor)
	return {
		"ok": True,
		"plan": plan_name,
		"version": version_name,
		"status": VERSION_IN_REVIEW,
		"open_version_slot": plan_doc.name,
		"concurrency_token": token,
		"task": task_id,
		"task_token": task_token,
		"assignee": assignee,
		"submitted_by": actor,
		"submitted_at": str(now),
	}
