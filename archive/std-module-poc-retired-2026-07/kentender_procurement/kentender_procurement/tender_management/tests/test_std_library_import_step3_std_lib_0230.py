# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-LIB-0230 — import wizard Step 3 detected structure contract."""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.std_library_import_wizard import (
	get_std_library_detected_structure,
)


class TestStdLibraryImportStep3StdLib0230(IntegrationTestCase):
	def test_detected_structure_contains_required_summary_areas(self) -> None:
		out = get_std_library_detected_structure(import_code="STD-IMPORT-DRAFT")
		self.assertTrue(out.get("ok"))
		summary = out.get("summary") or {}
		self.assertIn("parts_sections", summary)
		self.assertIn("parameters", summary)
		self.assertIn("forms", summary)
		self.assertIn("boq_rules", summary)
		self.assertIn("source_mappings", summary)

	def test_works_boq_rules_visibility_flag_is_true_when_applicable(self) -> None:
		out = get_std_library_detected_structure(import_code="STD-IMPORT-DRAFT")
		summary = out.get("summary") or {}
		self.assertTrue(summary.get("works_boq_applicable"))
		self.assertIn("Works BOQ rules detected", str(summary.get("boq_rules") or ""))

	def test_summary_payload_avoids_raw_package_blob(self) -> None:
		out = get_std_library_detected_structure(import_code="STD-IMPORT-DRAFT")
		summary = out.get("summary") or {}
		self.assertNotIn("raw_json", summary)
		self.assertNotIn("raw_xml", summary)
