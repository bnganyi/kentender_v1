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

	# Bid sealed — can_open probe
	try:
		from kentender_procurement.tender_configurations.services.bid_submissions import (
			get_bid_submission_sealed_status,
			list_bid_submission_tenders,
		)

		listed = list_bid_submission_tenders(page=1, page_size=50)
		rows = (listed or {}).get("rows") or []
		stages = {r.get("submission_stage") for r in rows}
		add(
			"bid_landing_stages",
			bool(rows)
			and bool(
				stages
				& {
					"Receiving submissions",
					"Closed and sealed",
					"Opened",
					"Released to evaluation",
				}
			),
			{"count": len(rows), "stages": sorted(stages)},
		)
		sealed_row = next(
			(r for r in rows if r.get("submission_stage") == "Closed and sealed"), None
		)
		if sealed_row:
			st = get_bid_submission_sealed_status(sealed_row["publication_id"])
			add(
				"bid_sealed_status",
				bool(st.get("status_label") or st.get("submission_stage")),
				{
					"can_open": st.get("can_open_submitted_bids"),
					"publication_id": sealed_row["publication_id"],
				},
			)
			if mutate and st.get("can_open_submitted_bids"):
				from kentender_procurement.tender_configurations.services.bid_submissions import (
					open_submitted_bids,
				)

				opened = open_submitted_bids(sealed_row["publication_id"])
				add(
					"bid_open_mutate",
					cstr(opened.get("submission_stage")) == "Opened"
					or bool(opened.get("opening_ref")),
					{
						"submission_stage": opened.get("submission_stage"),
						"opening_ref": opened.get("opening_ref"),
						"active_bids_opened": opened.get("active_bids_opened"),
					},
				)
		else:
			add("bid_sealed_status", False, "no sealed row")
	except Exception as exc:  # noqa: BLE001
		add("bid_landing_stages", False, str(exc))

	# Optional DIA submit mutate on a throwaway copy
	if mutate and draft:
		try:
			from kentender_procurement.demand_intake.api.lifecycle import submit_demand

			# Do not mutate the canonical demo draft — clone
			src = frappe.get_doc("Demand", draft.name)
			clone = frappe.copy_doc(src)
			clone.demand_id = f"{DEMAND_DRAFT}-SMOKE"
			clone.title = (src.title or "Demo") + " (transition smoke)"
			clone.status = "Draft"
			clone.insert(ignore_permissions=True)
			submit_demand(clone.name)
			new_status = frappe.db.get_value("Demand", clone.name, "status")
			add("dia_submit_mutate", new_status == "Pending HoD Approval", new_status)
			frappe.delete_doc("Demand", clone.name, force=True, ignore_permissions=True)
		except Exception as exc:  # noqa: BLE001
			add("dia_submit_mutate", False, str(exc))

	failed = [p for p in probes if not p["ok"]]
	return {"ok": not failed, "probes": probes, "failed": failed, "mutate": mutate}
