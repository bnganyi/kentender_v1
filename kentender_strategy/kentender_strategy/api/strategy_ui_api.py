# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.7 §10/§12 — thin whitelisted wrappers over
`kentender_strategy.services.strategy_ui_contracts` for STR-UI-01..04."""

from __future__ import annotations

import frappe

from kentender_strategy.services import strategy_ui_contracts as ui


@frappe.whitelist()
def get_strategy_portfolio(search: str | None = None, plan_role: str | None = None, status: str | None = None):
	# One site is one Procuring Entity; no entity parameter exists (§12.1).
	return ui.get_strategy_portfolio(search=search or None, plan_role=plan_role or None, status=status or None)


@frappe.whitelist()
def get_plan_workspace(plan_id: str):
	return ui.get_plan_workspace(plan_id)


@frappe.whitelist()
def get_plan_history(plan_id: str):
	return ui.get_plan_history(plan_id)


@frappe.whitelist()
def get_version_history(plan_version_id: str):
	return ui.get_version_history(plan_version_id)


@frappe.whitelist()
def get_strategy_tree(plan_version_id: str):
	return ui.get_strategy_tree(plan_version_id)


@frappe.whitelist()
def get_version_review_overview(plan_version_id: str):
	return ui.get_version_review_overview(plan_version_id)


@frappe.whitelist()
def diff_strategy_versions(compare_version_id: str, base_version_id: str | None = None):
	return ui.diff_strategy_versions(base_version_id or None, compare_version_id)


@frappe.whitelist()
def list_available_fiscal_years(plan_id: str | None = None):
	return ui.list_available_fiscal_years(plan_id or None)
