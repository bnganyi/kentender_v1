"""The seed world's calendar (SEED-002 v0.8 R1 to R5): the anchor, the three years and the mapping of story
coordinates into the world. Pure arithmetic; the stored state is faked in memory, so no site is read.

Run:
  bench --site kentender-test.local run-tests --app kentender_core --module kentender_core.tests.test_calendar
(or, with no site: `env/bin/python -m unittest kentender_core.tests.test_calendar` from the bench)."""

from __future__ import annotations

import unittest
from contextlib import contextmanager
from datetime import datetime, timedelta
from unittest.mock import patch

from kentender_core.seeds import calendar as cal


@contextmanager
def anchored(anchor: str, started: str | None = None):
	before = dict(cal._resolved)
	cal._resolved["state"] = {"mode": "anchored", "anchor": anchor, "started": started or anchor}
	cal._resolved["signature"] = "test"
	try:
		yield
	finally:
		cal._resolved.clear()
		cal._resolved.update(before)


@contextmanager
def legacy():
	before = dict(cal._resolved)
	cal._resolved["state"] = None
	cal._resolved["signature"] = "null"
	try:
		yield
	finally:
		cal._resolved.clear()
		cal._resolved.update(before)


def dt(text: str) -> datetime:
	return datetime.strptime(text, "%Y-%m-%d %H:%M:%S")


class TestLegacyIsTheV07World(unittest.TestCase):
	def test_every_mapping_is_the_identity_and_the_years_are_the_authored_ones(self):
		with legacy():
			self.assertEqual(cal.mode(), "legacy")
			self.assertEqual(cal.world("2027-03-15 10:00:00"), "2027-03-15 10:00:00")
			self.assertEqual(cal.world("2027-06-30"), "2027-06-30")
			self.assertEqual(cal.fiscal("2027-06-30"), "2027-06-30")
			self.assertEqual(cal.as_at(), "2027-06-18 10:00:00")
			self.assertEqual((cal.YEAR0.fiscal_year, cal.YEAR1.fiscal_year, cal.YEAR2.fiscal_year), ("2025-2026", "2026-2027", "2027-2028"))
			self.assertEqual((cal.YEAR0.shift_days, cal.YEAR1.shift_days, cal.YEAR2.shift_days), (-728, -364, 0))
			self.assertEqual(cal.YEAR1.label, "FY 2026/27")
			self.assertEqual(cal.default_next_stage(), "annual_plan")
			self.assertEqual(cal.prepared_pull_days(), 0)

	def test_a_year_moves_a_journey_instant_by_whole_weeks_and_keeps_its_weekday(self):
		with legacy():
			moved = cal.YEAR1.at("2026-11-24 09:00:00")
			self.assertEqual(moved, "2025-11-25 09:00:00")
			self.assertEqual(dt(moved).weekday(), dt("2026-11-24 09:00:00").weekday())


