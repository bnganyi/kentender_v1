# CFG-CHG-002 v0.14 §10.9 (tracker CFG14-5F) — a schedule's and a working-day
# calendar's new version carry the "Reason for change" the spec's new-version
# forms ask for, and every read of a version says who recorded it, when, and
# which versions it replaced. Called through the whitelisted API, as the
# screen calls it. Writes fixture-namespaced rows, purged before and after.
import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_core.api import procurement_settings_api as api
from kentender_core.services import procurement_settings as settings

NS = "KT_TEST_SCHED_CAL"


def _milestones():
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
		rows.append({"milestone": key, "sequence": index + 1, "default_days": default, "basis": basis})
	return rows


class TestScheduleAndCalendarVersionReasons(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		settings.purge_fixture_profiles(NS)
		frappe.db.commit()
		self.addCleanup(lambda: (settings.purge_fixture_profiles(NS), frappe.db.commit()))

	def _tag(self, doctype, name):
		frappe.db.set_value(doctype, name, "fixture_namespace", NS)
		frappe.db.commit()

	def test_a_calendar_version_keeps_its_reason_and_says_who_recorded_it(self):
		first = api.register_business_day_calendar_version(
			calendar_name="KT Test calendar", effective_from="2091-01-01", effective_until="2091-12-31", weekend_days=["Saturday", "Sunday"]
		)
		self._tag(settings.CALENDAR, first["calendar"])
		second = api.register_business_day_calendar_version(
			calendar_name="KT Test calendar",
			effective_from="2091-06-01",
			effective_until="2091-12-31",
			weekend_days=["Saturday", "Sunday"],
			supersedes_version_ids=[first["calendar"]],
			change_reason="Gazetted holidays added.",
		)
		self._tag(settings.CALENDAR, second["calendar"])
		read = settings.get_business_day_calendar(second["calendar"])
		self.assertEqual(read["change_reason"], "Gazetted holidays added.")
		self.assertEqual(read["supersedes_version_ids"], [first["calendar"]])
		self.assertEqual(read["recorded_by"], "Administrator")
		self.assertTrue(read["recorded_at"])

	def test_a_schedule_version_keeps_its_reason_and_says_who_recorded_it(self):
		out = api.register_schedule_profile_version(
			procurement_method="Open Tender",
			procurement_category="Goods",
			profile_name="KT Test schedule",
			effective_from="2091-07-01",
			effective_until="2091-12-31",
			milestones=_milestones(),
			change_reason="Award approval period shortened.",
		)
		self._tag(settings.SCHEDULE_PROFILE, out["profile"])
		read = settings.get_schedule_profile(out["profile"])
		self.assertEqual(read["change_reason"], "Award approval period shortened.")
		self.assertEqual(read["supersedes_version_ids"], [])
		self.assertEqual(read["recorded_by"], "Administrator")


class TestPlaywrightCalendarPurge(FrappeTestCase):
	"""Browser specs add calendars through the screen (tracker CFG14-5F); the
	cleanup removes calendars named "Playwright…" and the source checks
	recorded on them, and nothing else."""

	def setUp(self):
		frappe.set_user("Administrator")
		settings.purge_playwright_calendars()
		frappe.db.commit()
		self.addCleanup(lambda: (settings.purge_playwright_calendars(), frappe.db.commit()))

	def test_removes_playwright_calendars_with_their_checks(self):
		from kentender_core.services import regulatory_reference as register

		out = api.register_business_day_calendar_version(
			calendar_name="Playwright purge calendar", effective_from="2092-01-01", weekend_days=["Saturday", "Sunday"]
		)
		register.record_reference_verification(target_doctype=settings.CALENDAR, target_name=out["calendar"], outcome="Pending", unresolved_points="x")
		frappe.db.commit()
		before = frappe.db.count(settings.CALENDAR)
		self.assertGreaterEqual(settings.purge_playwright_calendars(), 1)
		frappe.db.commit()
		self.assertFalse(frappe.db.exists(settings.CALENDAR, out["calendar"]))
		self.assertEqual(frappe.db.count(settings.CALENDAR), before - 1)


class TestPlaywrightSchedulePurge(FrappeTestCase):
	"""Browser specs add schedules through the screen (tracker CFG14-5F); the
	cleanup removes schedules named "Playwright…" and nothing else."""

	def setUp(self):
		frappe.set_user("Administrator")
		settings.purge_playwright_schedules()
		frappe.db.commit()
		self.addCleanup(lambda: (settings.purge_playwright_schedules(), frappe.db.commit()))

	def test_removes_playwright_schedules_only(self):
		out = api.register_schedule_profile_version(
			procurement_method="Open Tender", procurement_category="Services", profile_name="Playwright purge schedule",
			effective_from="2093-07-01", effective_until="2093-12-31", milestones=_milestones(),
		)
		frappe.db.commit()
		before = frappe.db.count(settings.SCHEDULE_PROFILE)
		self.assertEqual(settings.purge_playwright_schedules(), 1)
		frappe.db.commit()
		self.assertFalse(frappe.db.exists(settings.SCHEDULE_PROFILE, out["profile"]))
		self.assertEqual(frappe.db.count(settings.SCHEDULE_PROFILE), before - 1)
