from __future__ import annotations

import frappe

from kentender_procurement.std_engine.api.template_version_workbench import (
	get_std_template_version_forms_catalogue,
)
from kentender_procurement.std_engine.services.template_version_forms_service import (
	build_std_template_version_forms_catalogue,
)
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR1010TemplateVersionFormsCatalogue(_Phase7Fixture):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		for doctype, field, value in (
			("STD Form Definition", "form_code", "STD-FORM-PH10-CT-1"),
			("STD Form Definition", "form_code", "STD-FORM-PH10-IV-2"),
			("STD Form Definition", "form_code", "STD-FORM-PH10-IV-1"),
			("STD Section Definition", "section_code", "STD-SEC-PH10-X"),
			("STD Section Definition", "section_code", "STD-SEC-PH10-IV"),
		):
			name = frappe.db.get_value(doctype, {field: value}, "name")
			if name:
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		super().tearDown()

	def _insert_forms_fixture(self):
		for section_code, section_number, section_title, idx in (
			("STD-SEC-PH10-IV", "IV", "Forms", 40),
			("STD-SEC-PH10-X", "X", "Contract Forms", 90),
		):
			if not frappe.db.exists("STD Section Definition", {"section_code": section_code}):
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

		for payload in (
			{
				"doctype": "STD Form Definition",
				"form_code": "STD-FORM-PH10-IV-1",
				"version_code": self.version_code,
				"section_code": "STD-SEC-PH10-IV",
				"title": "Form of Tender",
				"form_type": "Tendering Form",
				"completed_by": "Tenderer",
				"is_required": 1,
				"supplier_submission_requirement": 1,
				"drives_dsm": 1,
				"drives_dem": 0,
				"drives_dcm": 0,
				"source_document_code": self.source_doc,
			},
			{
				"doctype": "STD Form Definition",
				"form_code": "STD-FORM-PH10-IV-2",
				"version_code": self.version_code,
				"section_code": "STD-SEC-PH10-IV",
				"title": "Tender Security Form",
				"form_type": "Security Form",
				"completed_by": "Bank",
				"is_required": 0,
				"supplier_submission_requirement": 1,
				"drives_dsm": 1,
				"drives_dem": 0,
				"drives_dcm": 0,
				"source_document_code": self.source_doc,
			},
			{
				"doctype": "STD Form Definition",
				"form_code": "STD-FORM-PH10-CT-1",
				"version_code": self.version_code,
				"section_code": "STD-SEC-PH10-X",
				"title": "Agreement Form",
				"form_type": "Contract Form",
				"completed_by": "Procuring Entity",
				"is_required": 1,
				"supplier_submission_requirement": 0,
				"contract_carry_forward": 1,
				"drives_dsm": 0,
				"drives_dem": 0,
				"drives_dcm": 1,
				"source_document_code": self.source_doc,
			},
		):
			frappe.get_doc(payload).insert()

	def test_catalogue_sections_and_impacts(self):
		self._insert_forms_fixture()
		out = build_std_template_version_forms_catalogue(self.version_code)
		self.assertTrue(out.get("ok"))
		self.assertTrue(out.get("read_only"))
		self.assertFalse(out.get("draft_editable"))
		self.assertEqual(out.get("version_code"), self.version_code)
		cats = out.get("categories") or []
		cat_ids = {c.get("id") for c in cats}
		self.assertIn("section_iv_forms", cat_ids)
		self.assertIn("contract_forms", cat_ids)
		forms = out.get("forms") or []
		self.assertEqual(len(forms), 3)
		row = next(x for x in forms if x.get("form_code") == "STD-FORM-PH10-IV-1")
		self.assertTrue((row.get("impact") or {}).get("drives_dsm"))
		self.assertTrue(row.get("supplier_submission_requirement"))
		preview = out.get("model_preview") or {}
		self.assertTrue(preview.get("read_only"))
		self.assertIn("STD-FORM-PH10-IV-1", preview.get("dsm_required_supplier_form_codes") or [])

	def test_draft_version_enables_field_builder(self):
		self._insert_forms_fixture()
		name = frappe.db.get_value("STD Template Version", {"version_code": self.version_code}, "name")
		frappe.db.set_value("STD Template Version", name, "version_status", "Draft")
		frappe.db.set_value("STD Template Version", name, "immutable_after_activation", 0)
		try:
			out = build_std_template_version_forms_catalogue(self.version_code)
			self.assertTrue(out.get("ok"))
			self.assertFalse(out.get("read_only"))
			self.assertTrue(out.get("draft_editable"))
		finally:
			frappe.db.set_value("STD Template Version", name, "version_status", "Active")
			frappe.db.set_value("STD Template Version", name, "immutable_after_activation", 1)

	def test_whitelist_rejects_guest(self):
		try:
			frappe.set_user("Guest")
			self.assertRaises(frappe.PermissionError, get_std_template_version_forms_catalogue, self.version_code)
		finally:
			frappe.set_user("Administrator")

	def test_whitelist_returns_for_admin(self):
		self._insert_forms_fixture()
		out = get_std_template_version_forms_catalogue(self.version_code)
		self.assertTrue(out.get("ok"))
		self.assertIn("categories", out)
