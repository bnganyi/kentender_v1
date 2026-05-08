# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-LIB-0140 — cards/list API contract tests."""

from __future__ import annotations

from unittest.mock import patch

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.std_library_templates import get_std_library_templates
from kentender_procurement.tender_management.services import std_template_governance as gov


class TestStdLibraryCardsStdLib0140(IntegrationTestCase):
	def test_items_contract_has_business_fields(self) -> None:
		fake_rows = [
			{
				"name": "STD-ACT",
				"template_code": "STDTV-WORKS-APR-2022",
				"template_title": "PPRA Works - Building",
				"template_version": "Rev April 2022",
				"procurement_category": "Works",
				"procurement_method_profile": "Open Tender, Restricted Tender",
				"source_authority": "PPRA",
				"source_document_code": "PPRA-2022",
				"lifecycle_status": gov.STATUS_ACTIVE,
				"latest_validation_status": gov.VALIDATION_PASS,
				"status_changed_at": "2026-04-01",
				"modified": "2026-04-02",
				"allowed_for_tender_creation": 1,
			}
		]

		def fake_get_all(doctype, **kwargs):
			if doctype == "STD Template":
				return fake_rows
			if doctype == "Procurement Tender":
				return [{"std_template": "STD-ACT"}]
			return []

		with (
			patch(
				"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
				side_effect=fake_get_all,
			),
			patch(
				"kentender_procurement.tender_management.api.std_library_templates.frappe.get_roles",
				return_value=["Administrator", "STD Template Administrator"],
			),
		):
			out = get_std_library_templates(queue="active")

		self.assertTrue(out.get("ok"))
		self.assertIn("items", out)
		self.assertEqual(len(out["items"]), 1)
		item = out["items"][0]
		for key in (
			"version_code",
			"title",
			"revision_label",
			"status",
			"procurement_category",
			"supported_methods",
			"source_authority",
			"validation_status",
			"bundle_preview_status",
			"used_by_tender_count",
			"supersession_status",
			"action_availability",
		):
			self.assertIn(key, item)
		self.assertEqual(item["version_code"], "STDTV-WORKS-APR-2022")
		self.assertEqual(item["used_by_tender_count"], 1)
		self.assertNotIn("create_std_instance", item["action_availability"])

	def test_queue_and_status_filters_still_deterministic_with_items(self) -> None:
		fake_rows = [
			{
				"name": "STD-READY",
				"template_code": "READY-1",
				"template_title": "Ready Std",
				"template_version": "Rev 1",
				"procurement_category": "Works",
				"procurement_method_profile": "Open Tender",
				"source_authority": "PPRA",
				"source_document_code": "DOC-1",
				"lifecycle_status": gov.STATUS_VALIDATED,
				"latest_validation_status": gov.VALIDATION_PASS,
				"status_changed_at": "2026-04-10",
				"modified": "2026-04-11",
				"allowed_for_tender_creation": 0,
			},
			{
				"name": "STD-ACTIVE",
				"template_code": "ACTIVE-1",
				"template_title": "Active Std",
				"template_version": "Rev 2",
				"procurement_category": "Works",
				"procurement_method_profile": "Open Tender",
				"source_authority": "PPRA",
				"source_document_code": "DOC-2",
				"lifecycle_status": gov.STATUS_ACTIVE,
				"latest_validation_status": gov.VALIDATION_PASS,
				"status_changed_at": "2026-04-12",
				"modified": "2026-04-13",
				"allowed_for_tender_creation": 1,
			},
		]

		def fake_get_all(doctype, **kwargs):
			if doctype == "STD Template":
				return fake_rows
			return []

		with (
			patch(
				"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
				side_effect=fake_get_all,
			),
			patch(
				"kentender_procurement.tender_management.api.std_library_templates.frappe.get_roles",
				return_value=["STD Template Reviewer"],
			),
		):
			out = get_std_library_templates(status=["Ready for Review"], queue="ready_review")

		self.assertEqual(out.get("total_count"), 1)
		self.assertEqual(out["items"][0]["version_code"], "READY-1")
