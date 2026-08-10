# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Projection for PLN-UI-06 Plan Item editor."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_procurement.procurement_planning.mvp1_constants import ITEM_PROPOSED
from kentender_procurement.procurement_planning.services.planning_permissions import (
	READ_PLAN_ROLES,
	assert_planning_scope,
	is_planning_read_only,
	require_operational_roles,
)


def _money(amount: float, currency: str = "KES") -> str:
	return f"{currency} {flt(amount):,.2f}"


def _funding_line_label(reservation_reference: str) -> str:
	ref = cstr(reservation_reference).strip()
	if not ref:
		return ""
	if not frappe.db.exists("DocType", "Funding Reservation"):
		return ref
	row = frappe.db.get_value(
		"Funding Reservation",
		{"generated_reference": ref},
		["budget_line", "demand_title", "status"],
		as_dict=True,
	)
	if not row:
		return ref
	line = cstr(row.budget_line or "").strip()
	if line and frappe.db.exists("Budget Line", line):
		label = cstr(frappe.db.get_value("Budget Line", line, "title") or "").strip()
		if label:
			return label
	return cstr(row.demand_title or "").strip() or ref


def _attention_message(*, iv: Any, fields: dict[str, Any]) -> str:
	"""Surface the highest-priority editor attention copy for Needs attention panels."""
	lotting = cstr(fields.get("lotting_decision") or "").strip()
	if lotting == "Multiple lots" and not cstr(fields.get("lot_basis") or "").strip():
		return "Confirm the indicative lot basis before departmental sign-off."
	missing_ms = [
		k
		for k in (
			"ms_invitation_published",
			"ms_tender_opening",
			"ms_evaluation_completed",
			"ms_award_approval",
			"ms_contract_signature",
			"ms_delivery_completion",
		)
		if not cstr(fields.get(k) or "").strip()
	]
	if missing_ms:
		return "Confirm all milestone dates before departmental sign-off."
	proj = cstr(getattr(iv, "validation_projection", "") or "").strip()
	if proj and proj not in ("Not run", "Pass", "Passed"):
		return proj
	return ""


