# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Home — Procuring Entity and Financial Year context."""

from __future__ import annotations

import re
from typing import Any

import frappe
from frappe import _

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


def _site_entity() -> str:
	"""The Procuring Entity this site is (AUTH-ADR-001 v1.11: one site is one Procuring Entity, configured once
	and never selected), as the name of its Procuring Entity record. Empty when the site has none configured."""
	code = _norm(frappe.db.get_single_value("Site Procuring Entity", "pe_code"))
	if not code:
		return ""
	if frappe.db.exists("Procuring Entity", code):
		return code
	return _norm(frappe.db.get_value("Procuring Entity", {"entity_code": code}, "name"))


def list_available_entities(user: str | None = None) -> list[dict[str, str]]:
	"""CTX-CHG-001 v1.1 §2: the site's own Procuring Entity, shown and never chosen. Who may read what Home
	composes is decided by the services Home calls, not by an entity picker."""
	name = _site_entity()
	return [_entity_display(name)] if name else []


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
	"""Resolve and validate the entity and Financial Year for Home. The entity is the site's own (CTX-CHG-001
	v1.1 §2); an explicit request for any other is refused. No global working-entity preference is read or written."""
	user = _norm(user) or _norm(frappe.session.user)
	entities = list_available_entities(user)
	if not entities:
		frappe.throw(_("No Procuring Entity is configured for this site."), frappe.PermissionError)
	selected_pe = entities[0]["id"]
	requested_pe = _norm(procuring_entity)
	if requested_pe and requested_pe != selected_pe:
		frappe.throw(_("You do not have access to that Procuring Entity."), frappe.PermissionError)

	years = list_available_fiscal_years(selected_pe)
	# CTX-CHG-001 rule 3 — Home's own per-module FY memory (kt_home_financial_year), a reversible filter that a
	# direct link or an explicit choice overrides. The vocabulary stays Home's int start year for now (CTX-FU-02).
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

	return {
		"procuring_entity": entities[0],
		"fiscal_year": selected_fy,
		"available_entities": entities,
		"available_fiscal_years": years,
		"show_entity_selector": False,
		"show_fiscal_year_selector": len(years) > 1,
	}
