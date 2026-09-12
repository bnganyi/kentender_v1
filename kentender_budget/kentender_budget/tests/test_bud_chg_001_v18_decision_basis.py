# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.3.3 / §7.3 (Budget owner work, tracker PLN18-107) —
`validate_plan_affordability_for_decision` and
`get_annual_procurement_budget_basis`.

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

	def test_the_annual_basis_is_the_complete_approved_budget_and_exact_version(self):
		budget, version, fiscal_year, _dhi = self._world()
		basis = lines.get_annual_procurement_budget_basis(fiscal_year)
		self.assertTrue(basis["available"])
		self.assertEqual(basis["budget_version"], version)
		self.assertEqual(basis["line_count"], 2)
		self.assertEqual(basis["lines_approved_total"], "160000000.00")
		self.assertEqual(basis["annual_approved_amount"], "160000000.00")
		self.assertEqual(basis["currency_precision"], 2)
		self.assertIsInstance(basis["annual_approved_amount"], str)
		self.assertFalse(lines.get_annual_procurement_budget_basis("1900-1901")["available"])

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
