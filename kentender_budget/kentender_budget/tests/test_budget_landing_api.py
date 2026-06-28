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

	def test_budget_rows_include_primary_line_name(self):
		"""W2-04: each row must include primary_line_name (string, may be empty
		if no allocated lines exist)."""
		frappe.set_user("Administrator")
		out = get_budget_landing_data()
		for row in out.get("budgets") or []:
			self.assertIn("primary_line_name", row,
				"budget row missing 'primary_line_name'")
			self.assertIsInstance(row["primary_line_name"], str)

	def test_landing_budget_rows_include_strategic_plan_title(self):
		frappe.set_user("Administrator")
		out = get_budget_landing_data()
		for row in out.get("budgets") or []:
			self.assertIn("strategic_plan_title", row)
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


# ── W2-06: health_status threshold and edge case tests ────────────────────────

def _make_health_budget(
	allocated: float,
	reserved: float = 0.0,
	committed: float = 0.0,
	consumed: float = 0.0,
	*,
	status: str = "Approved",
):
	"""Create a minimal Approved/Draft Budget + Budget Line for health_status testing.
	Returns the Budget doc (already status-promoted via set_value).
	No tearDown needed — IntegrationTestCase rolls back the transaction.
	"""
	ensure_currency_kes()
	h = frappe.generate_hash(length=6)
	entity = ensure_procuring_entity(f"HL-{h}", f"Health Test {h}")
	plan = frappe.get_doc({
		"doctype": "Strategic Plan",
		"strategic_plan_name": f"Plan-HL-{h}",
		"procuring_entity": entity,
		"start_year": 2026,
		"end_year": 2030,
		"status": "Draft",
		"version_no": 1,
		"is_current_version": 1,
	}).insert(ignore_permissions=True)
	prog = frappe.get_doc({
		"doctype": "Strategy Program",
		"strategic_plan": plan.name,
		"program_title": f"Prog-HL-{h}",
		"order_index": 1,
	}).insert(ignore_permissions=True)
	bud = frappe.get_doc({
		"doctype": "Budget",
		"budget_name": f"BUD-HL-{h}",
		"procuring_entity": entity,
		"fiscal_year": 2026,
		"strategic_plan": plan.name,
		"currency": "KES",
		"total_budget_amount": allocated or 1_000_000,
		"version_no": 1,
		"is_current_version": 1,
		"order_index": 0,
	}).insert(ignore_permissions=True)

	if allocated > 0:
		frappe.get_doc({
			"doctype": "Budget Line",
			"budget_line_code": f"BL-HL-{h}",
			"budget_line_name": f"Health Line {h}",
			"budget": bud.name,
			"procuring_entity": entity,
			"fiscal_year": 2026,
			"amount_allocated": allocated,
			"amount_reserved": reserved,
			"amount_committed": committed,
			"amount_consumed": consumed,
			"currency": "KES",
			"strategic_plan": plan.name,
			"program": prog.name,
			"is_active": 1,
		}).insert(ignore_permissions=True)

	frappe.db.set_value("Budget", bud.name, "status", status)
	return bud


def _health_row(bname: str) -> dict:
	frappe.set_user("Administrator")
	out = get_budget_landing_data()
	return next((r for r in out["budgets"] if r["name"] == bname), {})


class TestHealthStatusEdgeCases(IntegrationTestCase):
	"""W2-06 — health_status threshold and edge-case coverage.

	Thresholds (available ÷ allocated × 100):
	  < 8%        → exhausted
	  8% ≤ x ≤ 20% → reviewing
	  > 20%       → healthy

	Edge cases:
	  allocated = 0      → avail_pct defaults to 100 → healthy
	  available = 0      → avail_pct = 0 → exhausted
	  Draft status       → health_status = "draft" regardless of amounts
	"""

	def test_healthy_above_20_pct(self):
		"""avail = 500 000 / 1 000 000 = 50% → healthy."""
		bud = _make_health_budget(allocated=1_000_000, reserved=500_000)
		row = _health_row(bud.name)
		self.assertAlmostEqual(flt(row.get("avail_pct")), 50.0, places=1)
		self.assertEqual(row.get("health_status"), "healthy")

	def test_reviewing_at_12_pct(self):
		"""avail = 120 000 / 1 000 000 = 12% (8–20%) → reviewing."""
		bud = _make_health_budget(allocated=1_000_000, reserved=880_000)
		row = _health_row(bud.name)
		self.assertAlmostEqual(flt(row.get("avail_pct")), 12.0, places=1)
		self.assertEqual(row.get("health_status"), "reviewing")

	def test_exhausted_at_3_pct(self):
		"""avail = 30 000 / 1 000 000 = 3% (< 8%) → exhausted."""
		bud = _make_health_budget(allocated=1_000_000, reserved=970_000)
		row = _health_row(bud.name)
		self.assertAlmostEqual(flt(row.get("avail_pct")), 3.0, places=1)
		self.assertEqual(row.get("health_status"), "exhausted")

	def test_boundary_exactly_8_pct_is_reviewing(self):
		"""avail = 80 000 / 1 000 000 = exactly 8% → reviewing (inclusive lower bound)."""
		bud = _make_health_budget(allocated=1_000_000, reserved=920_000)
		row = _health_row(bud.name)
		self.assertAlmostEqual(flt(row.get("avail_pct")), 8.0, places=1)
		self.assertEqual(row.get("health_status"), "reviewing")

	def test_boundary_exactly_20_pct_is_reviewing(self):
		"""avail = 200 000 / 1 000 000 = exactly 20% → reviewing (inclusive upper bound)."""
		bud = _make_health_budget(allocated=1_000_000, reserved=800_000)
		row = _health_row(bud.name)
		self.assertAlmostEqual(flt(row.get("avail_pct")), 20.0, places=1)
		self.assertEqual(row.get("health_status"), "reviewing")

	def test_just_above_20_pct_is_healthy(self):
		"""avail = 201 000 / 1 000 000 = 20.1% → healthy (just above reviewing ceiling)."""
		bud = _make_health_budget(allocated=1_000_000, reserved=799_000)
		row = _health_row(bud.name)
		self.assertGreater(flt(row.get("avail_pct")), 20.0)
		self.assertEqual(row.get("health_status"), "healthy")

	def test_edge_all_consumed_is_exhausted(self):
		"""Edge: amount_available = 0 (fully obligated) → avail_pct = 0 → exhausted."""
		bud = _make_health_budget(allocated=1_000_000, consumed=1_000_000)
		row = _health_row(bud.name)
		self.assertAlmostEqual(flt(row.get("avail_pct")), 0.0, places=1)
		self.assertEqual(row.get("health_status"), "exhausted")

	def test_edge_zero_allocated_is_healthy(self):
		"""Edge: no Budget Lines (allocated = 0) → avail_pct defaults to 100 → healthy."""
		bud = _make_health_budget(allocated=0)
		row = _health_row(bud.name)
		self.assertAlmostEqual(flt(row.get("avail_pct")), 100.0, places=1)
		self.assertEqual(row.get("health_status"), "healthy")

	def test_draft_status_ignores_financial_amounts(self):
		"""Draft budgets always return health_status='draft' regardless of available amount."""
		bud = _make_health_budget(allocated=1_000_000, reserved=990_000, status="Draft")
		row = _health_row(bud.name)
		self.assertEqual(row.get("health_status"), "draft")

	def test_submitted_status_returns_submitted(self):
		"""Submitted budgets return health_status='submitted' (pending review)."""
		bud = _make_health_budget(allocated=1_000_000, status="Submitted")
		row = _health_row(bud.name)
		self.assertEqual(row.get("health_status"), "submitted")
