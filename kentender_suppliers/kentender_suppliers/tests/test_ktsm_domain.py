# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from kentender_suppliers.services.compliance import recompute_compliance
from kentender_suppliers.services.eligibility import check_supplier_eligibility
from kentender_suppliers.services import supplier_policy


class TestKTSMProfile(IntegrationTestCase):
	def test_recompute_compliance(self):
		sg = frappe.db.get_value("Supplier Group", {"is_group": 0}, "name")
		if not sg:
			sg = frappe.db.get_value("Supplier Group", {}, "name")
		erp = frappe.get_doc(
			{
				"doctype": "Supplier",
				"supplier_name": "Test KTSM Co",
				"supplier_type": "Company",
				"supplier_group": sg,
				"kentender_supplier_code": "SUP-KE-2030-9998",
			}
		)
		erp.insert(ignore_permissions=True)
		prof = frappe.get_doc(
			{
				"doctype": "KTSM Supplier Profile",
				"erpnext_supplier": erp.name,
			}
		)
		prof.insert(ignore_permissions=True)
		r = recompute_compliance(prof.name)
		req = frappe.get_all(
			"KTSM Document Type",
			filters={"required_for_registration": 1, "is_active": 1},
			pluck="name",
		)
		if not req:
			self.assertEqual(r, "Complete")
		else:
			self.assertEqual(r, "Incomplete")

	def test_eligibility_unknown_code(self):
		r = check_supplier_eligibility("NOT-A-CODE-EVER", None)
		self.assertFalse(r.get("eligible"))
		self.assertTrue(r.get("reasons"))

	def test_supplier_code_format_rejected_in_validation(self):
		"""B1: invalid kentender_supplier_code is rejected on Supplier (when column exists)."""
		if not frappe.db.has_column("Supplier", "kentender_supplier_code"):
			return
		sg = frappe.db.get_value("Supplier Group", {"is_group": 0}, "name")
		if not sg:
			sg = frappe.db.get_value("Supplier Group", {}, "name")
		erp = frappe.get_doc(
			{
				"doctype": "Supplier",
				"supplier_name": "Invalid Code Co",
				"supplier_type": "Company",
				"supplier_group": sg,
				"kentender_supplier_code": "BAD",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			erp.insert(ignore_permissions=True)

	def test_h3_blacklist_policy_managers(self):
		self.assertIsInstance(supplier_policy.can_blacklist(), bool)
