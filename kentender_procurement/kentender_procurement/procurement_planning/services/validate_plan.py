# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-007 — Issue-led Draft plan validation (Gate 04 slice)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, getdate

from kentender_procurement.procurement_planning.mvp1_constants import (
	ITEM_PROPOSED,
	ITEM_ACTIVE,
	VALIDATION_BLOCKED,
	VALIDATION_NEEDS_ATTENTION,
	VALIDATION_NOT_RUN,
	VALIDATION_READY,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	READ_PLAN_ROLES,
	assert_planning_scope,
	require_operational_roles,
)

_MILESTONE_FIELDS = (
	("ms_invitation_published", "Invitation published"),
	("ms_tender_opening", "Tender opening"),
	("ms_evaluation_completed", "Evaluation completed"),
	("ms_award_approval", "Award approval"),
	("ms_contract_signature", "Contract signature"),
	("ms_delivery_completion", "Delivery and completion"),
)


def validate_plan(*, plan: str, user: str | None = None) -> dict[str, Any]:
	actor = (user or frappe.session.user or "").strip()
	require_operational_roles(*READ_PLAN_ROLES, user=actor)
	plan_name = cstr(plan).strip()
	if not plan_name or not frappe.db.exists("Procurement Plan", plan_name):
		frappe.throw(frappe._("Procurement Plan not found."), title="PLN_PLAN_NOT_FOUND")

	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	assert_planning_scope(
		procuring_entity=cstr(plan_doc.procuring_entity).strip(),
		org_unit=cstr(plan_doc.coordinating_org_unit or "").strip() or None,
		user=actor,
		require_write=False,
	)

	focus = cstr(plan_doc.open_draft_version or plan_doc.current_approved_version or "").strip()
	issues: list[dict[str, Any]] = []
	items = frappe.get_all(
		"Procurement Plan Item",
		filters={
			"plan": plan_name,
			"baseline_state": ["in", [ITEM_PROPOSED, ITEM_ACTIVE]],
		},
		fields=["name", "plan_item_code", "draft_item_version", "current_approved_item_version"],
	)

	for it in items:
		iv_name = None
		if focus:
			iv_name = frappe.db.get_value(
				"Procurement Plan Item Version",
				{"plan_item": it.name, "plan_version": focus},
				"name",
			)
		iv_name = iv_name or it.draft_item_version or it.current_approved_item_version
		if not iv_name:
			continue
		iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
		title = cstr(iv.requirement_title or it.plan_item_code)

		method = cstr(iv.procurement_method or "").strip()
		recommended = cstr(iv.recommended_method or "Open tender").strip() or "Open tender"
		if method and method != recommended:
			if not cstr(iv.method_override_grounds or "").strip() or not cstr(
				iv.method_override_reason or ""
			).strip():
				issues.append(
					_issue(
						it.name,
						title,
						"method",
						"Needs attention",
						"Confirm alternative method grounds, reason and evidence.",
						"Provide configured grounds, reason and evidence for the confirmed method.",
					)
				)

		if cstr(iv.arrangement or "") == "Multi-year" and (
			not cstr(iv.multi_year_justification or "").strip()
			or not cstr(iv.annual_funding_schedule or "").strip()
		):
			issues.append(
				_issue(
					it.name,
					title,
					"arrangement",
					"Needs attention",
					"Multi-year arrangement is incomplete.",
					"Add multi-year justification and annual funding schedule.",
				)
			)

		# Package structure is established at Add Demand (UI-04); do not require
		# editor aggregation_reason for Combine.

		if cstr(iv.lotting_decision or "") == "Multiple lots" and not cstr(
			iv.lot_basis or ""
		).strip():
			issues.append(
				_issue(
					it.name,
					title,
					"lot_basis",
					"Needs attention",
					"Confirm the indicative lot basis before departmental sign-off.",
					"Enter the lot basis for multiple indicative lots.",
				)
			)

		dates = []
		for field, label in _MILESTONE_FIELDS:
			raw = getattr(iv, field, None)
			if raw:
				dates.append((field, label, getdate(raw)))
		for i in range(1, len(dates)):
			if dates[i][2] < dates[i - 1][2]:
				issues.append(
					_issue(
						it.name,
						title,
						dates[i][0],
						"Blocked",
						f"{dates[i][1]} is before {dates[i - 1][1]}.",
						"Correct milestone dates so they are chronological.",
					)
				)

		# Persist per-item projection
		item_status = VALIDATION_READY
		item_issues = [i for i in issues if i["plan_item"] == it.name]
		if any(i["severity"] == "Blocked" for i in item_issues):
			item_status = VALIDATION_BLOCKED
		elif item_issues:
			item_status = VALIDATION_NEEDS_ATTENTION
		elif not cstr(iv.procurement_method or "").strip() or not any(
			getattr(iv, f, None) for f, _ in _MILESTONE_FIELDS
		):
			item_status = VALIDATION_NEEDS_ATTENTION
			if not item_issues:
				issues.append(
					_issue(
						it.name,
						title,
						"form",
						"Needs attention",
						"Complete method and schedule before departmental sign-off.",
						"Open the Plan Item editor and complete required decisions.",
					)
				)
		frappe.db.set_value(
			"Procurement Plan Item Version",
			iv_name,
			"validation_projection",
			item_status,
			update_modified=False,
		)

	plan_status = VALIDATION_READY
	if any(i["severity"] == "Blocked" for i in issues):
		plan_status = VALIDATION_BLOCKED
	elif issues:
		plan_status = VALIDATION_NEEDS_ATTENTION
	elif not items:
		plan_status = VALIDATION_NOT_RUN

	if focus and frappe.db.exists("Procurement Plan Version", focus):
		frappe.db.set_value(
			"Procurement Plan Version",
			focus,
			"validation_projection",
			plan_status,
			update_modified=False,
		)

	return {
		"ok": True,
		"plan": plan_name,
		"status": plan_status,
		"issue_count": len(issues),
		"issues": issues,
		# Users cannot set Ready — projection only.
		"user_may_set_ready": False,
	}


def _issue(
	plan_item: str,
	title: str,
	field: str,
	severity: str,
	reason: str,
	corrective_action: str,
) -> dict[str, Any]:
	return {
		"plan_item": plan_item,
		"title": title,
		"field": field,
		"severity": severity,
		"owner": "Procurement Planner",
		"reason": reason,
		"corrective_action": corrective_action,
	}
