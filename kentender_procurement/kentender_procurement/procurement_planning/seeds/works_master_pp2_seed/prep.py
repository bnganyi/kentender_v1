# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared WORKS master seed prep helpers for queue eligibility tests and P5 golden path."""

from __future__ import annotations

import frappe

from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	INCLUSION_CODE,
	PLAN_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.plan import (
	ensure_procurement_plan,
)


def ensure_works_demand_queue_ready() -> None:
	"""Reset master planning seed and deactivate orphan lines blocking WORKS demand eligibility."""
	clear_master_planning_seed()
	for row in frappe.get_all(
		"Procurement Package Line",
		filters={"demand_item_code": DEMAND_ITEM_CODE, "is_active": 1},
		fields=["name"],
	):
		frappe.db.set_value(
			"Procurement Package Line",
			row.name,
			"is_active",
			0,
			update_modified=False,
		)
	demand_name = frappe.db.get_value("Demand", {"demand_id": DEMAND_CODE}, "name")
	if demand_name:
		for row in frappe.get_all(
			"Procurement Package Line",
			filters={"demand_id": demand_name, "is_active": 1},
			fields=["name"],
		):
			frappe.db.set_value(
				"Procurement Package Line",
				row.name,
				"is_active",
				0,
				update_modified=False,
			)
	for row in frappe.get_all(
		"Procurement Package",
		filters={"planning_inclusion_code": INCLUSION_CODE, "is_active": 1},
		fields=["name"],
	):
		frappe.db.set_value(
			"Procurement Package",
			row.name,
			"is_active",
			0,
			update_modified=False,
		)
	# clear_master_planning_seed removes PLAN-MOH-2026; restore active plan so Workbench
	# and queue prep tests do not leave the site without a golden-path active plan.
	ensure_procurement_plan()
	if frappe.db.exists("Procurement Plan", PLAN_CODE):
		frappe.db.set_value(
			"Procurement Plan",
			PLAN_CODE,
			{"status": PLAN_ACTIVE, "is_active": 1},
			update_modified=True,
		)
	frappe.db.commit()
