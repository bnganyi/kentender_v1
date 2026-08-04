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
