# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §8.1 `ResolvePlanningContexts` / §10 / §12.1.

There is no Procuring Entity to select. The Financial Year is a visible,
changeable local filter that grants nothing: options derive from the ERPNext
`Fiscal Year` catalogue and the module's own eligibility (departmental-plan
intake open, an Annual Plan present, or a current/upcoming year), never from
a user grant. The last valid selection is remembered server-side through
`kentender_core.services.working_context` as a convenience, always
resettable; an invalid or stale value is discarded, never a trap.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, getdate, nowdate

from kentender_core.services import site_configuration
from kentender_procurement.procurement_planning.services import planning_authorization as authz

PLANNING_MODULE = "planning"
SOURCE_SELECTED = "selected"
SOURCE_SAVED_DEFAULT = "saved_default"
SOURCE_LEGACY = "legacy"


def _fy_label(year_start_date) -> str:
	start = getdate(year_start_date)
	return f"FY {start.year}/{str(start.year + 1)[-2:]}"


def selectable_years() -> list[dict[str, Any]]:
	"""§10 — years the module can operate in, from configured records only."""
	today = getdate(nowdate())
	dpp_state = site_configuration.get_dpp_submission_state()
	open_year = dpp_state["fiscal_year"] if dpp_state.get("open") else ""
	plan_years = set(frappe.get_all("Annual Plan", pluck="fiscal_year", limit_page_length=0))
	dpp_years = set(frappe.get_all("Departmental Plan", pluck="fiscal_year", limit_page_length=0))
	rows = frappe.get_all(
		"Fiscal Year",
		filters={"disabled": 0},
		fields=["name", "year_start_date", "year_end_date"],
		order_by="year_start_date asc",
		limit_page_length=0,
	)
	options = []
	for row in rows:
		start, end = getdate(row.year_start_date), getdate(row.year_end_date)
		is_current = start <= today <= end
		is_future = start > today
		has_plan = row.name in plan_years or row.name in dpp_years
		intake_open = row.name == open_year
		if not (is_current or is_future or has_plan or intake_open):
			continue
		options.append(
			{
				"id": row.name,
				"label": _fy_label(row.year_start_date),
				"start_date": cstr(row.year_start_date),
				"end_date": cstr(row.year_end_date),
				"is_current": is_current,
				"is_future": is_future,
				"is_past": end < today,
				"intake_open": intake_open,
				"has_open_plan": has_plan,
				"planning_open": bool(intake_open or has_plan or not (end < today)),
			}
		)
	return options


def _default_year(options: list[dict[str, Any]]) -> str:
	for key in ("intake_open", "has_open_plan", "is_current"):
		hit = [row for row in options if row[key]]
		if hit:
			return hit[0]["id"]
	future = [row for row in options if row["is_future"]]
	if future:
		return min(future, key=lambda row: getdate(row["start_date"]))["id"]
	return options[-1]["id"] if options else ""


def _site() -> dict[str, str]:
	single = frappe.get_cached_doc("Site Procuring Entity")
	return {"pe_name": cstr(single.pe_name), "pe_code": cstr(single.pe_code)}


def resolve_planning_context(*, financial_year: str | None = None, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	if not authz.holds_any_planning_responsibility(actor):
		return {
			"financial_year": "",
			"financial_years": [],
			"selection_source": "none",
			"resolved_financial_year_source": SOURCE_LEGACY,
			"selection_required": False,
			"no_scope": True,
			"site": _site(),
		}
	years = selectable_years()
	by_id = {row["id"]: row for row in years}
	explicit = cstr(financial_year).strip()
	source = ""
	if explicit:
		if explicit not in by_id:
			frappe.throw("Selected financial year is not available for Planning.", title="PLN_FY_NOT_SELECTABLE")
		fy, source = explicit, "explicit"
	else:
		from kentender_core.services.working_context import get_module_fy

		saved = get_module_fy(PLANNING_MODULE, actor, offered=[row["id"] for row in years])
		if saved.get("selected"):
			fy, source = saved["selected"]["id"], "saved"
		else:
			fy = _default_year(years)
			source = "default" if fy else ""
	return {
		"financial_year": fy,
		"financial_year_label": by_id.get(fy, {}).get("label", ""),
		"financial_years": years,
		"selection_source": source or "selection_required",
		"resolved_financial_year_source": (
			SOURCE_SELECTED if explicit else SOURCE_SAVED_DEFAULT if source == "saved" else SOURCE_LEGACY
		),
		"selection_required": not bool(fy),
		"no_scope": False,
		"site": _site(),
	}


def select_planning_context(*, financial_year: str, user: str | None = None) -> dict[str, Any]:
	from kentender_core.services.working_context import select_module_fy

	actor = authz.actor(user)
	context = resolve_planning_context(financial_year=financial_year, user=actor)
	if context["financial_year"]:
		select_module_fy(PLANNING_MODULE, context["financial_year"], actor, offered=[context["financial_year"]])
	return context
