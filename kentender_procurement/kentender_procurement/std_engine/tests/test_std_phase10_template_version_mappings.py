from __future__ import annotations

import frappe

from kentender_procurement.std_engine.api.template_version_workbench import (
	get_std_template_version_mappings_catalogue,
)
from kentender_procurement.std_engine.services.template_version_mappings_service import (
	build_std_template_version_mappings_catalogue,
)
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR1012TemplateVersionMappingsCatalogue(_Phase7Fixture):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		for doctype, field, value in (
			("STD Extraction Mapping", "mapping_code", "STD-MAP-PH10-B1"),
			("STD Extraction Mapping", "mapping_code", "STD-MAP-PH10-D1"),
			("STD Extraction Mapping", "mapping_code", "STD-MAP-PH10-IV"),
			("STD Extraction Mapping", "mapping_code", "STD-MAP-PH10-III"),
			("STD Extraction Mapping", "mapping_code", "STD-MAP-PH10-BAD"),
			("STD Form Definition", "form_code", "STD-FORM-PH10-GAP"),
			("STD Form Definition", "form_code", "STD-FORM-PH10-III"),
			("STD Form Definition", "form_code", "STD-FORM-PH10-IVMAP"),
			("STD Section Definition", "section_code", "STD-SEC-PH10-III"),
			("STD Section Definition", "section_code", "STD-SEC-PH10-IVMAP"),
		):
			name = frappe.db.get_value(doctype, {field: value}, "name")
			if name:
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		super().tearDown()

	def _insert_sections_and_forms(self):
		for section_code, section_number, section_title, idx in (
			("STD-SEC-PH10-IVMAP", "IV", "Forms IV map", 41),
			("STD-SEC-PH10-III", "III", "Evaluation", 39),
		):
			frappe.get_doc(
				{
					"doctype": "STD Section Definition",
					"section_code": section_code,
					"version_code": self.version_code,
					"part_code": self.part_code,
					"section_number": section_number,
					"section_title": section_title,
					"section_classification": "Core",
					"editability": "Structured Editable",
					"is_mandatory": 1,
					"is_supplier_facing": 1,
					"is_contract_facing": 1,
					"order_index": idx,
					"source_document_code": self.source_doc,
				}
			).insert()
		frappe.get_doc(
			{
				"doctype": "STD Form Definition",
				"form_code": "STD-FORM-PH10-IVMAP",
				"version_code": self.version_code,
				"section_code": "STD-SEC-PH10-IVMAP",
				"title": "IV Form for DSM",
				"form_type": "Tendering Form",
				"completed_by": "Tenderer",
				"is_required": 1,
				"supplier_submission_requirement": 0,
				"drives_dsm": 1,
				"drives_dem": 0,
				"drives_dcm": 0,
				"source_document_code": self.source_doc,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Form Definition",
				"form_code": "STD-FORM-PH10-III",
				"version_code": self.version_code,
				"section_code": "STD-SEC-PH10-III",
				"title": "III Form DEM",
				"form_type": "Evaluation Form",
				"completed_by": "Procuring Entity",
				"is_required": 1,
				"supplier_submission_requirement": 0,
				"drives_dsm": 0,
				"drives_dem": 1,
				"drives_dcm": 0,
				"source_document_code": self.source_doc,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Form Definition",
				"form_code": "STD-FORM-PH10-GAP",
				"version_code": self.version_code,
				"section_code": "STD-SEC-PH10-III",
				"title": "Gap form",
				"form_type": "Other",
				"completed_by": "Tenderer",
				"is_required": 0,
				"supplier_submission_requirement": 0,
				"drives_dsm": 0,
				"drives_dem": 1,
				"drives_dcm": 0,
				"source_document_code": self.source_doc,
			}
		).insert()

	def test_not_found(self):
		out = build_std_template_version_mappings_catalogue("NO-SUCH-VERSION-999")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error"), "not_found")

	def test_tabs_and_validation_missing(self):
		self._insert_sections_and_forms()
		frappe.get_doc(
			{
				"doctype": "STD Extraction Mapping",
				"mapping_code": "STD-MAP-PH10-B1",
				"version_code": self.version_code,
				"source_object_type": "Section",
				"source_object_code": "STD-SEC-PH10-IVMAP",
				"target_model": "Bundle",
				"target_component_type": "ITT Bundle",
				"mandatory": 1,
				"validation_status": "Valid",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Extraction Mapping",
				"mapping_code": "STD-MAP-PH10-D1",
				"version_code": self.version_code,
				"source_object_type": "Form",
				"source_object_code": "STD-FORM-PH10-IVMAP",
				"target_model": "DSM",
				"target_component_type": "Tender Return",
				"mandatory": 1,
				"validation_status": "Valid",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Extraction Mapping",
				"mapping_code": "STD-MAP-PH10-BAD",
				"version_code": self.version_code,
				"source_object_type": "Clause",
				"source_object_code": "MISSING-CLAUSE",
				"target_model": "DOM",
				"target_component_type": "Deadline",
				"mandatory": 0,
				"validation_status": "Missing Source",
			}
		).insert()
		out = build_std_template_version_mappings_catalogue(self.version_code)
		self.assertTrue(out.get("ok"))
		tabs = out.get("tabs") or {}
		self.assertEqual(len(tabs.get("Bundle") or []), 1)
		self.assertEqual(len(tabs.get("DSM") or []), 1)
		self.assertEqual(len(tabs.get("DOM") or []), 1)
		miss = out.get("missing_coverage") or []
		self.assertTrue(any(m.get("validation_status") == "Missing Source" for m in miss))
		self.assertTrue(any(m.get("kind") == "gap" and m.get("source_object_code") == "STD-FORM-PH10-GAP" for m in miss))
		hi = out.get("highlights") or {}
		iv = hi.get("section_iv_dsm") or []
		self.assertTrue(any("STD-MAP-PH10-D1" == str(x.get("mapping_code")) for x in iv))
		frappe.get_doc(
			{
				"doctype": "STD Extraction Mapping",
				"mapping_code": "STD-MAP-PH10-III",
				"version_code": self.version_code,
				"source_object_type": "Form",
				"source_object_code": "STD-FORM-PH10-III",
				"target_model": "DEM",
				"target_component_type": "Scoring",
				"mandatory": 1,
				"validation_status": "Valid",
			}
		).insert()
		out2 = build_std_template_version_mappings_catalogue(self.version_code)
		hi2 = out2.get("highlights") or {}
		iii = hi2.get("section_iii_dem") or []
		self.assertTrue(any(str(x.get("mapping_code")) == "STD-MAP-PH10-III" for x in iii))

	def test_read_only_active_immutable(self):
		out = build_std_template_version_mappings_catalogue(self.version_code)
		self.assertTrue(out.get("ok"))
		self.assertTrue(out.get("read_only"))

	def test_whitelist_rejects_guest(self):
		try:
			frappe.set_user("Guest")
			self.assertRaises(frappe.PermissionError, get_std_template_version_mappings_catalogue, self.version_code)
		finally:
			frappe.set_user("Administrator")

	def test_whitelist_returns_for_admin(self):
		out = get_std_template_version_mappings_catalogue(self.version_code)
		self.assertTrue(out.get("ok"))
		self.assertIn("tabs", out)
