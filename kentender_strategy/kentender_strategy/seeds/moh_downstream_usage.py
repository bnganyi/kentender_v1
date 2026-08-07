# Copyright (c) 2026, KenTender and contributors
"""Link MOH demo Demand / Budget Line records to MOH-TGT-AVAIL-2028 for Downstream Usage."""

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

	for code in SEED_DEMAND_CODES:
		demand_name = frappe.db.get_value("Demand", {"demand_id": code}, "name")
		if demand_name and _link_consumer("Demand", demand_name, target_name):
			linked["demand"] = demand_name
			break

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

	# XMOD-STR-006 — Planning package strategy_* for Downstream Usage.
	if frappe.db.exists("DocType", "Procurement Package"):
		pkg_name = frappe.db.get_value(
			"Procurement Package",
			{"package_code": SEED_PACKAGE_CODE},
			"name",
		)
		if not pkg_name:
			try:
				from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
					seed_procurement_planning_works_master,
				)

				seed_procurement_planning_works_master(
					checkpoint="PACKAGE_DRAFT", force_reset=False
				)
			except Exception:
				frappe.log_error(title="moh_downstream_usage: PP2 package seed skipped")
			pkg_name = frappe.db.get_value(
				"Procurement Package",
				{"package_code": SEED_PACKAGE_CODE},
				"name",
			)
		if pkg_name and _link_consumer("Procurement Package", pkg_name, target_name):
			linked["package"] = pkg_name

	return {
		"ok": bool(linked["demand"] or linked["budget_line"] or linked["package"]),
		"linked": linked,
	}


def seed_moh_performance_contribution_depth(
	plan_name: str | None = None,
	target_name: str | None = None,
) -> dict[str, Any]:
	"""XMOD-STR-007 — link downstream refs + apply Included treatments for Required PVCs."""
	base = seed_moh_downstream_usage_refs(plan_name=plan_name, target_name=target_name)
	linked = dict(base.get("linked") or {})
	# DIA Demand Value Treatment wiring retired with Demand Intake teardown.
	treated = 0

	package_name = linked.get("package")
	if package_name and frappe.db.has_column("Procurement Package", "estimated_value"):
		cur = frappe.db.get_value("Procurement Package", package_name, "estimated_value")
		if not cur or float(cur or 0) <= 0:
			frappe.db.set_value(
				"Procurement Package",
				package_name,
				"estimated_value",
				12_500_000,
				update_modified=False,
			)

	return {
		"ok": bool(base.get("ok")),
		"linked": linked,
		"required_treatments_applied": treated,
	}
