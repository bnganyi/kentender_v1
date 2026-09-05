# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 — Procurement Planning API surface (§8.1 reads, §8.2
commands).

Every endpoint keeps an explicit signature: the framework passes the whole
`form_dict` (including `cmd`/`csrf_token`) into a whitelisted method that
declares **kwargs, which is exactly how NDS-914 broke four commands over HTTP
while every direct-service test passed. Playwright fixture endpoints live in
seed/fixture modules, never here (decision D8). No endpoint takes or returns
a Procuring Entity; the Fiscal Year is record data (§10).
"""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.procurement_planning.services import dpp_lifecycle, dpp_validation, planning_context


def _parse_json(value, default):
	"""HTTP transports lists/dicts as JSON strings; direct callers pass values.
	`from __future__ import annotations` disables Frappe's own coercion."""
	if value is None:
		return default
	if isinstance(value, str):
		return json.loads(value) if value.strip() else default
	return value


def _truthy(value) -> bool:
	return value in (True, 1, "1", "true", "True")


# --- context (PLN-UI-01) -------------------------------------------------------


@frappe.whitelist()
def resolve_planning_context(financial_year: str | None = None) -> dict[str, Any]:
	return planning_context.resolve_planning_context(financial_year=financial_year)


@frappe.whitelist()
def select_planning_context(financial_year: str) -> dict[str, Any]:
	return planning_context.select_planning_context(financial_year=financial_year)


@frappe.whitelist()
def get_regulatory_reference(fiscal_year: str) -> dict[str, Any]:
	"""§8.1 `GetRegulatoryReference` — read-only; Planning never writes it."""
	from kentender_core.services.regulatory_reference import get_regulatory_reference as read
	from kentender_procurement.procurement_planning.services import planning_authorization as authz

	if not authz.holds_any_planning_responsibility():
		authz.not_found()
	return read(fiscal_year)


# --- §8.2 DPP commands -------------------------------------------------------


@frappe.whitelist()
def open_departmental_plan(organisation_unit: str, fiscal_year: str, idempotency_key: str) -> dict[str, Any]:
	return dpp_lifecycle.open_departmental_plan(organisation_unit=organisation_unit, fiscal_year=fiscal_year, idempotency_key=idempotency_key)


