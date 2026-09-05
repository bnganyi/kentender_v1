# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §7.3 — the Budget & Funding contracts, under the spec's
verbs (decision D6/D11).

Planning calls only Budget's published API module and never reads Budget
tables directly. Two contracts remain after v1.7's lifecycle simplification:

	ListEligibleBudgetLines   → budget_api.list_eligible_budget_lines
	CheckPlanAffordability    → budget_api.check_plan_affordability

Planning creates no reservation at any point (§7.3, BUD-BR-009): the v1.2
module's check/reserve/release/revalidate gateway paths are deleted, not
wrapped. Neither contract takes a Procuring Entity argument (§16.2).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import frappe
from frappe.utils import cstr


@contextmanager
def _system_principal():
	"""Temporarily evaluate one cross-module read as Administrator WITHOUT
	`frappe.set_user` (v1.2 finding: `set_user` inside a web request mangles
	the live session so every later request arrives as Guest).

	Budget's read scope admits only Budget-side responsibilities; §7.3/§12.3
	require the *departmental* author to see their department's eligible
	Active lines and the Planner to see the affordability statement. Every
	Planning caller authorises its own actor first; the result is already
	narrowed to the department or the plan's own totals."""
	local = frappe.local
	session = local.session
	saved = (session.user, session.sid, session.data)
	saved_form_dict = local.form_dict
	saved_user_obj = getattr(local, "user_obj", None)
	try:
		session.user = "Administrator"
		local.role_permissions = {}
		local.user_obj = None
		yield
	finally:
		session.user, session.sid, session.data = saved
		local.form_dict = saved_form_dict
		local.role_permissions = {}
		local.user_obj = saved_user_obj


def list_eligible_budget_lines(*, fiscal_year: str, source_org_unit: str | None = None) -> list[dict[str, Any]]:
	"""BUD v1.5 §9.1 — Active eligible lines (Entity-wide or matching the
	source unit), each with its human `reference`."""
	from kentender_budget.api.budget_api import list_eligible_budget_lines as contract

	with _system_principal():
		return contract(fiscal_year=fiscal_year, source_org_unit=source_org_unit)


def eligible_line_ids(*, fiscal_year: str, source_org_unit: str | None = None) -> set[str]:
	return {
		cstr(row.get("id") or row.get("name"))
		for row in list_eligible_budget_lines(fiscal_year=fiscal_year, source_org_unit=source_org_unit)
	}


def line_labels(fiscal_year: str) -> dict[str, dict[str, Any]]:
	"""`id` → {reference, title, label, funding_source, currency} for display."""
	out = {}
	for row in list_eligible_budget_lines(fiscal_year=fiscal_year):
		reference = cstr(row.get("reference")) or cstr(row.get("id"))
		out[cstr(row.get("id"))] = {
			"reference": reference,
			"title": cstr(row.get("title")),
			"label": f"{reference} — {row.get('title')}" if row.get("title") else reference,
			"funding_source": cstr(row.get("funding_source")),
			"approved": row.get("approved"),
		}
	return out


def check_plan_affordability(*, fiscal_year: str, planned_totals: dict[str, float]) -> dict[str, Any]:
	"""BUD v1.5 §8.2 — non-mutating; blocking within-approved, advisory
	within-available. No token, no lock, no ledger event."""
	from kentender_budget.api.budget_api import check_plan_affordability as contract

	with _system_principal():
		return contract(fiscal_year=fiscal_year, planned_totals=planned_totals)
