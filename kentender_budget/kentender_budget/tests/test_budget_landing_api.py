# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests import IntegrationTestCase

from kentender_budget.api.landing import get_budget_landing_data


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
