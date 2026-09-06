# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.9 / KT-STD-001 v1.2 §3A — System setup resolves its
Administrator/System Manager verdict as data, never a raised
`frappe.PermissionError` triggered by the framework's Page-role gate."""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.site_configuration import get_system_setup_workspace


class TestSystemSetupWorkspace(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.suffix = uuid4().hex[:6]
		cls._cleanup: list[tuple[str, str]] = []

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		for doctype, name in reversed(cls._cleanup):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		super().tearDownClass()

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.addCleanup(frappe.set_user, "Administrator")

	def _non_technical_user(self) -> str:
		email = f"setup.nobody.{self.suffix}.{uuid4().hex[:6]}@test.local"
		user = frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": "Nobody", "enabled": 1, "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		user.add_roles("Desk User")
		self.__class__._cleanup.append(("User", email))
		return email

	def test_non_technical_user_resolves_to_the_forbidden_panel_never_a_raise(self):
		user = self._non_technical_user()
		frappe.set_user(user)
		result = get_system_setup_workspace()
		self.assertEqual(result["outcome"], "FORBIDDEN")
		self.assertEqual(result["forbidden"]["heading"], "You do not have access to System setup")
		self.assertIn("Administrator or System Manager access", result["forbidden"]["text"])

	def test_administrator_is_never_forbidden(self):
		frappe.set_user("Administrator")
		result = get_system_setup_workspace()
		self.assertEqual(result["outcome"], "OK")
		self.assertIn("configured", result)

	def test_system_manager_is_never_forbidden(self):
		user = self._non_technical_user()
		frappe.get_doc("User", user).add_roles("System Manager")
		frappe.set_user(user)
		result = get_system_setup_workspace()
		self.assertEqual(result["outcome"], "OK")
