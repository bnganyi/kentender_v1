# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Load PP2 WORKS planning without importing the full loader module graph."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	CHECKPOINT_ORDER,
	DEFAULT_CHECKPOINT,
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


def load_works_planning_checkpoint(
	*,
	checkpoint: str = DEFAULT_CHECKPOINT,
	force_reset: bool = False,
) -> dict[str, Any]:
	"""Run PP2 WORKS planning seed steps up to ``checkpoint``."""
	frappe.set_user("Administrator")
	checkpoint = (checkpoint or DEFAULT_CHECKPOINT).strip().upper()
	idx = _checkpoint_index(checkpoint)

	if force_reset:
		from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.clear import (
			run_clear,
		)

		run_clear(skip_guard=True)

	upstream = validate_upstream_for_checkpoint(checkpoint)
	if not upstream.get("ok"):
		return {**upstream, "checkpoint": checkpoint, "ok": False}

	steps_run: list[str] = []

	if idx >= _checkpoint_index("INCLUDED_IN_PLAN"):
		from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.plan import (
			ensure_procurement_plan,
		)
		from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.inclusion import (
			ensure_planning_inclusion,
		)

		ensure_procurement_plan()
		steps_run.append("plan")
		ensure_planning_inclusion()
		steps_run.append("inclusion")

	if idx >= _checkpoint_index("PACKAGE_DRAFT"):
		from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.package import (
			ensure_master_package,
		)
		from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.method_decision import (
			ensure_method_decision,
		)

		ensure_master_package()
		steps_run.append("package")
		ensure_method_decision()
		steps_run.append("method_decision")

	if idx >= _checkpoint_index("READY_FOR_RELEASE"):
		from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.readiness_review import (
			ensure_review_readiness_and_ready,
		)

		ensure_review_readiness_and_ready()
		steps_run.append("readiness_review")

	if idx >= _checkpoint_index("RELEASED_TO_TENDER"):
		from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.release import (
			ensure_planning_release,
		)

		ensure_planning_release()
		steps_run.append("release")

	if idx >= _checkpoint_index("CONSUMED_BY_TENDER"):
		from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.consumption import (
			ensure_release_consumed,
		)

		ensure_release_consumed()
		steps_run.append("consumption")

	if idx >= _checkpoint_index("INCLUDED_IN_PLAN"):
		from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.audit_events import (
			ensure_planning_audit_events,
		)

		ensure_planning_audit_events(checkpoint=checkpoint)
		steps_run.append("audit_events")

	frappe.db.commit()

	from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
		INCLUSION_CODE,
		PKGREL_CODE,
		PKG_CODE,
		PLAN_CODE,
		TENDER_CODE,
	)
	from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
		JOURNEY_CODE,
	)

	summary = {
		"module": "Procurement Planning v2",
		"scenario": "District Hospital Renovation Works",
		"checkpoint": checkpoint,
		"ok": True,
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
			"audit_events": frappe.db.count(
				"Planning Audit Event",
				{"journey_code": JOURNEY_CODE, "is_master_seed": 1},
			),
		},
		"links": {
			"demand": "DEM-MOH-2026-001",
			"package": PKG_CODE if frappe.db.exists("Procurement Package", PKG_CODE) else "",
			"release": PKGREL_CODE if frappe.db.exists("Procurement Handoff Card", PKGREL_CODE) else "",
			"tender": TENDER_CODE if frappe.db.exists("TM2 Tender", TENDER_CODE) else "",
		},
		"failures": [],
	}
	return {
		"ok": True,
		"checkpoint": checkpoint,
		"force_reset": force_reset,
		"steps_run": steps_run,
		**summary,
	}
