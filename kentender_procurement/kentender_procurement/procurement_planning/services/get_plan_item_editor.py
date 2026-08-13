# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Projection for PLN-UI-06 Plan Item editor."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_procurement.procurement_planning.mvp1_constants import (
	ITEM_PROPOSED,
	VERSION_DRAFT,
	VERSION_EDITABLE_STATUSES,
	VERSION_RETURNED,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	READ_PLAN_ROLES,
	assert_planning_scope,
	is_planning_read_only,
	require_operational_roles,
)
from kentender_procurement.procurement_planning.services.plan_item_field_issues import (
	MILESTONE_FIELDS,
	collect_plan_item_field_issues,
)
from kentender_procurement.procurement_planning.services.get_plan_update import (
	plan_canvas_routes,
)
from kentender_procurement.procurement_planning.services.preference_reservation import (
	ELIGIBLE_GROUP_OPTIONS,
	SCHEME_OPTIONS,
	SCOPE_OPTIONS,
	format_money,
	parse_eligible_groups,
	scheme_is_assigned,
)


def _money(amount: float, currency: str = "KES") -> str:
	return format_money(amount, currency)


def _finance_label(iv: Any) -> str:
	from kentender_procurement.procurement_planning.services.plan_item_finance import (
		finance_status_label,
	)

	return finance_status_label(iv)


def _is_internal_id(value: str) -> bool:
	"""Hash-style Frappe names must never appear in Desk UI."""
	raw = cstr(value).strip()
	if not raw:
		return False
	# Business codes use separators / uppercase prefixes (RSV-, BUD-, …).
	if "-" in raw or " " in raw or raw != raw.lower():
		return False
	return len(raw) >= 8 and raw.isalnum()


def _funding_reservation_row(reservation_reference: str) -> dict[str, Any] | None:
	"""Resolve by business generated_reference or by Funding Reservation name."""
	ref = cstr(reservation_reference).strip()
	if not ref or not frappe.db.exists("DocType", "Funding Reservation"):
		return None
	fields = ["name", "generated_reference", "budget_line", "demand_title", "status"]
	row = frappe.db.get_value(
		"Funding Reservation",
		{"generated_reference": ref},
		fields,
		as_dict=True,
	)
	if row:
		return row
	if frappe.db.exists("Funding Reservation", ref):
		return frappe.db.get_value("Funding Reservation", ref, fields, as_dict=True)
	return None


def _funding_line_label(reservation_reference: str) -> str:
	"""Human funding line for Source Demand — never an internal primary key."""
	ref = cstr(reservation_reference).strip()
	if not ref:
		return ""
	row = _funding_reservation_row(ref)
	if not row:
		# Unknown token: hide hash IDs; allow business codes through.
		return "" if _is_internal_id(ref) else ref
	line = cstr(row.budget_line or "").strip()
	if line and frappe.db.exists("Budget Line", line):
		label = cstr(frappe.db.get_value("Budget Line", line, "title") or "").strip()
		if label and not _is_internal_id(label):
			return label
	generated = cstr(row.generated_reference or "").strip()
	if generated and not _is_internal_id(generated):
		return generated
	demand_title = cstr(row.demand_title or "").strip()
	if demand_title and not _is_internal_id(demand_title):
		return demand_title
	return ""


