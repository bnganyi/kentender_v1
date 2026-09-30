# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Every Bid Opening demo profile loads on the canonical world and gives each
named person the next step it promises; restoring puts the finished
canonical opening back with every seed check passing and no test clock.
Run on the canonical world (`make bop-profiles-gate`); it leaves the world as
it found it."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.bid_opening.seeds import profiles


class TestDemoProfiles(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.addClassCleanup(profiles.restore_base)

	def test_every_profile_loads_with_its_promised_next_steps(self):
		for profile in profiles.PROFILES:
			with self.subTest(profile=profile):
				report = profiles.load_profile(profile=profile)
				self.assertEqual(profiles.loaded_profile(), profile)
				self.assertTrue(report["site_clock"])
				self.assertEqual([c for c in report["checks"] if not c["ok"]], [])
				self.assertTrue(report["do"] or profiles.PROFILES[profile].get("world") == "browser")

	def test_restore_puts_the_finished_opening_back(self):
		from kentender_core.services.test_clock import current_instant

		profiles.load_profile(profile="BOP-DEMO-READ-ALOUD")
		restored = profiles.restore_base()
		self.assertEqual(restored["failures"], [])
		self.assertIsNone(current_instant())
		self.assertEqual(frappe.db.get_value("Bid Opening Case", {"tender_reference": restored["tender"]}, "state"), "Opening complete")
