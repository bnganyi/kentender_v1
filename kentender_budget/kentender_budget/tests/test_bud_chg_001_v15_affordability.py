# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.5 §8.2 / §9.1 — `check_plan_affordability` (BUD-AC-011a) and
the human `reference` on `list_eligible_budget_lines` (PLN FU-02).

Run:
  bench --site kentender.midas.com run-tests --app kentender_budget \\
    --module kentender_budget.tests.test_bud_chg_001_v15_affordability
"""

from __future__ import annotations

import frappe

from kentender_budget.services import budget_line_contracts as lines
from kentender_budget.tests.test_bud_chg_001_phase3_check_reserve import _FinanceTestBase


class TestPlanAffordability(_FinanceTestBase):
	def test_affordability_statement_carries_both_verdicts_and_writes_nothing(self):
		"""BUD-AC-011a — per-line approved, planned, positions with as_at, two
		verdicts; no token, no lock, no ledger event."""
		budget, version = self._create_active_baseline(dhi_amount=100_000_000, hwd_amount=60_000_000)
		fiscal_year = frappe.db.get_value("Procurement Budget", budget, "fiscal_year")
		dhi = frappe.db.get_value(
			"Procurement Budget Line Version", {"budget_version": version, "title": "DHI test line"}, "budget_line"
		)
		# Planning's gateway evaluates this contract as a system principal
		# (see procurement_planning/services/budget_gateway.py); the read
		# scope itself is Budget's own DocPerm + scope-map concern.
		self._as("Administrator")
		reservations_before = frappe.db.count("Funding Reservation")

		out = lines.check_plan_affordability(fiscal_year, {dhi: 80_000_000})
		self.assertTrue(out["within_approved"])
		self.assertTrue(out["within_available"])
		self.assertEqual(out["failing_lines"], [])
		self.assertTrue(out["as_at"])
		row = next(r for r in out["lines"] if r["budget_line"] == dhi)
		self.assertEqual(row["approved"], 100_000_000)
		self.assertEqual(row["planned"], 80_000_000)
		self.assertTrue(row["within_approved"])
		self.assertEqual(row["reference"], frappe.db.get_value("Procurement Budget Line", dhi, "generated_reference"))
		untouched = next(r for r in out["lines"] if r["budget_line"] != dhi)
		self.assertEqual(untouched["planned"], 0)

		over = lines.check_plan_affordability(fiscal_year, [{"budget_line": dhi, "planned": 120_000_000}])
		self.assertFalse(over["within_approved"])
		self.assertEqual(over["failing_lines"][0]["budget_line"], dhi)
		self.assertEqual(over["failing_lines"][0]["excess"], 20_000_000)

		unknown = lines.check_plan_affordability(fiscal_year, {"NOT-A-LINE": 1})
		self.assertFalse(unknown["within_approved"])
		self.assertEqual(unknown["unknown_lines"], ["NOT-A-LINE"])

		self.assertEqual(frappe.db.count("Funding Reservation"), reservations_before)

	def test_eligible_lines_expose_the_human_reference(self):
		budget, version = self._create_active_baseline(dhi_amount=10_000_000, hwd_amount=1)
		fiscal_year = frappe.db.get_value("Procurement Budget", budget, "fiscal_year")
		self._as("Administrator")
		rows = lines.list_eligible_budget_lines(fiscal_year)
		self.assertTrue(rows)
		for row in rows:
			self.assertEqual(row["reference"], frappe.db.get_value("Procurement Budget Line", row["id"], "generated_reference"))
			self.assertTrue(row["reference"])
