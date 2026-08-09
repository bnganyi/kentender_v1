# Copyright (c) 2026, KenTender and contributors
"""Link MOH demo Demand / Budget Line records to MOH-TGT-AVAIL-2028 for Downstream Usage."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_lifecycle.demand_module_gate import (
	demand_doctype_available,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	STRATEGY_PLAN_CODE,
	TARGET_CODE,
)
from kentender_strategy.services.strategy_consumer import apply_strategy_reference_to_doc

# Canonical Demands MVP-1 principal fixture (DEM-SEED-001).
SEED_DEMAND_CODES = ("DMD-MOH-2027-014",)
# Canonical MVP-1 Budget Line (Budget portfolio fixture).
SEED_BUDGET_LINE_CODE = "MOH-BL-DHI-2027"
# PP2 WORKS master package (PACKAGE_DRAFT+).
SEED_PACKAGE_CODE = "PKG-MOH-2026-001"
CANONICAL_DEMAND_TREATMENTS = {
	"MOH-PVC-EFT-01": (
		"Embedded in specification",
		"Infrastructure supports reliable critical health services",
	),
	"MOH-PVC-ECO-01": (
		"To be determined in Planning",
		"Whole-life costing, energy use and lifecycle optimisation must be resolved during plan preparation",
	),
	"MOH-PVC-RES-01": (
		"Contract obligation",
		"Redundancy, continuity and support requirements must carry forward",
	),
	"MOH-PVC-SUS-02": (
		"Delivery or disposal obligation",
		"Replaced ICT equipment requires controlled end-of-life handling",
	),
}


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


def _link_demand(name: str, plan_name: str, target_name: str) -> bool:
	"""Upsert the MVP Demand Strategy Reference related record."""
	target = frappe.db.get_value(
		"Performance Target",
		target_name,
		["target_code", "title"],
		as_dict=True,
	)
	if not target:
		return False
	values = {
		"plan": plan_name,
		"plan_version_id": plan_name,
		"target_id": target_name,
		"target_code": target.target_code,
		"target_name": target.title,
		"snapshot_label": f"{target.target_code} — {target.title}",
		"selection_source": "Canonical fixture",
	}
	reference = frappe.db.get_value(
		"Demand Strategy Reference",
		{"demand": name, "reference_type": "Primary"},
		"name",
	)
	if reference:
		frappe.db.set_value(
			"Demand Strategy Reference",
			reference,
			values,
			update_modified=False,
		)
	else:
		frappe.get_doc(
			{
				"doctype": "Demand Strategy Reference",
				"demand": name,
				"reference_type": "Primary",
				**values,
			}
		).insert(ignore_permissions=True)
	return True


def _apply_canonical_value_treatments(
	demand_name: str | None, plan_name: str | None
) -> int:
	"""Upsert the four canonical principal-Demand PVC treatments."""
	if not demand_name or not plan_name:
		return 0
	commitments = frappe.get_all(
		"Plan Value Commitment",
		filters={
			"plan_version": plan_name,
			"commitment_code": ["in", list(CANONICAL_DEMAND_TREATMENTS)],
		},
		fields=["name", "commitment_code"],
	)
	for pvc in commitments:
		treatment, rationale = CANONICAL_DEMAND_TREATMENTS[pvc.commitment_code]
		values = {
			"pvc_version_id": pvc.name,
			"pvc_snapshot": pvc.commitment_code,
			"applicability": "Applicable",
			"treatment": treatment,
			"rationale": rationale,
		}
		existing = frappe.db.get_value(
			"Demand Value Treatment",
			{"demand": demand_name, "plan_value_commitment": pvc.name},
			"name",
		)
		if existing:
			frappe.db.set_value(
				"Demand Value Treatment",
				existing,
				values,
				update_modified=False,
			)
		else:
			frappe.get_doc(
				{
					"doctype": "Demand Value Treatment",
					"demand": demand_name,
					"plan_value_commitment": pvc.name,
					**values,
				}
			).insert(ignore_permissions=True)
	return len(commitments)


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

	if demand_doctype_available():
		for code in SEED_DEMAND_CODES:
			demand_name = frappe.db.get_value("Demand", {"demand_code": code}, "name")
			if demand_name and _link_demand(demand_name, plan_name, target_name):
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
	"""DEM-INT-008 — link MVP Demand refs and address Required PVCs."""
	base = seed_moh_downstream_usage_refs(plan_name=plan_name, target_name=target_name)
	linked = dict(base.get("linked") or {})
	treated = _apply_canonical_value_treatments(
		linked.get("demand"),
		linked.get("plan"),
	)

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
