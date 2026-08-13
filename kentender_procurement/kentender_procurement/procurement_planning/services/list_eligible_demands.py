# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-003 — Eligible Approved Demands for PLN-UI-04."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_procurement.procurement_planning.mvp1_constants import ALLOC_DRAFT, ALLOC_EFFECTIVE
from kentender_procurement.procurement_planning.services.planning_permissions import (
	READ_PLAN_ROLES,
	assert_planning_scope,
	has_planning_scope,
	require_operational_roles,
)


def _money(amount: float, currency: str = "KES") -> str:
	return f"{currency} {flt(amount):,.2f}"


def _already_planned_amount(demand: str) -> float:
	"""Effective + Draft allocations count toward 'already planned' for remaining availability."""
	total = 0.0
	for row in frappe.get_all(
		"Plan Demand Allocation",
		filters={
			"demand": demand,
			"status": ["in", [ALLOC_DRAFT, ALLOC_EFFECTIVE]],
		},
		fields=["allocated_amount"],
	):
		total += flt(row.allocated_amount)
	return total


def _ou_label(ou: str) -> str:
	if not ou:
		return ""
	return cstr(
		frappe.db.get_value("Organisation Unit", ou, "unit_name")
		or frappe.db.get_value("Organisation Unit", ou, "organisation_unit_name")
		or ou
	)


def _need_items_breakdown(demand: str, currency: str) -> list[dict[str, Any]]:
	rows = frappe.get_all(
		"Demand Item",
		filters={"demand": demand},
		fields=[
			"name",
			"item_code",
			"description",
			"confirmed_estimate",
			"requester_estimate",
			"currency",
		],
		order_by="creation asc",
	)
	out: list[dict[str, Any]] = []
	for r in rows:
		amt = flt(r.confirmed_estimate or r.requester_estimate)
		if amt <= 0:
			continue
		cur = cstr(r.currency or currency or "KES")
		out.append(
			{
				"id": r.name,
				"code": cstr(r.item_code or ""),
				"description": cstr(r.description or r.item_code or r.name),
				"available_amount": amt,
				"available_amount_display": _money(amt, cur),
				"currency": cur,
			}
		)
	return out


def _proposed_funding(demand: str) -> dict[str, str | None]:
	"""Budget Line identity for Proposed Funding column — never expose hash PK as display."""
	empty = {
		"id": None,
		"code": "",
		"name": "",
		"display": "—",
	}
	if not frappe.db.exists("DocType", "Demand Funding Allocation"):
		return empty
	row = frappe.db.get_value(
		"Demand Funding Allocation",
		{"demand": demand},
		["budget_line", "funding_reservation"],
		as_dict=True,
	)
	if not row:
		return empty
	line_id = cstr(row.budget_line or "").strip()
	if not line_id and row.funding_reservation:
		# Resolve Budget Line via Funding Reservation when DFA only stores RSV.
		from kentender_procurement.procurement_planning.services.get_plan_item_editor import (
			_funding_line_label,
		)

		label = _funding_line_label(cstr(row.funding_reservation))
		if label:
			return {"id": None, "code": "", "name": label, "display": label}
		return empty
	if not line_id or not frappe.db.exists("Budget Line", line_id):
		return empty
	title = cstr(frappe.db.get_value("Budget Line", line_id, "title") or "").strip()
	meta = frappe.get_meta("Budget Line")
	code = ""
	for field in ("generated_reference", "budget_line_code", "code"):
		if not meta.has_field(field):
			continue
		code = cstr(frappe.db.get_value("Budget Line", line_id, field) or "").strip()
		if code:
			break
	name = title or code or line_id
	# Never show internal hash as the primary display.
	if name == line_id and len(line_id) <= 12 and name.isalnum():
		return empty
	display = f"{name} ({code})" if code and name != code else name
	return {"id": line_id, "code": code, "name": name, "display": display or "—"}


