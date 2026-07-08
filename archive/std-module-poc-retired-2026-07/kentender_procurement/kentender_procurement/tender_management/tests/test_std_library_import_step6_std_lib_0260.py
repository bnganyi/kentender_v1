# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-LIB-0260 — import wizard Step 6 final review/activation contract."""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.std_library_import_wizard import (
	activate_std_library_import,
	get_std_library_import_final_review,
	submit_std_library_import_review,
)


class TestStdLibraryImportStep6StdLib0260(IntegrationTestCase):
	def test_final_summary_contains_required_fields(self) -> None:
		out = get_std_library_import_final_review(import_code="STD-IMPORT-DRAFT")
		self.assertTrue(out.get("ok"))
		summary = out.get("summary") or {}
		for key in (
			"std_title",
			"revision",
			"source_authority",
			"source_evidence_status",
			"validation_result",
			"bundle_preview_status",
			"generated_model_status",
			"warnings",
		):
			self.assertIn(key, summary)

	def test_submit_for_review_available_when_allowed(self) -> None:
		out = get_std_library_import_final_review(import_code="STD-IMPORT-DRAFT")
		self.assertTrue((out.get("actions") or {}).get("can_submit_review"))
		res = submit_std_library_import_review(import_code="STD-IMPORT-DRAFT")
		self.assertTrue(res.get("ok"))
		self.assertIn("Submitted", str(res.get("status") or ""))

	def test_activation_blocked_when_governance_disallows(self) -> None:
		out = activate_std_library_import(import_code="STD-IMPORT-DRAFT")
		self.assertFalse(out.get("ok"))
		self.assertIn("Blocked", str(out.get("status") or ""))
		self.assertIn("review", str(out.get("message") or "").lower())

	def test_error_payloads_are_business_readable(self) -> None:
		out = activate_std_library_import(import_code="STD-IMPORT-DRAFT")
		self.assertNotIn("Traceback", str(out))
		self.assertNotIn("frappe.exceptions", str(out))
