# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-LIB-0410 — validate library summary contract."""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.std_library_import_wizard import (
	get_std_library_validation_summary,
	run_std_library_validation,
)


class TestStdLibraryValidateLibraryStdLib0410(IntegrationTestCase):
	def test_validation_summary_contains_required_row_fields(self) -> None:
		out = get_std_library_validation_summary()
		self.assertTrue(out.get("ok"))
		rows = out.get("rows") or []
		self.assertGreaterEqual(len(rows), 1)
		for key in ("version", "status", "last_validated", "result", "blockers", "bundle_status"):
			self.assertIn(key, rows[0])

	def test_run_validation_returns_summary_rows(self) -> None:
		out = run_std_library_validation()
		self.assertTrue(out.get("ok"))
		self.assertGreaterEqual(len(out.get("rows") or []), 1)
		self.assertIn("Validation run completed", str(out.get("message") or ""))

	def test_summary_payload_is_business_readable(self) -> None:
		out = get_std_library_validation_summary()
		payload = str(out)
		self.assertNotIn("Traceback", payload)
		self.assertNotIn("frappe.exceptions", payload)
