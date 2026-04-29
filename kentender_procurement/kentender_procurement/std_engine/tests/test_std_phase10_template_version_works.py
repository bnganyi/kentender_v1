from __future__ import annotations

import frappe

from kentender_procurement.std_engine.api.template_version_workbench import (
	get_std_template_version_works_configuration,
)
from kentender_procurement.std_engine.services.template_version_works_service import (
	build_std_template_version_works_configuration,
)
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR1011TemplateVersionWorksConfiguration(_Phase7Fixture):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		for doctype, field, value in (
			("STD Extraction Mapping", "mapping_code", "STD-CARRY-PH10-1"),
			("STD Extraction Mapping", "mapping_code", "STD-EVAL-PH10-1"),
			("STD Works Requirement Component Definition", "component_code", "STD-WRC-PH10-1"),
		):
			name = frappe.db.get_value(doctype, {field: value}, "name")
			if name:
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		super().tearDown()

	def _insert_works_records(self):
		frappe.get_doc(
			{
				"doctype": "STD Works Requirement Component Definition",
				"component_code": "STD-WRC-PH10-1",
				"version_code": self.version_code,
				"section_code": self.section_code,
				"component_title": "Site Access Requirements",
				"component_type": "Site",
				"is_required": 1,
				"supports_structured_text": 1,
				"supports_table_data": 0,
				"supports_attachments": 1,
				"attachment_required": 1,
				"drives_dsm": 1,
				"drives_dem": 0,
				"drives_dcm": 1,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Extraction Mapping",
				"mapping_code": "STD-EVAL-PH10-1",
				"version_code": self.version_code,
				"source_object_type": "Evaluation Rule",
				"source_object_code": "DOC1-EVAL-RULE-001",
				"target_model": "DEM",
				"target_component_type": "Evaluation Criterion",
				"mandatory": 1,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Extraction Mapping",
				"mapping_code": "STD-CARRY-PH10-1",
				"version_code": self.version_code,
				"source_object_type": "SCC Parameter",
				"source_object_code": "DOC1-SCC-001",
				"target_model": "DCM",
				"target_component_type": "Contract Particulars",
				"mandatory": 1,
			}
		).insert()

	def test_works_configuration_contains_profile_boq_and_warnings(self):
		self._insert_works_records()
		out = build_std_template_version_works_configuration(self.version_code)
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("version_code"), self.version_code)
		profile = out.get("works_profile") or {}
		self.assertEqual(profile.get("profile_code"), self.profile_code)
		self.assertTrue(profile.get("requires_boq"))
		boq = out.get("boq_definition") or {}
		self.assertEqual(boq.get("arithmetic_correction_stage"), "Evaluation")
		self.assertIn("Evaluation Model", ((out.get("warnings") or {}).get("boq_warning") or ""))
		self.assertIn("Evaluation/Award", ((out.get("warnings") or {}).get("contract_price_warning") or ""))
		components = out.get("works_components") or []
		self.assertTrue(any(c.get("component_code") == "STD-WRC-PH10-1" for c in components))
		eval_templates = out.get("evaluation_rule_templates") or []
		self.assertTrue(any(r.get("mapping_code") == "STD-EVAL-PH10-1" for r in eval_templates))
		carry_forward = out.get("contract_carry_forward_templates") or []
		self.assertTrue(any(r.get("mapping_code") == "STD-CARRY-PH10-1" for r in carry_forward))
		self.assertTrue(out.get("readiness_rules"))

	def test_whitelist_rejects_guest(self):
		try:
			frappe.set_user("Guest")
			self.assertRaises(frappe.PermissionError, get_std_template_version_works_configuration, self.version_code)
		finally:
			frappe.set_user("Administrator")

	def test_whitelist_returns_for_admin(self):
		out = get_std_template_version_works_configuration(self.version_code)
		self.assertTrue(out.get("ok"))
		self.assertIn("works_profile", out)
