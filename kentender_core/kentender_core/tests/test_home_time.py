"""HOME-CHG-001 v0.6 §5.1 items 2 and 4 — Home's server-made greeting and labels.

Run:
  bench --site kentender-test.local run-tests --app kentender_core \\
    --module kentender_core.tests.test_home_time
"""

from __future__ import annotations

from datetime import date, datetime
from unittest.mock import patch

from frappe.tests import IntegrationTestCase

from kentender_core.services import home_time as ht

NOW = datetime(2027, 6, 18, 10, 0)


class TestGreeting(IntegrationTestCase):
	def test_greeting_follows_site_time(self):
		self.assertEqual(ht.greeting(datetime(2027, 6, 18, 0, 0)), "Good morning")
		self.assertEqual(ht.greeting(datetime(2027, 6, 18, 11, 59)), "Good morning")
		self.assertEqual(ht.greeting(datetime(2027, 6, 18, 12, 0)), "Good afternoon")
		self.assertEqual(ht.greeting(datetime(2027, 6, 18, 16, 59)), "Good afternoon")
		self.assertEqual(ht.greeting(datetime(2027, 6, 18, 17, 0)), "Good evening")
		self.assertEqual(ht.greeting(datetime(2027, 6, 18, 23, 59)), "Good evening")


class TestRelativeLabels(IntegrationTestCase):
	"""Every string below is copied from HOME §5.1 item 4 and §10B (HOME-DES-21, 29)."""

	def test_received_today_yesterday_and_days_ago(self):
		self.assertEqual(ht.entered("Received", datetime(2027, 6, 18, 9, 0), NOW), "Received today (18 June, 09:00)")
		self.assertEqual(ht.entered("Received", datetime(2027, 6, 17, 11, 0), NOW), "Received yesterday (17 June, 11:00)")
		self.assertEqual(ht.entered("Received", datetime(2027, 6, 16, 11, 0), NOW), "Received 2 days ago (16 June, 11:00)")
		self.assertEqual(ht.entered("Received", datetime(2027, 5, 14, 10, 0), NOW), "Received 35 days ago (14 May, 10:00)")

	def test_submitted_uses_its_own_verb(self):
		self.assertEqual(ht.entered("Submitted", datetime(2027, 6, 17, 14, 0), NOW), "Submitted yesterday (17 June, 14:00)")

	def test_days_are_calendar_days_not_24_hour_periods(self):
		late_evening = datetime(2027, 6, 17, 23, 59)
		early = datetime(2027, 6, 18, 0, 5)
		self.assertEqual(ht.entered("Received", late_evening, early), "Received yesterday (17 June, 23:59)")
		self.assertEqual(ht.entered("Received", datetime(2027, 6, 17, 0, 1), datetime(2027, 6, 18, 23, 59)), "Received yesterday (17 June, 00:01)")

	def test_waiting_and_outstanding(self):
		self.assertEqual(ht.waiting(datetime(2027, 6, 16, 15, 30), NOW), "Waiting 2 days (since 16 June, 15:30)")
		self.assertEqual(ht.waiting(datetime(2027, 6, 17, 10, 0), NOW), "Waiting 1 day (since 17 June, 10:00)")
		self.assertEqual(ht.waiting(datetime(2027, 6, 18, 8, 0), NOW), "Waiting today (since 18 June, 08:00)")
		self.assertEqual(ht.outstanding(datetime(2027, 6, 3, 10, 0), NOW), "Outstanding 15 days (since 3 June, 10:00)")
		self.assertEqual(ht.outstanding(datetime(2027, 6, 17, 11, 0), NOW), "Outstanding 1 day (since 17 June, 11:00)")

	def test_a_stated_fact_names_the_exact_instant(self):
		self.assertEqual(ht.stated("Evaluation report delivered", datetime(2027, 6, 16, 14, 7), NOW), "Evaluation report delivered 16 June, 14:07")
		self.assertEqual(ht.stated("Evaluation report delivered", datetime(2026, 12, 1, 9, 0), NOW), "Evaluation report delivered 1 December 2026, 09:00")

	def test_the_year_is_shown_only_when_it_is_not_the_read_year(self):
		self.assertEqual(ht.entered("Submitted", datetime(2026, 11, 24, 12, 20), NOW), "Submitted 206 days ago (24 November 2026, 12:20)")
		self.assertEqual(ht.outstanding(datetime(2026, 12, 30, 9, 0), NOW), "Outstanding 170 days (since 30 December 2026, 09:00)")

	def test_due_within_14_days_is_relative(self):
		self.assertEqual(ht.due(date(2027, 6, 18), NOW), "Due today (18 June)")
		self.assertEqual(ht.due(date(2027, 6, 19), NOW), "Due tomorrow (19 June)")
		self.assertEqual(ht.due(date(2027, 6, 25), NOW), "Due in 7 days (25 June)")
		self.assertEqual(ht.due(date(2027, 7, 2), NOW), "Due in 14 days (2 July)")

	def test_due_beyond_14_days_shows_the_date_only(self):
		self.assertEqual(ht.due(date(2027, 7, 3), NOW), "Due 3 July")

	def test_overdue_appears_only_for_a_passed_owner_deadline(self):
		self.assertEqual(ht.due(date(2027, 6, 16), NOW), "Overdue since 16 June")
		self.assertTrue(ht.is_overdue(date(2027, 6, 17), NOW))
		self.assertFalse(ht.is_overdue(date(2027, 6, 18), NOW))
		self.assertFalse(ht.is_overdue(None, NOW))

	def test_a_deadline_with_a_time_is_overdue_once_that_time_has_passed(self):
		self.assertFalse(ht.is_overdue(datetime(2027, 6, 18, 17, 0), NOW))
		self.assertTrue(ht.is_overdue(datetime(2027, 6, 18, 9, 59), NOW))
		self.assertEqual(ht.due(datetime(2027, 6, 18, 9, 59), NOW), "Overdue since 18 June")

	def test_age_alone_never_makes_anything_overdue(self):
		# there is no function that takes a received/since instant and says overdue
		self.assertFalse(hasattr(ht, "overdue_by_age"))
		self.assertEqual(ht.entered("Received", datetime(2027, 1, 4, 9, 0), NOW), "Received 165 days ago (4 January, 09:00)")


