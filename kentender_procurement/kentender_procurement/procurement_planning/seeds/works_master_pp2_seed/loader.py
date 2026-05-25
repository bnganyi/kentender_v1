# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP2 WORKS master planning seed — orchestration, reset, summary (spec §19–§21)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	CHECKPOINT_ORDER,
	DEFAULT_CHECKPOINT,
	DEMAND_CODE,
	INCLUSION_CODE,
	PKGREL_CODE,
	PKG_CODE,
	PLAN_CODE,
	SEED_ACTOR,
	TENDER_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.consumption import (
	ensure_release_consumed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.audit_events import (
	ensure_planning_audit_events,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.inclusion import (
	ensure_planning_inclusion,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.method_decision import (
	ensure_method_decision,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.package import (
	ensure_master_package,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.plan import (
	ensure_procurement_plan,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.readiness_review import (
	ensure_review_readiness_and_ready,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.release import (
	ensure_planning_release,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.upstream import (
	validate_upstream_for_checkpoint,
)


def _checkpoint_index(checkpoint: str) -> int:
	cp = (checkpoint or DEFAULT_CHECKPOINT).strip().upper()
	try:
		return CHECKPOINT_ORDER.index(cp)
	except ValueError:
		frappe.throw(f"Unsupported checkpoint: {checkpoint}", title="INVALID_CHECKPOINT")


def clear_master_planning_seed() -> dict[str, Any]:
	"""Delete PP2 master planning rows by stable business codes (dev/test reset)."""
	from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.clear import (
		run_clear,
	)

	return run_clear(skip_guard=True)


def _count_audit_events() -> int:
	return frappe.db.count(
		"Planning Audit Event",
		{
			"journey_code": "JRN-MOH-2026-001",
			"is_master_seed": 1,
		},
	)


def build_summary(*, checkpoint: str, ok: bool, failures: list[str] | None = None) -> dict[str, Any]:
	return {
		"module": "Procurement Planning v2",
		"scenario": "District Hospital Renovation Works",
		"checkpoint": checkpoint,
		"ok": ok,
		"records": {
			"procurement_plans": 1 if frappe.db.exists("Procurement Plan", PLAN_CODE) else 0,
			"planning_inclusions": 1 if frappe.db.exists("Procurement Handoff Card", INCLUSION_CODE) else 0,
			"procurement_packages": 1 if frappe.db.exists("Procurement Package", PKG_CODE) else 0,
			"package_lines": frappe.db.count(
				"Procurement Package Line", {"package_id": PKG_CODE, "is_active": 1}
			),
			"method_decisions": frappe.db.count("Package Method Decision", {"package_code": PKG_CODE}),
			"readiness_results": frappe.db.count("Package Readiness Result", {"package_code": PKG_CODE}),
			"review_decisions": frappe.db.count("Package Review Decision", {"package_code": PKG_CODE}),
			"planning_releases": 1 if frappe.db.exists("Procurement Handoff Card", PKGREL_CODE) else 0,
			"consumption_records": frappe.db.count(
				"Planning Release Consumption Record", {"release_code": PKGREL_CODE}
			),
			"audit_events": _count_audit_events(),
		},
		"links": {
			"demand": DEMAND_CODE,
			"package": PKG_CODE if frappe.db.exists("Procurement Package", PKG_CODE) else "",
			"release": PKGREL_CODE if frappe.db.exists("Procurement Handoff Card", PKGREL_CODE) else "",
			"tender": TENDER_CODE if frappe.db.exists("TM2 Tender", TENDER_CODE) else "",
		},
		"failures": failures or [],
	}


def run_load(*, checkpoint: str = DEFAULT_CHECKPOINT, force_reset: bool = False) -> dict[str, Any]:
	frappe.set_user(SEED_ACTOR)
	checkpoint = (checkpoint or DEFAULT_CHECKPOINT).strip().upper()
	idx = _checkpoint_index(checkpoint)

	if force_reset:
		clear_master_planning_seed()

	upstream = validate_upstream_for_checkpoint(checkpoint)
	if not upstream.get("ok"):
		summary = build_summary(checkpoint=checkpoint, ok=False, failures=[upstream.get("message") or ""])
		return {**upstream, **summary}

	steps_run: list[str] = []

	if idx >= _checkpoint_index("INCLUDED_IN_PLAN"):
		ensure_procurement_plan()
		steps_run.append("plan")
		ensure_planning_inclusion()
		steps_run.append("inclusion")

	if idx >= _checkpoint_index("PACKAGE_DRAFT"):
		ensure_master_package()
		steps_run.append("package")
		ensure_method_decision()
		steps_run.append("method_decision")

	if idx >= _checkpoint_index("READY_FOR_RELEASE"):
		ensure_review_readiness_and_ready()
		steps_run.append("readiness_review")

	if idx >= _checkpoint_index("RELEASED_TO_TENDER"):
		ensure_planning_release()
		steps_run.append("release")

	if idx >= _checkpoint_index("CONSUMED_BY_TENDER"):
		ensure_release_consumed()
		steps_run.append("consumption")

	if idx >= _checkpoint_index("INCLUDED_IN_PLAN"):
		ensure_planning_audit_events(checkpoint=checkpoint)
		steps_run.append("audit_events")

	frappe.db.commit()
	summary = build_summary(checkpoint=checkpoint, ok=True)
	return {
		"ok": True,
		"checkpoint": checkpoint,
		"force_reset": force_reset,
		"steps_run": steps_run,
		**summary,
	}
