# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 — Procurement Planning API surface (§8.2 commands).

Every endpoint keeps an explicit signature: the framework passes the whole
`form_dict` (including `cmd`/`csrf_token`) into a whitelisted method that
declares **kwargs, which is exactly how NDS-914 broke four commands over HTTP
while every direct-service test passed. Playwright fixture endpoints live in
seed/fixture modules, never here (decision D8).
"""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.procurement_planning.services import (
	dpp_lifecycle,
	dpp_validation,
	planning_context,
)


def _parse_json(value, default):
	"""HTTP transports lists/dicts as JSON strings; direct callers pass values.
	`from __future__ import annotations` disables Frappe's own coercion."""
	if value is None:
		return default
	if isinstance(value, str):
		return json.loads(value) if value.strip() else default
	return value


# --- context (PLN-UI-01 groundwork; CTX-CHG-001) -----------------------------


@frappe.whitelist()
def resolve_planning_context(
	procuring_entity: str | None = None, financial_year: str | None = None
) -> dict[str, Any]:
	return planning_context.resolve_planning_context(
		procuring_entity=procuring_entity, financial_year=financial_year
	)


@frappe.whitelist()
def select_planning_context(procuring_entity: str, financial_year: str) -> dict[str, Any]:
	return planning_context.select_planning_context(
		procuring_entity=procuring_entity, financial_year=financial_year
	)


# --- §8.2 DPP commands -------------------------------------------------------


@frappe.whitelist()
def open_departmental_plan(
	procuring_entity: str,
	organisation_unit: str,
	financial_year: str,
	idempotency_key: str,
) -> dict[str, Any]:
	return dpp_lifecycle.open_departmental_plan(
		procuring_entity=procuring_entity,
		organisation_unit=organisation_unit,
		financial_year=financial_year,
		idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def save_need_funding(
	dpp_version: str,
	entry_id: str,
	budget_line: str,
	indicative_amount,
	expected_record_version,
	idempotency_key: str,
) -> dict[str, Any]:
	return dpp_lifecycle.save_need_funding(
		dpp_version=dpp_version,
		entry_id=entry_id,
		budget_line=budget_line,
		indicative_amount=indicative_amount,
		expected_record_version=expected_record_version,
		idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def save_direct_requirement(
	dpp_version: str,
	entry_values,
	expected_record_version,
	idempotency_key: str,
	entry_id: str | None = None,
) -> dict[str, Any]:
	# `entry_values`, deliberately not `values`: a form-encoded field named
	# "values" shadows frappe._dict.values() on frappe.local.form_dict, and
	# frappe internals that call form_dict.values() then receive a string —
	# observed live as the whole request degrading to Guest ("User None not
	# found" + a not-whitelisted refusal) while the same payload succeeded as
	# JSON. The NDS-914 transport-field family, new member.
	return dpp_lifecycle.save_direct_requirement(
		dpp_version=dpp_version,
		values=_parse_json(entry_values, {}),
		entry_id=entry_id,
		expected_record_version=expected_record_version,
		idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def remove_direct_requirement(
	dpp_version: str,
	entry_id: str,
	expected_record_version,
	idempotency_key: str,
) -> dict[str, Any]:
	return dpp_lifecycle.remove_direct_requirement(
		dpp_version=dpp_version,
		entry_id=entry_id,
		expected_record_version=expected_record_version,
		idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def submit_departmental_plan(
	dpp_version: str,
	certification_confirmed,
	expected_record_version,
	idempotency_key: str,
) -> dict[str, Any]:
	confirmed = certification_confirmed in (True, 1, "1", "true", "True")
	return dpp_lifecycle.submit_departmental_plan(
		dpp_version=dpp_version,
		certification_confirmed=confirmed,
		expected_record_version=expected_record_version,
		idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def withdraw_departmental_plan_version(
	dpp_version: str,
	expected_record_version,
	idempotency_key: str,
) -> dict[str, Any]:
	return dpp_lifecycle.withdraw_departmental_plan_version(
		dpp_version=dpp_version,
		expected_record_version=expected_record_version,
		idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def create_departmental_plan_update(
	departmental_plan: str,
	expected_record_version,
	idempotency_key: str,
) -> dict[str, Any]:
	return dpp_lifecycle.create_departmental_plan_update(
		departmental_plan=departmental_plan,
		expected_record_version=expected_record_version,
		idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def return_departmental_plan(
	task: str,
	issues,
	task_token: str,
	idempotency_key: str,
) -> dict[str, Any]:
	return dpp_validation.return_departmental_plan(
		task=task,
		issues=_parse_json(issues, []),
		task_token=task_token,
		idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def accept_departmental_plan(
	task: str,
	classifications,
	task_token: str,
	idempotency_key: str,
) -> dict[str, Any]:
	return dpp_validation.accept_departmental_plan(
		task=task,
		classifications=_parse_json(classifications, {}),
		task_token=task_token,
		idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def get_planning_workspace(
	procuring_entity: str | None = None, financial_year: str | None = None
) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import workspace

	return workspace.get_planning_workspace(
		procuring_entity=procuring_entity, financial_year=financial_year
	)


@frappe.whitelist()
def get_departmental_plan(dpp_reference: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import dpp_read

	return dpp_read.get_departmental_plan(dpp_reference=dpp_reference)


@frappe.whitelist()
def get_dpp_entry_editor(
	dpp_reference: str, entry_id: str | None = None
) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import dpp_read

	return dpp_read.get_dpp_entry_editor(dpp_reference=dpp_reference, entry_id=entry_id)
