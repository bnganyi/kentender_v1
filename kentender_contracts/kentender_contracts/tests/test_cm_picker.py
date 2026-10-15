# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AGENTS.md section 6.12 (plan Phase 4; tracker CM8-415): a choice of one person or one record on the contract screens is the shared record picker, the sources are registered and well shaped,
the picker and the command agree about every person, and whoever may not choose gets the masked not-found."""

from __future__ import annotations

import unittest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_contracts.services import delivery, errors, picker_sources as sources
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_core.services import record_picker


class TestPickerSources(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if frappe.db.db_type != "mariadb":
			raise unittest.SkipTest("the picker reads ERPNext records on the MariaDB test site")
		world.build()
		cls.people = tw.build()
		cls.addClassCleanup(tw.teardown)
		cls.addClassCleanup(lambda: world.teardown())

	def ask(self, who, source, context, query=""):
		frappe.set_user(self.people[who])
		self.addCleanup(frappe.set_user, "Administrator")
		return record_picker.search(source, query, context)

	def test_the_sources_are_registered_and_well_shaped(self):
		self.assertEqual(record_picker.check_sources(), [])
		keys = {s["key"] for s in record_picker._load()}
		self.assertTrue({sources.PERSON, sources.RECORD} <= keys)

	def test_the_picker_and_the_command_agree_about_every_person(self):
		for role in sources.ROLES:
			listed = {row["id"] for row in self.ask("charles", sources.PERSON, {"role": role}, "")["rows"]}
			self.assertTrue(listed, role)
			for user in listed:
				self.assertEqual(delivery.eligibility(user, role), "", f"{user} is listed for {role} so the command accepts them")
			holders = set(frappe.get_all("User Responsibility Assignment", filters={"business_role": role, "status": "Enabled"}, pluck="user"))
			for user in holders - listed:
				self.assertNotEqual(delivery.eligibility(user, role), "", f"{user} is not listed for {role} so the command refuses them")
		self.assertIn(self.people["julia"], {r["id"] for r in self.ask("charles", sources.PERSON, {"role": "Contract inspection"}, "julia")["rows"]})
		refused = delivery.eligibility(self.people["grace"], "Contract inspection")
		self.assertIn("does not hold the Contract inspection responsibility", refused)

	def test_a_person_who_is_not_preparing_gets_the_masked_not_found_and_so_does_an_unknown_kind(self):
		for who in ("stranger", "mary", "grace"):
			with self.assertRaises(frappe.DoesNotExistError):
				self.ask(who, sources.PERSON, {"role": "Contract inspection"})
		with self.assertRaises(frappe.DoesNotExistError):
			self.ask("charles", sources.PERSON, {"role": "Accounting Officer"})
		with self.assertRaises(frappe.DoesNotExistError):
			self.ask("charles", sources.RECORD, {"kind": "user"})
		with self.assertRaises(frappe.DoesNotExistError):
			self.ask("charles", sources.RECORD, {"kind": "account.bank"})  # Finance's choice, not procurement's

	def test_native_records_are_filtered_in_the_database_and_finance_chooses_its_own(self):
		found = self.ask("charles", sources.RECORD, {"kind": "item"}, "CM-TEST-LAPTOP")
		self.assertTrue({world.ITEM_FA, world.ITEM_STK} <= {r["id"] for r in found["rows"]})
		self.assertEqual([r["id"] for r in self.ask("charles", sources.RECORD, {"kind": "supplier"}, world.SUPPLIER)["rows"]][:1], [world.SUPPLIER])
		bank = self.ask("josphat", sources.RECORD, {"kind": "account.bank"}, "CM Test Bank")
		self.assertIn(world.BANK_ACCOUNT, {r["id"] for r in bank["rows"]})
		self.assertTrue(self.ask("josphat", sources.RECORD, {"kind": "cost_centre"})["rows"])

	def test_a_member_the_command_refuses_is_named_in_its_words(self):
		with self.assertRaises(errors.InputError) as caught:
			delivery._members([{"user": self.people["julia"], "capacity": "Chair"}, {"user": self.people["grace"]}, {"user": self.people["brian"]}])
		self.assertIn("does not hold the Contract inspection responsibility", caught.exception.fields["members"])

	def test_units_are_listed_only_where_the_person_prepares_contracts(self):
		everyone = {r["id"] for r in self.ask("charles", sources.UNIT, {})["rows"]}
		self.assertEqual(everyone, set(frappe.get_all("Organisation Unit", pluck="name")), "the head of procurement prepares for every unit")
		brian = {r["id"] for r in self.ask("brian", sources.UNIT, {})["rows"]}
		self.assertEqual(brian, {tw.unit()}, "a Contract preparation assignment reaches its own unit")
		for who in ("julia", "mary", "grace", "stranger"):
			with self.assertRaises(frappe.DoesNotExistError):
				self.ask(who, sources.UNIT, {})
		self.assertEqual([r["id"] for r in self.ask("brian", sources.UNIT, {}, "no such unit anywhere")["rows"]], [])

	def test_the_native_documents_an_opening_position_links_are_chosen_by_preparers_only(self):
		for kind in ("purchase_order", "purchase_receipt", "purchase_invoice", "payment_entry"):
			self.assertIn("rows", self.ask("brian", sources.RECORD, {"kind": kind}), kind)
			for who in ("julia", "mary"):
				with self.assertRaises(frappe.DoesNotExistError):
					self.ask(who, sources.RECORD, {"kind": kind})
