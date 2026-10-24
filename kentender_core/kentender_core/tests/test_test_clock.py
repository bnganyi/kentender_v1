"""The shared test clock's policy (seed-world real-date anchor plan, step 1).

A site decides in its own site_config how its test clock may be used:

- `free` (no key): today's behaviour, any instant may be set.
- `never_ahead`: an instant later than the real clock is refused, and a stored one that is ahead is ignored.
- `off`: the site runs on the real clock; nothing may be stored, a stored value is ignored and may only be cleared.

Native ERPNext documents carry the real date and refuse a later one (a Purchase Receipt's "Posting Date cannot be future date"),
so a simulated moment later than the real clock cannot be followed by them (CM follow-up FU-CM-61).

Run:
  bench --site kentender-test.local run-tests --app kentender_core \\
    --module kentender_core.tests.test_test_clock
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import calendar, canonical
from kentender_core.services import test_clock

POLICY = "kt_test_clock_policy"
REAL_NOW = datetime(2026, 10, 15, 12, 0, 0)
PAST = "2026-10-01 09:00:00"
FUTURE = "2027-06-18 10:00:00"

_STORE: dict = {"instant": None}
_REAL_GET_HOOKS = frappe.get_hooks


def _stored():
	return _STORE["instant"]


def _store(instant) -> bool:
	_STORE["instant"] = instant
	return True


def _hooks(name=None, *args, **kwargs):
	if name == test_clock.HOOK:
		return [f"{__name__}._stored"]
	if name == test_clock.SET_HOOK:
		return [f"{__name__}._store"]
	return _REAL_GET_HOOKS(name, *args, **kwargs)


class _ClockCase(IntegrationTestCase):
	"""One fake persisted instant and a fixed real clock, so no site state is read or written."""

	def setUp(self):
		super().setUp()
		_STORE["instant"] = None
		for patcher in (patch.object(frappe, "get_hooks", _hooks), patch.object(test_clock, "now_datetime", return_value=REAL_NOW)):
			patcher.start()
			self.addCleanup(patcher.stop)

	def policy(self, value):
		patcher = patch.dict(frappe.conf, {POLICY: value} if value is not None else {})
		patcher.start()
		self.addCleanup(patcher.stop)
		if value is None:
			frappe.conf.pop(POLICY, None)


class TestFreePolicy(_ClockCase):
	def test_without_a_policy_any_instant_is_taken_and_read_back(self):
		self.policy(None)
		self.assertTrue(test_clock.set_instant(FUTURE))
		self.assertEqual(str(test_clock.current_instant()), FUTURE)

	def test_the_free_policy_is_the_default_name(self):
		self.policy("free")
		self.assertTrue(test_clock.set_instant(FUTURE))
		self.assertEqual(str(test_clock.current_instant()), FUTURE)


class TestNeverAheadPolicy(_ClockCase):
	def setUp(self):
		super().setUp()
		self.policy("never_ahead")

	def test_an_instant_in_the_past_is_taken(self):
		self.assertTrue(test_clock.set_instant(PAST))
		self.assertEqual(str(test_clock.current_instant()), PAST)

	def test_the_real_clock_itself_is_taken(self):
		self.assertTrue(test_clock.set_instant("2026-10-15 12:00:00"))

	def test_an_instant_later_than_the_real_clock_is_refused_and_not_stored(self):
		with self.assertRaises(frappe.ValidationError) as caught:
			test_clock.set_instant(FUTURE)
		self.assertIn("later than the real clock", str(caught.exception))
		self.assertIsNone(_STORE["instant"])

	def test_a_stored_instant_that_is_ahead_is_ignored_so_the_site_reads_real_time(self):
		_STORE["instant"] = FUTURE
		self.assertIsNone(test_clock.current_instant())

	def test_clearing_is_always_allowed(self):
		_STORE["instant"] = FUTURE
		self.assertTrue(test_clock.set_instant(None))
		self.assertIsNone(_STORE["instant"])


class TestOffPolicy(_ClockCase):
	def setUp(self):
		super().setUp()
		self.policy("off")

	def test_nothing_is_taken_and_nothing_is_stored(self):
		self.assertFalse(test_clock.set_instant(PAST))
		self.assertIsNone(_STORE["instant"])

	def test_a_stored_instant_is_ignored(self):
		_STORE["instant"] = PAST
		self.assertIsNone(test_clock.current_instant())

	def test_a_stored_instant_can_still_be_cleared(self):
		_STORE["instant"] = FUTURE
		self.assertTrue(test_clock.set_instant(None))
		self.assertIsNone(_STORE["instant"])

	def test_an_unknown_policy_is_read_as_off_never_as_free(self):
		self.policy("of")
		_STORE["instant"] = PAST
		self.assertIsNone(test_clock.current_instant())
		self.assertFalse(test_clock.set_instant(PAST))


class TestWhatAValidationSeesOfTheClock(_ClockCase):
	def test_free_on_a_test_environment_must_read_the_expected_instant(self):
		self.policy(None)
		_STORE["instant"] = FUTURE
		self.assertEqual(test_clock.problem(expected=FUTURE), "")
		self.assertIn("is not at", test_clock.problem(expected="2027-06-19 10:00:00"))

	def test_free_with_nothing_expected_reports_nothing(self):
		self.policy(None)
		_STORE["instant"] = FUTURE
		self.assertEqual(test_clock.problem(expected=None), "")

	def test_off_reports_any_stored_instant(self):
		self.policy("off")
		self.assertEqual(test_clock.problem(expected=FUTURE), "")
		_STORE["instant"] = PAST
		self.assertIn("policy is off", test_clock.problem(expected=FUTURE))

	def test_never_ahead_reports_a_stored_instant_that_is_ahead(self):
		self.policy("never_ahead")
		self.assertEqual(test_clock.problem(expected=None), "")
		_STORE["instant"] = PAST
		self.assertEqual(test_clock.problem(expected=None), "")
		_STORE["instant"] = FUTURE
		self.assertIn("ahead of the real clock", test_clock.problem(expected=None))

	def test_describe_gives_the_policy_the_stored_instant_and_whether_it_is_ahead(self):
		self.policy("never_ahead")
		_STORE["instant"] = FUTURE
		self.assertEqual(test_clock.describe(), {"policy": "never_ahead", "stored": FUTURE, "real_now": str(REAL_NOW), "ahead": True})


class TestTheCanonicalValidationReadsThePolicy(_ClockCase):
	"""`canonical.validate()` asks `_clock_problem()`; the full world is not built here."""

	def test_a_test_environment_on_the_default_policy_expects_the_as_at_instant(self):
		self.policy(None)
		with patch.dict(frappe.conf, {"kt_bds_simulation_environment": 1}):
			_STORE["instant"] = calendar.as_at()
			self.assertEqual(canonical._clock_problem(), "")
			_STORE["instant"] = PAST
			self.assertIn("is not at", canonical._clock_problem())

	def test_a_site_that_is_not_a_test_environment_expects_nothing_on_the_default_policy(self):
		self.policy(None)
		with patch.dict(frappe.conf, {"kt_bds_simulation_environment": 0}):
			_STORE["instant"] = PAST
			self.assertEqual(canonical._clock_problem(), "")

	def test_never_ahead_fails_the_world_whose_clock_is_still_the_2027_as_at(self):
		self.policy("never_ahead")
		with patch.dict(frappe.conf, {"kt_bds_simulation_environment": 1}):
			_STORE["instant"] = calendar.AS_AT
			self.assertIn("ahead of the real clock", canonical._clock_problem())

	def test_off_expects_no_instant_even_on_a_test_environment(self):
		self.policy("off")
		with patch.dict(frappe.conf, {"kt_bds_simulation_environment": 1}):
			self.assertEqual(canonical._clock_problem(), "")
			_STORE["instant"] = PAST
			self.assertIn("policy is off", canonical._clock_problem())
