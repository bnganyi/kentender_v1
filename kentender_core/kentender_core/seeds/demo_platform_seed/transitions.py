# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Post-seed transition smoke probes (read-mostly + safe advances)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.seeds.demo_platform_seed.constants import (
	CFG_GATE_READY,
	CFG_WALKABLE,
	DEMAND_DRAFT,
	DEMAND_PENDING_HOD,
)


def probe_demo_platform_transitions(*, mutate: bool = False) -> dict[str, Any]:
	"""Exercise next-step APIs for seeded walkable/gate-ready records.

	When mutate=False (default), only read/probe readiness without changing lifecycle.
	When mutate=True, may submit a clone demand or open a sealed pub (destructive to that pub).
	"""
	frappe.set_user("Administrator")
	probes: list[dict[str, Any]] = []

	def add(name: str, ok: bool, detail: Any = None) -> None:
		probes.append({"name": name, "ok": ok, "detail": detail})

	# DIA — walkable draft exists and is Draft
	draft = frappe.db.get_value(
		"Demand", {"demand_id": DEMAND_DRAFT}, ["name", "status"], as_dict=True
	)
	add("dia_draft_present", bool(draft and draft.status == "Draft"), draft)

	hod = frappe.db.get_value(
		"Demand",
		{"demand_id": DEMAND_PENDING_HOD},
		["name", "status"],
		as_dict=True,
	)
	add(
		"dia_pending_hod_present",
		bool(hod and hod.status == "Pending HoD Approval"),
		hod,
	)

	# CFG walkable — configuration home / steps
	try:
		from kentender_procurement.tender_configurations.services.configuration_home import (
			get_configuration_home,
		)

		home = get_configuration_home(CFG_WALKABLE)
		steps = (home or {}).get("steps") or (home or {}).get("configuration_steps") or []
		add(
			"cfg_walkable_home",
			bool(home) and (bool(steps) or bool((home or {}).get("configuration_ref"))),
			{"keys": list((home or {}).keys())[:12], "step_count": len(steps) if steps else 0},
		)
	except Exception as exc:  # noqa: BLE001
		add("cfg_walkable_home", False, str(exc))

	# CFG gate-ready — must pass live readiness with zero blockers
	try:
		from kentender_procurement.tender_configurations.services.readiness import (
			_build_findings_and_checklist,
		)

		_findings, _checklist, blockers, warnings = _build_findings_and_checklist(
			CFG_GATE_READY
		)
		add(
			"cfg_gate_ready_readiness",
			int(blockers or 0) == 0,
			{
				"blocker_count": blockers,
				"warning_count": warnings,
				"status": frappe.db.get_value("Tender Configuration", CFG_GATE_READY, "status"),
			},
		)
	except Exception as exc:  # noqa: BLE001
		std = frappe.db.get_value("Tender Configuration", CFG_GATE_READY, "std_version")
		status = frappe.db.get_value("Tender Configuration", CFG_GATE_READY, "status")
		add(
			"cfg_gate_ready_readiness",
			False,
			{"error": str(exc), "std": std, "status": status},
		)

	# Bid sealed / open probes — the legacy bid-submission slice was retired by
	# BDS-CHG-001 v0.8 Phase 1; the new Bid Submission module owns bids.
	add("bid_landing_stages", True, "skipped: BID_SUBMISSION_MODULE_RETIRED")

	# Optional DIA submit mutate — retired with Demand Intake teardown.
	if mutate and draft:
		add(
			"dia_submit_mutate",
			True,
			"skipped: DEMAND_MODULE_RETIRED",
		)
	elif mutate:
		add("dia_submit_mutate", True, "skipped: no draft / DEMAND_MODULE_RETIRED")

	failed = [p for p in probes if not p["ok"]]
	return {"ok": not failed, "probes": probes, "failed": failed, "mutate": mutate}
