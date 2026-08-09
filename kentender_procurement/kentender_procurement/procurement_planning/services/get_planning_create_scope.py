# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Create-plan scope DTO for PLN-UI-02 (zero / single / multi PE)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services.org_scope_access import user_scope_rows
from kentender_procurement.procurement_planning.services._invariants import (
	period_dates_for_financial_year,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	CREATE_PLAN_ROLES,
	CREATE_SCOPE_ROLES,
	MODE_BLOCKED,
	MODE_MULTI,
	MODE_SINGLE,
	list_eligible_procuring_entities,
	require_operational_roles,
	resolve_pe_for_create,
)


def _ou_ref(ou: str) -> dict[str, str]:
	name = ou
	code = ou
	if ou and frappe.db.exists("Organisation Unit", ou):
		name = str(frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou)
		code = str(frappe.db.get_value("Organisation Unit", ou, "unit_code") or ou)
	return {"id": ou, "code": code, "name": name}


def list_eligible_coordinating_units(
	user: str | None = None,
	*,
	procuring_entity: str | None = None,
) -> list[dict[str, str]]:
	user = user or frappe.session.user
	pe = cstr(procuring_entity or "").strip()
	seen: set[str] = set()
	out: list[dict[str, str]] = []
	for row in user_scope_rows(user):
		if (row.get("role") or "") not in CREATE_SCOPE_ROLES:
			continue
		row_pe = cstr(row.get("procuring_entity") or "").strip()
		if pe and row_pe != pe:
			continue
		ou = cstr(row.get("organisation_unit") or "").strip()
		if not ou:
			# Entity-wide: offer all Active OUs under PE (capped).
			if not row_pe:
				continue
			for unit in frappe.get_all(
				"Organisation Unit",
				filters={"procuring_entity": row_pe, "status": "Active"},
				pluck="name",
				limit_page_length=40,
			):
				if unit in seen:
					continue
				seen.add(unit)
				out.append(_ou_ref(unit))
			continue
		if ou in seen:
			continue
		seen.add(ou)
		out.append(_ou_ref(ou))
	out.sort(key=lambda u: u["name"])
	return out


def get_planning_create_scope(
	*,
	selected_pe: str | None = None,
	financial_year: str | None = "2027/28",
	user: str | None = None,
) -> dict[str, Any]:
	actor = (user or frappe.session.user or "").strip()
	if not actor or actor == "Guest":
		frappe.throw(
			frappe._("Login required."),
			frappe.PermissionError,
			title="PLN_LOGIN_REQUIRED",
		)
	require_operational_roles(*CREATE_PLAN_ROLES, user=actor)

	scope = resolve_pe_for_create(actor, selected_pe)
	fy = cstr(financial_year or "2027/28").strip() or "2027/28"
	period_start, period_end = period_dates_for_financial_year(fy)
	entities = list_eligible_procuring_entities(actor)
	pe = scope.get("procuring_entity")
	units = list_eligible_coordinating_units(actor, procuring_entity=pe) if pe else []

	title_default = ""
	if pe:
		pe_name = next((e["name"] for e in entities if e["id"] == pe), pe)
		title_default = f"{pe_name} Annual Procurement Plan {fy}"

	currencies = [{"id": "KES", "label": "KES"}]
	return {
		"ok": True,
		"selection_mode": scope["selection_mode"],
		"procuring_entities": entities,
		"procuring_entity": pe,
		"blocked_reason": scope.get("blocked_reason"),
		"financial_year": fy,
		"financial_years": [
			{"id": "2027/28", "label": "2027/28"},
			{"id": "2028/29", "label": "2028/29"},
			{"id": "2026/27", "label": "2026/27"},
			{"id": "2029/30", "label": "2029/30"},
		],
		"period_start": period_start,
		"period_end": period_end,
		"period_label": f"Plan period: {period_start} – {period_end}",
		"title_default": title_default,
		"currencies": currencies,
		"currency": "KES",
		"currency_mode": "single_readonly" if len(currencies) == 1 else "multi_required",
		"coordinating_org_units": units,
		"coordinating_org_unit": units[0]["id"] if len(units) == 1 else None,
		"coordinating_org_unit_mode": (
			MODE_BLOCKED
			if not units
			else (MODE_SINGLE if len(units) == 1 else MODE_MULTI)
		),
		"helper_pe": "Choose the entity that owns this plan. This cannot be changed after the plan is created.",
		"helper_fy": "Derived from the configured financial year.",
		"helper_ou": (
			"Choose the unit authorised to coordinate procurement for this entity. "
			"It does not have to be the lowest organisation unit."
		),
		"single_pe_helper": "Assigned from your authorised scope.",
		"has_budget_fields": False,
	}
