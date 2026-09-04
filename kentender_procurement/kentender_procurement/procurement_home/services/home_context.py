# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Home — Procuring Entity and Financial Year context."""

from __future__ import annotations

import re
from typing import Any

import frappe
from frappe import _

from kentender_procurement.procurement_lifecycle.demand_module_gate import (
	demand_doctype_available,
)

_YEAR_RE = re.compile(r"(\d{4})")


def _norm(value: str | None) -> str:
	return (value or "").strip()


def year_from_fiscal_period(value: Any) -> int | None:
	"""Map Budget.fiscal_period (e.g. 2026/27) or legacy int year → calendar start year."""
	if value in (None, ""):
		return None
	if isinstance(value, int):
		return value
	try:
		return int(value)
	except (TypeError, ValueError):
		pass
	match = _YEAR_RE.search(str(value).strip())
	return int(match.group(1)) if match else None


def _entity_display(name: str) -> dict[str, str]:
	code = ""
	label = name
	if frappe.db.exists("Procuring Entity", name):
		row = frappe.db.get_value(
			"Procuring Entity",
			name,
			["name", "entity_code", "entity_name"],
			as_dict=True,
		) or {}
		code = _norm(row.get("entity_code")) or _norm(row.get("name"))
		label = _norm(row.get("entity_name")) or code or name
	return {"id": name, "code": code or name, "name": label}


def list_available_entities(user: str | None = None) -> list[dict[str, str]]:
	# CTX-CHG-001 rule 1 — the offer is permission-derived: the one canonical
	# eligibility rule (permitted_procuring_entities; None = unrestricted).
	# The previous version offered EVERY user the same unfiltered list.
	from kentender_core.services.org_scope_access import permitted_procuring_entities

	allowed = permitted_procuring_entities(_norm(user) or frappe.session.user)
	if allowed is None:
		# Unrestricted users: prefer operational entities over demo PE clutter.
		preferred = ["PE-MOH", "PE-MOE"]
		active: set[str] = set()
		if demand_doctype_available():
			active = set(
				frappe.get_all("Demand", pluck="procuring_entity", distinct=True, limit=50)
				or []
			)
		if frappe.db.exists("DocType", "Procurement Budget") and frappe.db.has_column("Procurement Budget", "procuring_entity"):
			active |= set(
				frappe.get_all("Procurement Budget", pluck="procuring_entity", distinct=True, limit=50) or []
			)
		names = [p for p in preferred if frappe.db.exists("Procuring Entity", p)]
		for n in sorted(active):
			if n and n not in names and frappe.db.exists("Procuring Entity", n):
				names.append(n)
		if not names:
			names = frappe.get_all("Procuring Entity", pluck="name", order_by="entity_name asc", limit=20)
	else:
		names = [
			n for n in sorted(allowed)
			if frappe.db.get_value("Procuring Entity", n, "status") == "Active"
		]
	return [_entity_display(n) for n in names if n]


def list_available_fiscal_years(procuring_entity: str | None = None) -> list[int]:
	"""Distinct FY start years from Budget rows.

	BUD-CHG-001 v1.3 Phase 4: `Procurement Budget` is keyed by the real
	ERPNext `fiscal_year` (e.g. "2027-2028") — there is no `fiscal_period`
	column (there never was) and no `procuring_entity` column any more (one
	site is one Procuring Entity); `procuring_entity` is accepted only for
	this function's own external callers' backward compatibility and is
	otherwise unused."""
	out: list[int] = []
	if frappe.db.exists("DocType", "Procurement Budget") and frappe.db.has_column("Procurement Budget", "fiscal_year"):
		years = frappe.get_all(
			"Procurement Budget",
			pluck="fiscal_year",
			distinct=True,
			order_by="fiscal_year desc",
		)
		out = sorted(
			{y for raw in years if (y := year_from_fiscal_period(raw)) is not None},
			reverse=True,
		)
	if not out:
		from frappe.utils import now_datetime

		out = [int(now_datetime().year)]
	return out


def resolve_home_context(
	procuring_entity: str | None = None,
	fiscal_year: int | str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""Resolve and validate PE/FY for Home. Raises PermissionError on unauthorized selection."""
	user = _norm(user) or _norm(frappe.session.user)
	entities = list_available_entities(user)
	if not entities:
		frappe.throw(_("No Procuring Entity is available for this user."), frappe.PermissionError)

	from kentender_core.services.working_context import get_working_pe, select_working_pe

	allowed_ids = {e["id"] for e in entities}
	requested_pe = _norm(procuring_entity)
	if requested_pe:
		if requested_pe not in allowed_ids:
			frappe.throw(_("You do not have access to that Procuring Entity."), frappe.PermissionError)
		selected_pe = requested_pe
		# CTX-CHG-001 rule 5 — an explicit pick is remembered as the GLOBAL
		# working PE (persistence never breaks a read).
		try:
			select_working_pe(selected_pe, user)
		except frappe.PermissionError:
			frappe.clear_last_message()
	else:
		# CTX-CHG-001 rule 2 — the global working PE preference; the retired
		# User.kt_procuring_entity custom field is migrated into it.
		try:
			working = get_working_pe(user)["selected"]
		except frappe.PermissionError:
			working = None
		if working and working["id"] in allowed_ids:
			selected_pe = working["id"]
		else:
			# Prefer canonical MOH codes over alphabetically-first demo entities.
			ids = {e["id"] for e in entities}
			selected_pe = next(
				(c for c in ("PE-MOH", "PE-MOE") if c in ids),
				entities[0]["id"],
			)

	years = list_available_fiscal_years(selected_pe)
	# CTX-CHG-001 rule 3 — Home's own per-module FY memory
	# (kt_home_financial_year). The vocabulary stays Home's int start year for
	# now (opaque to the core service); unifying onto governed Financial Year
	# docnames is the recorded CTX-FU-02 follow-up.
	from kentender_core.services.working_context import get_module_fy

	requested_fy = None
	if fiscal_year not in (None, ""):
		try:
			requested_fy = int(fiscal_year)
		except (TypeError, ValueError):
			frappe.throw(_("Invalid financial year."), frappe.ValidationError)
		if requested_fy not in years:
			frappe.throw(_("You do not have access to that financial year."), frappe.PermissionError)
	fy_state = get_module_fy(
		"home",
		user,
		requested=str(requested_fy) if requested_fy is not None else None,
		offered=[str(y) for y in years],
	)
	selected_fy = int(fy_state["selected"]["id"]) if fy_state["selected"] else years[0]

	pe_display = next((e for e in entities if e["id"] == selected_pe), _entity_display(selected_pe))
	return {
		"procuring_entity": pe_display,
		"fiscal_year": selected_fy,
		"available_entities": entities,
		"available_fiscal_years": years,
		"show_entity_selector": len(entities) > 1,
		"show_fiscal_year_selector": len(years) > 1,
	}
