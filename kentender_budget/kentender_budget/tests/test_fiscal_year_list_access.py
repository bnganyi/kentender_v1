# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KT-ACCESS-REV-001 AR-14 — the Budget fiscal-year catalogue is for internal users."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_budget.services.budget_contracts import list_available_fiscal_years


class TestFiscalYearListAccess(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")

	def test_a_website_account_is_refused_and_an_internal_user_is_served(self):
		email = "ar14.budget.supplier@example.test"
		if not frappe.db.exists("User", email):
			frappe.get_doc({"doctype": "User", "email": email, "first_name": "Supplier", "user_type": "Website User", "send_welcome_email": 0}).insert(ignore_permissions=True)
		frappe.set_user(email)
		with self.assertRaises(frappe.PermissionError):
			list_available_fiscal_years()
		frappe.set_user("Administrator")
		self.assertIsInstance(list_available_fiscal_years(), list)
