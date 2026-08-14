# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-GAP-FR-001 / PLN-AC-003 — post-formation aggregate is hard-denied."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.aggregate_plan_allocations import (
	aggregate_plan_allocations,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	create_plan_as_planner,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
)


class TestAggregatePlanAllocations(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def test_post_formation_aggregate_is_denied(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Aggregate deny plan")
		d1 = make_approved_demand(title="Primary agg demand")
		d2 = make_approved_demand(title="Secondary agg demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d1["demand"], user=planner)
		before = frappe.db.count(
			"Plan Demand Allocation",
			{"plan_item": added["plan_item"], "status": "Draft"},
		)
		result = aggregate_plan_allocations(
			plan_item=added["plan_item"],
			demand=d2["demand"],
			aggregation_reason="Compatible ICT scope under same PE",
			user=planner,
		)
		self.assertFalse(result.get("ok"))
		self.assertIn("form", result.get("errors") or {})
		self.assertIn("source", (result["errors"].get("form") or "").lower())
		self.assertEqual(
			frappe.db.count(
				"Plan Demand Allocation",
				{"plan_item": added["plan_item"], "status": "Draft"},
			),
			before,
		)

	def test_parallel_item_aggregate_is_denied(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Anti split deny plan")
		d1 = make_approved_demand(title="Split A")
		d2 = make_approved_demand(title="Split B")
		a = add_demand_to_plan(plan=plan["plan"], demand=d1["demand"], user=planner)
		b = add_demand_to_plan(plan=plan["plan"], demand=d2["demand"], user=planner)
		result = aggregate_plan_allocations(
			plan_item=b["plan_item"],
			demand=d1["demand"],
			aggregation_reason="attempt split",
			user=planner,
		)
		self.assertFalse(result.get("ok"))
		self.assertIn("form", result.get("errors") or {})
		self.assertTrue(a["plan_item"])
		self.assertEqual(
			frappe.db.count(
				"Plan Demand Allocation",
				{"plan_item": b["plan_item"], "demand": d1["demand"]},
			),
			0,
		)
