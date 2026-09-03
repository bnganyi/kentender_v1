"""CTX-CHG-001 Phase A — whitelisted working-context endpoints."""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.api import working_context_api as api


class TestWorkingContextApi(IntegrationTestCase):
	def setUp(self):
		self.suffix = uuid4().hex[:8]
		self.addCleanup(frappe.set_user, "Administrator")
		self.pe = f"PE-CTXAPI-{self.suffix}".upper()
		frappe.get_doc(
			{
				"doctype": "Procuring Entity",
				"entity_code": self.pe,
				"legal_name": "Context API Entity",
				"reporting_currency": "KES",
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		self.addCleanup(frappe.delete_doc, "Procuring Entity", self.pe, force=True, ignore_permissions=True)
		self.user = f"ctxapi.{self.suffix}@test.local"
		frappe.get_doc(
			{"doctype": "User", "email": self.user, "first_name": "Ctx", "enabled": 1, "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		self.addCleanup(frappe.delete_doc, "User", self.user, force=True, ignore_permissions=True)
		name = frappe.get_doc(
			{"doctype": "User Permission", "user": self.user, "allow": "Procuring Entity", "for_value": self.pe}
		).insert(ignore_permissions=True).name
		self.addCleanup(frappe.delete_doc, "User Permission", name, force=True, ignore_permissions=True)
		frappe.clear_cache(user=self.user)
		self.addCleanup(frappe.clear_cache, user=self.user)

	def test_endpoints_are_whitelisted(self):
		for fn in (api.get_working_context, api.select_working_pe, api.select_module_financial_year):
			self.assertTrue(getattr(fn, "__func__", fn) in frappe.whitelisted or fn in frappe.whitelisted)

	def test_get_working_context_resolves_for_the_session_user(self):
		frappe.set_user(self.user)
		resolved = api.get_working_context()
		self.assertEqual(resolved["pe"]["selected"]["id"], self.pe)
		self.assertIsNone(resolved["fy"])

	def test_select_working_pe_persists(self):
		frappe.set_user(self.user)
		api.select_working_pe(self.pe)
		frappe.set_user("Administrator")
		frappe.set_user(self.user)
		self.assertEqual(api.get_working_context()["pe"]["selected"]["id"], self.pe)

	def test_module_fy_requires_a_selected_pe(self):
		outsider = f"ctxapi.none.{self.suffix}@test.local"
		frappe.get_doc(
			{"doctype": "User", "email": outsider, "first_name": "None", "enabled": 1, "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		self.addCleanup(frappe.delete_doc, "User", outsider, force=True, ignore_permissions=True)
		frappe.set_user(outsider)
		with self.assertRaises(frappe.ValidationError):
			api.select_module_financial_year("home", "FY-2222-2223")
