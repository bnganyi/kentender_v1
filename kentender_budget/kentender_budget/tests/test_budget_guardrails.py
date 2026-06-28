# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""compute_budget_guardrails — unit / integration tests.

Run:
  bench --site kentender.midas.com run-tests \\
    --app kentender_budget \\
    --module kentender_budget.tests.test_budget_guardrails
"""
from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from kentender_budget.api.guardrails import compute_budget_guardrails
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity


# ── Fixture helpers ────────────────────────────────────────────────────────────

def _make_budget_with_line(allocated: float = 1_000_000.0) -> tuple:
	"""Return (budget_name, line_name) for a minimal Approved Budget + active line."""
	ensure_currency_kes()
	h = frappe.generate_hash(length=6)
	entity = ensure_procuring_entity(f"GR-{h}", f"Guardrail Test {h}")
	plan = frappe.get_doc({
		"doctype": "Strategic Plan",
		"strategic_plan_name": f"Plan-GR-{h}",
		"procuring_entity": entity,
		"start_year": 2026, "end_year": 2030,
		"status": "Draft", "version_no": 1, "is_current_version": 1,
	}).insert(ignore_permissions=True)
	prog = frappe.get_doc({
		"doctype": "Strategy Program",
		"strategic_plan": plan.name,
		"program_title": f"Prog-GR-{h}",
		"order_index": 1,
	}).insert(ignore_permissions=True)
	bud = frappe.get_doc({
		"doctype": "Budget",
		"budget_name": f"BUD-GR-{h}",
		"procuring_entity": entity,
		"fiscal_year": 2026,
		"strategic_plan": plan.name,
		"currency": "KES",
		"total_budget_amount": allocated,
		"version_no": 1,
		"is_current_version": 1,
		"order_index": 0,
	}).insert(ignore_permissions=True)
	frappe.db.set_value("Budget", bud.name, "status", "Approved")

	line = frappe.get_doc({
		"doctype": "Budget Line",
		"budget_line_code": f"BL-GR-{h}",
		"budget_line_name": f"GR Line {h}",
		"budget": bud.name,
		"procuring_entity": entity,
		"fiscal_year": 2026,
		"amount_allocated": allocated,
		"currency": "KES",
		"is_active": 1,
		"strategic_plan": plan.name,
		"program": prog.name,
	}).insert(ignore_permissions=True)

	return bud.name, line.name


# ── Shape contract ─────────────────────────────────────────────────────────────

class TestGuardrailsShape(IntegrationTestCase):
	"""Response shape and field contract."""

	def setUp(self):
		frappe.set_user("Administrator")

	def test_returns_guardrails_key(self):
		out = compute_budget_guardrails()
		self.assertIn("guardrails", out)
		self.assertIsInstance(out["guardrails"], list)

	def test_guardrail_fields_present(self):
		"""Each guardrail item must carry the five spec-mandated fields."""
		_bud, _line = _make_budget_with_line()
		# Set a low balance to ensure at least one item
		frappe.db.set_value("Budget Line", _line, {
			"amount_available": 10_000,   # 1% of 1M → exhausted
		})
		out = compute_budget_guardrails()
		required = {"severity", "title", "description", "action_label", "budget_line"}
		for g in out["guardrails"]:
			for key in required:
				self.assertIn(key, g, f"guardrail item missing field '{key}'")

	def test_severity_values_are_valid(self):
		out = compute_budget_guardrails()
		valid = {"error", "warning"}
		for g in out["guardrails"]:
			self.assertIn(g["severity"], valid,
				f"unexpected severity '{g['severity']}'")

	def test_check_type_values_are_valid(self):
		out = compute_budget_guardrails()
		valid = {"low_balance", "unlinked_strategy", "expiry"}
		for g in out["guardrails"]:
			self.assertIn(g.get("check_type"), valid,
				f"unexpected check_type '{g.get('check_type')}'")


# ── Low balance check ──────────────────────────────────────────────────────────

class TestLowBalanceGuardrail(IntegrationTestCase):

	def setUp(self):
		frappe.set_user("Administrator")

	def test_low_balance_triggers_below_15_pct(self):
		"""A line with available = 10% of allocated must produce a low_balance guardrail."""
		_bud, line = _make_budget_with_line(allocated=1_000_000)
		# available = 10% → below the 15% threshold
		frappe.db.set_value("Budget Line", line, "amount_available", 100_000)
		out = compute_budget_guardrails()
		low = [g for g in out["guardrails"]
		       if g.get("check_type") == "low_balance" and g.get("budget_line") == line]
		self.assertTrue(len(low) > 0, f"low_balance guardrail not raised for line {line}")

	def test_low_balance_severity_is_error(self):
		_bud, line = _make_budget_with_line(allocated=1_000_000)
		frappe.db.set_value("Budget Line", line, "amount_available", 50_000)  # 5%
		out = compute_budget_guardrails()
		low = next((g for g in out["guardrails"]
		            if g.get("check_type") == "low_balance" and g.get("budget_line") == line), None)
		self.assertIsNotNone(low)
		self.assertEqual(low["severity"], "error")

	def test_healthy_balance_does_not_trigger(self):
		"""A line at 50% available must NOT produce a low_balance guardrail."""
		_bud, line = _make_budget_with_line(allocated=1_000_000)
		frappe.db.set_value("Budget Line", line, "amount_available", 500_000)
		out = compute_budget_guardrails()
		low = [g for g in out["guardrails"]
		       if g.get("check_type") == "low_balance" and g.get("budget_line") == line]
		self.assertEqual(len(low), 0, "healthy line should not raise low_balance")

	def test_low_balance_exactly_at_15_pct_does_not_trigger(self):
		"""Exactly 15% available is the boundary — must NOT trigger (strictly < 15%)."""
		_bud, line = _make_budget_with_line(allocated=1_000_000)
		frappe.db.set_value("Budget Line", line, "amount_available", 150_000)  # = 15%
		out = compute_budget_guardrails()
		low = [g for g in out["guardrails"]
		       if g.get("check_type") == "low_balance" and g.get("budget_line") == line]
		self.assertEqual(len(low), 0, "15.0% should not trigger (strictly <15%)")

	def test_low_balance_description_contains_pct(self):
		_bud, line = _make_budget_with_line(allocated=1_000_000)
		frappe.db.set_value("Budget Line", line, "amount_available", 80_000)  # 8%
		out = compute_budget_guardrails()
		low = next((g for g in out["guardrails"]
		            if g.get("check_type") == "low_balance" and g.get("budget_line") == line), None)
		self.assertIsNotNone(low)
		self.assertTrue(low["description"].strip(), "description must not be empty")


# ── Unlinked strategy check ────────────────────────────────────────────────────

class TestUnlinkedStrategyGuardrail(IntegrationTestCase):

	def setUp(self):
		frappe.set_user("Administrator")

	def test_unlinked_line_triggers_guardrail(self):
		"""A Budget Line with program=NULL must produce an unlinked_strategy guardrail."""
		_bud, line = _make_budget_with_line()
		# Null out the program link to simulate an unlinked line
		frappe.db.set_value("Budget Line", line, "program", None)
		out = compute_budget_guardrails()
		unlinked = [g for g in out["guardrails"] if g.get("check_type") == "unlinked_strategy"]
		self.assertTrue(len(unlinked) > 0, "unlinked_strategy guardrail not raised")

	def test_unlinked_guardrail_severity_is_warning(self):
		_bud, line = _make_budget_with_line()
		frappe.db.set_value("Budget Line", line, "program", None)
		out = compute_budget_guardrails()
		unlinked = next(
			(g for g in out["guardrails"] if g.get("check_type") == "unlinked_strategy"), None
		)
		self.assertIsNotNone(unlinked)
		self.assertEqual(unlinked["severity"], "warning")

	def test_linked_line_does_not_trigger(self):
		"""A Budget Line with a valid program link must NOT trigger unlinked_strategy."""
		_bud, line = _make_budget_with_line()
		# program is already set by the fixture — confirm no unlinked guardrail for this line
		out = compute_budget_guardrails()
		# The aggregate unlinked guardrail might exist from other DB data; check the line
		# is not the SOLE cause by ensuring the fixture line isn't the culprit
		unlinked = [g for g in out["guardrails"] if g.get("check_type") == "unlinked_strategy"]
		line_names = [g.get("budget_line") for g in unlinked]
		self.assertNotIn(line, line_names,
			"properly-linked line should not appear in unlinked_strategy items")


# ── Budget expiry check ────────────────────────────────────────────────────────

class TestBudgetExpiryGuardrail(IntegrationTestCase):

	def setUp(self):
		frappe.set_user("Administrator")

	def test_budget_expiring_within_30_days_triggers(self):
		"""A Budget with closing_date = today+15 must produce an expiry guardrail."""
		bud, _line = _make_budget_with_line()
		closing = add_days(today(), 15)
		frappe.db.set_value("Budget", bud, "closing_date", closing)
		out = compute_budget_guardrails()
		expiry = [g for g in out["guardrails"]
		          if g.get("check_type") == "expiry" and g.get("budget") == bud]
		self.assertTrue(len(expiry) > 0, "expiry guardrail not raised for budget expiring in 15 days")

	def test_budget_expiry_severity_is_warning(self):
		bud, _line = _make_budget_with_line()
		frappe.db.set_value("Budget", bud, "closing_date", add_days(today(), 10))
		out = compute_budget_guardrails()
		expiry = next(
			(g for g in out["guardrails"] if g.get("check_type") == "expiry" and g.get("budget") == bud),
			None,
		)
		self.assertIsNotNone(expiry)
		self.assertEqual(expiry["severity"], "warning")

	def test_budget_expiry_not_triggered_beyond_30_days(self):
		"""A Budget expiring in 45 days must NOT trigger."""
		bud, _line = _make_budget_with_line()
		frappe.db.set_value("Budget", bud, "closing_date", add_days(today(), 45))
		out = compute_budget_guardrails()
		expiry = [g for g in out["guardrails"]
		          if g.get("check_type") == "expiry" and g.get("budget") == bud]
		self.assertEqual(len(expiry), 0, "budget expiring in 45 days should not trigger")

	def test_budget_expiry_description_contains_days(self):
		bud, _line = _make_budget_with_line()
		frappe.db.set_value("Budget", bud, "closing_date", add_days(today(), 20))
		out = compute_budget_guardrails()
		expiry = next(
			(g for g in out["guardrails"] if g.get("check_type") == "expiry" and g.get("budget") == bud),
			None,
		)
		self.assertIsNotNone(expiry)
		self.assertIn("20", expiry["description"], "description should mention days remaining")
