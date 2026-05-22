# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests import IntegrationTestCase

from kentender_budget.api.builder import get_budget_builder_data
from kentender_budget.api.landing import get_budget_landing_data
from kentender_budget.api.review import get_budget_review_data


class TestBudgetLandingAPI(IntegrationTestCase):
	def test_get_budget_landing_data_shape(self):
		frappe.set_user("Administrator")
		out = get_budget_landing_data()
		self.assertIn("portfolio", out)
		self.assertIn("budgets", out)
		p = out["portfolio"]
		for key in (
			"active_count",
			"draft_count",
			"submitted_count",
			"approved_count",
			"my_drafts_count",
			"rejected_count",
			"pending_approval_count",
			"total_budget_sum",
			"allocated_sum",
			"allocation_pct",
		):
			self.assertIn(key, p)

	def test_landing_budget_rows_include_strategic_plan_title(self):
		frappe.set_user("Administrator")
		out = get_budget_landing_data()
		for row in out.get("budgets") or []:
			self.assertIn("strategic_plan_title", row)

	def test_builder_totals_include_programs_funded(self):
		frappe.set_user("Administrator")
		budget = frappe.db.get_value("Budget", {"is_current_version": 1}, "name")
		if not budget:
			self.skipTest("No current-version budget on site")
		payload = get_budget_builder_data(budget)
		self.assertIn("programs_funded", payload.get("totals") or {})

	def test_review_payload_matches_builder_active_lines(self):
		frappe.set_user("Administrator")
		budget = frappe.db.get_value("Budget", {"is_current_version": 1}, "name")
		if not budget:
			self.skipTest("No current-version budget on site")
		review = get_budget_review_data(budget)
		builder = get_budget_builder_data(budget, lines_filter="active")
		self.assertEqual(review.get("budget", {}).get("name"), builder.get("budget", {}).get("name"))
		self.assertEqual(len(review.get("budget_lines") or []), len(builder.get("budget_lines") or []))
