# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.3.3 / §7.3 (Budget owner work, tracker PLN18-107) —
`validate_plan_affordability_for_decision`; and BUD-CHG-001 v1.10
BUD20-AC-002 — the annual procurement budget is not the 30% reservation
denominator, so Budget publishes no contract that offers it as one.

Run:
  bench --site kentender.midas.com run-tests --app kentender_budget \\
    --module kentender_budget.tests.test_bud_chg_001_v18_decision_basis
"""

from __future__ import annotations

import frappe

from kentender_budget.services import budget_line_contracts as lines
from kentender_budget.tests.test_bud_chg_001_phase3_check_reserve import _FinanceTestBase


class TestDecisionBasis(_FinanceTestBase):
	def _world(self):
		budget, version = self._create_active_baseline(dhi_amount=100_000_000, hwd_amount=60_000_000)
		fiscal_year = frappe.db.get_value("Procurement Budget", budget, "fiscal_year")
		dhi = frappe.db.get_value(
			"Procurement Budget Line Version", {"budget_version": version, "title": "DHI test line"}, "budget_line"
		)
		self._as("Administrator")
		return budget, version, fiscal_year, dhi

	def test_budget_publishes_no_reservation_denominator(self):
		"""BUD20-AC-002: the old annual-basis contract is gone, with no alias.
		The 30% target is a share of the plan's eligible value (Planning's
		calculation); the approved budget is only the funding ceiling."""
		from kentender_budget.api import budget_api

		for module in (lines, budget_api):
			self.assertFalse(hasattr(module, "get_annual_procurement_budget_basis"), module.__name__)
			self.assertFalse(
				[n for n in dir(module) if "annual" in n.lower() and "basis" in n.lower()],
				f"{module.__name__} still offers an annual budget basis",
			)

	def test_decision_validation_returns_no_denominator(self):
		"""BUD20-AC-001: the decision statement is ceiling/affordability evidence only."""
		_budget, _version, fiscal_year, dhi = self._world()
		out = lines.validate_plan_affordability_for_decision(fiscal_year, {dhi: 80_000_000})
		self.assertFalse([k for k in out if "annual" in k or "reservation" in k or "denominator" in k])

	def test_decision_validation_locks_validates_revisions_and_writes_nothing(self):
		budget, version, fiscal_year, dhi = self._world()
		reservations_before = frappe.db.count("Funding Reservation")
		line_version = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version, "budget_line": dhi}, "name")

		out = lines.validate_plan_affordability_for_decision(
			fiscal_year, {dhi: 80_000_000}, expected_revisions={dhi: line_version, "budget_version": version}, correlation="fin-1"
		)
		self.assertTrue(out["decision_basis"])
		self.assertTrue(out["within_approved"])
		self.assertEqual(out["budget_version"], version)
		self.assertEqual(out["line_versions"][dhi], line_version)
		row = next(r for r in out["lines"] if r["budget_line"] == dhi)
		self.assertEqual(row["approved"], "100000000.00")
		self.assertEqual(row["planned"], "80000000.00")
		self.assertEqual(row["line_version"], line_version)
		self.assertEqual(len(out["basis_digest"]), 64)
		again = lines.validate_plan_affordability_for_decision(fiscal_year, {dhi: 80_000_000}, expected_revisions={dhi: line_version})
		self.assertEqual(again["basis_digest"], out["basis_digest"], "same basis, same digest")
		changed = lines.validate_plan_affordability_for_decision(fiscal_year, {dhi: 90_000_000})
		self.assertNotEqual(changed["basis_digest"], out["basis_digest"], "a changed planned total is a different basis")

		over = lines.validate_plan_affordability_for_decision(fiscal_year, {dhi: 120_000_000})
		self.assertFalse(over["within_approved"])
		self.assertEqual(over["failing_lines"][0]["excess"], "20000000.00")

		# A reviewed revision that is no longer the Active line version, or a
		# reviewed Budget Version that is no longer Active, fails the decision.
		with self.assertRaises(frappe.ValidationError) as caught:
			lines.validate_plan_affordability_for_decision(fiscal_year, {dhi: 80_000_000}, expected_revisions={dhi: "not-the-line-version"})
		self.assertIn("revision has changed", str(caught.exception))
		with self.assertRaises(frappe.ValidationError) as caught:
			lines.validate_plan_affordability_for_decision(fiscal_year, {dhi: 80_000_000}, expected_revisions={"budget_version": "PBV-OLD"})
		self.assertIn("no longer the Active one", str(caught.exception))
		with self.assertRaises(frappe.ValidationError):
			lines.validate_plan_affordability_for_decision("1900-1901", {dhi: 1})

		self.assertEqual(frappe.db.count("Funding Reservation"), reservations_before)
		# The display read is untouched: floats, no lock, no line versions.
		display = lines.check_plan_affordability(fiscal_year, {dhi: 80_000_000})
		self.assertNotIn("line_versions", display)
		self.assertIsInstance(display["lines"][0]["approved"], float)
