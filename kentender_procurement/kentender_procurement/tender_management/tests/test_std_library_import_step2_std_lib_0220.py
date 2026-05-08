# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-LIB-0220 — import wizard Step 2 source evidence contract."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.std_library_import_wizard import (
	save_std_library_source_evidence,
)


class TestStdLibraryImportStep2StdLib0220(IntegrationTestCase):
	def test_source_evidence_accepts_required_fields(self) -> None:
		out = save_std_library_source_evidence(
			import_code="STD-IMPORT-DRAFT",
			source_authority="PPRA",
			source_title="KE-PPRA-WORKS-BLDG-2022-04-POC",
			source_revision="Rev April 2022",
			review_status="Draft",
		)
		self.assertTrue(out.get("ok"))
		evidence = out.get("source_evidence") or {}
		self.assertEqual(evidence.get("source_authority"), "PPRA")
		self.assertEqual(evidence.get("source_revision"), "Rev April 2022")

	def test_source_file_and_hash_are_conditional_pair(self) -> None:
		with self.assertRaises(frappe.ValidationError):
			save_std_library_source_evidence(
				import_code="STD-IMPORT-DRAFT",
				source_authority="PPRA",
				source_title="KE-PPRA-WORKS-BLDG-2022-04-POC",
				source_revision="Rev April 2022",
				review_status="Draft",
				source_file="evidence.pdf",
				source_hash="",
			)

	def test_required_fields_are_enforced(self) -> None:
		with self.assertRaises(frappe.ValidationError):
			save_std_library_source_evidence(
				import_code="STD-IMPORT-DRAFT",
				source_authority="",
				source_title="",
				source_revision="",
				review_status="",
			)
