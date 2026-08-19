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
	allowed = None  # PP2 pp_scope retired; unrestricted entity list
	if allowed is None:
		# Unrestricted users: prefer operational entities over demo PE clutter.
		preferred = ["PE-MOH", "PE-MOE"]
		active: set[str] = set()
		if demand_doctype_available():
			active = set(
				frappe.get_all("Demand", pluck="procuring_entity", distinct=True, limit=50)
				or []
			)
		if frappe.db.exists("DocType", "Budget") and frappe.db.has_column("Budget", "procuring_entity"):
			active |= set(
				frappe.get_all("Budget", pluck="procuring_entity", distinct=True, limit=50) or []
			)
		names = [p for p in preferred if frappe.db.exists("Procuring Entity", p)]
		for n in sorted(active):
			if n and n not in names and frappe.db.exists("Procuring Entity", n):
				names.append(n)
		if not names:
			names = frappe.get_all("Procuring Entity", pluck="name", order_by="entity_name asc", limit=20)
	else:
		names = sorted(allowed)
	return [_entity_display(n) for n in names if n]


def list_available_fiscal_years(procuring_entity: str | None = None) -> list[int]:
	"""Distinct FY start years from Budget rows (column is fiscal_period, not fiscal_year)."""
	out: list[int] = []
	if frappe.db.exists("DocType", "Budget"):
		filters: dict[str, Any] = {}
		if procuring_entity and frappe.db.has_column("Budget", "procuring_entity"):
			filters["procuring_entity"] = procuring_entity
		if frappe.db.has_column("Budget", "fiscal_period"):
			periods = frappe.get_all(
				"Budget",
				filters=filters or None,
				pluck="fiscal_period",
				distinct=True,
			)
			out = sorted(
				{y for p in periods if (y := year_from_fiscal_period(p)) is not None},
				reverse=True,
			)
		elif frappe.db.has_column("Budget", "fiscal_year"):
			years = frappe.get_all(
				"Budget",
				filters=filters or None,
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

	allowed_ids = {e["id"] for e in entities}
	requested_pe = _norm(procuring_entity)
	if requested_pe:
		if requested_pe not in allowed_ids:
			frappe.throw(_("You do not have access to that Procuring Entity."), frappe.PermissionError)
		selected_pe = requested_pe
	else:
		# Prefer user default PE when present.
		default_pe = ""
		if frappe.db.has_column("User", "kt_procuring_entity"):
			default_pe = _norm(frappe.db.get_value("User", user, "kt_procuring_entity"))
		if default_pe and default_pe in allowed_ids:
			selected_pe = default_pe
		else:
			# Prefer canonical MOH codes over alphabetically-first demo entities.
			ids = {e["id"] for e in entities}
			selected_pe = next(
				(c for c in ("PE-MOH", "PE-MOE") if c in ids),
				entities[0]["id"],
			)

	years = list_available_fiscal_years(selected_pe)
	requested_fy = None
	if fiscal_year not in (None, ""):
		try:
			requested_fy = int(fiscal_year)
		except (TypeError, ValueError):
			frappe.throw(_("Invalid financial year."), frappe.ValidationError)
		if requested_fy not in years:
			frappe.throw(_("You do not have access to that financial year."), frappe.PermissionError)
		selected_fy = requested_fy
	else:
		selected_fy = years[0]

	pe_display = next((e for e in entities if e["id"] == selected_pe), _entity_display(selected_pe))
	return {
		"procuring_entity": pe_display,
		"fiscal_year": selected_fy,
		"available_entities": entities,
		"available_fiscal_years": years,
		"show_entity_selector": len(entities) > 1,
		"show_fiscal_year_selector": len(years) > 1,
	}