def _attention_message(
	*,
	iv: Any,
	fields: dict[str, Any],
	field_issues: dict[str, str] | None = None,
) -> str:
	"""Human issue copy for the editor attention panel — never a bare status label.

	Returns empty when the item is Ready / Not run so the red banner stays hidden.
	"""
	issues = field_issues or {}
	for key in MILESTONE_FIELDS:
		msg = cstr(issues.get(key) or "").strip()
		if msg:
			return msg
	if issues.get("lot_basis") or issues.get("expected_lot_count"):
		return cstr(
			issues.get("lot_basis")
			or issues.get("expected_lot_count")
			or "Confirm the indicative lot basis before submit for review."
		)
	lotting = cstr(fields.get("lotting_decision") or "").strip()
	if lotting == "Multiple lots" and not cstr(fields.get("lot_basis") or "").strip():
		return "Confirm the indicative lot basis before submit for review."
	missing_ms = [k for k in MILESTONE_FIELDS if not cstr(fields.get(k) or "").strip()]
	if missing_ms:
		# Default incomplete state — do not paint the red banner until Request Finance.
		return ""
	# Prefer concrete field issue copy over bare projection labels.
	for key in (
		"method_override_grounds",
		"method_override_reason",
		"method_override_evidence",
		"multi_year_justification",
		"annual_funding_schedule",
		"planned_reserved_value",
		"eligible_groups",
		"reservation_scope",
		"preference_reservation_scheme",
	):
		msg = cstr(issues.get(key) or "").strip()
		if msg:
			return msg
	proj = cstr(getattr(iv, "validation_projection", "") or "").strip()
	# Status labels must never become the banner body under "Needs attention".
	if proj == "Blocked":
		return "Resolve blocking validation issues before submit for review."
	if proj == "Stale":
		return "Re-run validation; this Plan Item projection is stale."
	if proj == "Needs attention" or issues:
		return "Review validation issues before submit for review."
	return ""


def _version_label(ver_num: int, status: str) -> str:
	st = cstr(status).strip()
	if st == VERSION_RETURNED:
		return f"Returned Plan Version {ver_num}"
	if st and st != VERSION_DRAFT:
		return f"Plan Version {ver_num} · {st}"
	return f"Draft Plan Version {ver_num}"


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
	funding_row = _funding_reservation_row(rsv_ref)
	funding_line = _funding_line_label(rsv_ref)
	# Prefer business reservation code for any downstream display; never the hash name.
	rsv_code = ""
	if funding_row:
		rsv_code = cstr(funding_row.generated_reference or "").strip()
	elif rsv_ref and not _is_internal_id(rsv_ref):
		rsv_code = rsv_ref
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
		"preference_reservation_scheme": cstr(iv.preference_reservation_scheme or ""),
		"reservation_scope": cstr(iv.reservation_scope or ""),
		"eligible_groups": parse_eligible_groups(iv.eligible_groups),
		"planned_reserved_value": flt(iv.planned_reserved_value),
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
	open_draft = cstr(plan.open_draft_version or "").strip()
	field_issues = collect_plan_item_field_issues(iv=iv, payload={}, include_preference=False)
	attention = _attention_message(iv=iv, fields=fields, field_issues=field_issues)
	scheme = cstr(fields["preference_reservation_scheme"] or "").strip()
	assigned = scheme_is_assigned(scheme)
	reserved_val = flt(fields["planned_reserved_value"]) if assigned else 0.0
	is_successor = bool(cstr(plan.current_approved_version or "").strip() and open_draft)
	ver_name = cstr(open_draft or plan.current_approved_version or "").strip()
	ver_num = 1
	ver_status = ""
	if ver_name:
		ver_row = frappe.db.get_value(
			"Procurement Plan Version",
			ver_name,
			["version_number", "status"],
			as_dict=True,
		)
		if ver_row:
			ver_num = int(ver_row.version_number or 1)
			ver_status = cstr(ver_row.status or "")
	editable_version = bool(open_draft) and ver_status in VERSION_EDITABLE_STATUSES
	if open_draft and not editable_version:
		attention = (
			f"This plan version is {ver_status}. "
			"Only Draft or Returned versions can be edited."
		)
	source_rows = _source_rows(allocs, currency)
	combined = len({a.demand for a in allocs if a.demand}) > 1

	return {
		"ok": True,
		"field_issues": field_issues,
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
		"can_edit": (not read_only) and editable_version,
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
			if is_successor
			else ""
		),
		"version_label": _version_label(ver_num, ver_status),
		"finance_status_label": _finance_label(iv),
		"formation_reason": cstr(iv.aggregation_reason or "").strip(),
		"source_rows": source_rows,
		"combined_sources": combined,
		"plan_crumb_label": plan_crumb or cstr(plan.financial_year or "Plan"),
		"attention_message": attention,
		"fields": fields,
		"preference_reservation": {
			"assigned": assigned,
			"scheme": scheme,
			"reservation_scope": fields["reservation_scope"],
			"eligible_groups": fields["eligible_groups"],
			"planned_reserved_value": reserved_val,
			"planned_reserved_value_display": _money(reserved_val, currency) if assigned else "",
			"contribution_note": (
				f"This contributes {_money(reserved_val, currency)} to the Plan’s calculated "
				"reservation coverage. It is a planned set-aside, not an award."
				if assigned and reserved_val > 0
				else ""
			),
			"scheme_options": list(SCHEME_OPTIONS),
			"scope_options": list(SCOPE_OPTIONS),
			"eligible_group_options": list(ELIGIBLE_GROUP_OPTIONS),
		},
		"approved_source": {
			"demand": demand_row.name if demand_row else None,
			"demand_code": demand_row.demand_code if demand_row else "",
			"title": demand_row.title if demand_row else "",
			"need_item_count": need_count,
			"funding_label": "Reserved" if rsv_ref else "Unreserved",
			"funding_line_label": funding_line or "—",
			"reservation_reference": rsv_code,
			"reservation_id": (funding_row.name if funding_row else None),
			"strategy_snapshot": strategy_text,
			"strategy_context": strategy_text,
			"pvc_snapshot": iv.pvc_snapshot or "",
			"owner_org_unit_label": demand_ou_label,
			"reserved_value_display": _money(flt(iv.confirmed_estimate), currency),
			"approved_value_display": _money(flt(iv.confirmed_estimate), currency),
		},
		"allocations": allocs,
		"source_allocation_summary": _source_allocation_summary(
			allocs, flt(iv.confirmed_estimate), currency
		),
		"can_add_another_demand": False,
		"builder_route": plan_canvas_routes(plan)["builder_route"],
		"demand_route": (
			f"/app/demand/{demand_row.name}" if demand_row and demand_row.name else ""
		),
		# ABS / AC-025: never claim realised savings.
		"aggregation_benefit_realised": False,
	}


