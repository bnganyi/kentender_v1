# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Found 4 Oct 2026 on a new server: a migrate on a running site registered
the Supplier Accounts module under Frappe (Module Def app_name = frappe), so
every Supplier Business Profile failed with "No module named
'frappe.core.doctype.supplier_business_profile'". After every migrate
KenTender puts each of its modules back under its own app."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core import install


class TestModuleDefRepair(IntegrationTestCase):
	def test_a_module_registered_under_frappe_is_put_back_under_its_app(self):
		self.assertEqual(frappe.db.get_value("Module Def", "Supplier Accounts", "app_name"), "kentender_suppliers")
		frappe.db.set_value("Module Def", "Supplier Accounts", "app_name", "frappe")
		frappe.clear_cache()
		self.addCleanup(lambda: (frappe.db.set_value("Module Def", "Supplier Accounts", "app_name", "kentender_suppliers"), frappe.clear_cache(),
			frappe.db.commit()))
		fixed = install.repair_module_defs()
		self.assertIn("Supplier Accounts", fixed)
		self.assertEqual(frappe.db.get_value("Module Def", "Supplier Accounts", "app_name"), "kentender_suppliers")
		self.assertEqual(frappe.new_doc("Supplier Business Profile").doctype, "Supplier Business Profile")
		self.assertEqual(install.repair_module_defs(), [])  # nothing left to repair
