# Copyright (c) 2026, KenTender and contributors
"""AUTH-ADR-001 v1.8 §8/§9 technical-read surface for Budget & Funding.

Registered through the `kt_technical_reference_resolvers` and
`kt_technical_read_probes` hooks (see kentender_budget/hooks.py). Resolvers
cover the three Budget doctypes a technical reader is handed a reference to:
`Procurement Budget`, `Procurement Budget Version` and
`Procurement Budget Line`. All three are named by `autoname: hash` — the
human-readable code lives in `generated_reference`, never in `name` itself
(see `budget_contracts._resolve_budget*`'s own dual-lookup pattern) — so
every route callable below resolves the code from the docname it is handed.

The one Budget & Funding Page ("budget-funding", not the spec's literal
"budget" — see `budget_funding_page.js`'s own note on the ERPNext `Budget`
DocType route collision) carries every route:
  - Budget detail:            ["budget-funding", budget_code]
  - Budget Version editor:    ["budget-funding", budget_code, "version", version_number]
  - Budget Line detail:       ["budget-funding", "line", line_code]
A Budget Version has no route distinct from its own editor slot, so it
resolves straight there rather than to a bare parent page (BudgetVersionEditorScreen.vue
opens on exactly this shape regardless of the version's status).
"""

from __future__ import annotations

import frappe

from kentender_budget.api import budget_api as api

PAGE = "budget-funding"


def _budget_code(name: str) -> str:
	return frappe.db.get_value("Procurement Budget", name, "generated_reference") or name


def _budget_route(name: str) -> list[str]:
	return [PAGE, _budget_code(name)]


def _version_route(name: str) -> list[str]:
	row = frappe.db.get_value("Procurement Budget Version", name, ["budget", "version_number"], as_dict=True)
	if not row or not row.budget:
		return [PAGE]
	return [PAGE, _budget_code(row.budget), "version", str(row.version_number)]


def _line_route(name: str) -> list[str]:
	code = frappe.db.get_value("Procurement Budget Line", name, "generated_reference") or name
	return [PAGE, "line", code]


def reference_resolvers() -> list[dict]:
	return [
		{
			"doctype": "Procurement Budget",
			"label": "Procurement Budget",
			"reference_field": "generated_reference",
			"title_field": "title",
			"status_field": None,
			"route": _budget_route,
		},
		{
			"doctype": "Procurement Budget Version",
			"label": "Procurement Budget Version",
			"reference_field": "generated_reference",
			"title_field": "generated_reference",
			"status_field": "status",
			"route": _version_route,
		},
		{
			"doctype": "Procurement Budget Line",
			"label": "Procurement Budget Line",
			"reference_field": "generated_reference",
			"title_field": "generated_reference",
			"status_field": None,
			"route": _line_route,
		},
	]


def _existing(doctype: str, filters: dict | None = None) -> str | None:
	rows = frappe.get_all(doctype, filters=filters or {}, limit=1, order_by="modified desc", pluck="name")
	return rows[0] if rows else None


def _budget_kwargs() -> dict | None:
	name = _existing("Procurement Budget")
	return {"budget": name} if name else None


def _version_kwargs() -> dict | None:
	name = _existing("Procurement Budget Version")
	return {"budget_version": name} if name else None


def _line_kwargs() -> dict | None:
	name = _existing("Procurement Budget Line")
	return {"budget_line": name} if name else None


def _existing_fiscal_year() -> str | None:
	"""A `Procurement Budget.fiscal_year` naming a `Fiscal Year` that still
	exists. Orphaned Budget rows outlive the Fiscal Year fixtures a test run
	created them against (live site, 2026-09-12: `2099-2100`/`2101-2102`
	referenced by leftover rows with no matching Fiscal Year) — picking the
	newest row blindly can hand a probe a reference `resolve_budget_context`
	then correctly rejects as `BUDGET_CONFIG_MISSING`, which is a data-
	hygiene artifact, not a technical-read gap."""
	for row in frappe.get_all(
		"Procurement Budget", fields=["fiscal_year"], order_by="modified desc", limit=50
	):
		if row.fiscal_year and frappe.db.exists("Fiscal Year", row.fiscal_year):
			return row.fiscal_year
	return None


def _fiscal_year_kwargs() -> dict | None:
	fy = _existing_fiscal_year()
	return {"fiscal_year": fy} if fy else None


def _eligible_lines_kwargs() -> dict | None:
	fy = _existing_fiscal_year()
	return {"fiscal_year": fy} if fy else None


def read_probes() -> list[dict]:
	return [
		{"label": "budget.list_available_fiscal_years", "call": api.list_available_fiscal_years, "kwargs": lambda: {}},
		{"label": "budget.resolve_budget_context", "call": api.resolve_budget_context, "kwargs": _fiscal_year_kwargs},
		{"label": "budget.get_budget_workspace", "call": api.get_budget_workspace, "kwargs": _fiscal_year_kwargs},
		{"label": "budget.get_budget_version_draft", "call": api.get_budget_version_draft, "kwargs": _version_kwargs},
		{"label": "budget.get_budget_detail", "call": api.get_budget_detail, "kwargs": _budget_kwargs},
		{"label": "budget.get_budget_line_position", "call": api.get_budget_line_position, "kwargs": _line_kwargs},
		{"label": "budget.get_budget_version_lines_editor", "call": api.get_budget_version_lines_editor, "kwargs": _version_kwargs},
		{"label": "budget.get_budget_lines_active", "call": api.get_budget_lines_active, "kwargs": _budget_kwargs},
		{"label": "budget.list_eligible_budget_lines", "call": api.list_eligible_budget_lines, "kwargs": _eligible_lines_kwargs},
		{"label": "budget.get_budget_approval_task", "call": api.get_budget_approval_task, "kwargs": _version_kwargs},
		{"label": "budget.get_budget_approval_task_lines", "call": api.get_budget_approval_task_lines, "kwargs": _version_kwargs},
		{"label": "budget.get_budget_approval_task_changes", "call": api.get_budget_approval_task_changes, "kwargs": _version_kwargs},
		{"label": "budget.get_funding_activity", "call": api.get_funding_activity, "kwargs": _budget_kwargs},
		{"label": "budget.get_budget_version_history", "call": api.get_budget_version_history, "kwargs": _version_kwargs},
		{"label": "budget.get_funding_lineage", "call": api.get_funding_lineage, "kwargs": lambda: {}},
	]
