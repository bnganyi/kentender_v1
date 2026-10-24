# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 plan D5 (tracker CM8-417): a native operation runs as the service (or as the Finance person) and the web request is put back exactly as it was -- the session id, its data and the
form values -- because `frappe.set_user` alone replaces the id with the user name and the next request then arrives as a Guest (found live on 15 Oct 2026)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_contracts.services import service_principal


class TestServicePrincipal(IntegrationTestCase):
	def setUp(self):
		self.addCleanup(frappe.set_user, "Administrator")
		frappe.set_user("Guest")
		frappe.local.session.sid = "REAL-SESSION-ID"
		frappe.local.session.data = frappe._dict(marker="kept")
		frappe.local.form_dict = frappe._dict(cmd="kentender_contracts.api.contract.run_contract_command", contract="CM-1")

	def test_the_service_acts_as_administrator_and_the_request_is_restored_exactly(self):
		with service_principal.acting():
			self.assertEqual(frappe.session.user, "Administrator")
		self.assertEqual(frappe.session.user, "Guest")
		self.assertEqual(frappe.local.session.sid, "REAL-SESSION-ID", "the browser's session id is never replaced by a user name")
		self.assertEqual(frappe.local.session.data.get("marker"), "kept")
		self.assertEqual(frappe.local.form_dict.get("contract"), "CM-1")

	def test_it_is_restored_when_the_operation_fails(self):
		with self.assertRaises(RuntimeError):
			with service_principal.acting_as("Administrator"):
				raise RuntimeError("stock service down")
		self.assertEqual((frappe.session.user, frappe.local.session.sid), ("Guest", "REAL-SESSION-ID"))

	def test_acting_as_the_user_already_in_the_session_changes_nothing(self):
		frappe.set_user("Administrator")
		frappe.local.session.sid = "ADMIN-SID"
		with service_principal.acting():
			self.assertEqual(frappe.session.sid, "ADMIN-SID")
		self.assertEqual(frappe.session.sid, "ADMIN-SID")
