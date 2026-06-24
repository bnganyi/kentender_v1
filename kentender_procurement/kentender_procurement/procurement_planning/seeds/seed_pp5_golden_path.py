# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5 golden path — Workbench Needs Planning starting state (P5-001+).

Run::

    bench --site kentender.midas.com execute \\
        kentender_procurement.procurement_planning.seeds.seed_pp5_golden_path.ensure_pp5_needs_planning_ready \\
        --kwargs '{"force_reset": True}'
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PLAN_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.prep import (
	ensure_works_demand_queue_ready,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.plan import (
	ensure_procurement_plan,
)


def ensure_pp5_needs_planning_ready(*, force_reset: bool = True) -> dict[str, Any]:
	"""Prepare P5-001 state: approved WORKS demand in Needs Planning with active plan, no inclusion."""
	if force_reset:
		ensure_works_demand_queue_ready()

	seed_out = seed_procurement_planning_works_master(
		checkpoint="APPROVED_DEMAND_READY",
		force_reset=force_reset,
	)
	if not seed_out.get("ok"):
		return {
			"ok": False,
			"checkpoint": "APPROVED_DEMAND_READY",
			"message": seed_out.get("message") or "WORKS master seed failed at APPROVED_DEMAND_READY.",
			"seed": seed_out,
		}

	plan_out = ensure_procurement_plan()
	# Ensure WORKS master plan wins within the current fiscal year context.
	if frappe.db.exists("Procurement Plan", PLAN_CODE):
		frappe.db.set_value(
			"Procurement Plan",
			PLAN_CODE,
			{"status": PLAN_ACTIVE, "is_active": 1},
			update_modified=True,
		)
	frappe.db.commit()

	return {
		"ok": True,
		"checkpoint": "APPROVED_DEMAND_READY",
		"plan_code": PLAN_CODE,
		"force_reset": force_reset,
		"seed": seed_out,
		"plan": plan_out,
	}
