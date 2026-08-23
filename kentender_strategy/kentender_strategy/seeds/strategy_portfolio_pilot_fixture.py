# Copyright (c) 2026, KenTender and contributors
"""Disposable fixture for the strategy_portfolio_pilot spike (Claude Design -> Vue 3 pilot).

Not called from any production code path. Run via `bench execute` for local
iteration and by the pilot's Playwright spec for setup/teardown. Clones a real
Active plan into a submit-ready Draft successor (reusing create_successor_version,
which brings the full structure — programmes/outcomes/indicators/targets — so it
passes the readiness engine without hand-authoring fixture structure data), and
tears the clone back down afterwards so repeated runs never collide with
create_successor_version's own "one open successor" guard.
"""

from __future__ import annotations

import frappe

from kentender_strategy.services.strategy_writes import create_successor_version

SOURCE_PLAN_CODE = "MOH-SP-2026-2030"

_CLONED_CHILD_DOCTYPES = (
	"Strategy Value Commitment",
	"Performance Target",
	"Performance Indicator",
	"Strategic Outcome",
	"Strategic Objective",
	"Strategy Sub Programme",
	"Strategy Programme",
)


def seed() -> str:
	"""Create (or reuse) a disposable Draft successor of SOURCE_PLAN_CODE. Returns its plan_code."""
	existing = frappe.db.get_value(
		"Strategic Plan",
		{
			"plan_code": SOURCE_PLAN_CODE,
			"status": ["in", ["Draft", "Returned", "Submitted"]],
			"version_number": [">", 1],
		},
		"plan_code",
	)
	if existing:
		return existing

	source_name = frappe.db.get_value(
		"Strategic Plan", {"plan_code": SOURCE_PLAN_CODE, "status": "Active"}, "name"
	)
	if not source_name:
		frappe.throw(f"No Active plan found for plan_code {SOURCE_PLAN_CODE}")

	result = create_successor_version(source_name)
	frappe.db.commit()
	return result["plan"]["code"]


def teardown() -> dict:
	"""Delete the disposable successor (and its cloned children) created by seed()."""
	successor_name = frappe.db.get_value(
		"Strategic Plan",
		{
			"plan_code": SOURCE_PLAN_CODE,
			"status": ["in", ["Draft", "Returned", "Submitted"]],
			"version_number": [">", 1],
		},
		"name",
	)
	if not successor_name:
		return {"ok": True, "deleted": False}

	for doctype in _CLONED_CHILD_DOCTYPES:
		for row_name in frappe.get_all(
			doctype, filters={"plan_version": successor_name}, pluck="name"
		):
			frappe.delete_doc(doctype, row_name, ignore_permissions=True, force=True)

	frappe.delete_doc("Strategic Plan", successor_name, ignore_permissions=True, force=True)
	frappe.db.commit()
	return {"ok": True, "deleted": True, "plan_version": successor_name}
