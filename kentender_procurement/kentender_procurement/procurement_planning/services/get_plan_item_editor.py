# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Authoritative PLN-UI-06 Plan Item editor projection."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, date_diff, flt

from kentender_procurement.procurement_planning.mvp1_constants import VERSION_EDITABLE_STATUSES
from kentender_procurement.procurement_planning.services.plan_item_field_issues import MILESTONE_FIELDS, collect_plan_item_field_issues
from kentender_procurement.procurement_planning.services.planning_permissions import READ_PLAN_ROLES, assert_planning_scope, is_planning_read_only, require_operational_roles
from kentender_procurement.procurement_planning.services.procurement_method_catalogue import resolve_procurement_methods

CATEGORY_OPTIONS = (
	"Goods", "Works", "Non-Consulting Services",
	"Training and professional development services", "Consulting Services",
)


def _money(amount: float, currency: str) -> str:
	return f"{currency} {flt(amount):,.0f}"


def demand_desk_route(demand_name: str, status: str | None = None) -> str:
	if not cstr(demand_name).strip():
		return ""
	page = "demand-form" if cstr(status) == "Returned" else "demand-detail"
	return f"/app/{page}/{demand_name}"


def _budget_line_label(source_funding_allocation: str | None) -> str:
	"""Budget Line no longer carries a title directly (BUD-CHG-001 v1.2
	§4.3/§4.4) — title lives on the Active Budget Version's Budget Line
	Version."""
	dfa = cstr(source_funding_allocation or "").strip()
	if not dfa or not frappe.db.exists("Demand Funding Allocation", dfa):
		return "—"
	line = cstr(frappe.db.get_value("Demand Funding Allocation", dfa, "budget_line") or "")
	if not line or not frappe.db.exists("Budget Line", line):
		return "—"
	budget = cstr(frappe.db.get_value("Budget Line", line, "budget") or "")
	version_name = cstr(frappe.db.get_value("Budget Version", {"budget": budget, "status": "Active"}, "name") or "") if budget else ""
	title = cstr(frappe.db.get_value("Budget Line Version", {"budget_version": version_name, "budget_line": line}, "title") or "") if version_name else ""
	code = cstr(frappe.db.get_value("Budget Line", line, "generated_reference") or "")
	return title or code or line


def _source_rows(plan_item: str, currency: str) -> list[dict[str, Any]]:
	allocs = frappe.get_all(
		"Plan Demand Allocation", filters={"plan_item": plan_item, "status": ["in", ["Draft", "Effective"]]},
		fields=["demand", "demand_item", "allocated_amount", "allocated_quantity", "source_org_unit", "source_funding_allocation"],
		order_by="creation asc",
	)
	rows: list[dict[str, Any]] = []
	for alloc in allocs:
		demand = frappe.db.get_value("Demand", alloc.demand, ["demand_code", "title", "owner_org_unit", "required_by_date", "status", "strategy_no_alignment_reason"], as_dict=True) or frappe._dict()
		need = frappe.db.get_value("Demand Item", alloc.demand_item, ["item_code", "description", "confirmed_quantity", "quantity", "confirmed_uom", "uom", "required_by_date"], as_dict=True) or frappe._dict()
		ou = cstr(alloc.source_org_unit or demand.owner_org_unit or "")
		rows.append({
			"demand": alloc.demand, "demand_code": cstr(demand.demand_code or alloc.demand),
			"demand_title": cstr(demand.title), "demand_route": demand_desk_route(alloc.demand, demand.status),
			"need_item": alloc.demand_item, "need_item_code": cstr(need.item_code or alloc.demand_item),
			"need_item_description": cstr(need.description), "organisation_unit": ou,
			"organisation_unit_label": cstr(frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou),
			"quantity": flt(alloc.allocated_quantity or need.confirmed_quantity or need.quantity),
			"uom": cstr(need.confirmed_uom or need.uom),
			"required_by_date": str(need.required_by_date or demand.required_by_date or ""),
			"approved_value": flt(alloc.allocated_amount), "approved_value_display": _money(flt(alloc.allocated_amount), currency),
			"budget_line_label": _budget_line_label(alloc.source_funding_allocation),
			"strategy_alignment": cstr(demand.strategy_no_alignment_reason or "Approved Demand strategy context"),
		})
	return rows


def _finance_return_context(plan_item: str) -> dict[str, Any] | None:
	row = frappe.get_all("Plan Decision", filters={"plan_item": plan_item, "decision_stage": "Plan Item finance", "decision": "Returned"}, fields=["reason", "actor", "decided_at"], order_by="decided_at desc", limit=1)
	if not row:
		return None
	return {"reason": cstr(row[0].reason), "actor": cstr(row[0].actor), "decided_at": str(row[0].decided_at)}


