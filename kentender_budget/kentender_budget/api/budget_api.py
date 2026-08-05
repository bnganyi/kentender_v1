# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Thin whitelisted wrappers for Budget MVP-1 portfolio / register services."""

from __future__ import annotations

import frappe

from kentender_budget.services import budget_contracts as contracts
from kentender_budget.services.budget_permissions import ensure_budget_roles


@frappe.whitelist()
def get_budget_portfolio(procuring_entity: str | None = None):
	ensure_budget_roles()
	return contracts.get_budget_portfolio(procuring_entity=procuring_entity or None)


@frappe.whitelist()
def list_budgets(
	procuring_entity: str | None = None,
	status: str | None = None,
	fiscal_period: str | None = None,
	search: str | None = None,
	registration_source: str | None = None,
):
	ensure_budget_roles()
	return contracts.list_budgets(
		procuring_entity=procuring_entity or None,
		status=status or None,
		fiscal_period=fiscal_period or None,
		search=search or None,
		registration_source=registration_source or None,
	)


@frappe.whitelist()
def get_register_form_context():
	ensure_budget_roles()
	return contracts.get_register_form_context()


@frappe.whitelist()
def register_budget(payload: dict | str | None = None):
	ensure_budget_roles()
	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	return contracts.register_budget(payload or {})


@frappe.whitelist()
def get_budget_overview(budget: str | None = None):
	ensure_budget_roles()
	return contracts.get_budget_overview(budget or "")


@frappe.whitelist()
def list_budget_lines(budget: str | None = None):
	ensure_budget_roles()
	from kentender_budget.services import budget_line_contracts as line_contracts

	return line_contracts.list_budget_lines(budget or "")


@frappe.whitelist()
def get_budget_line(line: str | None = None):
	ensure_budget_roles()
	from kentender_budget.services import budget_line_contracts as line_contracts

	return line_contracts.get_budget_line(line or "")


@frappe.whitelist()
def save_budget_line(payload: dict | str | None = None):
	ensure_budget_roles()
	from kentender_budget.services import budget_line_contracts as line_contracts

	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	return line_contracts.save_budget_line(payload or {})


@frappe.whitelist()
def list_funding_activity(budget: str | None = None):
	ensure_budget_roles()
	from kentender_budget.services import budget_funding_activity as activity

	return activity.list_funding_activity(budget or "")


@frappe.whitelist()
def list_downstream_usage(budget: str | None = None):
	ensure_budget_roles()
	from kentender_budget.services import budget_downstream_contracts as downstream

	return downstream.list_downstream_usage(budget or "")


@frappe.whitelist()
def get_budget_usage(budget: str | None = None):
	"""Pack §8 alias for list_downstream_usage."""
	ensure_budget_roles()
	from kentender_budget.services import budget_downstream_contracts as downstream

	return downstream.get_budget_usage(budget or "")


@frappe.whitelist()
def list_budget_revisions(budget: str | None = None):
	ensure_budget_roles()
	from kentender_budget.services import budget_revision_contracts as revisions

	return revisions.list_budget_revisions(budget or "")


@frappe.whitelist()
def get_budget_revision_create_context(
	budget: str | None = None, revision: str | None = None
):
	ensure_budget_roles()
	from kentender_budget.services import budget_revision_contracts as revisions

	return revisions.get_budget_revision_create_context(budget or "", revision)


@frappe.whitelist()
def create_budget_revision(payload: dict | str | None = None):
	ensure_budget_roles()
	from kentender_budget.services import budget_revision_contracts as revisions

	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	return revisions.create_budget_revision(payload or {})


@frappe.whitelist()
def submit_budget_revision(payload: dict | str | None = None):
	ensure_budget_roles()
	from kentender_budget.services import budget_revision_contracts as revisions

	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	return revisions.submit_budget_revision(payload or {})


@frappe.whitelist()
def get_budget_revision_review_context(revision: str | None = None):
	ensure_budget_roles()
	from kentender_budget.services import budget_revision_contracts as revisions

	return revisions.get_budget_revision_review_context(revision or "")


@frappe.whitelist()
def review_budget_revision(revision: str | None = None):
	"""Pack §8 alias for get_budget_revision_review_context."""
	ensure_budget_roles()
	from kentender_budget.services import budget_revision_contracts as revisions

	return revisions.review_budget_revision(revision or "")


@frappe.whitelist()
def return_budget_revision(payload: dict | str | None = None):
	ensure_budget_roles()
	from kentender_budget.services import budget_revision_contracts as revisions

	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	return revisions.return_budget_revision(payload or {})


@frappe.whitelist()
def reject_budget_revision(payload: dict | str | None = None):
	ensure_budget_roles()
	from kentender_budget.services import budget_revision_contracts as revisions

	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	return revisions.reject_budget_revision(payload or {})


@frappe.whitelist()
def apply_budget_revision(payload: dict | str | None = None):
	ensure_budget_roles()
	from kentender_budget.services import budget_revision_contracts as revisions

	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	return revisions.apply_budget_revision(payload or {})


@frappe.whitelist()
def get_budget_readiness(budget: str | None = None):
	ensure_budget_roles()
	from kentender_budget.services import budget_readiness_contracts as readiness

	return readiness.get_budget_readiness(budget or "")


@frappe.whitelist()
def submit_budget(payload: dict | str | None = None):
	ensure_budget_roles()
	from kentender_budget.services import budget_readiness_contracts as readiness

	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	return readiness.submit_budget(payload or {})


@frappe.whitelist()
def return_budget(payload: dict | str | None = None):
	ensure_budget_roles()
	from kentender_budget.services import budget_readiness_contracts as readiness

	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	return readiness.return_budget(payload or {})


@frappe.whitelist()
def mark_budget_reviewed(payload: dict | str | None = None):
	ensure_budget_roles()
	from kentender_budget.services import budget_readiness_contracts as readiness

	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	return readiness.mark_budget_reviewed(payload or {})


@frappe.whitelist()
def activate_budget(payload: dict | str | None = None):
	ensure_budget_roles()
	from kentender_budget.services import budget_readiness_contracts as readiness

	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	return readiness.activate_budget(payload or {})


@frappe.whitelist()
def get_budget_audit(
	budget: str | None = None,
	event_type: str | None = None,
	actor: str | None = None,
	date_from: str | None = None,
	date_to: str | None = None,
):
	ensure_budget_roles()
	from kentender_budget.services import budget_audit_contracts as audit

	return audit.get_budget_audit(
		budget or "",
		event_type=event_type or None,
		actor=actor or None,
		date_from=date_from or None,
		date_to=date_to or None,
	)
