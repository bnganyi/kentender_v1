# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-006 / PLN-AC-013 / PLN-AC-014."""

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

	def test_combines_second_demand_with_reason_and_lineage(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Aggregate plan")
		d1 = make_approved_demand(title="Primary agg demand")
		d2 = make_approved_demand(title="Secondary agg demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d1["demand"], user=planner)
		result = aggregate_plan_allocations(
			plan_item=added["plan_item"],
			demand=d2["demand"],
			aggregation_reason="Compatible ICT scope under same PE",
			user=planner,
		)
		self.assertTrue(result["ok"])
		self.assertFalse(result["expected_benefit_realised"])
		count = frappe.db.count(
			"Plan Demand Allocation",
			{"plan_item": added["plan_item"], "status": "Draft"},
		)
		self.assertGreaterEqual(count, 2)
		iv = frappe.db.get_value(
			"Procurement Plan Item", added["plan_item"], "draft_item_version"
		)
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item Version", iv, "aggregation_decision"),
			"Combine",
		)
		self.assertTrue(
			frappe.db.get_value("Procurement Plan Item Version", iv, "aggregation_reason")
		)

	def test_anti_split_blocks_parallel_items(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Anti split plan")
		d1 = make_approved_demand(title="Split A")
		d2 = make_approved_demand(title="Split B")
		a = add_demand_to_plan(plan=plan["plan"], demand=d1["demand"], user=planner)
		b = add_demand_to_plan(plan=plan["plan"], demand=d2["demand"], user=planner)
		# Try to put d1 again onto b's item while it already lives on a — anti-split.
		with self.assertRaises(Exception) as ctx:
			aggregate_plan_allocations(
				plan_item=b["plan_item"],
				demand=d1["demand"],
				aggregation_reason="attempt split",
				user=planner,
			)
		self.assertIn("anti-splitting", str(ctx.exception).lower())
		self.assertTrue(a["plan_item"])
