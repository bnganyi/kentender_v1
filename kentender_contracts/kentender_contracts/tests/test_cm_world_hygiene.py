# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A test world removes only what it made, and gives back what it changed.

The people of the test and browser worlds are the seed world's own people (the entity signatory, the head of procurement, ...), so a responsibility one of them already held before a world was built belongs to the
seed world and must be held after the world is removed. An earlier teardown purged every assignment of a persona's address, and with it the seed world's Accounting Officer for the entity signatory: Award's
tests, which read that person as the Accounting Officer, then failed on the test site for a reason no Award change explained. `thread_world.teardown` now removes only the namespace it granted in.

The browser and demonstration worlds also give the seed world's people a password they know; every other module's browser specs sign those people in with the seed password, so the original is kept and put back
(`known_passwords`) and a world that is cleaned leaves nobody locked out."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils.password import check_password, update_password

from kentender_contracts.tests import known_passwords, thread_world as tw

NAMESPACE = "CM_HYGIENE"


class TestTheWorldLeavesWhatItDidNotMake(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if frappe.db.db_type != "mariadb":
			raise unittest.SkipTest("the people of a test world are granted responsibilities in the organisation structure: MariaDB test site only")

	def held(self) -> dict[str, tuple[str, str]]:
		people = [tw.email(p) for p in tw.PEOPLE]
		return {r.name: (r.user, r.business_role) for r in frappe.get_all("User Responsibility Assignment", filters={"user": ["in", people]}, fields=["name", "user", "business_role"])}

	def test_a_responsibility_held_before_the_world_was_built_is_held_after_it_is_removed(self):
		self.addCleanup(tw.teardown, NAMESPACE)
		before = self.held()
		tw.build(NAMESPACE)
		made = {n: v for n, v in self.held().items() if n not in before}
		self.assertTrue(made or before, "the world granted something, or the people already held it all")
		tw.teardown(NAMESPACE)
		after = self.held()
		self.assertEqual({n: v for n, v in before.items() if n not in after}, {}, "a responsibility the world did not grant was removed with it")
		self.assertEqual({n: v for n, v in after.items() if n not in before}, {}, "a responsibility the world granted is still there after it was removed")


class TestAWorldGivesBackThePasswordsItChanged(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if frappe.db.db_type != "mariadb":
			raise unittest.SkipTest("a world's passwords are kept for the MariaDB test site only")

	def test_the_original_password_comes_back_byte_for_byte_and_a_person_who_had_none_has_none(self):
		kept, bare = "cm.hygiene.kept@test.example.test", "cm.hygiene.bare@test.example.test"
		for address in (kept, bare):
			if not frappe.db.exists("User", address):
				frappe.get_doc({"doctype": "User", "email": address, "first_name": "Hygiene", "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True)
			frappe.db.delete("__Auth", {"doctype": "User", "name": address, "fieldname": "password"})
		update_password(kept, "Original-1-Aa1!")
		frappe.db.commit()
		original = known_passwords._current(kept)
		folder = Path(tempfile.mkdtemp())
		self.addCleanup(lambda: [frappe.delete_doc("User", a, force=True, ignore_permissions=True) for a in (kept, bare)] and frappe.db.commit())
		with mock.patch.object(known_passwords, "store", lambda: folder / "kept.json"):
			known_passwords.set_known([kept, bare, "nobody@test.example.test"], "Known-2-Aa1!")
			self.assertEqual(check_password(kept, "Known-2-Aa1!"), kept)
			known_passwords.set_known([kept], "Another-3-Aa1!")  # an earlier original is never replaced by a later world's password
			self.assertEqual(known_passwords.restore(), sorted([kept, bare]))
		self.assertEqual(known_passwords._current(kept), original)
		self.assertEqual(check_password(kept, "Original-1-Aa1!"), kept)
		self.assertIsNone(known_passwords._current(bare), "a person who had no password has none again")
		self.assertFalse((folder / "kept.json").exists())
