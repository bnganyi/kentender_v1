# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-LIB-0400 — register source document contract."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.std_library_import_wizard import (
	register_std_library_source_document,
)


class TestStdLibraryRegisterSourceStdLib0400(IntegrationTestCase):
	def test_register_source_document_requires_mandatory_fields(self) -> None:
		with self.assertRaises(frappe.ValidationError):
			register_std_library_source_document(
				source_document_code="",
				source_title="",
				source_authority="",
				revision_label="",
			)

	def test_register_source_document_success_payload(self) -> None:
		out = register_std_library_source_document(
			source_document_code="PPRA-WORKS-2022-04-PDF",
			source_title="PPRA Works Building STD Source PDF",
			source_authority="PPRA",
			revision_label="Rev April 2022",
			source_file="/files/ppra_works_rev_apr_2022.pdf",
			source_hash="sha256:abc123",
			notes="Evidence registered for audit traceability.",
		)
		self.assertTrue(out.get("ok"))
		source_document = out.get("source_document") or {}
		self.assertEqual(source_document.get("source_document_code"), "PPRA-WORKS-2022-04-PDF")
		self.assertEqual(source_document.get("activation_status"), "Not Activated")

	def test_register_source_message_clarifies_non_activation(self) -> None:
		out = register_std_library_source_document(
			source_document_code="PPRA-WORKS-2022-04-PDF",
			source_title="PPRA Works Building STD Source PDF",
			source_authority="PPRA",
			revision_label="Rev April 2022",
		)
		message = str(out.get("message") or "")
		self.assertIn("does not make an STD available for tenders", message)
		self.assertNotIn("Traceback", message)
