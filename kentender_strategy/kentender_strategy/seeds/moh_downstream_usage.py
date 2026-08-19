# Copyright (c) 2026, KenTender and contributors
"""Link MOH demo Budget Line records to MOH-TGT-AVAIL-2028 for Downstream Usage."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	STRATEGY_PLAN_CODE,
	TARGET_CODE,
)
from kentender_strategy.services.strategy_consumer import apply_strategy_reference_to_doc

# Canonical MVP-1 Budget Line (Budget portfolio fixture).
SEED_BUDGET_LINE_CODE = "MOH-BL-DHI-2027"
# PP2 WORKS master package (PACKAGE_DRAFT+).
SEED_PACKAGE_CODE = "PKG-MOH-2026-001"


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


def _link_budget_line(name: str, plan_name: str, target_name: str) -> bool:
	"""Set Budget Line primary_* Strategy Reference fields (STR-SUP-001)."""
	if not frappe.db.exists("DocType", "Budget Line"):
		return False
	if not frappe.db.has_column("Budget Line", "primary_plan_version_id"):
		return False
	if not frappe.db.exists("Budget Line", name):
		return False

	tgt = frappe.db.get_value(
		"Performance Target",
		target_name,
		["name", "target_code", "title", "plan_version"],
		as_dict=True,
	)
	if not tgt:
		return False

	plan_version = plan_name or tgt.plan_version
	snapshot = f"{tgt.target_code} — {tgt.title}" if tgt.title else tgt.target_code
	frappe.db.set_value(
		"Budget Line",
		name,
		{
			"primary_target_id": tgt.name,
			"primary_target_code": tgt.target_code,
			"primary_target_name": tgt.title or tgt.target_code,
			"primary_plan_version_id": plan_version,
			"primary_snapshot_label": snapshot,
			"primary_strategy_linked": 1,
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
		"package": None,
		"plan": plan_name,
		"target": target_name,
	}
	if not plan_name or not target_name:
		return {"ok": False, "reason": "Missing Active MOH plan or target", "linked": linked}

	# Demands package retired; no demand consumer link (STR-FR-020).

	# Prefer Budget portfolio fixture; ensure primary_* points at MOH strategy plan/target.
	if frappe.db.exists("DocType", "Budget Line"):
		try:
			from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio

			upsert_moh_mvp_v1_portfolio()
		except Exception:
			frappe.log_error(title="moh_downstream_usage: budget portfolio upsert skipped")

		bl_name = frappe.db.get_value(
			"Budget Line",
			{"generated_reference": SEED_BUDGET_LINE_CODE},
			"name",
		)
		if bl_name and _link_budget_line(bl_name, plan_name, target_name):
			linked["budget_line"] = bl_name

	# XMOD-STR-006 — PP2 Procurement Package retired; skip package consumer link.

	return {
		"ok": bool(linked["budget_line"] or linked.get("package")),
		"linked": linked,
	}
