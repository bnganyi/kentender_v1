# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Validate demo platform seed invariants."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

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
	# Gate-ready must pass live readiness (never status-theater / empty CFG blobs).
	# Use the read-only findings builder — run_readiness_check can TimestampMismatch
	# when CFG probes touch the same document mid-save.
	try:
		from kentender_procurement.tender_configurations.services.readiness import (
			_build_findings_and_checklist,
		)

		if frappe.db.exists("Tender Configuration", CFG_GATE_READY):
			_findings, _checklist, blockers, warnings = _build_findings_and_checklist(
				CFG_GATE_READY
			)
			ok(
				"cfg_gate_ready_zero_blockers",
				int(blockers or 0) == 0,
				f"blockers={blockers} warnings={warnings}",
			)
			ok(
				"cfg_gate_ready_zero_warnings",
				int(warnings or 0) == 0,
				f"warnings={warnings}",
			)
		else:
			ok("cfg_gate_ready_zero_blockers", False, "missing CFG_GATE_READY")
			ok("cfg_gate_ready_zero_warnings", False, "missing CFG_GATE_READY")
	except Exception as exc:  # noqa: BLE001
		ok("cfg_gate_ready_zero_blockers", False, str(exc))
		ok("cfg_gate_ready_zero_warnings", False, str(exc))

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

	# Bidder portal: Open ≠ officer Published. Past-deadline pubs are Closed on /tenders.
	try:
		from kentender_procurement.tender_configurations.services.available_tenders import (
			STATUS_CLOSED,
			STATUS_OPEN,
			list_available_tenders,
		)

		open_list = list_available_tenders({"status": STATUS_OPEN}, user="Guest", page_size=50)
		closed_list = list_available_tenders({"status": STATUS_CLOSED}, user="Guest", page_size=50)
		open_total = int((open_list.get("pagination") or {}).get("total") or 0)
		closed_total = int((closed_list.get("pagination") or {}).get("total") or 0)
		open_titles = [
			cstr((t or {}).get("title") or (t or {}).get("tender_title") or "")
			for t in (open_list.get("tenders") or [])
		]
		# At least two open receiving tenders; sealed/opened land under Closed.
		ok(
			"portal_open_count",
			open_total >= 2,
			f"open={open_total} titles={open_titles[:5]}",
		)
		ok(
			"portal_closed_has_past_deadline",
			closed_total >= 2,
			f"closed={closed_total}",
		)
		joined = " | ".join(open_titles).lower()
		ok(
			"portal_titles_no_demo_prefix",
			"demo published" not in joined
			and "demo sealed" not in joined
			and "demo opened" not in joined
			and not any(t.lower().startswith("demo ") for t in open_titles if t),
			joined[:200],
		)
	except Exception as exc:  # noqa: BLE001
		ok("portal_open_count", False, str(exc))
		ok("portal_closed_has_past_deadline", False, str(exc))
		ok("portal_titles_no_demo_prefix", False, str(exc))

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
