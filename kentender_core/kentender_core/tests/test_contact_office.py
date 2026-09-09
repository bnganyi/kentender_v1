# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §8.5 / plan D6 — the shared `Contact Office` master.

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \
    --module kentender_core.tests.test_contact_office
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import site_setup


class TestContactOffice(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._created: list[str] = []

	def tearDown(self):
		for name in self._created:
			if frappe.db.exists("Contact Office", name):
				frappe.delete_doc("Contact Office", name, force=1, ignore_permissions=True)
		super().tearDown()

	def _make(self, **overrides):
		values = {
			"doctype": "Contact Office",
			"office_name": "Test Office — Contact Office Case",
			"contact_email": "test.office@example.test",
			"contact_phone": "",
			"status": "Active",
		}
		values.update(overrides)
		doc = frappe.get_doc(values).insert(ignore_permissions=True)
		self._created.append(doc.name)
		return doc

	def test_office_name_is_unique(self):
		self._make()
		with self.assertRaises(frappe.exceptions.DuplicateEntryError):
			self._make()

	def test_contact_email_is_required(self):
		with self.assertRaises(frappe.ValidationError):
			self._make(contact_email="")

	def test_status_defaults_to_active(self):
		doc = self._make(status=None)
		self.assertEqual(doc.status, "Active")

	def test_display_is_name_email_and_optional_phone(self):
		doc = self._make()
		self.assertEqual(doc.display(), "Test Office — Contact Office Case, test.office@example.test")
		doc.contact_phone = "+254 20 000 0000"
		self.assertEqual(doc.display(), "Test Office — Contact Office Case, test.office@example.test, +254 20 000 0000")

	def test_seed_is_idempotent(self):
		first = site_setup._seed_contact_offices()
		second = site_setup._seed_contact_offices()
		self.assertEqual(second["created"], 0)
		self.assertEqual(first["total"], len(site_setup.CONTACT_OFFICES))
		for office_name, contact_email, contact_phone, address in site_setup.CONTACT_OFFICES:
			doc = frappe.get_doc("Contact Office", office_name)
			self.assertEqual(doc.contact_email, contact_email)
			self.assertEqual(doc.status, "Active")
			# TPR-CHG-001 v0.6 §13.5 fixture: the Ministry of Health Procurement Office.
			self.assertEqual(doc.display(), site_setup.contact_office_display(office_name))