@frappe.whitelist()
def save_need_funding(
	dpp_version: str, entry_id: str, expected_record_version, idempotency_key: str,
	budget_line: str | None = None, indicative_amount=None, not_proceeding_reason: str | None = None,
) -> dict[str, Any]:
	return dpp_lifecycle.save_need_funding(
		dpp_version=dpp_version, entry_id=entry_id, budget_line=budget_line or "", indicative_amount=indicative_amount,
		not_proceeding_reason=not_proceeding_reason or "", expected_record_version=expected_record_version,
		idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def save_direct_requirement(dpp_version: str, entry_values, expected_record_version, idempotency_key: str, entry_id: str | None = None) -> dict[str, Any]:
	# `entry_values`, deliberately not `values`: a form-encoded field named
	# "values" shadows frappe._dict.values() on frappe.local.form_dict and
	# degrades the whole request to Guest (v1.2 finding).
	return dpp_lifecycle.save_direct_requirement(
		dpp_version=dpp_version, values=_parse_json(entry_values, {}), entry_id=entry_id,
		expected_record_version=expected_record_version, idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def remove_direct_requirement(dpp_version: str, entry_id: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return dpp_lifecycle.remove_direct_requirement(dpp_version=dpp_version, entry_id=entry_id, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def submit_departmental_plan(dpp_version: str, certification_confirmed, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return dpp_lifecycle.submit_departmental_plan(
		dpp_version=dpp_version, certification_confirmed=_truthy(certification_confirmed),
		expected_record_version=expected_record_version, idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def withdraw_departmental_plan_version(dpp_version: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return dpp_lifecycle.withdraw_departmental_plan_version(dpp_version=dpp_version, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def create_departmental_plan_update(departmental_plan: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return dpp_lifecycle.create_departmental_plan_update(departmental_plan=departmental_plan, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def return_departmental_plan(task: str, issues, task_token: str, idempotency_key: str) -> dict[str, Any]:
	return dpp_validation.return_departmental_plan(task=task, issues=_parse_json(issues, []), task_token=task_token, idempotency_key=idempotency_key)


@frappe.whitelist()
def accept_departmental_plan(task: str, classifications, task_token: str, idempotency_key: str) -> dict[str, Any]:
	return dpp_validation.accept_departmental_plan(task=task, classifications=_parse_json(classifications, {}), task_token=task_token, idempotency_key=idempotency_key)


# --- §8.1 reads ------------------------------------------------------------


@frappe.whitelist()
def get_planning_workspace(financial_year: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import workspace

	return workspace.get_planning_workspace(financial_year=financial_year)


@frappe.whitelist()
def get_departmental_plan(dpp_reference: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import dpp_read

	return dpp_read.get_departmental_plan(dpp_reference=dpp_reference)


@frappe.whitelist()
def get_dpp_entry_editor(dpp_reference: str, entry_id: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import dpp_read

	return dpp_read.get_dpp_entry_editor(dpp_reference=dpp_reference, entry_id=entry_id)


@frappe.whitelist()
def get_dpp_validation_task(task: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import dpp_read

	return dpp_read.get_dpp_validation_task(task=task)


@frappe.whitelist()
def get_annual_plan(plan_reference: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_read

	return plan_read.get_annual_plan(plan_reference=plan_reference)


@frappe.whitelist()
def get_plan_item(plan_item_id: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_read

	return plan_read.get_plan_item(plan_item_id=plan_item_id)


@frappe.whitelist()
def get_finance_task(task: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_read

	return plan_read.get_finance_task(task=task)


@frappe.whitelist()
def get_plan_governance_task(task: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_read

	return plan_read.get_plan_governance_task(task=task)


@frappe.whitelist()
def get_publication_task(publication: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_read

	return plan_read.get_publication_task(publication=publication)


# --- workbench, formation, Plan Item -------------------------------------------


@frappe.whitelist()
def form_plan_items(plan_version: str, dpp_entries, mode: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_workbench

	return plan_workbench.form_plan_items(
		plan_version=plan_version, dpp_entries=_parse_json(dpp_entries, []), mode=mode,
		expected_record_version=expected_record_version, idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def dissolve_plan_item(plan_item: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_workbench

	return plan_workbench.dissolve_plan_item(plan_item=plan_item, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def save_plan_item(plan_item: str, item_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_workbench

	return plan_workbench.save_plan_item(plan_item=plan_item, values=_parse_json(item_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def confirm_splitting_advisory(plan_version: str, confirmation: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_workbench

	return plan_workbench.confirm_splitting_advisory(plan_version=plan_version, confirmation=confirmation, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


# --- plan-level Finance ---------------------------------------------------------


@frappe.whitelist()
def request_plan_funding_confirmation(plan_version: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_finance

	return plan_finance.request_plan_funding_confirmation(plan_version=plan_version, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def confirm_plan_funding(task: str, task_token: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_finance

	return plan_finance.confirm_plan_funding(task=task, task_token=task_token, idempotency_key=idempotency_key)


@frappe.whitelist()
def return_from_finance(task: str, reason: str, task_token: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_finance

	return plan_finance.return_from_finance(task=task, reason=reason, task_token=task_token, idempotency_key=idempotency_key)


# --- governance ---------------------------------------------------------------


@frappe.whitelist()
def submit_consolidated_plan(plan_version: str, expected_record_version, idempotency_key: str, late_activation_reason: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_governance

	return plan_governance.submit_consolidated_plan(
		plan_version=plan_version, expected_record_version=expected_record_version, idempotency_key=idempotency_key,
		late_activation_reason=late_activation_reason or "",
	)


@frappe.whitelist()
def adopt_and_submit_plan(task: str, task_token: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_governance

	return plan_governance.adopt_and_submit_plan(task=task, task_token=task_token, idempotency_key=idempotency_key)


@frappe.whitelist()
def approve_annual_plan(task: str, task_token: str, idempotency_key: str, resolution_reference: str = "") -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_governance

	return plan_governance.approve_annual_plan(task=task, task_token=task_token, resolution_reference=resolution_reference, idempotency_key=idempotency_key)


@frappe.whitelist()
def return_plan_version(task: str, reason: str, task_token: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_governance

	return plan_governance.return_plan_version(task=task, reason=reason, task_token=task_token, idempotency_key=idempotency_key)


@frappe.whitelist()
def submit_corrected_plan(plan_version: str, expected_record_version, idempotency_key: str, late_activation_reason: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_governance

	return plan_governance.submit_corrected_plan(
		plan_version=plan_version, expected_record_version=expected_record_version, idempotency_key=idempotency_key,
		late_activation_reason=late_activation_reason or "",
	)


# --- publication, Active, successor --------------------------------------------


@frappe.whitelist()
def retry_publication(publication: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_publication

	return plan_publication.retry_publication(publication=publication, idempotency_key=idempotency_key)


@frappe.whitelist()
def begin_plan_update(plan_reference: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_publication

	return plan_publication.begin_plan_update(plan_reference=plan_reference, idempotency_key=idempotency_key)


@frappe.whitelist()
def remove_plan_item_in_successor(plan_item: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_publication

	return plan_publication.remove_plan_item_in_successor(plan_item=plan_item, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def cancel_plan_update(plan_reference: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_publication

	return plan_publication.cancel_plan_update(plan_reference=plan_reference, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


# --- forecast cascade (Active Version only) -------------------------------------


@frappe.whitelist()
def preview_forecast_cascade(plan_item: str, milestone: str, new_forecast_date: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import schedule

	return schedule.preview_forecast_cascade(plan_item=plan_item, milestone=milestone, new_forecast_date=new_forecast_date)


@frappe.whitelist()
def confirm_forecast_cascade(plan_item: str, milestone: str, new_forecast_date: str, reason: str, expected_record_version, idempotency_key: str, included_milestones=None) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import schedule

	return schedule.confirm_forecast_cascade(
		plan_item=plan_item, milestone=milestone, new_forecast_date=new_forecast_date,
		included_milestones=_parse_json(included_milestones, None), reason=reason,
		expected_record_version=expected_record_version, idempotency_key=idempotency_key,
	)


# --- §7.4 Requisition eligibility — published for a sibling module ----------------


@frappe.whitelist()
def get_requisition_eligible_plan_item(plan_item_id: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_requisition

	return plan_requisition.get_requisition_eligible_plan_item(plan_item_id=plan_item_id)


@frappe.whitelist()
def record_requisition_drawdown(plan_item_id: str, requisition_reference: str, requesting_org_unit: str, allocations, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_requisition

	return plan_requisition.record_requisition_drawdown(
		plan_item_id=plan_item_id, requisition_reference=requisition_reference, requesting_org_unit=requesting_org_unit,
		allocations=_parse_json(allocations, []), expected_record_version=expected_record_version, idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def reverse_requisition_drawdown(drawdown_reference: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_requisition

	return plan_requisition.reverse_requisition_drawdown(drawdown_reference=drawdown_reference, expected_record_version=expected_record_version, idempotency_key=idempotency_key)
