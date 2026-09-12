"""PLN-CHG-001 v1.18 §13.1–13.2 / plan D19 — the frozen seed clock.

A seed command run inside `clock.at(instant)` sees that instant as the
wall clock (site-local), so authority windows are evaluated for real and
nothing is back-stamped afterwards.

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_seed_clock
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now, now_datetime, nowdate

from kentender_core.seeds import clock
from kentender_core.services import authorization as auth
from kentender_core.services import responsibility_administration as administration
from kentender_core.tests import v16_fixtures as fx
from kentender_core.tests.responsibility_test_cleanup import purge

NS = "KT_TEST_CLOCK"


class TestSeedClock(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.root = fx.ensure_site_configured()
		cls.unit = fx.unit("KT Test Clock Unit", namespace=NS)
		cls.user = fx.user("clock.acting", "Clock Acting")
		administration.grant(
			user=cls.user,
			business_role="Head of User Department",
			organisation_unit=cls.unit,
			appointment_type="Acting",
			authority_reference="Test acting window",
			effective_from="2026-10-01 00:00:00",
			effective_to="2026-11-30 23:59:59",
			fixture_namespace=NS,
			actor="Administrator",
		)
		cls.addClassCleanup(purge)
		frappe.db.commit()

	def test_the_block_freezes_every_frappe_clock_at_the_site_local_instant(self):
		self.assertEqual(clock.frozen_at(), "")
		with clock.at("2026-11-25 10:30:00"):
			self.assertEqual(str(now_datetime())[:19], "2026-11-25 10:30:00")
			self.assertEqual(now()[:19], "2026-11-25 10:30:00")
			# Time ticks inside the block, so two consecutive stamps differ but
			# stay within the fixture second (Frappe's optimistic lock relies
			# on distinct `modified` values).
			first, second = now(), now()
			self.assertLessEqual(first, second)
			self.assertEqual(second[:19], "2026-11-25 10:30:00")
			self.assertEqual(nowdate(), "2026-11-25")
			self.assertEqual(clock.frozen_at(), "2026-11-25 10:30:00")
		self.assertEqual(clock.frozen_at(), "")
		self.assertNotEqual(nowdate(), "2026-11-25")

	def test_authority_is_evaluated_at_the_frozen_instant(self):
		def active() -> bool:
			return any(
				a.organisation_unit == self.unit
				for a in auth.resolve_assignments(self.user, business_role="Head of User Department")
			)

		with clock.at("2026-09-15 09:00:00"):
			self.assertFalse(active(), "scheduled, not yet effective")
		with clock.at("2026-11-25 10:30:00"):
			self.assertTrue(active(), "inside the acting window")
		with clock.at("2026-12-01 09:00:00"):
			self.assertFalse(active(), "expired")
