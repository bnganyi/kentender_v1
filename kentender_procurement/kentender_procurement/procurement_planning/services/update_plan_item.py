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
from kentender_procurement.procurement_planning.services.plan_item_field_issues import (
	MILESTONE_FIELDS,
	PREF_KEYS,
	collect_plan_item_field_issues,
)
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
	# C02: preference/reservation no longer writable from Plan Item editor (coverage fields retained).
	"ms_invitation_published",
	"ms_tender_opening",
	"ms_evaluation_completed",
	"ms_award_approval",
	"ms_contract_signature",
	"ms_delivery_completion",
	"schedule_change_reason",
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

	# Soft field issues — Draft save must still persist; UI flags fields inline.
	# C02: preference keys in payload are ignored (not writable from editor).
	field_issues = collect_plan_item_field_issues(
		iv=iv,
		payload={k: v for k, v in payload.items() if k not in PREF_KEYS},
		include_preference=False,
	)

	for key in _WRITABLE:
		if key not in payload:
			continue
		val = payload[key]
		if key == "expected_lot_count":
			try:
				iv.set(key, int(val or 0))
			except (TypeError, ValueError):
				iv.set(key, 0)
		elif key in MILESTONE_FIELDS:
			if val:
				try:
					iv.set(key, getdate(val))
				except Exception:
					# Keep prior value; field_issues already marks Invalid date.
					pass
			else:
				iv.set(key, None)
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
	# Recompute against saved state so callers/UI stay aligned with persistence.
	field_issues = collect_plan_item_field_issues(iv=iv, payload={}, include_preference=False)
	return {
		"ok": True,
		"plan_item": item_name,
		"item_version": iv.name,
		"field_issues": field_issues,
		"validation": validation,
		"actor": actor,
	}
