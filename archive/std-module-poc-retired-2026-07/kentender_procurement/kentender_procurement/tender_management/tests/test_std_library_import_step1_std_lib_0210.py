# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-LIB-0210 — import wizard Step 1 package selection contract."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.std_library_import_wizard import (
	SOURCE_BUILTIN,
	SOURCE_REGISTRY,
	SOURCE_UPLOADED,
	get_std_library_package_sources,
	select_std_library_import_package,
)


class TestStdLibraryImportStep1StdLib0210(IntegrationTestCase):
	def test_package_sources_contract_contains_required_sources(self) -> None:
		out = get_std_library_package_sources()
		self.assertTrue(out.get("ok"))
		sources = out.get("sources") or []
		labels = {str(s.get("label") or "") for s in sources}
		self.assertIn("Built-in Seed Package", labels)
		self.assertIn("Uploaded Structured Package", labels)
		self.assertIn("Connected Registry", labels)

	def test_seed_package_selection_returns_detected_metadata(self) -> None:
		out = select_std_library_import_package(
			import_code="IMPORT-0210-TEST",
			package_source=SOURCE_BUILTIN,
			package_entry="PPRA-WORKS-BLDG-2022-04",
		)
		self.assertTrue(out.get("ok"))
		metadata = out.get("metadata") or {}
		self.assertEqual(metadata.get("package_type"), "Works STD Structured Package")
		self.assertEqual(metadata.get("expected_std_category"), "WORKS")
		self.assertEqual(metadata.get("package_version"), "Rev April 2022")

	def test_raw_file_upload_is_rejected_for_runtime_package(self) -> None:
		with self.assertRaises(frappe.ValidationError):
			select_std_library_import_package(
				import_code="IMPORT-0210-TEST",
				package_source=SOURCE_UPLOADED,
				package_entry="raw_source.pdf",
			)

	def test_registry_selection_returns_structured_metadata(self) -> None:
		out = select_std_library_import_package(
			import_code="IMPORT-0210-TEST",
			package_source=SOURCE_REGISTRY,
			package_entry="registry://ppra/works/building/2022-04",
		)
		self.assertTrue(out.get("ok"))
		metadata = out.get("metadata") or {}
		self.assertEqual(metadata.get("package_type"), "Registry Structured Package")
