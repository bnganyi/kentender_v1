"""ANL-CHG-001 v0.8 §4A, §5.4, §5.5 — the arithmetic, on plain values.

Run:
  bench --site kentender-test.local run-tests --app kentender_core \\
    --module kentender_core.tests.test_analytics_measures
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal as D

from frappe.tests import IntegrationTestCase

from kentender_core.services import analytics_contract as ac
from kentender_core.services import analytics_measures as am


class TestWindowAndDays(IntegrationTestCase):
	def test_window_is_twelve_months_ending_with_the_read_month(self):
		months = am.window_months(datetime(2027, 6, 18, 10, 0))
		self.assertEqual(len(months), 12)
		self.assertEqual(months[0]["label"], "Jul 2026")
		self.assertEqual(months[-1]["label"], "Jun 2027 (to date)")
		self.assertEqual([m["label"] for m in months][1:11], [f"{m} {y}" for m, y in (("Aug", 2026), ("Sep", 2026), ("Oct", 2026), ("Nov", 2026),
			("Dec", 2026), ("Jan", 2027), ("Feb", 2027), ("Mar", 2027), ("Apr", 2027), ("May", 2027))])

	def test_window_crosses_a_year_and_a_month_boundary(self):
		months = am.window_months(datetime(2027, 1, 1, 0, 0))
		self.assertEqual((months[0]["label"], months[-1]["label"]), ("Feb 2026", "Jan 2027 (to date)"))
		self.assertEqual(months[0]["start"], date(2026, 2, 1))
		self.assertEqual(months[0]["end"], date(2026, 2, 28))

	def test_in_window_is_inclusive_at_both_ends(self):
		at = datetime(2027, 6, 18, 10, 0)
		self.assertTrue(am.in_window(datetime(2026, 7, 1, 0, 0), at))
		self.assertFalse(am.in_window(datetime(2026, 6, 30, 23, 59), at))
		self.assertTrue(am.in_window(datetime(2027, 6, 30, 23, 59), at))
		self.assertFalse(am.in_window(datetime(2027, 7, 1, 0, 0), at))
		self.assertFalse(am.in_window(None, at))

	def test_month_counts_and_empty_months(self):
		at = datetime(2027, 6, 18, 10, 0)
		counts = am.month_counts([datetime(2027, 4, 9), datetime(2027, 4, 12), datetime(2027, 5, 14), None, datetime(2025, 1, 1)], at)
		self.assertEqual(counts, [0] * 9 + [2, 1, 0])

	def test_calendar_days_use_local_dates_not_elapsed_hours(self):
		self.assertEqual(am.calendar_days(datetime(2027, 6, 16, 23, 59), datetime(2027, 6, 17, 0, 1)), 1)
		self.assertEqual(am.calendar_days(datetime(2027, 6, 17, 9, 0), datetime(2027, 6, 17, 17, 0)), 0)
		self.assertEqual(am.calendar_days(datetime(2027, 3, 9, 10, 0), datetime(2027, 3, 15, 11, 0)), 6)

	def test_calendar_days_refuse_an_end_before_the_start(self):
		with self.assertRaises(ValueError):
			am.calendar_days(datetime(2027, 6, 18), datetime(2027, 6, 17))


class TestBands(IntegrationTestCase):
	def test_band_boundaries(self):
		cases = {0: "0_7", 7: "0_7", 8: "8_30", 30: "8_30", 31: "31_90", 90: "31_90", 91: "over_90", 400: "over_90"}
		for days, key in cases.items():
			self.assertEqual(am.band_key(days), key, days)
		self.assertEqual(am.band_label("over_90"), "Over 90 days")
		with self.assertRaises(ValueError):
			am.band_key(-1)


class TestStepStats(IntegrationTestCase):
	def test_median_odd_even_and_half(self):
		self.assertEqual(am.step_stats([6, 7, 7, 10, 12, 14])["median"], 8.5)  # A1 T1
		self.assertEqual(am.step_stats([1, 2, 3, 4, 4, 5])["median"], 3.5)  # A1 T2
		self.assertEqual(am.step_stats([21, 24, 26, 29, 56])["median"], 26)  # A1 T3, odd count
		self.assertEqual(am.step_stats([28, 37])["median"], 32.5)  # A1 T4
		self.assertEqual(am.step_stats([5, 7])["median"], 6)  # even count, whole mean, no decimal
		self.assertIsInstance(am.step_stats([5, 7])["median"], int)

	def test_stats_shape_and_empty(self):
		self.assertEqual(am.step_stats([13]), {"completed": 1, "median": 13, "shortest": 13, "longest": 13})
		self.assertIsNone(am.step_stats([]))

	def test_day_phrase(self):
		self.assertEqual([am.day_phrase(x) for x in (1, 8.5, 26, 0, 13.0)], ["1 day", "8.5 days", "26 days", "0 days", "13 days"])

	def test_axis_default_and_widening(self):
		self.assertEqual(am.axis_max([14, 56]), 60)
		self.assertEqual(am.axis_max([]), 60)
		self.assertEqual(am.axis_max([61]), 70)
		self.assertEqual(am.axis_max([120]), 120)


class TestPercentAndMoney(IntegrationTestCase):
	def test_coverage_percentages_of_a1(self):
		self.assertEqual(am.percent_half_up(D(55_500_000), D(68_500_000)), 81)
		self.assertEqual(am.percent_half_up(D(34_000_000), D(46_000_000)), 74)
		self.assertEqual(am.percent_half_up(D(21_500_000), D(22_500_000)), 96)

	def test_half_rounds_up_and_zero_planned_has_no_percentage(self):
		self.assertEqual(am.percent_half_up(D(1), D(8)), 13)  # 12.5
		self.assertEqual(am.percent_half_up(D(1), D(200)), 1)  # 0.5
		self.assertIsNone(am.percent_half_up(D(0), D(0)))
		self.assertEqual(am.percent_half_up(D(0), D(10)), 0)

	def test_kes_shows_cents_only_when_not_zero(self):
		self.assertEqual(am.kes(D(55_500_000)), "KES 55,500,000")
		self.assertEqual(am.kes(D("7185000.50")), "KES 7,185,000.50")
		self.assertEqual(am.kes(D("7185000.00")), "KES 7,185,000")
		self.assertEqual(am.kes(D(0)), "KES 0")

	def test_axis_tick_abbreviates_millions_only(self):
		self.assertEqual(am.kes_tick(D(20_000_000)), "KES 20 m")
		self.assertEqual(am.kes_tick(D(2_500_000)), "KES 2.5 m")

	def test_phrases(self):
		self.assertEqual(am.join_and(["a", "b", "c"]), "a, b and c")
		self.assertEqual(am.join_and(["a"]), "a")
		self.assertEqual(am.count_phrase(1, "Need", "Needs"), "1 Need")


class TestContract(IntegrationTestCase):
	def test_money_parses_owner_data_strings_and_refuses_junk(self):
		self.assertEqual(ac.money("7,185,000.50"), D("7185000.50"))
		self.assertEqual(ac.money(12), D(12))
		for bad in (None, "", "abc", True):
			with self.assertRaises(ValueError):
				ac.money(bad)

	def test_a_record_with_a_float_amount_or_a_bad_bucket_is_refused(self):
		base = dict(id="T-1", title="t", org_units=[], state="x")
		with self.assertRaises(ValueError):
			ac.record(ac.REQUISITIONS, **base, value_kind=ac.AUTHORISED, value_lines=[{"org_unit": "u", "amount": 1.5}], submitted_at=None,
				authorised_at=None, consumed_at=None, submission_events=[], authorisation_events=[], tender_reference="")
		with self.assertRaises(ValueError):
			ac.validate({"kind": "nope", "id": "x", "title": "x", "org_units": []})