class TestChoosingTheAnchor(unittest.TestCase):
	def test_the_anchor_is_the_latest_friday_ten_not_later_than_the_start(self):
		for started, expected in (
			("2026-10-16 00:23:00", "2026-10-09 10:00:00"),
			("2026-10-16 10:00:00", "2026-10-16 10:00:00"),
			("2026-10-16 09:59:59", "2026-10-09 10:00:00"),
			("2026-12-20 09:00:00", "2026-12-18 10:00:00"),
		):
			anchor, _notice = cal.choose_anchor(dt(started))
			self.assertEqual(anchor.strftime("%Y-%m-%d %H:%M:%S"), expected)
			self.assertEqual(anchor.weekday(), 4)
			self.assertLessEqual(anchor, dt(started))

	def test_a_run_early_in_the_year_anchors_on_the_end_of_the_previous_season_with_a_notice(self):
		anchor, notice = cal.choose_anchor(dt("2026-07-20 12:00:00"))
		self.assertEqual(anchor.strftime("%Y-%m-%d %H:%M:%S"), "2026-06-12 10:00:00")
		self.assertIn("anchored on the end of the previous season", notice)
		self.assertEqual(anchor.weekday(), 4)

	def test_a_run_in_the_last_days_of_the_year_anchors_on_the_end_of_its_season_with_a_notice(self):
		anchor, notice = cal.choose_anchor(dt("2027-06-26 12:00:00"))
		self.assertEqual(anchor.strftime("%Y-%m-%d %H:%M:%S"), "2027-06-18 10:00:00")
		self.assertIn("after the end of FY 2026/27's season", notice)
		anchor, notice = cal.choose_anchor(dt("2028-06-30 12:00:00"))
		self.assertEqual((anchor.strftime("%Y-%m-%d %H:%M:%S"), anchor.weekday()), ("2028-06-16 10:00:00", 4))
		self.assertIn("after the end of FY 2027/28's season", notice)

	def test_a_run_on_the_last_friday_of_the_season_is_not_clamped(self):
		self.assertEqual(cal.choose_anchor(dt("2027-06-18 11:00:00")), (dt("2027-06-18 10:00:00"), ""))

	def test_a_run_with_enough_of_the_year_gone_has_no_notice(self):
		self.assertEqual(cal.choose_anchor(dt("2027-01-20 12:00:00"))[1], "")


class TestTheWorldAtAnOctoberAnchor(unittest.TestCase):
	ANCHOR = "2026-10-09 10:00:00"

	def test_the_three_years_follow_the_anchor_and_execution_moves_whole_weeks(self):
		with anchored(self.ANCHOR):
			self.assertEqual((cal.YEAR0.fiscal_year, cal.YEAR1.fiscal_year, cal.YEAR2.fiscal_year), ("2025-2026", "2026-2027", "2027-2028"))
			self.assertEqual(cal.execution_shift_days(), -252)
			self.assertEqual(cal.execution_shift_days() % 7, 0)
			self.assertEqual(cal.world("2027-06-18 10:00:00"), self.ANCHOR)
			self.assertEqual(cal.world("2027-03-01 09:00:00"), "2026-06-22 09:00:00")
			self.assertEqual(dt(cal.world("2027-03-01 09:00:00")).weekday(), dt("2027-03-01 09:00:00").weekday())

	def test_a_story_instant_after_the_stories_now_is_a_live_deadline_a_week_further_out(self):
		with anchored(self.ANCHOR):
			self.assertEqual(cal.world("2027-06-25 11:00:00"), "2026-10-23 11:00:00")

	def test_nothing_before_2025_moves(self):
		with anchored(self.ANCHOR):
			self.assertEqual(cal.world("2023-07-01 08:00:00"), "2023-07-01 08:00:00")

	def test_the_prepared_years_journey_is_pulled_whole_weeks_so_its_needs_have_happened(self):
		with anchored(self.ANCHOR):
			self.assertEqual(cal.prepared_pull_days(), 49)
			self.assertEqual(cal.YEAR2.shift_days, -49)
			self.assertEqual(cal.YEAR2.at("2026-11-25 10:00:00"), "2026-10-07 10:00:00")
			self.assertLessEqual(dt(cal.YEAR2.at("2026-11-25 10:00:00")), dt(self.ANCHOR))
			self.assertEqual(cal.YEAR1.at("2026-11-24 09:00:00"), "2025-11-25 09:00:00")

	def test_the_prepared_year_stops_at_departmental_needs(self):
		with anchored(self.ANCHOR):
			self.assertEqual({stage: cal.prepared_stage_available(stage) for stage, _ in cal.PREPARED_STAGE_ENDS}, {"budget": True, "needs": True, "departmental_plans": False, "annual_plan": False})
			self.assertEqual(cal.default_next_stage(), "needs")

	def test_an_intake_close_stays_on_the_fiscal_calendar_and_is_not_pulled_forward(self):
		with anchored(self.ANCHOR):
			self.assertEqual(cal.YEAR2.window("2026-11-25 23:59:00"), "2026-11-25 23:59:00")
			self.assertGreater(dt(cal.YEAR2.window("2026-11-25 23:59:00")), dt(self.ANCHOR))

	def test_fiscal_dates_move_by_whole_years_only(self):
		with anchored(self.ANCHOR):
			self.assertEqual(cal.fiscal("2027-06-30"), "2027-06-30")

	def test_a_block_that_runs_past_the_stories_now_moves_earlier_by_whole_weeks(self):
		with anchored(self.ANCHOR):
			self.assertEqual(cal.block_shift_days("2027-07-02 09:00:00"), -14)
			self.assertEqual(cal.block_shift_days("2027-06-18 10:00:00"), 0)
			self.assertEqual(cal.block_shift_days("2028-07-28 11:00:00"), -413)

	def test_a_story_told_in_months_moves_back_by_whole_years_so_a_month_still_starts_on_its_first_day(self):
		with anchored(self.ANCHOR):
			self.assertEqual(cal.years_back("2028-07-28 11:00:00"), 2)
			self.assertEqual(cal.years_back("2027-06-18 10:00:00"), 1)
			move = cal.years_block("2028-07-28 11:00:00")
			self.assertEqual(move("2027-07-01"), "2025-07-01")
			self.assertEqual(move("2027-07-02 09:00:00"), "2025-07-02 09:00:00")
			self.assertLessEqual(dt(move("2028-07-28 11:00:00")), dt(self.ANCHOR))
			self.assertEqual(move(""), "")


