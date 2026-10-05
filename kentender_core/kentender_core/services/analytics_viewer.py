"""ANL-CHG-001 v0.8 §6, D-ANL-10, KT-STD-001 v1.22 §3A.6 — who is looking at Analytics.

Analytics grants no record permission: each owner's provider decides what the
actor may know (`analytics_contract`). This module only describes the viewer
for the page: whether they are an internal user, a technical reader (who reads
every tab site-wide, read-only), whether their scope is site-wide or limited to
Organisation Units, and which departments they may choose in the filter.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import frappe
from frappe.utils import cstr, getdate

from kentender_core.services import authorization, home_viewer
from kentender_core.services.business_role_registry import SCOPE_SITE, scope_type


def describe(user: str, at: datetime) -> dict[str, Any]:
	"""``internal``, ``technical`` (Administrator, System Manager, Technical
	Operator: D-ANL-10 — never forbidden, never an action), ``site_wide`` and
	``units`` (the Organisation Units the viewer's responsibilities cover with
	their descendants; ``None`` means every unit)."""
	internal = home_viewer.is_internal(user)
	if not internal:
		return {"internal": False, "technical": False, "site_wide": False, "units": set()}
	technical = home_viewer.is_technical_reader(user, at)
	rows = authorization.active_assignment_rows(user, at)
	site_wide = technical or any(scope_type(row["business_role"]) == SCOPE_SITE for row in rows)
	units: set[str] | None = None
	if not site_wide:
		units = authorization.descendants_of({row["organisation_unit"] for row in rows if row.get("organisation_unit")})
	return {"internal": True, "technical": technical, "site_wide": site_wide, "units": units}


def unit_label(unit: str) -> str:
	return cstr(frappe.db.get_value("Organisation Unit", unit, "unit_name") or unit)


def unit_labels(units: set[str]) -> dict[str, str]:
	if not units:
		return {}
	rows = frappe.get_all("Organisation Unit", filters={"name": ["in", sorted(units)]}, fields=["name", "unit_name", "parent_organisation_unit"], limit_page_length=0)
	return {row["name"]: cstr(row["unit_name"] or row["name"]) for row in rows}


def selectable_unit(unit: str, viewer: dict[str, Any]) -> bool:
	"""§8: a department must exist and lie in the viewer's permitted area."""
	if not unit or not frappe.db.exists("Organisation Unit", unit):
		return False
	return viewer["units"] is None or unit in viewer["units"]


def unit_scope(unit: str) -> set[str]:
	"""A selected department with its descendants (a record attributed to a
	child unit belongs to the parent department's selection)."""
	return authorization.descendants_of({unit}) if unit else set()


def root_units() -> set[str]:
	"""The Procuring Entity root(s): never offered as a department."""
	return set(frappe.get_all("Organisation Unit", filters={"parent_organisation_unit": ["is", "not set"]}, pluck="name", limit_page_length=0))


def fy_label(year_start_date: Any) -> str:
	start = getdate(year_start_date)
	return f"FY {start.year}/{str(start.year + 1)[-2:]}"


def fiscal_year_labels(names: set[str]) -> dict[str, str]:
	if not names:
		return {}
	rows = frappe.get_all("Fiscal Year", filters={"name": ["in", sorted(names)]}, fields=["name", "year_start_date"], limit_page_length=0)
	return {row["name"]: fy_label(row["year_start_date"]) for row in rows}


def fiscal_year_exists(name: str) -> bool:
	return bool(name) and bool(frappe.db.exists("Fiscal Year", name))
