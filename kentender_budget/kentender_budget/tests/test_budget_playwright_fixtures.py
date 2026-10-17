# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Budget browser fixtures leave the canonical world as they found it.

Two defects found on 17 October 2026, both of which cost a rebuild of the shared test site: `purge()` deleted EVERY reservation on the canonical budget (the canonical Requisitions' own reservations are the
canonical world's evidence, `kentender_core.seeds.canonical.REQUISITIONS_NS`), and the fixtures took "the canonical budget" from the Year 1 budget while the lines, hold and successor Version 2 the browser
specs are written for (Digital Health 100m, Workforce 60m, 160m in all) belong to the Year 2 budget, so a spec was handed Year 1's code with a Version 2 that was not on it and `purge()` never removed that Version 2.

Everything here runs inside one transaction that is rolled back, so a failure of these tests cannot itself damage the shared world."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_budget.seeds import kentender_mvp_v1_portfolio as portfolio
from kentender_budget.seeds import playwright_ui_fixtures as fixtures
from kentender_core.seeds.canonical import REQUISITIONS_NS


def _canonical_reservations() -> dict[str, dict]:
	return {r.name: dict(r) for r in frappe.get_all("Funding Reservation", filters={"fixture_namespace": REQUISITIONS_NS}, fields=["name", "budget", "status", "remaining_amount", "original_amount"])}


def _trail(reservations) -> set[str]:
	return set(frappe.get_all("Budget Audit Event", filters={"reservation": ["in", list(reservations) or ["-"]]}, pluck="name"))


class TestTheBrowserFixturesLeaveTheCanonicalWorld(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.year2 = portfolio.canonical_budget("year2")
		cls.year1 = portfolio.canonical_budget("year1")

	def setUp(self):
		if not (self.year1 and self.year2):
			self.skipTest("needs the canonical two-year world (make seed-canonical)")
		frappe.set_user("Administrator")
		self.addCleanup(frappe.db.rollback)

	# -- which budget the fixtures call the canonical one ---------------------------------------------------------------------
	def test_the_fixtures_baseline_is_the_year_two_budget_with_its_own_year_and_lines(self):
		ids = fixtures._canonical_ids()
		self.assertEqual(ids["budget"], self.year2)
		self.assertEqual(ids["fiscal_year"], frappe.db.get_value("Procurement Budget", self.year2, "fiscal_year"))
		self.assertEqual(ids["dhi_line"], portfolio.canonical_budget_line("dhi", "year2"))
		self.assertEqual(ids["hwd_line"], portfolio.canonical_budget_line("hwd", "year2"))
		self.assertEqual(frappe.db.get_value("Procurement Budget Version", ids["version"], "budget"), self.year2, "Version 1 of the baseline is on the baseline budget")

	# -- purge keeps what the canonical world is made of ----------------------------------------------------------------------
	def test_purge_removes_a_reservation_that_is_not_canonical_and_keeps_every_canonical_one_with_its_trail(self):
		for year in ("year1", "year2"):
			with self.subTest(year=year):
				canonical = _canonical_reservations()
				trail = _trail(canonical)
				stray = fixtures._reserve(portfolio.canonical_budget_line("dhi", year), 1_000_000, ref=f"REQ-FIXTURE-PURGE-{year}")
				self.assertTrue(frappe.db.exists("Funding Reservation", stray))
				self.assertNotIn(stray, canonical)

				fixtures.purge(commit=False)

				self.assertFalse(frappe.db.exists("Funding Reservation", stray), "the reservation the fixtures made is removed")
				self.assertEqual(_canonical_reservations(), canonical, "every canonical reservation is exactly as it was")
				self.assertEqual(_trail(canonical), trail, "and so is the audit trail that belongs to them")
				self.assertFalse(frappe.db.exists("Budget Audit Event", {"reservation": stray}), "the removed reservation leaves no trail of its own behind")

	def test_purge_removes_the_isolated_successor_version_from_the_budget_it_was_built_on(self):
		version = portfolio.upsert_isolated_successor_version()["version"]
		self.assertEqual(frappe.db.get_value("Procurement Budget Version", version, "budget"), self.year2)

		fixtures.purge(commit=False)

		self.assertFalse(frappe.db.exists("Procurement Budget Version", version), "Version 2 goes with the reset that made it")
		first = frappe.db.get_value("Procurement Budget Version", {"budget": self.year2, "version_number": 1}, "status")
		self.assertEqual(first, "Active", "and Version 1 is the Active baseline again")

	def test_purge_keeps_the_events_the_canonical_seed_recorded_and_removes_those_a_fixture_run_wrote(self):
		budgets = [self.year1, self.year2]
		for year in ("year1", "year2"):
			with self.subTest(year=year):
				canonical_events = set(frappe.get_all("Budget Audit Event", filters={"budget": ["in", budgets]}, pluck="name"))
				stray = fixtures._reserve(portfolio.canonical_budget_line("dhi", year), 1_000_000, ref=f"REQ-FIXTURE-EVENTS-{year}")
				made = set(frappe.get_all("Budget Audit Event", filters={"budget": ["in", budgets]}, pluck="name")) - canonical_events
				self.assertTrue(made, "reserving wrote events")

				fixtures.purge(commit=False)

				left = set(frappe.get_all("Budget Audit Event", filters={"budget": ["in", budgets]}, pluck="name"))
				self.assertEqual(left & made, set(), f"what the reservation {stray} wrote is gone")
				self.assertEqual(canonical_events - left, set(), "nothing the canonical seed recorded was removed")

	# -- a run leaves no Fiscal Year behind ------------------------------------------------------------------------------------
	def test_purge_removes_the_scaffolding_years_and_a_budget_a_spec_registered_on_one(self):
		other = fixtures._ensure_isolated_fy(fixtures.EMPTY_FY_START + 1)
		canonical_years = {frappe.db.get_value("Procurement Budget", b, "fiscal_year") for b in (self.year1, self.year2)}
		# a budget recorded through the screen is not named BUD19-: it is found by its year (the fixture builds one through the real commands, then takes the name the system would have generated)
		iso = fixtures._isolated_budget(code="BUD19-SCREEN-TEST", fy_start_year=fixtures.EMPTY_FY_START, dhi=1_000_000, hwd=None, submit=False)
		fy = frappe.db.get_value("Procurement Budget", iso["budget"], "fiscal_year")
		frappe.db.set_value("Procurement Budget", iso["budget"], "generated_reference", "MOH-BUD-SCREEN-TEST", update_modified=False)
		registered = frappe._dict(name=iso["budget"])

		fixtures.purge(commit=False)

		self.assertFalse(frappe.db.exists("Procurement Budget", registered.name), "the budget a spec registered on the year goes")
		self.assertFalse(frappe.db.exists("Fiscal Year", fy), "and so does the year")
		self.assertFalse(frappe.db.exists("Fiscal Year", other))
		for year in canonical_years:
			self.assertTrue(frappe.db.exists("Fiscal Year", year), f"the canonical year {year} stays")

	def test_every_start_year_a_fixture_scaffolds_is_one_purge_removes(self):
		import inspect
		import re

		from kentender_budget.seeds import funding_ui_fixtures

		found = set(re.findall(r"fy_start_year=(\d{4})", "".join(inspect.getsource(module) for module in (fixtures, portfolio, funding_ui_fixtures))))
		found = {int(year) for year in found} | {fixtures.EMPTY_FY_START, fixtures.EMPTY_FY_START + 1, funding_ui_fixtures.ISOLATED_YEAR, funding_ui_fixtures.ISOLATED_YEAR + 1}
		self.assertLessEqual(found, fixtures.ISOLATED_FY_STARTS, "a fixture scaffolds a Fiscal Year that purge would leave behind: add its start year to ISOLATED_FY_STARTS")
		self.assertTrue(found.isdisjoint({2025, 2026, 2027, 2028}), "and none of them is a canonical year")

