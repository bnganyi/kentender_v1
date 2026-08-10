# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-005 — Update Draft Plan Item Version decisions (PLN-UI-06)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt, getdate

from kentender_procurement.procurement_planning.mvp1_constants import (
	VALIDATION_NOT_RUN,
	VERSION_EDITABLE_STATUSES,
)
from kentender_procurement.procurement_planning.services._invariants import assert_version_mutable
from kentender_procurement.procurement_planning.services.planning_permissions import (
	assert_can_add_demand,
	assert_planning_scope,
)

_WRITABLE = (
	"requirement_description",
	"procurement_category",
	"procurement_method",
	"method_override_grounds",
	"method_override_reason",
	"method_override_evidence",
	"arrangement",
	"multi_year_justification",
	"annual_funding_schedule",
	# Package structure (aggregation_decision / reason) is set at Add Demand time — not editable here.
	"lotting_decision",
	"expected_lot_count",
	"lot_basis",
	"statutory_treatment",
	"statutory_target_groups",
	"planned_treatment_value",
	"value_treatment_note",
	"ms_invitation_published",
	"ms_tender_opening",
	"ms_evaluation_completed",
	"ms_award_approval",
	"ms_contract_signature",
	"ms_delivery_completion",
	"schedule_change_reason",
)

_MILESTONE_FIELDS = (
	"ms_invitation_published",
	"ms_tender_opening",
	"ms_evaluation_completed",
	"ms_award_approval",
	"ms_contract_signature",
	"ms_delivery_completion",
)


def update_plan_item(
	*,
	plan_item: str,
	fields: dict[str, Any] | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	actor = assert_can_add_demand(user)
	item_name = cstr(plan_item).strip()
	payload = fields or {}
	if not item_name or not frappe.db.exists("Procurement Plan Item", item_name):
		return {"ok": False, "errors": {"form": "Plan Item not found"}}

	item = frappe.get_doc("Procurement Plan Item", item_name)
	plan = frappe.get_doc("Procurement Plan", item.plan)
	assert_planning_scope(
		procuring_entity=cstr(plan.procuring_entity).strip(),
		org_unit=cstr(item.owner_org_unit or plan.coordinating_org_unit or "").strip() or None,
		user=actor,
		require_write=True,
	)
	draft = cstr(plan.open_draft_version or "").strip()
	if not draft:
		return {"ok": False, "errors": {"form": "Open a Draft revision before editing items."}}
	ver = frappe.get_doc("Procurement Plan Version", draft)
	assert_version_mutable(ver.status)
	if ver.status not in VERSION_EDITABLE_STATUSES:
		return {"ok": False, "errors": {"form": "Only Draft or Returned versions are editable."}}

	iv_name = cstr(item.draft_item_version or "").strip()
	if not iv_name:
		iv_name = frappe.db.get_value(
			"Procurement Plan Item Version",
			{"plan_item": item_name, "plan_version": draft},
			"name",
		)
	if not iv_name:
		return {"ok": False, "errors": {"form": "Draft Plan Item Version not found."}}

	iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
	errors: dict[str, str] = {}

	method = cstr(payload.get("procurement_method", iv.procurement_method) or "").strip()
	recommended = cstr(iv.recommended_method or "Open tender").strip() or "Open tender"
	if method and method != recommended:
		if not cstr(payload.get("method_override_grounds", iv.method_override_grounds) or "").strip():
			errors["method_override_grounds"] = "Alternative method requires configured grounds."
		if not cstr(payload.get("method_override_reason", iv.method_override_reason) or "").strip():
			errors["method_override_reason"] = "Alternative method requires a reason."
		if not cstr(payload.get("method_override_evidence", iv.method_override_evidence) or "").strip():
			errors["method_override_evidence"] = "Alternative method requires evidence."

	arrangement = cstr(payload.get("arrangement", iv.arrangement) or "").strip()
	if arrangement == "Multi-year":
		if not cstr(payload.get("multi_year_justification", iv.multi_year_justification) or "").strip():
			errors["multi_year_justification"] = "Multi-year arrangement requires justification."
		if not cstr(payload.get("annual_funding_schedule", iv.annual_funding_schedule) or "").strip():
			errors["annual_funding_schedule"] = "Multi-year arrangement requires an annual funding schedule."

	lotting = cstr(payload.get("lotting_decision", iv.lotting_decision) or "").strip()
	if lotting == "Multiple lots":
		count = int(payload.get("expected_lot_count", iv.expected_lot_count) or 0)
		if count < 2:
			errors["expected_lot_count"] = "Multiple lots requires an expected lot count of at least 2."
		if not cstr(payload.get("lot_basis", iv.lot_basis) or "").strip():
			errors["lot_basis"] = "Confirm the indicative lot basis before departmental sign-off."

	# Chronological milestones
	dates: list[tuple[str, Any]] = []
	for key in _MILESTONE_FIELDS:
		raw = payload.get(key, getattr(iv, key, None))
		if raw:
			try:
				dates.append((key, getdate(raw)))
			except Exception:
				errors[key] = "Invalid date."
	for i in range(1, len(dates)):
		if dates[i][1] < dates[i - 1][1]:
			errors[dates[i][0]] = "Milestone dates must be in chronological order."

	if errors:
		return {"ok": False, "errors": errors}

	for key in _WRITABLE:
		if key not in payload:
			continue
		val = payload[key]
		if key == "expected_lot_count":
			iv.set(key, int(val or 0))
		elif key == "planned_treatment_value":
			iv.set(key, flt(val))
		elif key in _MILESTONE_FIELDS:
			iv.set(key, getdate(val) if val else None)
		else:
			iv.set(key, val)

	if not cstr(iv.governing_regime or "").strip():
		iv.governing_regime = "PPADA"
	if not cstr(iv.recommended_method or "").strip():
		iv.recommended_method = "Open tender"
	if not cstr(iv.method_basis or "").strip():
		iv.method_basis = "Open tender is the preferred method under PPADA."
	iv.validation_projection = VALIDATION_NOT_RUN
	iv.save(ignore_permissions=True)
	frappe.db.commit()

	from kentender_procurement.procurement_planning.services.validate_plan import (
		validate_plan,
	)

	validation = validate_plan(plan=plan.name, user=actor)
	return {
		"ok": True,
		"plan_item": item_name,
		"item_version": iv.name,
		"validation": validation,
		"actor": actor,
	}
