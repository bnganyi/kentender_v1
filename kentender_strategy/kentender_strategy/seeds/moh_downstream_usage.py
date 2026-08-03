# Copyright (c) 2026, KenTender and contributors
"""Link MOH demo Demand / Budget Line records to MOH-TGT-01 for Downstream Usage."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	STRATEGY_PLAN_CODE,
	TARGET_CODE,
)
from kentender_strategy.services.strategy_consumer import apply_strategy_reference_to_doc

# Prefer IT demand (Approved masters may be workflow-locked — set via db).
SEED_DEMAND_CODES = ("DEM-MOH-2026-002", "DEMO-MOH-2026-DEM-DRAFT", "DEM-MOH-2026-001")
SEED_BUDGET_LINE_CODE = "BUD-MOH-IT-2026-001"


def _link_consumer(doctype: str, name: str, target_name: str) -> bool:
	"""Set strategy_* without consumer workflow save guards (usage is derived metadata)."""
	if not frappe.db.has_column(doctype, "strategy_plan_version"):
		return False
	doc = frappe.get_doc(doctype, name)
	apply_strategy_reference_to_doc(doc, target_name, require_active=True)
	frappe.db.set_value(
		doctype,
		name,
		{
			"strategy_plan_version": doc.strategy_plan_version,
			"strategy_target": doc.strategy_target,
			"strategy_snapshot_label": doc.strategy_snapshot_label,
		},
		update_modified=True,
	)
	return True


def seed_moh_downstream_usage_refs(
	plan_name: str | None = None,
	target_name: str | None = None,
) -> dict[str, Any]:
	"""Idempotently apply Strategy Reference on known MOH consumer docs."""
	if not plan_name:
		plan_name = frappe.db.get_value(
			"Strategic Plan",
			{"plan_code": STRATEGY_PLAN_CODE, "status": "Active"},
			"name",
		) or frappe.db.get_value("Strategic Plan", {"plan_code": STRATEGY_PLAN_CODE}, "name")
	if not target_name:
		target_name = frappe.db.get_value(
			"Performance Target",
			{"target_code": TARGET_CODE, "plan_version": plan_name},
			"name",
		) or frappe.db.get_value("Performance Target", {"target_code": TARGET_CODE}, "name")

	linked: dict[str, str | None] = {
		"demand": None,
		"budget_line": None,
		"plan": plan_name,
		"target": target_name,
	}
	if not plan_name or not target_name:
		return {"ok": False, "reason": "Missing Active MOH plan or target", **linked}

	for code in SEED_DEMAND_CODES:
		demand_name = frappe.db.get_value("Demand", {"demand_id": code}, "name")
		if demand_name and _link_consumer("Demand", demand_name, target_name):
			linked["demand"] = demand_name
			break

	budget_name = frappe.db.get_value(
		"Budget Line", {"budget_line_code": SEED_BUDGET_LINE_CODE}, "name"
	)
	if budget_name and _link_consumer("Budget Line", budget_name, target_name):
		linked["budget_line"] = budget_name

	return {
		"ok": bool(linked["demand"] or linked["budget_line"]),
		"linked": linked,
	}
