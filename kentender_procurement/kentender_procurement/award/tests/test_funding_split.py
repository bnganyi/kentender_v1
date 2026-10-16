# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AWD-CHG-001 v0.7 section 7.1 / AWD-FUND-AC-001 and -002: the arithmetic that splits an awarded price over the sources that asked for the goods.

The cases are pure (no record is read), so they run anywhere. The canonical fixture is the 250 identical laptops at KES 185,600 each, requested by two departments for 100 and 150."""

from __future__ import annotations

import unittest
from decimal import Decimal as D

from kentender_procurement.award.services.funding_split import Common, Coverage, Row, SourceIssue, allocate, check_total

HRMD, DHI = "PSA-HRMD", "PSA-DHI"


def row(row_id, amount, *covers):
	return Row(row_id, D(amount), tuple(Coverage(s, D(q)) for s, q in covers))


class TestTheAwardedPriceFollowsTheSourcesQuantities(unittest.TestCase):
	def test_the_canonical_laptops_split_by_quantity_not_by_reservation_size(self):
		result = allocate([row("1", "46400000.00", (HRMD, 100), (DHI, 150))])
		self.assertEqual(result.totals, {HRMD: D("18560000.00"), DHI: D("27840000.00")})
		check_total(result, D("46400000.00"))

	def test_a_separately_priced_item_belongs_to_its_own_source(self):
		result = allocate([row("1", "1000.00", (HRMD, 1)), row("2", "2500.50", (DHI, 3))])
		self.assertEqual(result.totals, {HRMD: D("1000.00"), DHI: D("2500.50")})

	def test_sources_with_different_rates_stay_separate_rows_and_keep_their_prices(self):
		result = allocate([row("1", "100.00", (HRMD, 10)), row("2", "300.00", (DHI, 10))])
		self.assertEqual((result.totals[HRMD], result.totals[DHI]), (D("100.00"), D("300.00")))

	def test_a_source_in_two_rows_adds_up(self):
		result = allocate([row("1", "10.00", (HRMD, 1)), row("2", "20.00", (HRMD, 1), (DHI, 1))])
		self.assertEqual(result.totals, {HRMD: D("20.00"), DHI: D("10.00")})
		check_total(result, D("30.00"))


class TestRoundingIsExactAndDeterministic(unittest.TestCase):
	def test_an_indivisible_row_gives_the_odd_minor_unit_to_the_largest_remainder_then_the_lowest_source(self):
		# 1.00 over three equal sources: 33, 33, 33 and one minor unit left; every remainder is equal, so the lowest source identity takes it
		result = allocate([row("1", "1.00", ("C", 1), ("A", 1), ("B", 1))])
		self.assertEqual(result.totals, {"A": D("0.34"), "B": D("0.33"), "C": D("0.33")})
		check_total(result, D("1.00"))

	def test_the_largest_fractional_remainder_wins_before_the_tie_break(self):
		# 0.10 over quantities 1:2 -> 3.33.. and 6.67.. minor units: floors 3 and 6, residual 1 goes to the 6.67 share
		result = allocate([row("1", "0.10", ("A", 1), ("B", 2))])
		self.assertEqual(result.totals, {"A": D("0.03"), "B": D("0.07")})

	def test_the_same_input_always_gives_the_same_answer_in_any_order(self):
		covers = [("S3", 7), ("S1", 3), ("S2", 5)]
		first = allocate([row("1", "12345.67", *covers)]).totals
		second = allocate([row("1", "12345.67", *reversed(covers))]).totals
		self.assertEqual(first, second)
		self.assertEqual(sum(first.values()), D("12345.67"))

	def test_money_with_more_places_than_the_scale_is_refused_not_rounded(self):
		with self.assertRaises(SourceIssue):
			allocate([row("1", "10.005", (HRMD, 1))])


class TestACommonAdjustmentFollowsTheRowsItCovers(unittest.TestCase):
	def test_a_common_charge_follows_the_proportion_of_the_covered_rows(self):
		result = allocate([row("1", "100.00", (HRMD, 1)), row("2", "300.00", (DHI, 1))], [Common("C1", D("40.00"))])
		self.assertEqual(result.totals, {HRMD: D("110.00"), DHI: D("330.00")})
		check_total(result, D("440.00"))

	def test_a_common_discount_reduces_by_the_same_proportions_and_rounds_on_its_absolute_value(self):
		result = allocate([row("1", "100.00", (HRMD, 1)), row("2", "200.00", (DHI, 1))], [Common("D1", D("-10.00"))])
		self.assertEqual(result.totals, {HRMD: D("96.67"), DHI: D("193.33")})
		check_total(result, D("290.00"))

	def test_a_common_adjustment_that_names_some_rows_ignores_the_others(self):
		result = allocate([row("1", "100.00", (HRMD, 1)), row("2", "100.00", (DHI, 1))], [Common("C1", D("10.00"), ("1",))])
		self.assertEqual(result.totals, {HRMD: D("110.00"), DHI: D("100.00")})

	def test_a_common_adjustment_over_a_row_not_in_the_award_is_a_source_issue(self):
		with self.assertRaises(SourceIssue):
			allocate([row("1", "100.00", (HRMD, 1))], [Common("C1", D("5.00"), ("9",))])

	def test_a_discount_larger_than_the_source_it_follows_is_a_source_issue_not_a_negative_amount(self):
		with self.assertRaises(SourceIssue):
			allocate([row("1", "5.00", (HRMD, 1))], [Common("D1", D("-6.00"))])


class TestUnknownCoverageBlocksTheSplitInsteadOfGuessing(unittest.TestCase):
	def test_a_row_that_names_no_source_is_a_source_issue(self):
		with self.assertRaises(SourceIssue):
			allocate([Row("1", D("10.00"), ())])

	def test_a_row_with_no_quantity_to_follow_is_a_source_issue(self):
		with self.assertRaises(SourceIssue):
			allocate([row("1", "10.00", (HRMD, 0), (DHI, 0))])

	def test_a_zero_amount_covered_row_gives_a_common_charge_nothing_to_follow(self):
		with self.assertRaises(SourceIssue):
			allocate([row("1", "0.00", (HRMD, 1))], [Common("C1", D("5.00"))])

	def test_no_rows_is_a_source_issue(self):
		with self.assertRaises(SourceIssue):
			allocate([])

	def test_a_repeated_row_identity_is_a_source_issue(self):
		with self.assertRaises(SourceIssue):
			allocate([row("1", "1.00", (HRMD, 1)), row("1", "2.00", (DHI, 1))])

	def test_shares_that_do_not_add_up_to_the_supported_price_are_refused(self):
		result = allocate([row("1", "100.00", (HRMD, 1))])
		with self.assertRaises(SourceIssue):
			check_total(result, D("100.01"))


if __name__ == "__main__":
	unittest.main()
