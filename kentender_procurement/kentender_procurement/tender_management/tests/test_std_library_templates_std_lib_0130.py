# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-LIB-0130 — templates API contract and filter semantics."""

from __future__ import annotations

from unittest.mock import patch

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.std_library_templates import (
	get_std_library_templates,
)
from kentender_procurement.tender_management.services import std_template_governance as gov


class TestStdLibraryTemplatesStdLib0130(IntegrationTestCase):
	def test_contract_accepts_expected_query_params(self) -> None:
		with patch(
			"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
			return_value=[],
		):
			out = get_std_library_templates(
				search="Works",
				procurement_category="Works",
				procurement_method="Open Tender",
				status=["Active"],
				source_authority="PPRA",
				validation_status=["Passed"],
				supersession_status=["Current"],
				used_by_tenders="Any",
				bundle_preview_status=["Available"],
				revision_from="2026-01-01",
				revision_to="2026-12-31",
				queue="active",
			)
		self.assertTrue(out.get("ok"))
		self.assertIn("rows", out)
		self.assertIn("total_count", out)
		self.assertIn("applied_filters", out)
		self.assertEqual(out["queue"], "active")

	def test_status_and_queue_filters_reduce_rows_deterministically(self) -> None:
		fake_rows = [
			{
				"name": "STD-ACT",
				"template_code": "A1",
				"template_title": "Works Active",
				"template_version": "Rev 2026",
				"procurement_category": "Works",
				"procurement_method_profile": "Open Tender",
				"source_authority": "PPRA",
				"source_document_code": "DOC-A",
				"lifecycle_status": gov.STATUS_ACTIVE,
				"latest_validation_status": gov.VALIDATION_PASS,
				"status_changed_at": "2026-04-01",
				"modified": "2026-04-02",
				"allowed_for_tender_creation": 1,
			},
			{
				"name": "STD-IMP",
				"template_code": "I1",
				"template_title": "Works Imported",
				"template_version": "Rev 2025",
				"procurement_category": "Works",
				"procurement_method_profile": "Open Tender",
				"source_authority": "PPRA",
				"source_document_code": "DOC-I",
				"lifecycle_status": gov.STATUS_IMPORTED,
				"latest_validation_status": gov.VALIDATION_NOT_RUN,
				"status_changed_at": "2026-03-10",
				"modified": "2026-03-11",
				"allowed_for_tender_creation": 0,
			},
		]

		def fake_get_all(doctype, **kwargs):
			if doctype == "STD Template":
				return fake_rows
			if doctype == "Procurement Tender":
				return [{"std_template": "STD-ACT"}]
			return []

		with patch(
			"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
			side_effect=fake_get_all,
		):
			out = get_std_library_templates(status=["Active"], queue="active")

		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("total_count"), 1)
		self.assertEqual(out["rows"][0]["name"], "STD-ACT")
		self.assertTrue(out["rows"][0]["used_by_tenders"])
