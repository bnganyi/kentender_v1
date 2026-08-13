# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-003 / PLN-AC-002 — eligible Demands queue."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services.list_eligible_demands import (
	list_eligible_demands,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	create_plan_as_planner,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
)


class TestListEligibleDemands(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def test_includes_approved_planning_ready_not_fully_planned(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Eligible queue plan")
		d = make_approved_demand(title="Eligible for queue")
		payload = list_eligible_demands(plan=plan["plan"], user=planner)
		self.assertTrue(payload["ok"])
		ids = {r["demand"] for r in payload["demands"]}
		self.assertIn(d["demand"], ids)
		row = next(r for r in payload["demands"] if r["demand"] == d["demand"])
		self.assertGreater(row["available_to_plan"], 0)
		self.assertEqual(row.get("status_label"), "Planning Ready")
		self.assertIn("proposed_funding", row)
		self.assertIn("display", row["proposed_funding"])
		self.assertIn("proposed_budget_line_display", row)

	def test_excludes_returned_and_fully_planned(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Exclude queue plan")
		returned = make_approved_demand(title="Returned demand")
		frappe.db.set_value("Demand", returned["demand"], "status", "Returned")
		fully = make_approved_demand(title="Fully planned demand")
		frappe.db.set_value("Demand", fully["demand"], "planning_usage", "Fully planned")
		payload = list_eligible_demands(plan=plan["plan"], user=planner)
		ids = {r["demand"] for r in payload["demands"]}
		self.assertNotIn(returned["demand"], ids)
		self.assertNotIn(fully["demand"], ids)
