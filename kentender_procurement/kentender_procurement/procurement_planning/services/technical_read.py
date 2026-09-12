# Copyright (c) 2026, KenTender and contributors
"""AUTH-ADR-001 v1.8 §8/§9 technical-read surface for Procurement Planning.

Registered through the `kt_technical_reference_resolvers` and
`kt_technical_read_probes` hooks (see kentender_procurement/hooks.py).

Route prefixes (`kentender_core.module_registry` / `ProcurementPlanning.vue`):
  - "procurement-planning"           workspace + the §10 task deep links
                                      (dpp-review/<task>, finance/<task>,
                                      review/<task>, publication/<publication>)
  - "departmental-procurement-plan"  Departmental Plan editor, by dpp_reference
  - "annual-procurement-plan"        Annual Plan detail, by plan_reference
  - "procurement-plan-item"          Annual Plan Item detail, by plan_item_id

A *Version* doctype (Departmental Plan Version, Annual Plan Version) has no
route of its own — it resolves to its parent Departmental Plan / Annual
Plan's own page (KT-STD-001 v1.5 §3A.6's child/version rule).
"""

from __future__ import annotations

import frappe

from kentender_procurement.procurement_planning import api

WORKSPACE_PAGE = "procurement-planning"
DPP_PAGE = "departmental-procurement-plan"
PLAN_PAGE = "annual-procurement-plan"
PLAN_ITEM_PAGE = "procurement-plan-item"


def _dpp_route(name: str) -> list[str]:
	return [DPP_PAGE, name]


def _dpp_version_route(name: str) -> list[str]:
	dpp = frappe.db.get_value("Departmental Plan Version", name, "departmental_plan")
	return [DPP_PAGE, dpp] if dpp else [WORKSPACE_PAGE]


def _plan_route(name: str) -> list[str]:
	return [PLAN_PAGE, name]


def _plan_version_route(name: str) -> list[str]:
	plan = frappe.db.get_value("Annual Plan Version", name, "annual_plan")
	return [PLAN_PAGE, plan] if plan else [WORKSPACE_PAGE]


def _plan_item_route(name: str) -> list[str]:
	plan_item_id = frappe.db.get_value("Annual Plan Item", name, "plan_item_id") or name
	return [PLAN_ITEM_PAGE, plan_item_id]


def _dpp_validation_task_route(name: str) -> list[str]:
	return [WORKSPACE_PAGE, "dpp-review", name]


def _finance_task_route(name: str) -> list[str]:
	return [WORKSPACE_PAGE, "finance", name]


def _governance_task_route(name: str) -> list[str]:
	return [WORKSPACE_PAGE, "review", name]


def reference_resolvers() -> list[dict]:
	return [
		{
			"doctype": "Departmental Plan",
			"label": "Departmental Plan",
			"reference_field": "dpp_reference",
			"title_field": "dpp_reference",
			"status_field": "current_state",
			"route": _dpp_route,
		},
		{
			"doctype": "Departmental Plan Version",
			"label": "Departmental Plan Version",
			"reference_field": "version_reference",
			"title_field": "version_reference",
			"status_field": "version_status",
			"route": _dpp_version_route,
		},
		{
			"doctype": "Annual Plan",
			"label": "Annual Plan",
			"reference_field": "plan_reference",
			"title_field": "title",
			"status_field": None,
			"route": _plan_route,
		},
		{
			"doctype": "Annual Plan Version",
			"label": "Annual Plan Version",
			"reference_field": "version_reference",
			"title_field": "version_reference",
			"status_field": "version_status",
			"route": _plan_version_route,
		},
		{
			"doctype": "Annual Plan Item",
			"label": "Annual Plan Item",
			"reference_field": "plan_item_id",
			"title_field": "title",
			"status_field": "item_status",
			"route": _plan_item_route,
		},
		{
			"doctype": "Departmental Plan Validation Task",
			"label": "Departmental Plan Validation Task",
			"reference_field": "task_reference",
			"title_field": "task_reference",
			"status_field": "status",
			"route": _dpp_validation_task_route,
		},
		{
			"doctype": "Plan Finance Task",
			"label": "Plan Finance Task",
			"reference_field": "task_reference",
			"title_field": "task_reference",
			"status_field": "status",
			"route": _finance_task_route,
		},
		{
			"doctype": "Plan Governance Task",
			"label": "Plan Governance Task",
			"reference_field": "task_reference",
			"title_field": "task_reference",
			"status_field": "status",
			"route": _governance_task_route,
		},
	]


def _existing_with_valid_fiscal_year(doctype: str) -> str | None:
	"""The newest row of `doctype` whose own `fiscal_year` names a live
	`Fiscal Year` record, skipping any that doesn't. Orphaned rows outlive
	the Fiscal Year fixtures a test run created them against (live site,
	fixtures a test run created them against (live site, 2026-09-12:
	`Departmental Plan`/`Annual Plan` rows referencing `2099-2100`); picking
	the newest one blindly hands a probe a reference the read contract then
	correctly rejects with `PLN_NO_CONTEXT`, a data-hygiene artifact, not a
	technical-read gap."""
	for row in frappe.get_all(doctype, fields=["name", "fiscal_year"], order_by="modified desc", limit=50):
		if row.fiscal_year and frappe.db.exists("Fiscal Year", row.fiscal_year):
			return row.name
	return None


