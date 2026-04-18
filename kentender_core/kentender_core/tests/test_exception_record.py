"""Phase E — Exception Record (Dynamic Link to any document)."""

import frappe
from frappe.tests import IntegrationTestCase


class TestExceptionRecord(IntegrationTestCase):
	doctype = None

	def test_exception_record_create_and_dynamic_link(self):
		code = "KT-TEST-ER-001"
		if frappe.db.exists("Procuring Entity", code):
			frappe.delete_doc("Procuring Entity", code, force=1)

		pe = frappe.get_doc(
			{
				"doctype": "Procuring Entity",
				"entity_code": code,
				"entity_name": "Test Procuring Entity for Exception Record",
			}
		)
		pe.insert()

		ex = frappe.get_doc(
			{
				"doctype": "Exception Record",
				"reference_doctype": "Procuring Entity",
				"reference_name": pe.name,
				"reason": "Integration test exception",
				"status": "Draft",
			}
		)
		ex.insert()

		self.assertTrue(frappe.db.exists("Exception Record", ex.name))
		row = frappe.get_doc("Exception Record", ex.name)
		self.assertEqual(row.reference_doctype, "Procuring Entity")
		self.assertEqual(row.reference_name, pe.name)
		self.assertEqual(row.reason, "Integration test exception")
		self.assertEqual(row.status, "Draft")
		self.assertEqual(row.created_by, frappe.session.user)

		frappe.delete_doc("Exception Record", ex.name, force=1)
		frappe.delete_doc("Procuring Entity", pe.name, force=1)
