# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The canonical supplier account's people sign in with the shared fixture
password, by the same rule as the KT-STD-001 §8.3 register's actors
(Project Owner, 30 Sep 2026: "Maintain the same universal password")."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase


class TestCanonicalSupplierSignIn(IntegrationTestCase):
	def test_the_canonical_supplier_people_get_the_fixture_password(self):
		from frappe.utils.password import check_password, update_password

		from kentender_core.seeds.constants import TEST_PASSWORD
		from kentender_suppliers.supplier_accounts.seeds import canonical

		frappe.set_user("Administrator")
		for email in (canonical.MARY, canonical.DAVID):
			if frappe.db.exists("User", email):
				self.addCleanup(update_password, email, TEST_PASSWORD)
				update_password(email, "Not-the-fixture-password-1!")
		saved = frappe.flags.get("kt_fixture_passwords")
		frappe.flags.kt_fixture_passwords = True
		self.addCleanup(setattr, frappe.flags, "kt_fixture_passwords", saved)
		canonical.ensure_canonical_supplier_accounts(commit=False)
		for email in (canonical.MARY, canonical.DAVID):
			self.assertEqual(check_password(email, TEST_PASSWORD), email)
