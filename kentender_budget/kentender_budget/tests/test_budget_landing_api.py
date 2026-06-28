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

	def test_budget_rows_include_procuring_entity_code(self):
		"""W2-02: each row must include procuring_entity_name and procuring_entity_code."""
		frappe.set_user("Administrator")
		out = get_budget_landing_data()
		for row in out.get("budgets") or []:
			self.assertIn("procuring_entity_name", row)
			self.assertIn("procuring_entity_code", row)
			# Both must be strings (empty string is fine when entity not set)
			self.assertIsInstance(row["procuring_entity_name"], str)
			self.assertIsInstance(row["procuring_entity_code"], str)

	def test_health_status_uses_avail_pct_thresholds(self):
		"""W2-03: health_status must be one of the canonical values; Approved/Active
		rows must derive from available÷allocated ratio (<8 exhausted, 8-20 reviewing,
		>20 healthy)."""
		_valid = {"healthy", "reviewing", "exhausted", "submitted", "draft", "rejected"}
		frappe.set_user("Administrator")
		out = get_budget_landing_data()
		for row in out.get("budgets") or []:
			self.assertIn(row.get("health_status"), _valid,
				f"unexpected health_status '{row.get('health_status')}'")
			# For Approved/Active rows, verify threshold logic
			if row.get("status") in ("Approved", "Active"):
				avail_pct = flt(row.get("avail_pct", 100.0))
				hs = row["health_status"]
				if avail_pct < 8.0:
					self.assertEqual(hs, "exhausted",
						f"avail_pct={avail_pct:.1f}% expected exhausted, got {hs}")
				elif avail_pct <= 20.0:
					self.assertEqual(hs, "reviewing",
						f"avail_pct={avail_pct:.1f}% expected reviewing, got {hs}")
				else:
					self.assertEqual(hs, "healthy",
						f"avail_pct={avail_pct:.1f}% expected healthy, got {hs}")

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
