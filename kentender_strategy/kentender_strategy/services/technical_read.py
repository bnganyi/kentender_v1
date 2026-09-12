# Copyright (c) 2026, KenTender and contributors
"""AUTH-ADR-001 v1.8 §8/§9 technical-read surface for Strategy.

Registered through the `kt_technical_reference_resolvers` and
`kt_technical_read_probes` hooks (see kentender_strategy/hooks.py) so the
core Technical search page/service and the conformance test
(`kentender_core.tests.test_technical_read_conformance`) can exercise every
read entry point in `kentender_strategy.api.strategy_ui_api` without any
Strategy-specific knowledge baked into core.

Resolvers cover the two Strategy doctypes a technical reader can be handed a
reference to: `Strategic Plan` (identity) and `Strategic Plan Version`
(version + status). A version has no route of its own in §10 — it resolves
to its parent plan's overview page, same as every other "child/version"
resolver in this KT-STD-001 v1.5 §3A.6 pass.
"""

from __future__ import annotations

import frappe

from kentender_strategy.api import strategy_ui_api as api
from kentender_strategy.services import strategy_ui_contracts as ui


def _plan_route(name: str) -> list[str]:
	reference = frappe.db.get_value("Strategic Plan", name, "plan_id") or name
	return ui.plan_route(reference)


def _version_route(name: str) -> list[str]:
	plan_id = frappe.db.get_value("Strategic Plan Version", name, "plan_id")
	if not plan_id:
		return [ui.PAGE]
	plan_reference = frappe.db.get_value("Strategic Plan", plan_id, "plan_id") or plan_id
	return ui.plan_route(plan_reference)


def reference_resolvers() -> list[dict]:
	return [
		{
			"doctype": "Strategic Plan",
			"label": "Strategic Plan",
			"reference_field": "plan_id",
			"title_field": "title",
			"status_field": None,
			"route": _plan_route,
		},
		{
			"doctype": "Strategic Plan Version",
			"label": "Strategic Plan Version",
			"reference_field": "plan_version_id",
			"title_field": "plan_version_id",
			"status_field": "status",
			"route": _version_route,
		},
	]


def _existing_plan_name() -> str | None:
	rows = frappe.get_all("Strategic Plan", limit=1, order_by="modified desc", pluck="name")
	return rows[0] if rows else None


def _existing_version_name() -> str | None:
	rows = frappe.get_all("Strategic Plan Version", limit=1, order_by="modified desc", pluck="name")
	return rows[0] if rows else None


def _plan_kwargs() -> dict | None:
	plan_name = _existing_plan_name()
	return {"plan_id": plan_name} if plan_name else None


def _version_kwargs() -> dict | None:
	version_name = _existing_version_name()
	return {"plan_version_id": version_name} if version_name else None


def _diff_kwargs() -> dict | None:
	version_name = _existing_version_name()
	return {"compare_version_id": version_name} if version_name else None


def read_probes() -> list[dict]:
	return [
		{"label": "strategy.get_strategy_portfolio", "call": api.get_strategy_portfolio, "kwargs": lambda: {}},
		{"label": "strategy.get_plan_workspace", "call": api.get_plan_workspace, "kwargs": _plan_kwargs},
		{"label": "strategy.get_plan_history", "call": api.get_plan_history, "kwargs": _plan_kwargs},
		{"label": "strategy.get_version_history", "call": api.get_version_history, "kwargs": _version_kwargs},
		{"label": "strategy.get_strategy_tree", "call": api.get_strategy_tree, "kwargs": _version_kwargs},
		{"label": "strategy.get_version_review_overview", "call": api.get_version_review_overview, "kwargs": _version_kwargs},
		{"label": "strategy.diff_strategy_versions", "call": api.diff_strategy_versions, "kwargs": _diff_kwargs},
		{"label": "strategy.list_available_fiscal_years", "call": api.list_available_fiscal_years, "kwargs": lambda: {}},
	]
