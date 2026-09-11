# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 D2 — the shared `Delivery Location` master.

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \
    --module kentender_core.tests.test_delivery_location
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import site_setup


class TestDeliveryLocation(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._created: list[str] = []

	def tearDown(self):
		for name in self._created:
			if frappe.db.exists("Delivery Location", name):
				frappe.delete_doc("Delivery Location", name, force=1, ignore_permissions=True)
		super().tearDown()

	def _make(self, **overrides):
		values = {
			"doctype": "Delivery Location",
			"location_name": "Test Location — Delivery Location Case",
			"address": "1 Test Street, Nairobi",
			"status": "Active",
		}
		values.update(overrides)
		doc = frappe.get_doc(values).insert(ignore_permissions=True)
		self._created.append(doc.name)
		return doc

	def test_location_name_is_unique(self):
		# `autoname: field:location_name` makes the primary key itself the
		# uniqueness enforcement — a duplicate raises DuplicateEntryError, not
		# UniqueValidationError (that is for a secondary unique column).
		self._make()
		with self.assertRaises(frappe.exceptions.DuplicateEntryError):
			self._make()

	def test_address_is_required(self):
		with self.assertRaises(frappe.ValidationError):
			self._make(address="")

	def test_status_defaults_to_active(self):
		doc = self._make(status=None)
		self.assertEqual(doc.status, "Active")

	def test_seed_is_idempotent(self):
		first = site_setup._seed_delivery_locations()
		second = site_setup._seed_delivery_locations()
		self.assertEqual(second["created"], 0)
		self.assertEqual(first["total"], len(site_setup.DELIVERY_LOCATIONS))
		for location_name, address in site_setup.DELIVERY_LOCATIONS:
			doc = frappe.get_doc("Delivery Location", location_name)
			self.assertEqual(doc.address, address)
			self.assertEqual(doc.status, "Active")
