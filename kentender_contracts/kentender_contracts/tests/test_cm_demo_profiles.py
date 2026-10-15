# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 13 and plan Phase 11 (tracker CM8-1101, CM8-1102; CM-AC-21): the demonstration profiles.

Each profile puts the site on one stage of one contract through the same services as production, with the seed world's own people and the site's clock at the stage. The profile already in place is left exactly
as it is (the same identities, no new history); another profile replaces it; `clean` removes the contract and puts the clock back."""

from __future__ import annotations

import unittest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_contracts.seeds import demo
from kentender_contracts.services import records
from kentender_core.services import test_clock


class TestTheProfileTable(IntegrationTestCase):
	def test_every_profile_names_a_stage_a_moment_and_people_the_seed_world_has(self):
		self.assertEqual(list(demo.PROFILES), ["RECEIVED", "SIGNING", "ACTIVE", "ACCEPTED", "PAID", "CHANGE", "WARRANTY", "TERMINATION", "CLOSED"])
		for name, profile in demo.PROFILES.items():
			self.assertEqual(profile.name, name)
			self.assertRegex(profile.at, r"^20\d\d-\d\d-\d\d \d\d:\d\d:\d\d$")
			self.assertTrue(profile.summary.endswith("."))
			self.assertIn(profile.lifecycle, ("Preparing", "Awaiting signatures", "Active", "Closed"))
			for person, command in profile.expects:
				self.assertIn(person, demo.CANONICAL, f"{name}: {person} is not a person of the seed world")
				self.assertTrue(command[0].isupper())

	def test_the_demonstration_is_refused_on_a_site_that_is_not_a_simulation_site(self):
		saved = {flag: frappe.conf.get(flag) for flag in ("kt_cm_simulation_environment", "kt_bds_simulation_environment")}
		try:
			for flag in saved:
				frappe.conf[flag] = 0
			with self.assertRaises(frappe.ValidationError):
				demo.run("ACTIVE")
		finally:
			for flag, value in saved.items():
				frappe.conf[flag] = value


class TestTheProfiles(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if frappe.db.db_type != "mariadb":
			raise unittest.SkipTest("a profile builds the ERPNext world: MariaDB test site only")

	def counts(self, case: str) -> dict[str, int]:
		mine = {d: frappe.db.count(d, {"contract_case": case}) for d in records.DOCTYPES if d not in ("Contract Case",) and frappe.get_meta(d).has_field("contract_case")}
		mine["cases"] = frappe.db.count("Contract Case", {"fixture_namespace": demo.NAMESPACE})
		return mine

	def test_a_profile_is_built_once_replaced_by_another_and_cleaned_with_the_clock_put_back(self):
		before_clock = test_clock.current_instant()
		self.addCleanup(lambda: (demo.clean(), test_clock.set_instant(before_clock), frappe.db.commit()))
		first = demo.run("SIGNING")
		self.assertTrue(first["built"] and not first["problems"], first)
		case = first["contract"]
		self.assertEqual(demo.present(), "SIGNING")
		self.assertEqual(str(test_clock.current_instant())[:19], demo.PROFILES["SIGNING"].at)
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Awaiting signatures")
		made = self.counts(case)

		again = demo.run("SIGNING")
		self.assertFalse(again["built"], "the profile in place is left as it is")
		self.assertEqual(again["contract"], case)
		self.assertEqual(self.counts(case), made, "a second run records nothing: same identities, no new history")
		self.assertEqual(demo.validate("SIGNING"), {"profile": "SIGNING", "problems": [], "ok": True})

		second = demo.run("ACTIVE")
		self.assertTrue(second["built"] and not second["problems"], second)
		self.assertFalse(frappe.db.exists("Contract Case", case), "another profile replaces the first: one contract at a time")
		self.assertEqual(demo.present(), "ACTIVE")
		self.assertEqual(self.counts(second["contract"])["cases"], 1)

		removed = demo.clean()
		self.assertEqual(removed["removed"], [second["contract"]])
		self.assertEqual(demo.present(), "")
		self.assertEqual(test_clock.current_instant(), before_clock, "the clock that was in place is put back")
		self.assertFalse(demo.state_file().exists())
