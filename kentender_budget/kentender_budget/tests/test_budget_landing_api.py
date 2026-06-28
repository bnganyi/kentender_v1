# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_budget.api.builder import get_budget_builder_data
from kentender_budget.api.landing import get_budget_landing_data
from kentender_budget.api.review import get_budget_review_data
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity


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

	def test_portfolio_includes_financial_sums(self):
		"""W1-01 / W2-01: portfolio must expose reserved_sum, committed_sum, consumed_sum, available_sum."""
		frappe.set_user("Administrator")
		out = get_budget_landing_data()
		p = out["portfolio"]
		for key in ("reserved_sum", "committed_sum", "consumed_sum", "available_sum"):
			self.assertIn(key, p, f"portfolio missing '{key}'")
		# All must be non-negative floats
		self.assertGreaterEqual(flt(p["reserved_sum"]), 0.0)
		self.assertGreaterEqual(flt(p["committed_sum"]), 0.0)
		self.assertGreaterEqual(flt(p["consumed_sum"]), 0.0)
		self.assertGreaterEqual(flt(p["available_sum"]), 0.0)

	def test_budget_rows_include_financial_fields(self):
		"""W1-01 / W2-01: per-budget rows must have committed_amount, consumed_amount, consumption_pct, health_status."""
		frappe.set_user("Administrator")
		out = get_budget_landing_data()
		for row in out.get("budgets") or []:
			for key in ("committed_amount", "consumed_amount", "consumption_pct",
			            "health_status", "procuring_entity_name"):
				self.assertIn(key, row, f"budget row missing '{key}'")
			# consumption_pct in [0, 100]
			pct = flt(row["consumption_pct"])
			self.assertGreaterEqual(pct, 0.0)
			self.assertLessEqual(pct, 100.0 + 1e-6)

	def test_budget_rows_consumed_amount_non_negative(self):
		"""W2-01: consumed_amount must be ≥ 0 for all rows."""
		frappe.set_user("Administrator")
		out = get_budget_landing_data()
		for row in out.get("budgets") or []:
			self.assertGreaterEqual(flt(row["consumed_amount"]), 0.0)

	def test_budget_rows_committed_amount_non_negative(self):
		"""W1-01: committed_amount must be ≥ 0 for all rows."""
		frappe.set_user("Administrator")
		out = get_budget_landing_data()
		for row in out.get("budgets") or []:
			self.assertGreaterEqual(flt(row["committed_amount"]), 0.0)

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