class TestTheClosedYear(unittest.TestCase):
	"""Year 0 (SEED-002 v0.8 §A7): the executed year's story one financial year earlier, in whole weeks."""

	ANCHOR = "2026-10-09 10:00:00"

	def test_the_closed_year_is_built_only_in_an_anchored_world(self):
		with legacy():
			self.assertEqual([y.key for y in cal.seeded_years()], ["year1", "year2"])
			self.assertEqual(cal.world0("2027-03-01 09:00:00"), "2027-03-01 09:00:00")
		with anchored(self.ANCHOR):
			self.assertEqual([y.key for y in cal.seeded_years()], ["year0", "year1", "year2"])

	def test_an_execution_instant_of_the_closed_year_is_the_executed_years_364_days_earlier_on_the_same_weekday(self):
		with anchored(self.ANCHOR):
			year1 = cal.world("2027-03-01 09:00:00")
			year0 = cal.world0("2027-03-01 09:00:00")
			self.assertEqual(year1, "2026-06-22 09:00:00")
			self.assertEqual(year0, "2025-06-23 09:00:00")
			self.assertEqual(dt(year0).weekday(), dt(year1).weekday())
			self.assertEqual((dt(year1) - dt(year0)).days, 364)

	def test_every_closed_year_instant_of_the_canonical_chain_is_before_the_anchor(self):
		with anchored(self.ANCHOR):
			for story in ("2027-06-18 10:00:00", "2027-06-15 09:00:00", "2027-04-16 00:00:00", "2027-06-25 11:00:00"):
				self.assertLess(dt(cal.world0(story)), dt(self.ANCHOR) - timedelta(days=300), story)

	def test_the_closed_years_fiscal_year_and_dates(self):
		with anchored(self.ANCHOR):
			self.assertEqual((cal.YEAR0.fiscal_year, cal.YEAR0.start_date, cal.YEAR0.end_date), ("2025-2026", "2025-07-01", "2026-06-30"))
		with anchored("2027-10-08 10:00:00"):
			self.assertEqual((cal.YEAR0.fiscal_year, cal.YEAR0.start_date, cal.YEAR0.end_date), ("2026-2027", "2026-07-01", "2027-06-30"))


