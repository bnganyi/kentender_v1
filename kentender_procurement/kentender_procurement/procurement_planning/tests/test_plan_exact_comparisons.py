# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RG-24 (Planning part) — the Planning decisions that compared amounts with an
epsilon compare exact decimals (PLN §4.1: "never binary float"; BUD §4.8: no
epsilon in a decision).

* `plan_read._purchase_changes` summed an item's allocations as binary floats and
  called two totals different only above 1e-9: a decision with an epsilon, so a
  difference below it (and, on an older interpreter, the noise of a ministry-scale
  float sum) was decided by luck rather than by the amounts.
* `guards._budget_guards` offered a fresh budget revision "only on a new basis"
  and judged a basis new only when a line moved by more than 0.005."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services import guards, plan_read, readiness

# these four sum to 184132482.07000002 when added one by one in binary floating point
NOISY_PARTS = (44872648.85, 28586332.99, 80884095.33, 29789404.90)


def _allocations(*amounts):
	return [SimpleNamespace(indicative_amount=a, budget_line="BL-1") for a in amounts]


class TestPurchaseChangesCompareExactly(IntegrationTestCase):
	def changes(self, before, after):
		allocations = {"I-BEFORE": _allocations(*before), "I-AFTER": _allocations(*after)}

		def rows(_doctype, filters=None, **_kwargs):
			version = filters["plan_version"]
			return [SimpleNamespace(name=f"I-{version}", plan_item="PI-1", plan_item_id="PLN-1", title="Laptops")]

		with (
			patch.object(plan_read.frappe, "get_all", side_effect=rows),
			patch.object(readiness, "_allocations", side_effect=lambda name: allocations[name]),
		):
			return plan_read._purchase_changes("BEFORE", "AFTER")

	def test_the_float_sum_really_carries_noise(self):
		total = 0.0
		for part in NOISY_PARTS:
			total += part
		self.assertNotEqual(total, 184132482.07)

	def test_an_unchanged_total_summed_in_another_order_is_no_change(self):
		self.assertEqual(self.changes(NOISY_PARTS, (184132482.07,)), [])
		self.assertEqual(self.changes(NOISY_PARTS, tuple(reversed(NOISY_PARTS))), [])

	def test_there_is_no_epsilon_in_the_decision(self):
		# 1e-10 is below the old 1e-9 tolerance: the amounts differ, so it is a change
		self.assertEqual(len(self.changes((1000000.0,), (1000000.0000000001,))), 1)

	def test_a_cent_is_a_change(self):
		rows = self.changes((184132482.07,), (184132482.08,))
		self.assertEqual([r["field"] for r in rows], ["Estimated cost"])
		self.assertEqual(rows[0]["plan_item_id"], "PLN-1")


class TestBudgetBasisComparesExactly(IntegrationTestCase):
	def fixes(self, *, planned, approved, declined_planned, declined_approved):
		blocker = {"lines": [{"budget_line": "BL-1", "reference": "BL-REF", "title": "Line", "over": 0, "planned": planned, "approved": approved}]}
		declined = {"BL-1": {"planned": declined_planned, "approved": declined_approved, "by": "Budget Officer", "at": "", "reason": "No."}}
		out = guards._budget_guards(blocker, open_requests=set(), declined=declined, departments={})
		return [fix.get("fix_id") for guard in out for fix in guard["fixes"]]

	def test_a_line_that_moved_by_less_than_half_a_cent_is_a_new_basis(self):
		fixes = self.fixes(planned=100.004, approved=100.0, declined_planned=100.0, declined_approved=100.0)
		self.assertIn(guards.FIX_REQUEST_BUDGET_REVISION, fixes)

	def test_the_same_amounts_are_not_a_new_basis(self):
		fixes = self.fixes(planned=100.0, approved=100.0, declined_planned=100.0, declined_approved=100.0)
		self.assertNotIn(guards.FIX_REQUEST_BUDGET_REVISION, fixes)
