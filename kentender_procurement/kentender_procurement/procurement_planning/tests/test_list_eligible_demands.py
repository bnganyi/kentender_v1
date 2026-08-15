# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-003 / PLN-AC-002 — eligible Demands queue."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services.list_eligible_demands import (
	list_eligible_demands,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	attach_demand_funding,
	create_plan_as_planner,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
	make_test_budget_line,
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

	def test_excludes_returned_but_does_not_trust_aggregate_usage_flag(self) -> None:
		planner = ensure_planner_user()
		plan = create_plan_as_planner(title="Exclude queue plan")
		returned = make_approved_demand(title="Returned demand")
		frappe.db.set_value("Demand", returned["demand"], "status", "Returned")
		fully = make_approved_demand(title="Fully planned demand")
		frappe.db.set_value("Demand", fully["demand"], "planning_usage", "Fully planned")
		payload = list_eligible_demands(plan=plan["plan"], user=planner)
		ids = {r["demand"] for r in payload["demands"]}
		self.assertNotIn(returned["demand"], ids)
		# Eligibility is per Need Item. A stale aggregate label cannot hide a
		# genuinely unheld item; active allocations are tested by formation.
		self.assertIn(fully["demand"], ids)

	def test_query_count_is_constant_with_funded_demand_growth(self) -> None:
		planner = ensure_planner_user()
		created = create_plan_as_planner()
		plan = frappe.get_doc("Procurement Plan", created["plan"])
		for index in range(3):
			demand = make_approved_demand(title=f"Bulk funded source {index}")
			funding = make_test_budget_line(
				approved_amount=2_000_000,
				fiscal_period=plan.financial_year,
				start_date=str(plan.period_start),
				end_date=str(plan.period_end),
				title=f"Bulk funding line {index}",
			)
			attach_demand_funding(
				demand=demand["demand"], budget_line=funding["budget_line"],
				budget=funding["budget"], amount=1_000_000,
			)
		with patch.object(frappe.db, "sql", wraps=frappe.db.sql) as many_sql:
			many = list_eligible_demands(plan=plan.name, user=planner)
		with patch.object(frappe.db, "sql", wraps=frappe.db.sql) as one_sql:
			one = list_eligible_demands(
				plan=plan.name, search="Bulk funded source 0", user=planner
			)
		self.assertGreaterEqual(len(many["demands"]), 3)
		self.assertEqual(len(one["demands"]), 1)
		self.assertLessEqual(abs(many_sql.call_count - one_sql.call_count), 1)