def list_eligible_demands(
	*,
	plan: str,
	search: str | None = None,
	organisation_unit: str | None = None,
	category: str | None = None,
	remaining_only: bool | int = True,
	user: str | None = None,
) -> dict[str, Any]:
	actor = (user or frappe.session.user or "").strip()
	require_operational_roles(*READ_PLAN_ROLES, user=actor)
	plan_name = cstr(plan).strip()
	if not plan_name or not frappe.db.exists("Procurement Plan", plan_name):
		frappe.throw(frappe._("Procurement Plan not found."), title="PLN_PLAN_NOT_FOUND")

	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	pe = cstr(plan_doc.procuring_entity).strip()
	assert_planning_scope(
		procuring_entity=pe,
		org_unit=cstr(plan_doc.coordinating_org_unit or "").strip() or None,
		user=actor,
		require_write=False,
	)

	if not frappe.db.exists("DocType", "Demand"):
		return {"ok": True, "plan": plan_name, "demands": []}

	filters: dict[str, Any] = {
		"procuring_entity": pe,
		"status": "Approved",
		"planning_ready": 1,
	}
	ou_filter = cstr(organisation_unit or "").strip()
	if ou_filter and ou_filter not in ("all", "__all__"):
		filters["owner_org_unit"] = ou_filter
	cat_filter = cstr(category or "").strip()
	if cat_filter and cat_filter not in ("all", "__all__"):
		filters["procurement_category"] = cat_filter

	rows = frappe.get_all(
		"Demand",
		filters=filters,
		fields=[
			"name",
			"demand_code",
			"title",
			"status",
			"owner_org_unit",
			"confirmed_estimate",
			"requester_estimate",
			"currency",
			"planning_usage",
			"procurement_category",
			"required_by_date",
		],
		order_by="modified desc",
		limit_page_length=100,
	)

	q = cstr(search or "").strip().lower()
	want_remaining = bool(int(remaining_only)) if remaining_only is not None else True
	out: list[dict[str, Any]] = []
	for r in rows:
		ou = cstr(r.owner_org_unit or "").strip()
		if not has_planning_scope(
			procuring_entity=pe, org_unit=ou or None, user=actor, require_write=False
		):
			continue
		usage = cstr(r.planning_usage or "Not taken up")
		if usage == "Fully planned":
			continue
		approved = flt(r.confirmed_estimate or r.requester_estimate)
		planned = _already_planned_amount(r.name)
		available = max(approved - planned, 0.0)
		if want_remaining and available <= 0:
			continue
		title = cstr(r.title or "")
		code = cstr(r.demand_code or "")
		if q and q not in title.lower() and q not in code.lower() and q not in ou.lower():
			continue
		currency = cstr(r.currency or plan_doc.currency or "KES")
		funding = "Reserved"
		rsv = frappe.db.get_value(
			"Demand Funding Allocation",
			{"demand": r.name},
			"funding_reservation",
		)
		if not rsv:
			funding = "Unreserved"
		need_items = _need_items_breakdown(r.name, currency)
		proposed = _proposed_funding(r.name)
		out.append(
			{
				"demand": r.name,
				"demand_code": code,
				"title": title,
				"organisation_unit": ou,
				"organisation_unit_label": _ou_label(ou),
				"approved_amount": approved,
				"approved_amount_display": _money(approved, currency),
				"already_planned": planned,
				"already_planned_display": _money(planned, currency),
				"available_to_plan": available,
				"available_to_plan_display": _money(available, currency),
				"required_by": str(r.required_by_date or ""),
				"funding": funding,
				"proposed_funding": proposed,
				"proposed_budget_line": proposed.get("id"),
				"proposed_budget_line_name": proposed.get("name") or "",
				"proposed_budget_line_code": proposed.get("code") or "",
				"proposed_budget_line_display": proposed.get("display") or "—",
				"status_label": "Planning Ready",
				"category": cstr(r.procurement_category or ""),
				"currency": currency,
				"need_item_count": len(need_items),
				"need_items": need_items,
			}
		)

	return {"ok": True, "plan": plan_name, "demands": out}