def get_plan_item_editor(*, plan_item: str, user: str | None = None) -> dict[str, Any]:
	actor = (user or frappe.session.user or "").strip()
	require_operational_roles(*READ_PLAN_ROLES, user=actor)
	item_name = cstr(plan_item).strip()
	if not item_name or not frappe.db.exists("Procurement Plan Item", item_name):
		frappe.throw(frappe._("Plan Item not found."), title="PLN_ITEM_NOT_FOUND")

	item = frappe.get_doc("Procurement Plan Item", item_name)
	plan = frappe.get_doc("Procurement Plan", item.plan)
	assert_planning_scope(
		procuring_entity=cstr(plan.procuring_entity).strip(),
		org_unit=cstr(item.owner_org_unit or "").strip() or None,
		user=actor,
		require_write=False,
	)

	focus = cstr(plan.open_draft_version or plan.current_approved_version or "").strip()
	iv_name = None
	if focus:
		iv_name = frappe.db.get_value(
			"Procurement Plan Item Version",
			{"plan_item": item_name, "plan_version": focus},
			"name",
		)
	iv_name = iv_name or item.draft_item_version or item.current_approved_item_version
	if not iv_name:
		frappe.throw(frappe._("Plan Item Version not found."), title="PLN_ITEM_VERSION_NOT_FOUND")
	iv = frappe.get_doc("Procurement Plan Item Version", iv_name)

	allocs = frappe.get_all(
		"Plan Demand Allocation",
		filters={"plan_item": item_name},
		fields=[
			"name",
			"demand",
			"demand_item",
			"allocated_amount",
			"status",
			"reservation_reference",
		],
	)
	primary_demand = allocs[0].demand if allocs else None
	demand_row = None
	if primary_demand and frappe.db.exists("Demand", primary_demand):
		demand_row = frappe.db.get_value(
			"Demand",
			primary_demand,
			["name", "demand_code", "title", "owner_org_unit", "status"],
			as_dict=True,
		)

	ou_label = ""
	if item.owner_org_unit:
		ou_label = cstr(
			frappe.db.get_value("Organisation Unit", item.owner_org_unit, "unit_name")
			or item.owner_org_unit
		)

	demand_ou_label = ou_label
	if demand_row and demand_row.owner_org_unit:
		demand_ou_label = cstr(
			frappe.db.get_value("Organisation Unit", demand_row.owner_org_unit, "unit_name")
			or demand_row.owner_org_unit
		)

	currency = cstr(iv.currency or plan.currency or "KES")
	read_only = is_planning_read_only(actor)
	rsv_ref = cstr(iv.reservation_reference or "").strip()
	funding_line = _funding_line_label(rsv_ref)
	need_count = len(allocs)
	fields = {
		"requirement_description": iv.requirement_description,
		"procurement_category": iv.procurement_category,
		"governing_regime": iv.governing_regime or "PPADA",
		"recommended_method": iv.recommended_method or "Open tender",
		"procurement_method": iv.procurement_method or "Open tender",
		"method_basis": iv.method_basis
		or "Open tender is the preferred method under PPADA.",
		"method_override_grounds": iv.method_override_grounds,
		"method_override_reason": iv.method_override_reason,
		"method_override_evidence": iv.method_override_evidence,
		"arrangement": iv.arrangement or "Single year",
		"multi_year_justification": iv.multi_year_justification,
		"annual_funding_schedule": iv.annual_funding_schedule,
		"aggregation_decision": cstr(iv.aggregation_decision or ""),
		"aggregation_reason": iv.aggregation_reason,
		"lotting_decision": iv.lotting_decision or "Single lot",
		"expected_lot_count": iv.expected_lot_count or 1,
		"lot_basis": iv.lot_basis,
		"statutory_treatment": iv.statutory_treatment,
		"statutory_target_groups": iv.statutory_target_groups,
		"planned_treatment_value": flt(iv.planned_treatment_value),
		"value_treatment_note": iv.value_treatment_note,
		"ms_invitation_published": str(iv.ms_invitation_published or ""),
		"ms_tender_opening": str(iv.ms_tender_opening or ""),
		"ms_evaluation_completed": str(iv.ms_evaluation_completed or ""),
		"ms_award_approval": str(iv.ms_award_approval or ""),
		"ms_contract_signature": str(iv.ms_contract_signature or ""),
		"ms_delivery_completion": str(iv.ms_delivery_completion or ""),
		"schedule_change_reason": iv.schedule_change_reason,
	}
	strategy_text = cstr(iv.strategy_snapshot or iv.pvc_snapshot or "").strip()
	plan_crumb = cstr(plan.title or plan.plan_code or plan.financial_year or "").strip()
	has_draft = bool(cstr(plan.open_draft_version or "").strip())
	attention = _attention_message(iv=iv, fields=fields)

	return {
		"ok": True,
		"plan": plan.name,
		"plan_code": plan.plan_code,
		"plan_title": plan.title,
		"financial_year": plan.financial_year,
		"plan_item": item.name,
		"plan_item_code": item.plan_item_code,
		"baseline_state": item.baseline_state,
		"lifecycle_label": cstr(item.baseline_state or ITEM_PROPOSED),
		"item_version": iv.name,
		"read_only": read_only,
		"can_edit": (not read_only) and has_draft,
		"requirement_title": iv.requirement_title,
		"requirement_description": iv.requirement_description,
		"confirmed_estimate": flt(iv.confirmed_estimate),
		"amount_display": _money(flt(iv.confirmed_estimate), currency),
		"currency": currency,
		"organisation_unit": item.owner_org_unit,
		"organisation_unit_label": ou_label,
		"validation_projection": iv.validation_projection or "Not run",
		"draft_banner": (
			"Draft Plan update · The current Approved Plan remains active."
			if has_draft
			else "Viewing Plan Item · Open a Draft revision to edit."
		),
		"plan_crumb_label": plan_crumb or cstr(plan.financial_year or "Plan"),
		"coverage_note": "Recalculated at Plan level after this item is saved",
		"attention_message": attention,
		"fields": fields,
		"approved_source": {
			"demand": demand_row.name if demand_row else None,
			"demand_code": demand_row.demand_code if demand_row else "",
			"title": demand_row.title if demand_row else "",
			"need_item_count": need_count,
			"funding_label": "Reserved" if rsv_ref else "Unreserved",
			"funding_line_label": funding_line or "—",
			"reservation_reference": rsv_ref,
			"strategy_snapshot": strategy_text,
			"pvc_snapshot": iv.pvc_snapshot or "",
			"owner_org_unit_label": demand_ou_label,
			"reserved_value_display": _money(flt(iv.confirmed_estimate), currency),
		},
		"allocations": allocs,
		"source_allocation_summary": _source_allocation_summary(
			allocs, flt(iv.confirmed_estimate), currency
		),
		"can_add_another_demand": (
			(not read_only)
			and has_draft
			and cstr(item.baseline_state) == ITEM_PROPOSED
		),
		"builder_route": f"/app/procurement-plan-builder?plan={plan.name}",
		"demand_route": (
			f"/app/demand/{demand_row.name}" if demand_row and demand_row.name else ""
		),
		# ABS / AC-025: never claim realised savings.
		"aggregation_benefit_realised": False,
	}


def _source_allocation_summary(
	allocs: list[Any], amount: float, currency: str
) -> str:
	demand_count = len({a.demand for a in allocs if a.demand})
	need_count = len(allocs)
	d_label = "Approved Demand" if demand_count == 1 else "Approved Demands"
	n_label = "Need Item" if need_count == 1 else "Need Items"
	return (
		f"{demand_count or 0} {d_label} · {need_count} {n_label} · "
		f"{_money(amount, currency)}"
	)