def get_plan_item_editor(*, plan_item: str, user: str | None = None) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user).strip()
	require_operational_roles(*READ_PLAN_ROLES, user=actor)
	item_name = cstr(plan_item).strip()
	if not item_name or not frappe.db.exists("Procurement Plan Item", item_name):
		frappe.throw(frappe._("Plan Item not found."), title="PLN_ITEM_NOT_FOUND")
	item = frappe.get_doc("Procurement Plan Item", item_name)
	plan = frappe.get_doc("Procurement Plan", item.plan)
	assert_planning_scope(procuring_entity=cstr(plan.procuring_entity), org_unit=cstr(item.owner_org_unit or "") or None, user=actor, require_write=False)
	draft = cstr(plan.open_draft_version or "").strip()
	if not draft:
		frappe.throw(frappe._("This Plan Item has no editable Draft context."), title="PLN_NO_OPEN_DRAFT")
	ver = frappe.get_doc("Procurement Plan Version", draft)
	iv_name = cstr(item.draft_item_version or "").strip() or cstr(frappe.db.get_value("Procurement Plan Item Version", {"plan_item": item_name, "plan_version": draft}, "name") or "")
	if not iv_name:
		frappe.throw(frappe._("Draft Plan Item Version not found."), title="PLN_ITEM_VERSION_NOT_FOUND")
	iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
	currency = cstr(iv.currency or plan.currency or "KES")
	finance_status = cstr(iv.finance_status or "Not requested")
	can_edit = bool(not is_planning_read_only(actor) and cstr(ver.status) in VERSION_EDITABLE_STATUSES and finance_status != "Awaiting confirmation")
	method_contract = resolve_procurement_methods()
	selected_method = cstr(iv.procurement_method).strip() or method_contract["recommended"]
	fields = {
		"requirement_description": cstr(iv.requirement_description), "procurement_category": cstr(iv.procurement_category),
		"procurement_method": selected_method, "arrangement": cstr(iv.arrangement or "Single year"),
		"multi_year_justification": cstr(iv.multi_year_justification), "annual_funding_schedule": cstr(iv.annual_funding_schedule),
		"lotting_decision": cstr(iv.lotting_decision or "Single lot"), "expected_lot_count": int(iv.expected_lot_count or 1),
		"lot_basis": cstr(iv.lot_basis), **{key: str(getattr(iv, key, None) or "") for key in MILESTONE_FIELDS},
		"schedule_change_reason": cstr(iv.schedule_change_reason),
	}
	issues = collect_plan_item_field_issues(iv=iv, payload={}, include_preference=False)
	duration = date_diff(iv.ms_contract_signature, iv.ms_invitation_published) if iv.ms_invitation_published and iv.ms_contract_signature else None
	sources = _source_rows(item_name, currency)
	is_successor = bool(cstr(plan.current_approved_version or "").strip())
	version_status = cstr(ver.status or "Draft")
	version_label = f"Draft Version {int(ver.version_number or 1)}" if version_status == "Draft" else f"{version_status} Version {int(ver.version_number or 1)}"
	attention_message = ""
	if not can_edit:
		attention_message = f"This Plan Item is read-only while the Plan Version is {version_status}."
	elif issues:
		attention_message = "Review the highlighted fields, including the chronological milestone sequence."
	return {
		"ok": True, "surface": "PLN-UI-06", "plan": plan.name, "plan_code": cstr(plan.plan_code), "plan_title": cstr(plan.title),
		"financial_year": cstr(plan.financial_year), "period_start": str(plan.period_start or ""), "period_end": str(plan.period_end or ""),
		"version": ver.name, "version_label": version_label, "concurrency_token": cstr(ver.concurrency_token),
		"plan_item": item.name, "plan_item_code": cstr(item.plan_item_code), "item_version": iv.name,
		"lifecycle_label": cstr(item.baseline_state or "Proposed"), "requirement_title": cstr(iv.requirement_title),
		"planned_value": flt(iv.confirmed_estimate), "planned_value_display": _money(flt(iv.confirmed_estimate), currency), "currency": currency,
		"owner_org_unit": cstr(item.owner_org_unit or ""),
		"owner_org_unit_label": cstr(frappe.db.get_value("Organisation Unit", item.owner_org_unit, "unit_name") or item.owner_org_unit or frappe.db.get_value("Procuring Entity", plan.procuring_entity, "legal_name") or plan.procuring_entity),
		"finance_status": finance_status, "finance_status_label": finance_status, "validation_projection": cstr(iv.validation_projection or "Not run"),
		"can_edit": can_edit, "read_only": not can_edit, "attention_message": attention_message, "fields": fields, "field_issues": issues,
		"category_options": list(CATEGORY_OPTIONS), "method_options": method_contract["methods"],
		"method_recommendation": method_contract["recommended"],
		"method_recommendation_reason_code": method_contract["recommendation_reason_code"],
		"method_catalogue_source": method_contract["source"],
		"method_catalogue_degraded": method_contract["degraded"],
		"method_recommendation_warning": (
			"Selected method differs from the current catalogue recommendation."
			if selected_method != method_contract["recommended"] else ""
		),
		"source_rows": sources, "source_count": len({row["demand"] for row in sources}), "need_item_count": len(sources),
		"combined_sources": len({row["demand"] for row in sources}) > 1, "formation_reason": cstr(iv.aggregation_reason),
		"derived_days_to_contract_signature": duration,
		"finance_return_context": _finance_return_context(item_name) if finance_status == "Returned" else None,
		"back_route": f"/app/procurement-plan-builder?plan={plan.name}",
		"workspace_route": f"/app/planning-workspace?procuring_entity={plan.procuring_entity}&financial_year={plan.financial_year}",
	}