class TestComingUp(IntegrationTestCase):
	def test_relative_badge_and_exact_time(self):
		self.assertEqual(ht.coming_up(datetime(2027, 6, 25, 11, 0), NOW), ("In 7 days", "25 June, 11:00"))
		self.assertEqual(ht.coming_up(date(2027, 7, 1), NOW), ("In 13 days", "1 July"))
		self.assertEqual(ht.coming_up(datetime(2027, 6, 18, 15, 0), NOW), ("Today", "18 June, 15:00"))
		self.assertEqual(ht.coming_up(datetime(2027, 6, 19, 9, 0), NOW), ("Tomorrow", "19 June, 09:00"))

	def test_window_is_the_read_date_plus_14_calendar_days(self):
		self.assertTrue(ht.in_coming_up_window(date(2027, 6, 18), NOW))
		self.assertTrue(ht.in_coming_up_window(date(2027, 7, 2), NOW))
		self.assertFalse(ht.in_coming_up_window(date(2027, 7, 3), NOW))
		self.assertFalse(ht.in_coming_up_window(date(2027, 6, 17), NOW))

	def test_an_instant_earlier_today_is_still_in_the_window(self):
		self.assertTrue(ht.in_coming_up_window(datetime(2027, 6, 18, 8, 0), NOW))


class TestLongInstants(IntegrationTestCase):
	def test_updated_and_owner_sentence_format(self):
		text = ht.long_instant(datetime(2027, 6, 18, 10, 0))
		self.assertTrue(text.startswith("18 June 2027, 10:00"), text)


class TestTrustedClock(IntegrationTestCase):
	def test_the_shared_test_clock_wins_when_a_test_world_set_one(self):
		with patch("kentender_core.services.home_time.test_clock.current_instant", return_value=datetime(2027, 6, 18, 10, 0)):
			self.assertEqual(ht.now(), datetime(2027, 6, 18, 10, 0))

	def test_the_site_clock_is_used_when_no_test_world_set_one(self):
		with patch("kentender_core.services.home_time.test_clock.current_instant", return_value=None):
			self.assertLess(abs((ht.now() - datetime.now()).total_seconds()), 86400)


class TestCompleted(IntegrationTestCase):
	def test_window_is_the_last_30_calendar_days_including_today(self):
		self.assertTrue(ht.in_completed_window(datetime(2027, 6, 18, 9, 0), NOW))
		self.assertTrue(ht.in_completed_window(datetime(2027, 5, 19, 0, 1), NOW))
		self.assertFalse(ht.in_completed_window(datetime(2027, 5, 18, 23, 59), NOW))
		self.assertFalse(ht.in_completed_window(datetime(2027, 6, 19, 9, 0), NOW))
		self.assertFalse(ht.in_completed_window(None, NOW))

	def test_the_sentence_names_the_action_and_the_exact_time(self):
		text = ht.completed_sentence("approved this Tender package", datetime(2027, 6, 16, 15, 30))
		self.assertTrue(text.startswith("You approved this Tender package on 16 June 2027, 15:30 "), text)
		self.assertTrue(text.endswith("."), text)

	def test_a_follow_on_clause_is_appended_after_a_space(self):
		text = ht.completed_sentence("submitted this Tender", datetime(2027, 6, 16, 9, 0), follow=ht.awaiting("publication authorisation", "Amina Hassan"))
		self.assertTrue(text.endswith(". It is awaiting publication authorisation by Amina Hassan."), text)