def _source_rows(allocs: list[Any], currency: str) -> list[dict[str, Any]]:
	"""Per-Demand rows for combined Approved sources (PLN-UI-06)."""
	grouped: dict[str, dict[str, Any]] = {}
	order: list[str] = []
	for a in allocs:
		demand = cstr(getattr(a, "demand", None) or "").strip()
		if not demand:
			continue
		if demand not in grouped:
			title = ""
			code = ""
			owner = ""
			if frappe.db.exists("Demand", demand):
				drow = frappe.db.get_value(
					"Demand",
					demand,
					["title", "demand_code", "owner_org_unit"],
					as_dict=True,
				)
				title = cstr(drow.title or "")
				code = cstr(drow.demand_code or "")
				if drow.owner_org_unit:
					owner = cstr(
						frappe.db.get_value("Organisation Unit", drow.owner_org_unit, "unit_name")
						or drow.owner_org_unit
					)
			rsv = cstr(getattr(a, "reservation_reference", None) or "").strip()
			grouped[demand] = {
				"demand": demand,
				"demand_code": code,
				"title": title,
				"owner_org_unit_label": owner,
				"need_item_count": 0,
				"amount": 0.0,
				"budget_line_label": _funding_line_label(rsv) or "—",
				"demand_route": f"/app/demand/{demand}",
			}
			order.append(demand)
		grouped[demand]["need_item_count"] += 1
		grouped[demand]["amount"] += flt(getattr(a, "allocated_amount", 0))
	rows: list[dict[str, Any]] = []
	for demand in order:
		row = grouped[demand]
		amount = flt(row.pop("amount"))
		row["approved_value_display"] = _money(amount, currency)
		rows.append(row)
	return rows


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
