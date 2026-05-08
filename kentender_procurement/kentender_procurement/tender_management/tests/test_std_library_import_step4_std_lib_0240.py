# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-LIB-0240 — import wizard Step 4 validation contract."""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.std_library_import_wizard import (
	get_std_library_import_validation,
	run_std_library_import_validation,
)


class TestStdLibraryImportStep4StdLib0240(IntegrationTestCase):
	def test_validation_payload_has_required_categories(self) -> None:
		out = run_std_library_import_validation(import_code="STD-IMPORT-DRAFT")
		self.assertTrue(out.get("ok"))
		validation = out.get("validation") or {}
		rows = validation.get("categories") or []
		keys = {str(r.get("key") or "") for r in rows}
		self.assertTrue(
			{
				"sections",
				"locked_legal_text",
				"parameters",
				"forms",
				"boq_rules",
				"source_mappings",
				"generated_models",
				"bundle_rendering",
			}.issubset(keys)
		)

	def test_status_values_are_from_allowed_set(self) -> None:
		out = get_std_library_import_validation(import_code="STD-IMPORT-DRAFT")
		validation = out.get("validation") or {}
		rows = validation.get("categories") or []
		allowed = {"Passed", "Needs Attention", "Blocked", "Not Applicable"}
		for row in rows:
			self.assertIn(str(row.get("status") or ""), allowed)

	def test_blockers_have_reason_fix_and_code_without_traceback(self) -> None:
		out = get_std_library_import_validation(import_code="STD-IMPORT-DRAFT")
		validation = out.get("validation") or {}
		blockers = validation.get("blockers") or []
		self.assertGreaterEqual(len(blockers), 1)
		for blocker in blockers:
			self.assertTrue(str(blocker.get("reason") or "").strip())
			self.assertTrue(str(blocker.get("fix_path") or "").strip())
			self.assertTrue(str(blocker.get("code") or "").strip())
			text_blob = str(blocker)
			self.assertNotIn("Traceback", text_blob)
