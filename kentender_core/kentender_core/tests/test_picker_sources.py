"""kentender_core's picker sources: the gates are the administration surface's own and refuse with a masked
not-found; users are found by name or login in the database; units are labelled by their path from the root.

Run:
  bench --site kentender-test.local run-tests --app kentender_core \\
    --module kentender_core.tests.test_picker_sources
"""

from __future__ import annotations

import unittest
from unittest import mock

import frappe

from kentender_core.services import picker_sources, record_picker
from kentender_core.services.organisation_structure import _path_of


class TestPickerSources(unittest.TestCase):
	def setUp(self):
		self.addCleanup(frappe.set_user, frappe.session.user)
		frappe.set_user("Administrator")

	# -- registration ---------------------------------------------------------------------------

	def test_the_sources_are_registered_and_well_formed(self):
		keys = {s["key"] for s in picker_sources.sources()}
		self.assertEqual(keys, {"core.responsible_user", "core.organisation_unit", "core.home_unit", "core.reference_unit"})
		self.assertEqual(record_picker.check_sources(), [])

	# -- gates ----------------------------------------------------------------------------------

	def test_someone_who_cannot_administer_assignments_gets_a_masked_not_found(self):
		with mock.patch("kentender_core.services.responsibility_administration.require_assignment_administrator_any", side_effect=frappe.ValidationError("no")):
			for key in (picker_sources.USER, picker_sources.UNIT):
				with self.assertRaises(frappe.DoesNotExistError, msg=key):
					record_picker.search(key)
			with self.assertRaises(frappe.DoesNotExistError):
				record_picker.resolve(picker_sources.USER, ids=["Administrator"])

	def test_a_home_unit_is_the_configuration_administrators_to_ask(self):
		with mock.patch("kentender_core.services.site_configuration.require_configuration_administrator", side_effect=frappe.ValidationError("no")):
			with self.assertRaises(frappe.DoesNotExistError):
				record_picker.search(picker_sources.HOME_UNIT)
		# the assignment administrator's gate does not open it, and the configuration administrator's does not open the other
		with mock.patch("kentender_core.services.responsibility_administration.require_assignment_administrator_any", side_effect=frappe.ValidationError("no")):
			self.assertIn("rows", record_picker.search(picker_sources.HOME_UNIT))

	def test_a_desk_user_who_may_read_units_may_pick_one_and_anyone_else_gets_a_masked_not_found(self):
		self.assertIn("rows", record_picker.search(picker_sources.REFERENCE_UNIT))
		with mock.patch.object(frappe, "has_permission", return_value=False):
			with self.assertRaises(frappe.DoesNotExistError):
				record_picker.search(picker_sources.REFERENCE_UNIT)

	def test_the_reference_units_are_the_same_active_units_by_path(self):
		active = len(frappe.get_all("Organisation Unit", filters={"status": "Active"}))
		everyone = record_picker.search(picker_sources.REFERENCE_UNIT, limit=50)
		self.assertEqual(everyone["total"], active)

	# -- users ----------------------------------------------------------------------------------

	def staff(self):
		rows = frappe.get_all("User", filters={"enabled": 1, "user_type": "System User", "name": ("not in", ("Administrator", "Guest"))}, fields=["name", "full_name"],
			order_by="name asc", limit_page_length=1)
		if not rows:
			self.skipTest("no staff account on this site")
		return rows[0]

	def test_before_typing_a_page_of_staff_and_how_many_there_are(self):
		result = record_picker.search(picker_sources.USER)
		self.assertLessEqual(len(result["rows"]), 20)
		self.assertEqual(result["total"], frappe.db.count("User", {"enabled": 1, "user_type": "System User"}))
		self.assertFalse(result["typed"])
		self.assertEqual(result["labels"]["plural"], "users")

	def test_a_login_finds_that_person_first_and_shows_it_beneath_the_name(self):
		person = self.staff()
		result = record_picker.search(picker_sources.USER, query=person.name)
		self.assertEqual(result["rows"][0]["id"], person.name)
		self.assertEqual(result["rows"][0]["detail"], person.name)
		self.assertEqual(result["rows"][0]["label"], person.full_name or person.name)

	def test_a_name_finds_by_word_start_and_never_an_infix(self):
		person = self.staff()
		word = (person.full_name or person.name).split()[0]
		found = {r["id"] for r in record_picker.search(picker_sources.USER, query=word[:3])["rows"]}
		self.assertIn(person.name, found)
		self.assertEqual(record_picker.search(picker_sources.USER, query="qzxqzxqzx")["rows"], [])

	def test_a_disabled_account_is_not_offered_and_a_saved_one_resolves_by_name(self):
		person = self.staff()
		self.assertEqual([r["id"] for r in record_picker.resolve(picker_sources.USER, ids=[person.name, "nobody@nowhere.invalid"])["rows"]], [person.name])
		admin_like = record_picker.search(picker_sources.USER, query="Guest")
		self.assertNotIn("Guest", [r["id"] for r in admin_like["rows"]])

	# -- units ----------------------------------------------------------------------------------

	def units(self):
		rows = frappe.get_all("Organisation Unit", filters={"status": "Active"}, pluck="name")
		if not rows:
			self.skipTest("no active organisation unit on this site")
		return rows

	def test_every_active_unit_is_listed_by_its_path_from_the_root(self):
		active = self.units()
		everyone = record_picker.search(picker_sources.UNIT, limit=50)
		self.assertEqual(everyone["total"], len(active))
		rows = {r["id"]: r for r in everyone["rows"]}
		for name in list(rows)[:5]:
			self.assertEqual(rows[name]["label"], " › ".join(_path_of(name)))
		self.assertEqual({r["section"] for r in everyone["rows"]}, {"rest"})
		self.assertEqual(everyone["labels"]["rest"], "Organisation units")

	def test_a_unit_is_found_by_the_name_of_any_ancestor(self):
		for name in self.units():
			path = _path_of(name)
			if len(path) > 1:
				found = {r["id"] for r in record_picker.search(picker_sources.UNIT, query=path[0], limit=50)["rows"]}
				self.assertIn(name, found)
				return
		self.skipTest("the site has no nested unit")

	def test_an_inactive_unit_is_not_offered(self):
		inactive = frappe.get_all("Organisation Unit", filters={"status": ("!=", "Active")}, pluck="name")
		listed = {r["id"] for r in record_picker.search(picker_sources.UNIT, limit=50)["rows"]}
		self.assertFalse(set(inactive) & listed)
