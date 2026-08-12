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


def submit_plan_for_review(
	*,
	plan: str,
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
			org_unit=cstr(plan_doc.coordinating_org_unit or "").strip() or None,
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

	try:
		assert_version_concurrency(version_name, concurrency_token)
	except frappe.ValidationError as exc:
		return {"ok": False, "errors": {"form": str(exc) or "Concurrency conflict"}}

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

	# C02: no Departmental Submission / contribution prerequisite.
	# C05 will add Finance-confirmed readiness (PLN-AC-009).

	now = now_datetime()
	token = new_concurrency_token()
	frappe.db.set_value(
		"Procurement Plan Version",
		version_name,
		{
			"status": VERSION_IN_REVIEW,
			"validation_projection": VALIDATION_READY,
			"concurrency_token": token,
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
		}
	).insert(ignore_permissions=True)

	frappe.db.commit()
	return {
		"ok": True,
		"plan": plan_name,
		"version": version_name,
		"status": VERSION_IN_REVIEW,
		"concurrency_token": token,
		"submitted_by": actor,
		"submitted_at": str(now),
	}
