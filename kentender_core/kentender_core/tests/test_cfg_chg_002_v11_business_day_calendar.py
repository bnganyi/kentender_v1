"""CFG-CHG-002 v0.11 §4.8 Phase 2d — Business Day Calendar and the
working-days schedule-profile requirement.

Covers: calendar version registration/projection, overlap supersession,
immutability, invalid-input rejection, and `register_schedule_profile_version`
requiring (and `resolve_schedule_profile` reporting) a verified calendar
whenever `counting_rule` is "Working days".

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_cfg_chg_002_v11_business_day_calendar
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import site_setup
from kentender_core.services import procurement_settings as settings
from kentender_core.services.configuration_errors import ConfigurationError
from kentender_core.tests import v16_fixtures as fx
from kentender_core.tests.responsibility_test_cleanup import purge

NS = "KT_TEST_CALENDAR"


def _milestones(**overrides):
	rows = []
	for index, (key, default, basis) in enumerate(
		(
			("invitation", None, "Statutory"),
			("bid_opening", 21, "Statutory"),
			("evaluation_completion", 30, "Statutory"),
			("award_approval", 5, "Planning assumption"),
			("award_notification", 2, "Planning assumption"),
			("contract_signing", 14, "Statutory"),
			("delivery_completion", None, "Source-derived"),
		)
	):
		row = {"milestone": key, "sequence": index + 1, "default_days": default, "basis": basis}
		row.update(overrides.get(key, {}))
		rows.append(row)
	return rows


class CalendarTestCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_site_configured()
		site_setup._seed_catalogues()
		settings.purge_fixture_profiles(NS)
		cls.addClassCleanup(cls._cleanup)
		frappe.db.commit()

	@classmethod
	def _cleanup(cls):
		frappe.set_user("Administrator")
		settings.purge_fixture_profiles(NS)
		purge()
		frappe.db.commit()

	def setUp(self):
		frappe.set_user("Administrator")

	def code(self, caught) -> str:
		return getattr(caught.exception, "code", "")

	def _register_calendar(self, name="KT Test Calendar", effective_from="2094-07-01", **kwargs):
		return settings.register_business_day_calendar_version(
			calendar_name=name,
			effective_from=effective_from,
			weekend_days=["Saturday", "Sunday"],
			fixture_namespace=NS,
			**kwargs,
		)


class TestCalendarRegistration(CalendarTestCase):
	def test_registers_a_version_with_sorted_holidays_and_default_verification(self):
		out = self._register_calendar(
			holidays=[
				{"holiday_date": "2094-12-25", "holiday_name": "Christmas Day"},
				{"holiday_date": "2094-01-01", "holiday_name": "New Year"},
			]
		)
		self.assertTrue(out["created"])
		projection = settings.get_business_day_calendar(out["calendar"])
		self.assertEqual(projection["weekend_days"], ["Saturday", "Sunday"])
		self.assertEqual(projection["verification_status"], settings.VERIFICATION_PENDING)
		self.assertEqual([h["holiday_date"] for h in projection["holidays"]], ["2094-01-01", "2094-12-25"])

	def test_a_new_overlapping_version_supersedes_the_earlier_one(self):
		first = self._register_calendar(name="KT Test Overlap Calendar", effective_until="2095-06-30")
		second = self._register_calendar(name="KT Test Overlap Calendar", effective_from="2094-09-01")
		self.assertIn(first["calendar"], second["superseded"])
		self.assertEqual(frappe.db.get_value("Business Day Calendar", first["calendar"], "status"), "Superseded")
		self.assertEqual(frappe.db.get_value("Business Day Calendar", second["calendar"], "status"), "Active")

	def test_a_calendar_version_is_never_edited_in_place_or_deleted(self):
		out = self._register_calendar(name="KT Test Immutable Calendar")
		doc = frappe.get_doc("Business Day Calendar", out["calendar"])
		doc.source_instrument = "Changed after the fact"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("Business Day Calendar", out["calendar"], ignore_permissions=True)

	def test_rejects_an_unknown_weekend_day(self):
		with self.assertRaises(frappe.ValidationError):
			settings.register_business_day_calendar_version(
				calendar_name="KT Test Bad Calendar",
				effective_from="2094-07-01",
				weekend_days=["Funday"],
				fixture_namespace=NS,
			)

	def test_rejects_a_duplicate_holiday_date(self):
		with self.assertRaises(ConfigurationError) as caught:
			settings.register_business_day_calendar_version(
				calendar_name="KT Test Dup Calendar",
				effective_from="2094-07-01",
				weekend_days=["Saturday", "Sunday"],
				holidays=[
					{"holiday_date": "2094-12-25", "holiday_name": "Christmas Day"},
					{"holiday_date": "2094-12-25", "holiday_name": "Christmas Day (again)"},
				],
				fixture_namespace=NS,
			)
		self.assertEqual(self.code(caught), "CFG_CALENDAR_REQUIRED")


class TestWorkingDaysScheduleProfile(CalendarTestCase):
	def test_working_days_without_a_calendar_is_rejected(self):
		with self.assertRaises(ConfigurationError) as caught:
			settings.register_schedule_profile_version(
				procurement_method="Open Tender",
				procurement_category="Goods",
				profile_name="KT Test — working days no calendar",
				effective_from="2094-07-01",
				milestones=_milestones(),
				counting_rule="Working days",
				fixture_namespace=NS,
			)
		self.assertEqual(self.code(caught), "CFG_CALENDAR_REQUIRED")

	def test_working_days_with_an_unknown_calendar_is_rejected(self):
		with self.assertRaises(ConfigurationError) as caught:
			settings.register_schedule_profile_version(
				procurement_method="Open Tender",
				procurement_category="Goods",
				profile_name="KT Test — working days bad calendar",
				effective_from="2094-07-01",
				milestones=_milestones(),
				counting_rule="Working days",
				calendar="Does Not Exist",
				fixture_namespace=NS,
			)
		self.assertEqual(self.code(caught), "CFG_CALENDAR_REQUIRED")

	def test_working_days_with_a_calendar_resolves_complete(self):
		# A window well clear of test_procurement_settings.py's own
		# Open Tender/Works "no profile in this window" fixture at
		# 2094-07-01..2095-06-30 (both files may run in one process).
		# CFG-UX-AC-20 — the calendar must be verified and must cover the
		# profile's own period, not merely exist.
		calendar = self._register_calendar(
			name="KT Test WD Calendar",
			effective_from="2193-07-01",
			effective_until="2194-06-30",
			verification_status=settings.VERIFICATION_VERIFIED,
		)["calendar"]
		settings.register_schedule_profile_version(
			procurement_method="Open Tender",
			procurement_category="Works",
			profile_name="KT Test — working days",
			effective_from="2193-07-01",
			effective_until="2194-06-30",
			milestones=_milestones(),
			counting_rule="Working days",
			calendar=calendar,
			fixture_namespace=NS,
		)
		resolved = settings.resolve_schedule_profile(
			procurement_method="Open Tender", procurement_category="Works", applicability_date="2193-10-01"
		)
		self.assertTrue(resolved["found"])
		self.assertTrue(resolved["complete"])
		self.assertEqual(resolved["calendar"]["calendar"], calendar)
		self.assertEqual(resolved["calendar"]["weekend_days"], ["Saturday", "Sunday"])

	def test_working_days_with_an_unverified_or_uncovering_calendar_is_rejected(self):
		"""CFG-UX-AC-20 — a calendar cannot pass on the strength of its name:
		it must be verified, and its period must cover the schedule's."""
		pending = self._register_calendar(
			name="KT Test WD Pending Calendar",
			effective_from="2193-07-01",
			effective_until="2194-06-30",
		)["calendar"]
		with self.assertRaises(ConfigurationError) as caught:
			settings.register_schedule_profile_version(
				procurement_method="Open Tender",
				procurement_category="Goods",
				profile_name="KT Test — working days unverified",
				effective_from="2193-07-01",
				effective_until="2194-06-30",
				milestones=_milestones(),
				counting_rule="Working days",
				calendar=pending,
				fixture_namespace=NS,
			)
		self.assertEqual(self.code(caught), "CFG_CALENDAR_REQUIRED")
		self.assertIn("verified", str(caught.exception))

		# Verified, but its period ends before the schedule's does.
		short = self._register_calendar(
			name="KT Test WD Short Calendar",
			effective_from="2193-07-01",
			effective_until="2193-12-31",
			verification_status=settings.VERIFICATION_VERIFIED,
		)["calendar"]
		with self.assertRaises(ConfigurationError) as caught:
			settings.register_schedule_profile_version(
				procurement_method="Open Tender",
				procurement_category="Goods",
				profile_name="KT Test — working days short calendar",
				effective_from="2193-07-01",
				effective_until="2194-06-30",
				milestones=_milestones(),
				counting_rule="Working days",
				calendar=short,
				fixture_namespace=NS,
			)
		self.assertEqual(self.code(caught), "CFG_CALENDAR_REQUIRED")
		self.assertIn("does not cover", str(caught.exception))

	def test_calendar_days_profile_carries_no_calendar_even_if_one_is_passed(self):
		# Same far-future window as the test above — clear of
		# test_procurement_settings.py's Open Tender/Services 2094-2095 fixture.
		calendar = self._register_calendar(name="KT Test Ignored Calendar")["calendar"]
		out = settings.register_schedule_profile_version(
			procurement_method="Open Tender",
			procurement_category="Services",
			profile_name="KT Test — calendar days",
			effective_from="2193-07-01",
			milestones=_milestones(),
			counting_rule="Calendar days",
			calendar=calendar,
			fixture_namespace=NS,
		)
		self.assertEqual(frappe.db.get_value("Procedure Schedule Profile", out["profile"], "calendar"), "")
