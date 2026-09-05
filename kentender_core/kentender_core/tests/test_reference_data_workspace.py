# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KT-STD-001 v1.2 §3A — the Reference Data workspace's page-load read
resolves a Forbidden verdict as data. Distinct from the write-command gate
(`require_reference_data_manager`, which deliberately excludes Administrator
per AUTH-AC-012 and is exercised only by user-initiated commands, not this
page-load read — see `reference_data_permissions.py`)."""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.reference_data_queries import get_reference_data_workspace


class TestReferenceDataWorkspace(IntegrationTestCase):
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

	def _plain_user(self) -> str:
		email = f"rd.nobody.{self.suffix}.{uuid4().hex[:6]}@test.local"
		user = frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": "Nobody", "enabled": 1, "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		user.add_roles("Desk User")
		self.__class__._cleanup.append(("User", email))
		return email

	def test_user_without_reference_data_manager_role_is_forbidden(self):
		user = self._plain_user()
		frappe.set_user(user)
		result = get_reference_data_workspace()
		self.assertEqual(result["outcome"], "FORBIDDEN")
		self.assertIn("Reference Data Manager", result["forbidden"]["text"])

	def test_administrator_is_never_forbidden(self):
		frappe.set_user("Administrator")
		self.assertEqual(get_reference_data_workspace()["outcome"], "OK")

	def test_reference_data_manager_role_is_never_forbidden(self):
		user = self._plain_user()
		frappe.get_doc("User", user).add_roles("Reference Data Manager")
		frappe.set_user(user)
		self.assertEqual(get_reference_data_workspace()["outcome"], "OK")
