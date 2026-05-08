# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-LIB-0150 — selected detail panel API contract tests."""

from __future__ import annotations

from unittest.mock import patch

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.std_library_templates import (
	get_std_library_template_detail,
)
from kentender_procurement.tender_management.services import std_template_governance as gov


class TestStdLibraryDetailStdLib0150(IntegrationTestCase):
	def test_detail_contract_by_version_code(self) -> None:
		with patch(
			"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
			return_value=[
				{
					"name": "STD-ACT",
					"template_code": "STD-ACT-001",
					"template_title": "Active STD",
					"template_version": "Rev 2",
					"source_authority": "PPRA",
					"lifecycle_status": gov.STATUS_ACTIVE,
					"latest_validation_status": gov.VALIDATION_PASS,
				}
			],
		):
			out = get_std_library_template_detail("STD-ACT-001")

		self.assertTrue(out.get("ok"))
		detail = out.get("detail") or {}
		for key in (
			"title",
			"version_code",
			"revision_label",
			"status",
			"authority",
			"validation_status",
			"bundle_preview_status",
			"state_banner",
			"summary",
			"validation",
			"bundle_preview",
			"usage",
			"supersession",
			"advanced",
			"audit",
		):
			self.assertIn(key, detail)
		self.assertEqual(detail.get("status"), "Active")
		self.assertIn("immutable", detail.get("state_banner", ""))
		self.assertIn("identity", detail.get("summary", {}))
		self.assertIn("next_action", detail.get("summary", {}))
		self.assertIn("status_bar", detail.get("bundle_preview", {}))
		self.assertIn("summary", detail.get("usage", {}))
		self.assertIn("lineage", detail.get("supersession", {}))
		self.assertIn("intro_text", detail.get("advanced", {}))
		self.assertIn("rows", detail.get("audit", {}))

	def test_state_banner_mapping_for_needs_attention_and_imported(self) -> None:
		rows = [
			{
				"name": "STD-NA",
				"template_code": "STD-NA-001",
				"template_title": "Needs Attention Std",
				"template_version": "Rev 1",
				"source_authority": "PPRA",
				"lifecycle_status": gov.STATUS_RETURNED,
				"latest_validation_status": gov.VALIDATION_FAILED,
			},
			{
				"name": "STD-IMP",
				"template_code": "STD-IMP-001",
				"template_title": "Imported Std",
				"template_version": "Rev 1",
				"source_authority": "PPRA",
				"lifecycle_status": gov.STATUS_IMPORTED,
				"latest_validation_status": gov.VALIDATION_NOT_RUN,
			},
		]

		def fake_get_all(*args, **kwargs):
			code = (kwargs.get("filters") or {}).get("template_code")
			for r in rows:
				if r["template_code"] == code:
					return [r]
			return []

		with patch(
			"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
			side_effect=fake_get_all,
		):
			na = get_std_library_template_detail("STD-NA-001")
			imp = get_std_library_template_detail("STD-IMP-001")

		self.assertIn("needs attention", na["detail"]["state_banner"].lower())
		self.assertIn("must be validated", imp["detail"]["state_banner"].lower())
		self.assertEqual(na["detail"]["summary"]["next_action"]["action"], "Resolve validation blockers.")
		self.assertEqual(imp["detail"]["summary"]["next_action"]["action"], "Validate package.")
		self.assertEqual(na["detail"]["validation"]["overall_status"], "Blocked")
		self.assertEqual(imp["detail"]["validation"]["overall_status"], "Needs Attention")

	def test_summary_payload_avoids_raw_json_or_xml(self) -> None:
		with patch(
			"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
			return_value=[
				{
					"name": "STD-R",
					"template_code": "STD-R-001",
					"template_title": "Summary STD",
					"template_version": "Rev 3",
					"source_authority": "PPRA",
					"source_document_code": "DOC1-WORKS",
					"procurement_category": "Works",
					"procurement_method_profile": "Open Tender",
					"lifecycle_status": gov.STATUS_ACTIVE,
					"latest_validation_status": gov.VALIDATION_PASS,
				}
			],
		):
			out = get_std_library_template_detail("STD-R-001")
		payload = str(out.get("detail", {}).get("summary", {})).lower()
		self.assertNotIn("raw json", payload)
		self.assertNotIn("xml", payload)

	def test_validation_payload_has_category_health_and_remediation(self) -> None:
		with patch(
			"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
			return_value=[
				{
					"name": "STD-V",
					"template_code": "STD-V-001",
					"template_title": "Validation STD",
					"template_version": "Rev 1",
					"source_authority": "PPRA",
					"source_document_code": "DOC-VAL",
					"procurement_category": "Works",
					"procurement_method_profile": "Open Tender",
					"lifecycle_status": gov.STATUS_IMPORTED,
					"latest_validation_status": gov.VALIDATION_BLOCKED,
				}
			],
		):
			out = get_std_library_template_detail("STD-V-001")
		validation = out.get("detail", {}).get("validation", {})
		self.assertIn("categories", validation)
		self.assertIn("issues", validation)
		self.assertIn("remediation", validation)
		self.assertEqual(validation.get("overall_status"), "Blocked")
		self.assertGreaterEqual(len(validation.get("categories") or []), 1)

	def test_bundle_preview_payload_has_required_sections(self) -> None:
		with patch(
			"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
			return_value=[
				{
					"name": "STD-B",
					"template_code": "STD-B-001",
					"template_title": "Bundle STD",
					"template_version": "Rev 2",
					"source_authority": "PPRA",
					"source_document_code": "DOC-BUNDLE",
					"procurement_category": "Works",
					"procurement_method_profile": "Open Tender",
					"lifecycle_status": gov.STATUS_ACTIVE,
					"latest_validation_status": gov.VALIDATION_PASS,
				}
			],
		):
			out = get_std_library_template_detail("STD-B-001")
		bundle = out.get("detail", {}).get("bundle_preview", {})
		self.assertIn("status_bar", bundle)
		self.assertIn("outline", bundle)
		self.assertIn("preview_blocks", bundle)
		self.assertIn("placeholders", bundle)
		self.assertIn("actions", bundle)
		self.assertGreaterEqual(len(bundle.get("outline") or []), 1)
		self.assertTrue(bundle.get("actions", {}).get("download_pdf", {}).get("visible"))

	def test_bundle_preview_action_mapping_hides_downloads_when_not_available(self) -> None:
		with patch(
			"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
			return_value=[
				{
					"name": "STD-B2",
					"template_code": "STD-B2-001",
					"template_title": "Bundle Pending STD",
					"template_version": "Rev 1",
					"source_authority": "PPRA",
					"source_document_code": "DOC-B2",
					"procurement_category": "Works",
					"procurement_method_profile": "Open Tender",
					"lifecycle_status": gov.STATUS_IMPORTED,
					"latest_validation_status": gov.VALIDATION_BLOCKED,
				}
			],
		):
			out = get_std_library_template_detail("STD-B2-001")
		actions = out.get("detail", {}).get("bundle_preview", {}).get("actions", {})
		self.assertFalse(actions.get("download_pdf", {}).get("visible"))
		self.assertFalse(actions.get("download_docx", {}).get("visible"))

	def test_bundle_preview_payload_avoids_raw_json_or_xml(self) -> None:
		with patch(
			"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
			return_value=[
				{
					"name": "STD-B3",
					"template_code": "STD-B3-001",
					"template_title": "Bundle Safe Copy STD",
					"template_version": "Rev 5",
					"source_authority": "PPRA",
					"source_document_code": "DOC-B3",
					"procurement_category": "Works",
					"procurement_method_profile": "Open Tender",
					"lifecycle_status": gov.STATUS_ACTIVE,
					"latest_validation_status": gov.VALIDATION_PASS,
				}
			],
		):
			out = get_std_library_template_detail("STD-B3-001")
		payload = str(out.get("detail", {}).get("bundle_preview", {})).lower()
		self.assertNotIn("raw json", payload)
		self.assertNotIn("<xml", payload)

	def test_usage_payload_has_required_sections(self) -> None:
		with patch(
			"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
			return_value=[
				{
					"name": "STD-U",
					"template_code": "STD-U-001",
					"template_title": "Usage STD",
					"template_version": "Rev 1",
					"source_authority": "PPRA",
					"source_document_code": "DOC-U",
					"procurement_category": "Works",
					"procurement_method_profile": "Open Tender",
					"lifecycle_status": gov.STATUS_ACTIVE,
					"latest_validation_status": gov.VALIDATION_PASS,
				}
			],
		):
			out = get_std_library_template_detail("STD-U-001")
		usage = out.get("detail", {}).get("usage", {})
		self.assertIn("summary", usage)
		self.assertIn("tenders", usage)
		self.assertIn("instances", usage)
		self.assertIn("outputs", usage)
		self.assertIn("addenda", usage)
		self.assertGreaterEqual(usage.get("summary", {}).get("tenders_using_count", 0), 0)

	def test_usage_payload_is_read_only_and_excludes_mutation_actions(self) -> None:
		with patch(
			"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
			return_value=[
				{
					"name": "STD-U2",
					"template_code": "STD-U2-001",
					"template_title": "Usage Safe STD",
					"template_version": "Rev 2",
					"source_authority": "PPRA",
					"source_document_code": "DOC-U2",
					"procurement_category": "Works",
					"procurement_method_profile": "Open Tender",
					"lifecycle_status": gov.STATUS_IMPORTED,
					"latest_validation_status": gov.VALIDATION_NOT_RUN,
				}
			],
		):
			out = get_std_library_template_detail("STD-U2-001")
		payload = str(out.get("detail", {}).get("usage", {}))
		self.assertNotIn("Create STD Instance", payload)
		self.assertNotIn("Edit STD Instance", payload)
		self.assertNotIn("Configure Tender Document", payload)

	def test_supersession_payload_has_lineage_and_impact(self) -> None:
		with patch(
			"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
			return_value=[
				{
					"name": "STD-S",
					"template_code": "STD-S-001",
					"template_title": "Supersession STD",
					"template_version": "Rev 6",
					"source_authority": "PPRA",
					"source_document_code": "DOC-S",
					"procurement_category": "Works",
					"procurement_method_profile": "Open Tender",
					"lifecycle_status": gov.STATUS_ACTIVE,
					"latest_validation_status": gov.VALIDATION_PASS,
				}
			],
		):
			out = get_std_library_template_detail("STD-S-001")
		sup = out.get("detail", {}).get("supersession", {})
		self.assertIn("lineage", sup)
		self.assertIn("impact", sup)
		self.assertIn("actions", sup)
		self.assertIn("current_version", sup.get("lineage", {}))
		self.assertIn("existing_tender_impact", sup.get("impact", {}))

	def test_supersession_create_revision_not_in_place_edit(self) -> None:
		with patch(
			"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
			return_value=[
				{
					"name": "STD-S2",
					"template_code": "STD-S2-001",
					"template_title": "Superseded STD",
					"template_version": "Rev 4",
					"source_authority": "PPRA",
					"source_document_code": "DOC-S2",
					"procurement_category": "Works",
					"procurement_method_profile": "Open Tender",
					"lifecycle_status": gov.STATUS_SUPERSEDED,
					"latest_validation_status": gov.VALIDATION_PASS,
				}
			],
		):
			out = get_std_library_template_detail("STD-S2-001")
		payload = str(out.get("detail", {}).get("supersession", {}))
		self.assertIn("Create New Revision", payload)
		self.assertNotIn("edit active version in place", payload.lower())

	def test_advanced_payload_has_required_shell_metadata(self) -> None:
		with patch(
			"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
			return_value=[
				{
					"name": "STD-A",
					"template_code": "STD-A-001",
					"template_title": "Advanced STD",
					"template_version": "Rev 1",
					"source_authority": "PPRA",
					"source_document_code": "DOC-A",
					"procurement_category": "Works",
					"procurement_method_profile": "Open Tender",
					"lifecycle_status": gov.STATUS_ACTIVE,
					"latest_validation_status": gov.VALIDATION_PASS,
				}
			],
		):
			out = get_std_library_template_detail("STD-A-001")
		advanced = out.get("detail", {}).get("advanced", {})
		self.assertIn("intro_text", advanced)
		self.assertIn("sections", advanced)
		self.assertIn("raw_package", advanced)
		self.assertIn("editing", advanced)
		self.assertTrue(advanced.get("raw_package", {}).get("collapsed_by_default"))
		self.assertTrue(advanced.get("raw_package", {}).get("read_only"))
		self.assertFalse(advanced.get("editing", {}).get("enabled"))

	def test_advanced_source_mappings_has_plain_label_targets(self) -> None:
		with patch(
			"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
			return_value=[
				{
					"name": "STD-M1",
					"template_code": "STD-M1-001",
					"template_title": "Mappings STD",
					"template_version": "Rev 1",
					"source_authority": "PPRA",
					"source_document_code": "DOC-M1",
					"procurement_category": "Works",
					"procurement_method_profile": "Open Tender",
					"lifecycle_status": gov.STATUS_ACTIVE,
					"latest_validation_status": gov.VALIDATION_PASS,
				}
			],
		):
			out = get_std_library_template_detail("STD-M1-001")
		targets = out.get("detail", {}).get("advanced", {}).get("source_mappings", {}).get("targets", [])
		labels = {x.get("label") for x in targets}
		self.assertIn("Submission Requirements (DSM)", labels)
		self.assertIn("Opening Register (DOM)", labels)
		self.assertIn("Evaluation Rules (DEM)", labels)
		self.assertIn("Contract Carry-Forward (DCM)", labels)
		self.assertIn("Tender Document Bundle", labels)

	def test_advanced_source_mappings_rows_have_required_columns(self) -> None:
		with patch(
			"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
			return_value=[
				{
					"name": "STD-M2",
					"template_code": "STD-M2-001",
					"template_title": "Mappings Rows STD",
					"template_version": "Rev 2",
					"source_authority": "PPRA",
					"source_document_code": "DOC-M2",
					"procurement_category": "Works",
					"procurement_method_profile": "Open Tender",
					"lifecycle_status": gov.STATUS_ACTIVE,
					"latest_validation_status": gov.VALIDATION_PASS,
				}
			],
		):
			out = get_std_library_template_detail("STD-M2-001")
		rows = out.get("detail", {}).get("advanced", {}).get("source_mappings", {}).get("rows", [])
		self.assertGreaterEqual(len(rows), 1)
		first = rows[0]
		for key in ("source", "target_code", "target_label", "generated_element", "mandatory", "status", "last_validated"):
			self.assertIn(key, first)

	def test_advanced_source_mappings_missing_rows_have_blocker_reference(self) -> None:
		with patch(
			"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
			return_value=[
				{
					"name": "STD-M3",
					"template_code": "STD-M3-001",
					"template_title": "Mappings Blocker STD",
					"template_version": "Rev 3",
					"source_authority": "PPRA",
					"source_document_code": "DOC-M3",
					"procurement_category": "Works",
					"procurement_method_profile": "Open Tender",
					"lifecycle_status": gov.STATUS_ACTIVE,
					"latest_validation_status": gov.VALIDATION_BLOCKED,
				}
			],
		):
			out = get_std_library_template_detail("STD-M3-001")
		rows = out.get("detail", {}).get("advanced", {}).get("source_mappings", {}).get("rows", [])
		blocked = [r for r in rows if r.get("status") in {"Missing", "Invalid"}]
		self.assertGreaterEqual(len(blocked), 1)
		self.assertIn("validation_blocker", blocked[0])

	def test_audit_payload_has_required_columns(self) -> None:
		with patch(
			"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
			return_value=[
				{
					"name": "STD-AUD",
					"template_code": "STD-AUD-001",
					"template_title": "Audit STD",
					"template_version": "Rev 1",
					"source_authority": "PPRA",
					"source_document_code": "DOC-AUD",
					"procurement_category": "Works",
					"procurement_method_profile": "Open Tender",
					"lifecycle_status": gov.STATUS_ACTIVE,
					"latest_validation_status": gov.VALIDATION_PASS,
				}
			],
		):
			out = get_std_library_template_detail("STD-AUD-001")
		rows = out.get("detail", {}).get("audit", {}).get("rows", [])
		self.assertGreaterEqual(len(rows), 1)
		first = rows[0]
		for key in ("timestamp", "actor", "event", "object", "result", "reason", "audit_code"):
			self.assertIn(key, first)

	def test_audit_payload_shows_denied_events_for_authorized_roles(self) -> None:
		with (
			patch(
				"kentender_procurement.tender_management.api.std_library_templates.frappe.get_all",
				return_value=[
					{
						"name": "STD-AUD2",
						"template_code": "STD-AUD2-001",
						"template_title": "Audit Denied STD",
						"template_version": "Rev 2",
						"source_authority": "PPRA",
						"source_document_code": "DOC-AUD2",
						"procurement_category": "Works",
						"procurement_method_profile": "Open Tender",
						"lifecycle_status": gov.STATUS_ACTIVE,
						"latest_validation_status": gov.VALIDATION_PASS,
					}
				],
			),
			patch(
				"kentender_procurement.tender_management.api.std_library_templates.frappe.get_roles",
				return_value=["Administrator"],
			),
		):
			out = get_std_library_template_detail("STD-AUD2-001")
		rows = out.get("detail", {}).get("audit", {}).get("rows", [])
		self.assertTrue(any((r.get("result") or "") == "Denied" for r in rows))
		self.assertTrue(out.get("detail", {}).get("audit", {}).get("read_only"))
