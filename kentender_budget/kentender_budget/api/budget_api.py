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
def decline_budget_revision_request(payload: dict | str | None = None):
	"""BUD v1.11 §9.2 — the Budget Officer's decline (BUD-DES-19)."""
	from kentender_budget.services import budget_revision_request_contracts as requests

	return requests.decline_budget_revision_request(payload)


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
def check_plan_affordability(fiscal_year: str | None = None, planned_totals=None):
	"""BUD v1.5 §9.1 — non-mutating plan affordability statement."""
	from kentender_budget.services import budget_line_contracts as lines

	return lines.check_plan_affordability(fiscal_year=fiscal_year or "", planned_totals=planned_totals)


def validate_plan_affordability_for_decision(
	fiscal_year: str | None = None, planned_totals=None, expected_revisions=None, correlation: str | None = None
):
	"""PLN-CHG-001 v1.18 §5.3.3 — decision-time basis validation inside the
	caller's transaction; locks, validates, writes nothing.

	Not a web endpoint (RG-22): it takes whole-Budget row locks, so any Budget reader
	who could post to it could stall reserve, approve and close. Procurement Planning
	calls it in-process through `budget_gateway.validate_plan_affordability_for_decision`
	inside the Finance decision's own transaction."""
	from kentender_budget.services import budget_line_contracts as lines

	return lines.validate_plan_affordability_for_decision(
		fiscal_year=fiscal_year or "",
		planned_totals=planned_totals,
		expected_revisions=expected_revisions,
		correlation=correlation or "",
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
def get_budget_closure_status(budget: str | None = None):
	"""BUD-CHG-001 v1.9 §9.4/§11.18 — year-end closure read: before year end,
	blocked, unavailable, ready or closed. Reads only."""
	from kentender_budget.services import budget_readiness_contracts as readiness

	return readiness.get_budget_closure_status(budget or "")


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


# check_funding, reserve_funding, release_reservation, convert_reservation,
# adjust_commitment and revalidate_reservations are deliberately NOT published
# here (AUD-XC-002, AUD-XC-012): they are in-process service calls made by a
# named downstream service principal (`services/budget_service_principal.py`)
# and no browser or HTTP caller can supply one.


# BUD-CHG-001 v1.11 §6 / §9.2 — the Planning service principal's two calls.
# Published for Procurement Planning's gateway, deliberately NOT whitelisted:
# no browser or HTTP caller may send or withdraw a request; the service
# checks the registered principal flag Planning's gateway sets.


def receive_budget_revision_request(payload: dict | str | None = None):
	from kentender_budget.services import budget_revision_request_contracts as requests

	return requests.receive_budget_revision_request(payload)


def withdraw_budget_revision_request(payload: dict | str | None = None):
	from kentender_budget.services import budget_revision_request_contracts as requests

	return requests.withdraw_budget_revision_request(payload)
