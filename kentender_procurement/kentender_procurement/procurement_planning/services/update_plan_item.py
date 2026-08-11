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
from kentender_procurement.procurement_planning.services.preference_reservation import (
	dump_eligible_groups,
	parse_eligible_groups,
	scheme_is_assigned,
	validate_designation,
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
	"preference_reservation_scheme",
	"reservation_scope",
	"eligible_groups",
	"planned_reserved_value",
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
	field_issues = collect_plan_item_field_issues(
		iv=iv,
		payload=payload,
		include_preference=any(k in payload for k in PREF_KEYS),
	)

	for key in _WRITABLE:
		if key not in payload:
			continue
		if key in PREF_KEYS:
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

	if any(k in payload for k in PREF_KEYS):
		scheme = payload.get(
			"preference_reservation_scheme", iv.preference_reservation_scheme
		)
		scope = payload.get("reservation_scope", iv.reservation_scope)
		groups = payload.get("eligible_groups", iv.eligible_groups)
		planned = payload.get("planned_reserved_value", iv.planned_reserved_value)
		pref_errors, pref_norm = validate_designation(
			scheme=scheme,
			scope=scope,
			eligible_groups=groups,
			planned_reserved_value=planned,
			item_value=flt(iv.confirmed_estimate),
		)
		field_issues.update(pref_errors)
		if pref_norm:
			iv.preference_reservation_scheme = pref_norm["preference_reservation_scheme"]
			iv.reservation_scope = pref_norm["reservation_scope"]
			iv.eligible_groups = pref_norm["eligible_groups"]
			iv.planned_reserved_value = pref_norm["planned_reserved_value"]
		elif scheme_is_assigned(scheme):
			# Persist partial designation so Draft work is not discarded.
			iv.preference_reservation_scheme = cstr(scheme).strip()
			iv.reservation_scope = cstr(scope or "").strip()
			iv.eligible_groups = dump_eligible_groups(parse_eligible_groups(groups))
			iv.planned_reserved_value = flt(planned)
		else:
			iv.preference_reservation_scheme = ""
			iv.reservation_scope = ""
			iv.eligible_groups = dump_eligible_groups([])
			iv.planned_reserved_value = 0

	# Never write retired questionnaire fields from the editor API.
	iv.statutory_treatment = None
	iv.statutory_target_groups = None
	iv.planned_treatment_value = 0
	iv.value_treatment_note = None

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
	field_issues = collect_plan_item_field_issues(iv=iv, payload={}, include_preference=True)
	return {
		"ok": True,
		"plan_item": item_name,
		"item_version": iv.name,
		"field_issues": field_issues,
		"validation": validation,
		"actor": actor,
	}
