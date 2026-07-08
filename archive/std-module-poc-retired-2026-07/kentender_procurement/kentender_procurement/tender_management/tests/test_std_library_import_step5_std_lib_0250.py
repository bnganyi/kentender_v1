# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-LIB-0250 — import wizard Step 5 bundle preview contract."""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.std_library_import_wizard import (
	generate_std_library_bundle_preview,
	get_std_library_bundle_preview,
	get_std_library_placeholder_list,
)


class TestStdLibraryImportStep5StdLib0250(IntegrationTestCase):
	def test_bundle_preview_contains_required_outline_sections(self) -> None:
		out = get_std_library_bundle_preview(import_code="STD-IMPORT-DRAFT")
		self.assertTrue(out.get("ok"))
		outline = out.get("outline") or []
		titles = {str(row.get("title") or "") for row in outline}
		self.assertIn("Invitation to Tender", titles)
		self.assertIn("Section X — Contract Forms", titles)

	def test_placeholder_list_is_available(self) -> None:
		out = get_std_library_placeholder_list(import_code="STD-IMPORT-DRAFT")
		self.assertTrue(out.get("ok"))
		rows = out.get("placeholders") or []
		self.assertGreaterEqual(len(rows), 1)
		self.assertIn("To be completed during tender preparation", str(rows[0]))

	def test_generate_preview_returns_business_readable_status(self) -> None:
		out = generate_std_library_bundle_preview(import_code="STD-IMPORT-DRAFT")
		self.assertTrue(out.get("ok"))
		self.assertIn("Preview", str(out.get("status") or ""))

	def test_default_preview_payload_excludes_raw_structure_blob(self) -> None:
		out = get_std_library_bundle_preview(import_code="STD-IMPORT-DRAFT")
		self.assertNotIn("raw_json", out)
		self.assertNotIn("raw_xml", out)
