# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.3 Phase 7 — thin whitelisted wrappers over
`kentender_strategy.services.strategy_ui_contracts` for STR-UI-01..04.

Kept separate from `strategy_api.py` (which still exposes the pre-Phase-1
broken portfolio/tree/overview functions the tracker documents as not yet
rebuilt outside this named scope) so the four Vue screens call a surface
that is fully correct against the current schema."""

from __future__ import annotations

import frappe

from kentender_strategy.services import strategy_ui_contracts as ui


@frappe.whitelist()
def get_strategy_portfolio(procuring_entity: str | None = None):
	return ui.get_strategy_portfolio(procuring_entity=procuring_entity or None)


@frappe.whitelist()
def get_plan_workspace(plan_id: str):
	return ui.get_plan_workspace(plan_id)


@frappe.whitelist()
def get_plan_history(plan_id: str):
	return ui.get_plan_history(plan_id)


@frappe.whitelist()
def get_strategy_tree(plan_version_id: str):
	return ui.get_strategy_tree(plan_version_id)


@frappe.whitelist()
def get_version_review_overview(plan_version_id: str):
	return ui.get_version_review_overview(plan_version_id)


@frappe.whitelist()
def diff_strategy_versions(compare_version_id: str, base_version_id: str | None = None):
	return ui.diff_strategy_versions(base_version_id or None, compare_version_id)
