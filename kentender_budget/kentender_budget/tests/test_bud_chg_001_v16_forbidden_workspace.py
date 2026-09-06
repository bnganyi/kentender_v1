# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.6 / KT-STD-001 v1.2 §3A — the Budget & Funding workspace
resolves a page-load Forbidden verdict as data, never a raised
`frappe.PermissionError`. Mirrors Procurement Planning's own reference test
(`test_no_responsibility_resolves_to_the_forbidden_panel_without_record_creation`).
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_budget.services.budget_contracts import get_budget_workspace


class TestForbiddenWorkspace(FrappeTestCase):
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

	def _user_with_no_budget_responsibility(self) -> str:
		email = f"bud.nobody.{self.suffix}.{uuid4().hex[:6]}@test.local"
		user = frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": "Nobody", "enabled": 1, "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		user.add_roles("Desk User")
		self.__class__._cleanup.append(("User", email))
		return email

	def test_no_responsibility_resolves_to_the_forbidden_panel_never_a_raise(self):
		user = self._user_with_no_budget_responsibility()
		frappe.set_user(user)
		result = get_budget_workspace()
		self.assertEqual(result["outcome"], "FORBIDDEN")
		self.assertEqual(result["forbidden"]["heading"], "You do not have access to Budget & Funding")
		self.assertIn("Budget Officer, Budget Approver, Finance Confirmation Officer or Auditor", result["forbidden"]["text"])
		self.assertIn("KenTender administrator", result["forbidden"]["text"])

	def test_no_responsibility_resolves_to_forbidden_even_with_a_fiscal_year_argument(self):
		"""The verdict is resolved before any Fiscal Year/Budget lookup, not
		only on the no-argument "selection_required" branch."""
		user = self._user_with_no_budget_responsibility()
		frappe.set_user(user)
		result = get_budget_workspace(fiscal_year="2026-2027")
		self.assertEqual(result["outcome"], "FORBIDDEN")

	def test_technical_reader_is_never_forbidden(self):
		frappe.set_user("Administrator")
		result = get_budget_workspace()
		self.assertNotEqual(result.get("outcome"), "FORBIDDEN")
