# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Thin whitelisted wrappers for BUD-CHG-001 v1.3's §9.1/§9.2 contracts.
Every function here is a pass-through; all business logic and server-side
authorization lives in the `services/` modules."""

from __future__ import annotations

import frappe

from kentender_budget.services import budget_contracts as contracts


@frappe.whitelist()
def resolve_budget_context(fiscal_year: str | None = None):
	return contracts.resolve_budget_context(fiscal_year=fiscal_year)


@frappe.whitelist()
def list_available_fiscal_years():
	return contracts.list_available_fiscal_years()


@frappe.whitelist()
def get_budget_workspace(fiscal_year: str | None = None):
	return contracts.get_budget_workspace(fiscal_year=fiscal_year)


@frappe.whitelist()
def save_budget_version_draft(payload: dict | str | None = None):
	return contracts.save_budget_version_draft(payload)


@frappe.whitelist()
def get_budget_version_draft(budget_version: str | None = None):
	return contracts.get_budget_version_draft(budget_version or "")


@frappe.whitelist()
def create_budget_successor_version(budget: str | None = None, payload: dict | str | None = None):
	return contracts.create_budget_successor_version(budget or "", payload)


@frappe.whitelist()
def get_budget_detail(budget: str | None = None):
	return contracts.get_budget_detail(budget or "")


@frappe.whitelist()
def get_budget_line_position(budget_line: str | None = None):
	return contracts.get_budget_line_position(budget_line or "")


@frappe.whitelist()
def save_budget_lines_draft(payload: dict | str | None = None):
	from kentender_budget.services import budget_line_contracts as lines

	return lines.save_budget_lines_draft(payload)


@frappe.whitelist()
def get_budget_version_lines_editor(budget_version: str | None = None):
	from kentender_budget.services import budget_line_contracts as lines

	return lines.get_budget_version_lines_editor(budget_version or "")


@frappe.whitelist()
def get_budget_lines_active(budget: str | None = None):
	from kentender_budget.services import budget_line_contracts as lines

	return lines.get_budget_lines_active(budget or "")


@frappe.whitelist()
def list_eligible_budget_lines(
	fiscal_year: str | None = None,
	source_org_unit: str | None = None,
	funding_source: str | None = None,
	search: str | None = None,
):
	from kentender_budget.services import budget_line_contracts as lines

	return lines.list_eligible_budget_lines(
		fiscal_year=fiscal_year or "",
		source_org_unit=source_org_unit,
		funding_source=funding_source,
		search=search,
	)


@frappe.whitelist()
def get_budget_approval_task(budget_version: str | None = None):
	from kentender_budget.services import budget_readiness_contracts as readiness

	return readiness.get_budget_approval_task(budget_version or "")


@frappe.whitelist()
def get_budget_approval_task_lines(budget_version: str | None = None):
	from kentender_budget.services import budget_readiness_contracts as readiness

	return readiness.get_budget_approval_task_lines(budget_version or "")


@frappe.whitelist()
def get_budget_approval_task_changes(budget_version: str | None = None):
	from kentender_budget.services import budget_readiness_contracts as readiness

	return readiness.get_budget_approval_task_changes(budget_version or "")


@frappe.whitelist()
def submit_budget_version(payload: dict | str | None = None):
	from kentender_budget.services import budget_readiness_contracts as readiness

	return readiness.submit_budget_version(payload)


@frappe.whitelist()
def return_budget_version(payload: dict | str | None = None):
	from kentender_budget.services import budget_readiness_contracts as readiness

	return readiness.return_budget_version(payload)


@frappe.whitelist()
def approve_budget_version(payload: dict | str | None = None):
	from kentender_budget.services import budget_readiness_contracts as readiness

	return readiness.approve_budget_version(payload)


@frappe.whitelist()
def close_budget(payload: dict | str | None = None):
	from kentender_budget.services import budget_readiness_contracts as readiness

	return readiness.close_budget(payload)


@frappe.whitelist()
def get_funding_activity(budget: str | None = None, budget_line: str | None = None, event_type: str | None = None):
	from kentender_budget.services import budget_audit_contracts as audit

	return audit.get_funding_activity(budget or "", budget_line=budget_line, event_type=event_type)


@frappe.whitelist()
def get_budget_version_history(budget_version: str | None = None):
	from kentender_budget.services import budget_audit_contracts as audit

	return audit.get_budget_version_history(budget_version or "")


@frappe.whitelist()
def get_funding_lineage(
	plan_item: str | None = None,
	plan_source_allocation: str | None = None,
	reservation: str | None = None,
	contract: str | None = None,
	commitment: str | None = None,
):
	from kentender_budget.services import budget_downstream_contracts as downstream

	return downstream.get_funding_lineage(
		plan_item=plan_item,
		plan_source_allocation=plan_source_allocation,
		reservation=reservation,
		contract=contract,
		commitment=commitment,
	)


# --- Finance confirmation boundary (Procurement Planning is the only caller) ---


@frappe.whitelist()
def check_funding(
	plan_item: str | None = None,
	plan_version: str | None = None,
	finance_task: str | None = None,
	source_set_hash: str | None = None,
	allocations: list | str | None = None,
	correlation_id: str | None = None,
):
	from kentender_budget.services import budget_check_reserve_contracts as cr

	if isinstance(allocations, str):
		allocations = frappe.parse_json(allocations)
	return cr.check_funding(
		plan_item=plan_item or "",
		plan_version=plan_version or "",
		finance_task=finance_task or "",
		source_set_hash=source_set_hash or "",
		allocations=allocations or [],
		correlation_id=correlation_id or "",
	)


@frappe.whitelist()
def reserve_funding(
	token: str | None = None,
	finance_task: str | None = None,
	source_set_hash: str | None = None,
	idempotency_key: str | None = None,
):
	from kentender_budget.services import budget_check_reserve_contracts as cr

	return cr.reserve_funding(
		token=token or "",
		finance_task=finance_task or "",
		source_set_hash=source_set_hash or "",
		idempotency_key=idempotency_key or "",
	)


# --- Later reservation/commitment lifecycle (Contract Management / Planning) ---


@frappe.whitelist()
def revalidate_reservations(
	reservations: list | str | None = None,
	downstream_event_id: str | None = None,
	downstream_event_type: str | None = None,
	idempotency_key: str | None = None,
):
	from kentender_budget.services import budget_commitment_contracts as commit

	if isinstance(reservations, str):
		reservations = frappe.parse_json(reservations)
	return commit.revalidate_reservations(
		reservations=reservations or [],
		downstream_event_id=downstream_event_id or "",
		downstream_event_type=downstream_event_type or "",
		idempotency_key=idempotency_key or "",
	)


@frappe.whitelist()
def release_reservation(
	reservation: str | None = None,
	amount: float | None = None,
	downstream_event_id: str | None = None,
	downstream_event_type: str | None = None,
	idempotency_key: str | None = None,
):
	from kentender_budget.services import budget_commitment_contracts as commit

	return commit.release_reservation(
		reservation=reservation or "",
		amount=amount,
		downstream_event_id=downstream_event_id or "",
		downstream_event_type=downstream_event_type or "",
		idempotency_key=idempotency_key or "",
	)


@frappe.whitelist()
def convert_reservation(
	reservation: str | None = None,
	contract: str | None = None,
	amount: float | None = None,
	idempotency_key: str | None = None,
):
	from kentender_budget.services import budget_commitment_contracts as commit

	return commit.convert_reservation(
		reservation=reservation or "",
		contract=contract or "",
		amount=amount,
		idempotency_key=idempotency_key or "",
	)


@frappe.whitelist()
def adjust_commitment(
	commitment: str | None = None,
	new_total: float | None = None,
	variation_event_id: str | None = None,
	variation_event_type: str | None = None,
	idempotency_key: str | None = None,
):
	from kentender_budget.services import budget_commitment_contracts as commit

	return commit.adjust_commitment(
		commitment=commitment or "",
		new_total=new_total,
		variation_event_id=variation_event_id or "",
		variation_event_type=variation_event_type or "",
		idempotency_key=idempotency_key or "",
	)