def _annual_plan_fiscal_year(plan_version: str | None) -> str | None:
	plan = frappe.db.get_value("Annual Plan Version", plan_version, "annual_plan") if plan_version else None
	return frappe.db.get_value("Annual Plan", plan, "fiscal_year") if plan else None


def _existing_via_plan_version(doctype: str) -> str | None:
	"""Like `_existing_with_valid_fiscal_year`, for a doctype one hop away
	from its Fiscal Year through `plan_version` -> `Annual Plan Version`
	-> `Annual Plan`."""
	for row in frappe.get_all(doctype, fields=["name", "plan_version"], order_by="modified desc", limit=50):
		fy = _annual_plan_fiscal_year(row.plan_version)
		if fy and frappe.db.exists("Fiscal Year", fy):
			return row.name
	return None


def _dpp_kwargs() -> dict | None:
	name = _existing_with_valid_fiscal_year("Departmental Plan")
	return {"dpp_reference": name} if name else None


def _dpp_validation_task_kwargs() -> dict | None:
	# `Departmental Plan Validation Task` carries its own `fiscal_year`.
	name = _existing_with_valid_fiscal_year("Departmental Plan Validation Task")
	return {"task": name} if name else None


def _plan_kwargs() -> dict | None:
	name = _existing_with_valid_fiscal_year("Annual Plan")
	return {"plan_reference": name} if name else None


def _plan_item_kwargs() -> dict | None:
	for row in frappe.get_all(
		"Annual Plan Item", fields=["plan_item_id", "plan_version"], order_by="modified desc", limit=50
	):
		fy = _annual_plan_fiscal_year(row.plan_version)
		if fy and frappe.db.exists("Fiscal Year", fy):
			return {"plan_item_id": row.plan_item_id}
	return None


def _finance_task_kwargs() -> dict | None:
	name = _existing_via_plan_version("Plan Finance Task")
	return {"task": name} if name else None


def _governance_task_kwargs() -> dict | None:
	# `Plan Governance Task` carries `annual_plan` directly.
	for row in frappe.get_all(
		"Plan Governance Task", fields=["name", "annual_plan"], order_by="modified desc", limit=50
	):
		fy = frappe.db.get_value("Annual Plan", row.annual_plan, "fiscal_year") if row.annual_plan else None
		if fy and frappe.db.exists("Fiscal Year", fy):
			return {"task": row.name}
	return None


def _publication_kwargs() -> dict | None:
	name = _existing_via_plan_version("Annual Plan Publication")
	return {"publication": name} if name else None


def _fiscal_year_kwargs() -> dict | None:
	for doctype in ("Annual Plan", "Departmental Plan"):
		for row in frappe.get_all(doctype, fields=["fiscal_year"], order_by="modified desc", limit=50):
			if row.fiscal_year and frappe.db.exists("Fiscal Year", row.fiscal_year):
				return {"fiscal_year": row.fiscal_year}
	return None


def read_probes() -> list[dict]:
	return [
		{"label": "planning.resolve_planning_context", "call": api.resolve_planning_context, "kwargs": lambda: {}},
		{"label": "planning.get_regulatory_reference", "call": api.get_regulatory_reference, "kwargs": _fiscal_year_kwargs},
		{"label": "planning.get_planning_workspace", "call": api.get_planning_workspace, "kwargs": lambda: {}},
		{"label": "planning.get_departmental_plan", "call": api.get_departmental_plan, "kwargs": _dpp_kwargs},
		{"label": "planning.get_dpp_entry_editor", "call": api.get_dpp_entry_editor, "kwargs": _dpp_kwargs},
		{"label": "planning.get_dpp_validation_task", "call": api.get_dpp_validation_task, "kwargs": _dpp_validation_task_kwargs},
		{"label": "planning.get_annual_plan", "call": api.get_annual_plan, "kwargs": _plan_kwargs},
		{"label": "planning.get_plan_item", "call": api.get_plan_item, "kwargs": _plan_item_kwargs},
		{"label": "planning.get_finance_task", "call": api.get_finance_task, "kwargs": _finance_task_kwargs},
		{"label": "planning.get_plan_governance_task", "call": api.get_plan_governance_task, "kwargs": _governance_task_kwargs},
		{"label": "planning.get_publication_task", "call": api.get_publication_task, "kwargs": _publication_kwargs},
		{
			"label": "planning.get_requisition_eligible_plan_item",
			"call": api.get_requisition_eligible_plan_item,
			"kwargs": _plan_item_kwargs,
		},
	]
