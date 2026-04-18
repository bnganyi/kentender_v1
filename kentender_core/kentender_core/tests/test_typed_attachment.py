"""Phase F — Typed Attachment (file + Dynamic Link to any document)."""

import frappe
from frappe.tests import IntegrationTestCase


class TestTypedAttachment(IntegrationTestCase):
	doctype = None

	def test_typed_attachment_create_and_dynamic_link(self):
		code = "KT-TEST-TA-001"
		if frappe.db.exists("Procuring Entity", code):
			frappe.delete_doc("Procuring Entity", code, force=1)

		pe = frappe.get_doc(
			{
				"doctype": "Procuring Entity",
				"entity_code": code,
				"entity_name": "Test Procuring Entity for Typed Attachment",
			}
		)
		pe.insert()

		file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "typed_attachment_test.txt",
				"content": b"typed attachment test content",
				"is_private": 0,
			}
		)
		file_doc.insert()

		ta = frappe.get_doc(
			{
				"doctype": "Typed Attachment",
				"file": file_doc.file_url,
				"attachment_type": "Contract",
				"linked_doctype": "Procuring Entity",
				"linked_name": pe.name,
				"sensitivity_level": "Internal",
			}
		)
		ta.insert()

		self.assertTrue(frappe.db.exists("Typed Attachment", ta.name))
		row = frappe.get_doc("Typed Attachment", ta.name)
		self.assertEqual(row.file, file_doc.file_url)
		self.assertEqual(row.attachment_type, "Contract")
		self.assertEqual(row.linked_doctype, "Procuring Entity")
		self.assertEqual(row.linked_name, pe.name)
		self.assertEqual(row.sensitivity_level, "Internal")

		frappe.delete_doc("Typed Attachment", ta.name, force=1)
		frappe.delete_doc("File", file_doc.name, force=1)
		frappe.delete_doc("Procuring Entity", pe.name, force=1)
