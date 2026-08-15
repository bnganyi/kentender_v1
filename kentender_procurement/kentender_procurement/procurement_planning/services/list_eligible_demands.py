"""Available Approved Demands and Need Items for PLN-UI-04."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import frappe
from frappe.utils import cstr, flt, getdate

from kentender_procurement.procurement_planning.services.planning_permissions import (
	READ_PLAN_ROLES,
	assert_planning_scope,
	has_planning_scope,
	require_operational_roles,
)


def _money(value: float, currency: str) -> str:
	return f"{currency} {flt(value):,.2f}"


def _budget_context(row: Any, plan: Any, contexts: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], str | None]:
	line = cstr(row.budget_line if row else "").strip()
	if not line:
		return {"id": None, "display": "—"}, None
	data = contexts.get(line)
	if not data:
		return {"id": line, "display": line}, "Proposed Budget Line is no longer available."
	label = data.get("budget_line_name") or data.get("budget_line_code") or line
	code = data.get("budget_line_code") or ""
	display = f"{label} ({code})" if code and label != code else label
	if not int(data.get("is_active") or 0):
		return {"id": line, "display": display}, "Proposed Budget Line is not active."
	if cstr(data.get("procuring_entity")) != cstr(plan.procuring_entity):
		return {"id": line, "display": display}, "Proposed Budget Line belongs to another Procuring Entity."
	if cstr(data.get("fiscal_year")) not in (cstr(plan.financial_year), cstr(getattr(plan, "fiscal_year", ""))):
		return {"id": line, "display": display}, "Proposed Budget Line financial year does not match the Plan."
	return {"id": line, "display": display, "context": data}, None


def _project(*, plan: Any, actor: str, requested_demand: str = "") -> tuple[list[dict[str, Any]], dict[str, str] | None]:
	demand_rows = frappe.get_all(
		"Demand",
		filters={"procuring_entity": plan.procuring_entity, "status": "Approved", "planning_ready": 1},
		fields=["name", "demand_code", "title", "owner_org_unit", "delivery_org_unit", "required_by_date", "currency", "procurement_category", "need_statement", "planning_usage"],
		order_by="creation asc",
		limit_page_length=500,
	)
	requested = cstr(requested_demand).strip()
	if requested and not any(r.name == requested for r in demand_rows):
		# Do not disclose cross-PE or out-of-scope Demand details.
		return [], {"demand": requested, "code": "PLN_DEMAND_NOT_ELIGIBLE", "reason": "The requested Demand is not available in this Plan scope."}
	ids = [r.name for r in demand_rows]
	items = frappe.get_all(
		"Demand Item", filters={"demand": ["in", ids]},
		fields=["name", "demand", "item_code", "description", "confirmed_estimate", "requester_estimate", "confirmed_quantity", "quantity", "confirmed_uom", "uom", "currency", "required_by_date"],
		order_by="creation asc", limit_page_length=2000,
	) if ids else []
	holds = set(frappe.get_all(
		"Plan Demand Allocation", filters={"demand_item": ["in", [r.name for r in items]], "status": ["in", ["Draft", "Effective"]]}, pluck="demand_item", limit_page_length=2000,
	)) if items else set()
	funding_rows = frappe.get_all(
		"Demand Funding Allocation", filters={"demand": ["in", ids]},
		fields=["name", "demand", "budget_line", "funding_reservation"], limit_page_length=1000,
	) if ids and frappe.db.exists("DocType", "Demand Funding Allocation") else []
	funding_by_demand = {r.demand: r for r in funding_rows}
	from kentender_budget.api.dia_budget_control import get_budget_lines_context

	budget_contexts = (
		get_budget_lines_context([row.budget_line for row in funding_rows if row.budget_line]).get("data")
		or {}
	)
	items_by_demand: dict[str, list[Any]] = defaultdict(list)
	for item in items:
		if item.name not in holds:
			items_by_demand[item.demand].append(item)
	ou_ids = {cstr(r.owner_org_unit) for r in demand_rows if r.owner_org_unit}
	ou_labels = dict(frappe.get_all(
		"Organisation Unit", filters={"name": ["in", list(ou_ids)]}, fields=["name", "unit_name"], as_list=True,
	)) if ou_ids else {}

	out: list[dict[str, Any]] = []
	requested_reason: dict[str, str] | None = None
	for demand in demand_rows:
		ou = cstr(demand.owner_org_unit).strip()
		if not has_planning_scope(procuring_entity=plan.procuring_entity, org_unit=ou or None, user=actor, require_write=False):
			continue
		reason = None
		required = getdate(demand.required_by_date) if demand.required_by_date else None
		if not required or required < getdate(plan.period_start) or required > getdate(plan.period_end):
			reason = f"Required-by date must fall within FY {plan.financial_year}."
		funding, funding_reason = _budget_context(funding_by_demand.get(demand.name), plan, budget_contexts)
		reason = reason or funding_reason
		available_items = items_by_demand.get(demand.name, [])
		if not available_items and not reason:
			reason = "All Need Items are already held by an open Draft or allocated to an Approved Plan."
		if reason:
			if requested == demand.name:
				requested_reason = {"demand": demand.name, "code": "PLN_DEMAND_NOT_ELIGIBLE", "reason": reason}
			continue
		need_items: list[dict[str, Any]] = []
		available = 0.0
		for item in available_items:
			amount = flt(item.confirmed_estimate or item.requester_estimate)
			if amount <= 0:
				continue
			available += amount
			currency = cstr(item.currency or demand.currency or plan.currency or "KES")
			need_items.append({
				"id": item.name, "code": cstr(item.item_code), "description": cstr(item.description),
				"available_amount": amount, "available_amount_display": _money(amount, currency),
				"quantity": flt(item.confirmed_quantity or item.quantity),
				"uom": cstr(item.confirmed_uom or item.uom), "currency": currency,
			})
		if not need_items:
			continue
		currency = cstr(demand.currency or plan.currency or "KES")
		out.append({
			"demand": demand.name, "demand_code": cstr(demand.demand_code), "title": cstr(demand.title),
			"need_statement": cstr(demand.need_statement), "delivery_org_unit": cstr(demand.delivery_org_unit),
			"organisation_unit": ou, "organisation_unit_label": cstr(ou_labels.get(ou) or ou),
			"available_to_plan": available, "available_to_plan_display": _money(available, currency),
			"required_by": str(demand.required_by_date or ""), "status_label": "Planning Ready",
			"category": cstr(demand.procurement_category), "currency": currency,
			"need_item_count": len(need_items), "need_items": need_items,
			"proposed_funding": funding, "proposed_budget_line": funding.get("id"),
			"proposed_budget_line_display": funding.get("display") or "—",
		})
	return out, requested_reason


def list_eligible_demands(
	*, plan: str, search: str | None = None, organisation_unit: str | None = None,
	requested_demand: str | None = None, user: str | None = None,
) -> dict[str, Any]:
	actor = (user or frappe.session.user or "").strip()
	require_operational_roles(*READ_PLAN_ROLES, user=actor)
	plan_name = cstr(plan).strip()
	if not plan_name or not frappe.db.exists("Procurement Plan", plan_name):
		frappe.throw(frappe._("Procurement Plan not found."), title="PLN_PLAN_NOT_FOUND")
	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	assert_planning_scope(procuring_entity=plan_doc.procuring_entity, user=actor, require_write=False)
	demands, exclusion = _project(plan=plan_doc, actor=actor, requested_demand=cstr(requested_demand))
	q = cstr(search).strip().lower()
	ou = cstr(organisation_unit).strip()
	if ou and ou not in ("all", "__all__"):
		demands = [d for d in demands if d["organisation_unit"] == ou]
	if q:
		demands = [d for d in demands if q in f"{d['demand_code']} {d['title']} {d['organisation_unit_label']}".lower()]
	options = sorted({(d["organisation_unit"], d["organisation_unit_label"]) for d in demands}, key=lambda r: r[1])
	return {
		"ok": True, "plan": plan_name, "demands": demands, "requested_exclusion": exclusion,
		"organisation_unit_options": [{"id": key, "label": label} for key, label in options],
		"eligible_demand_count": len(demands),
		"available_need_item_count": sum(d["need_item_count"] for d in demands),
		"available_value": sum(flt(d["available_to_plan"]) for d in demands),
	}
