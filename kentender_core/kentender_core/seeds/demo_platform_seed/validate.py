# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Validate demo platform seed invariants."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds.demo_platform_seed.constants import (
	CFG_GATE_READY,
	CFG_WALKABLE,
	DEMAND_DRAFT,
	DEMAND_PENDING_HOD,
	PE_MOE,
	PE_MOH,
)
from kentender_core.seeds.stable_platform_seed.constants import (
	IT_DEMAND_CODE,
	IT_PKG_CODE,
	PE_CODE,
	WORKS_DEMAND_CODE,
	WORKS_PLAN_CODE,
)


def validate_demo_platform_seed() -> dict[str, Any]:
	checks: list[dict[str, Any]] = []

	def ok(name: str, passed: bool, detail: str = "") -> None:
		checks.append({"name": name, "ok": passed, "detail": detail})

	ok("pe_moh", bool(frappe.db.exists("Procuring Entity", PE_MOH)), PE_MOH)
	ok("pe_moe", bool(frappe.db.exists("Procuring Entity", PE_MOE)), PE_MOE)
	ok("legacy_moh_absent", not frappe.db.exists("Procuring Entity", "MOH"))
	ok("legacy_doe_absent", not frappe.db.exists("Procuring Entity", "PE-DOE"))

	ok("works_demand", bool(frappe.db.exists("Demand", {"demand_id": WORKS_DEMAND_CODE})))
	ok("it_demand", bool(frappe.db.exists("Demand", {"demand_id": IT_DEMAND_CODE})))
	ok("plan", bool(frappe.db.exists("Procurement Plan", {"plan_code": WORKS_PLAN_CODE}))
	   or bool(frappe.db.exists("Procurement Plan", WORKS_PLAN_CODE)))
	ok("it_package", bool(frappe.db.exists("Procurement Package", IT_PKG_CODE)))

	ok(
		"demand_draft",
		bool(frappe.db.exists("Demand", {"demand_id": DEMAND_DRAFT, "status": "Draft"})),
	)
	ok(
		"demand_pending_hod",
		bool(
			frappe.db.exists(
				"Demand", {"demand_id": DEMAND_PENDING_HOD, "status": "Pending HoD Approval"}
			)
		),
	)

	ok(
		"cfg_walkable",
		bool(
			frappe.db.exists(
				"Tender Configuration",
				{"configuration_ref": CFG_WALKABLE, "procuring_entity_code": PE_MOH},
			)
		),
	)
	ok(
		"cfg_gate_ready",
		bool(frappe.db.exists("Tender Configuration", {"configuration_ref": CFG_GATE_READY})),
	)

	demo_cfgs = frappe.get_all(
		"Tender Configuration",
		filters={"procuring_entity_code": PE_MOH, "configuration_ref": ("like", "DEMO-MOH-2026%")},
		pluck="name",
	)
	pub_receiving = []
	if demo_cfgs:
		pub_receiving = frappe.get_all(
			"IT Tender Publication Record",
			filters={"status": "Published", "configuration": ("in", demo_cfgs)},
			limit=5,
		)
	ok("published_pe_moh", bool(pub_receiving), f"count={len(pub_receiving)}")

	opened = frappe.get_all("IT Bid Opening Record", filters={"status": "Completed"}, limit=1)
	ok("bid_opening_completed", bool(opened))

	# Home preferred entities should resolve to clean set
	from kentender_procurement.procurement_home.services.home_context import list_available_entities

	entities = list_available_entities("Administrator")
	ids = [e["id"] for e in entities]
	ok("home_has_pe_moh", PE_MOH in ids, str(ids))
	ok("home_has_pe_moe", PE_MOE in ids, str(ids))
	ok("home_no_pe_doe", "PE-DOE" not in ids, str(ids))
	ok("home_no_legacy_moh", "MOH" not in ids, str(ids))

	ok("stable_pe_code", PE_CODE == PE_MOH)

	failed = [c for c in checks if not c["ok"]]
	return {
		"ok": not failed,
		"checks": checks,
		"failed": failed,
		"entity_ids": ids,
	}