class TestABlockOfEvents(unittest.TestCase):
	ANCHOR = "2026-10-09 10:00:00"

	def test_a_block_that_runs_past_the_stories_now_moves_as_a_whole_so_its_last_instant_is_not_after_the_anchor(self):
		with anchored(self.ANCHOR):
			moved = cal.block("2027-10-11 10:00:00")
			self.assertLessEqual(dt(moved("2027-10-11 10:00:00")), dt(self.ANCHOR))
			self.assertEqual(dt(moved("2027-10-11 10:00:00")).weekday(), dt("2027-10-11 10:00:00").weekday())
			self.assertEqual(dt(moved("2027-10-11 10:00:00")) - dt(moved("2027-06-17 09:00:00")), dt("2027-10-11 10:00:00") - dt("2027-06-17 09:00:00"))

	def test_a_block_adds_no_live_deadline_week(self):
		with anchored(self.ANCHOR):
			self.assertEqual(cal.block("2027-06-18 10:00:00")("2027-06-25 11:00:00"), "2026-10-16 11:00:00")

	def test_a_block_is_the_identity_in_a_legacy_world(self):
		with legacy():
			self.assertEqual(cal.block("2027-10-11 10:00:00")("2027-07-02 09:00:00"), "2027-07-02 09:00:00")

	def test_a_step_held_to_the_anchor_never_passes_it(self):
		with anchored(self.ANCHOR):
			self.assertEqual(cal.not_after_anchor("2026-10-14 10:00:00"), "2026-10-09 08:00:00")
			self.assertEqual(cal.not_after_anchor("2026-10-06 15:00:00"), "2026-10-06 15:00:00")


class TestDeliveryDates(unittest.TestCase):
	"""A delivery date of the executed year's story is held to the year's last day (a Requisition refuses a later one)."""

	def test_legacy_keeps_the_story_date(self):
		with legacy():
			self.assertEqual((cal.delivery("2027-06-24"), cal.delivery("2027-06-30")), ("2027-06-24", "2027-06-30"))

	def test_at_an_october_anchor_the_date_is_the_stories_moved_with_the_world(self):
		with anchored("2026-10-09 10:00:00"):
			self.assertEqual((cal.delivery("2027-06-24"), cal.delivery("2027-06-30")), ("2026-10-22", "2026-10-28"))

	def test_at_the_end_of_the_season_the_date_stops_at_the_boundary(self):
		with anchored("2027-06-18 10:00:00"):
			self.assertEqual((cal.delivery("2027-06-24"), cal.delivery("2027-06-30")), ("2027-06-30", "2027-06-30"))
		with anchored("2026-06-12 10:00:00"):
			self.assertEqual(cal.delivery("2027-06-30"), "2026-06-30")

	def test_no_anchor_the_run_can_have_puts_a_delivery_date_past_the_boundary(self):
		for started in ("2026-10-16 00:23:00", "2027-01-20 12:00:00", "2027-06-04 12:00:00", "2027-06-26 12:00:00", "2028-06-30 12:00:00"):
			anchor, _ = cal.choose_anchor(dt(started))
			with anchored(anchor.strftime("%Y-%m-%d %H:%M:%S"), started):
				self.assertLessEqual(cal.delivery("2027-06-30"), cal.fiscal("2027-06-30"), started)


class TestDescribe(unittest.TestCase):
	"""`describe()` is what `tests/ui/helpers/anchor.ts` mirrors the mapping from."""

	def test_a_legacy_world_describes_no_shifts(self):
		with legacy():
			info = cal.describe()
		self.assertEqual((info["mode"], info["anchor"], info["execution_shift_days"], info["year2_journey_shift_days"], info["fiscal_years_from_authored"]), ("legacy", "2027-06-18 10:00:00", 0, 0, 0))

	def test_an_anchored_world_describes_the_numbers_world_is_computed_from(self):
		with anchored("2026-10-09 10:00:00"):
			info = cal.describe()
		self.assertEqual(info["mode"], "anchored")
		self.assertEqual((info["execution_shift_days"], info["history_shift_days"], info["year2_journey_shift_days"], info["closed_year_extra_shift_days"]), (-252, 0, -49, -364))
		self.assertEqual({k: v["shift_days"] for k, v in info["years"].items()}, {"year0": -728, "year1": -364, "year2": -49})


class TestOtherAnchors(unittest.TestCase):
	def test_after_the_stories_prepared_journey_everything_is_built(self):
		with anchored("2027-01-15 10:00:00"):
			self.assertEqual(cal.prepared_pull_days(), 0)
			self.assertEqual(cal.YEAR2.shift_days, 0)
			self.assertEqual(cal.default_next_stage(), "annual_plan")

	def test_between_the_departmental_plans_and_the_annual_plan(self):
		with anchored("2026-12-04 10:00:00"):
			self.assertEqual(cal.default_next_stage(), "departmental_plans")

	def test_the_financial_years_roll_over_with_the_anchor(self):
		with anchored("2027-10-08 10:00:00"):
			self.assertEqual((cal.YEAR1.fiscal_year, cal.YEAR2.fiscal_year, cal.YEAR0.fiscal_year), ("2027-2028", "2028-2029", "2026-2027"))
			self.assertEqual(cal.fiscal("2027-06-30"), "2028-06-30")
			self.assertEqual(cal.YEAR1.shift_days % 7, 0)
			self.assertEqual(cal.YEAR1.at("2026-11-24 09:00:00"), "2026-11-24 09:00:00")

	def test_a_stored_state_changed_after_resolution_is_refused(self):
		with anchored("2026-10-09 10:00:00"):
			cal._resolved["signature"] = "something else"
			with self.assertRaises(cal.AnchorChangedError):
				original = cal._load_state
				cal._load_state = lambda: {"mode": "anchored", "anchor": "2026-10-16 10:00:00"}
				try:
					cal.assert_resolution_current()
				finally:
					cal._load_state = original


class TestTheLaddersFollowTheAnchor(unittest.TestCase):
	"""`canonical.resolve_years`: the default prepared-year stage is the furthest the anchor allows (SEED-002 v0.8 R5)."""

	def test_legacy_defaults_to_the_full_world(self):
		from kentender_core.seeds import canonical

		with legacy():
			self.assertEqual(canonical.resolve_years(), ("award", "annual_plan"))

	def test_an_october_anchor_stops_the_prepared_year_at_needs_and_refuses_a_later_cap(self):
		from kentender_core.seeds import canonical

		# the executed year's default stage is its own question (see the contracts test below); this one is about the prepared year
		with anchored("2026-10-09 10:00:00"), patch("kentender_core.seeds.canonical.contracts_available", return_value=False):
			self.assertEqual(canonical.resolve_years(), ("award", "needs"))
			self.assertEqual(canonical.resolve_years(next_year="budget"), ("award", "budget"))
			self.assertEqual(canonical.resolve_years(next_year="none"), ("award", "none"))
			def refuse(message, *args, **kwargs):
				raise ValueError(message)

			with patch("kentender_core.seeds.canonical.frappe.throw", side_effect=refuse), self.assertRaises(ValueError) as caught:
				canonical.resolve_years(next_year="annual_plan")
			self.assertIn("later than the world's anchor", str(caught.exception))

	def test_a_january_anchor_allows_the_whole_prepared_year(self):
		from kentender_core.seeds import canonical

		with anchored("2027-01-15 10:00:00"), patch("kentender_core.seeds.canonical.contracts_available", return_value=False):
			self.assertEqual(canonical.resolve_years(), ("award", "annual_plan"))

	def test_an_anchored_world_with_contract_management_goes_on_to_the_contracts_stage_by_default(self):
		"""SEED-002 v0.10 §A8.1: where Contract Management is installed and the world is anchored, the executed year carries the closed year's awards through Contract Management."""
		from kentender_core.seeds import canonical

		with anchored("2027-01-15 10:00:00"), patch("kentender_core.seeds.canonical.contracts_available", return_value=True):
			self.assertEqual(canonical.resolve_years(), ("contracts", "annual_plan"))
		with anchored("2027-01-15 10:00:00"), patch("kentender_core.seeds.canonical.contracts_available", return_value=False):
			self.assertEqual(canonical.default_current(), "award")  # without the app (or an anchor) it stops at the award, with a notice


if __name__ == "__main__":
	unittest.main()
