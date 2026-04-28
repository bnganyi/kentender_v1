# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase


def _delete_if_exists(doctype: str, field: str, value: str):
	name = frappe.db.get_value(doctype, {field: value}, "name")
	if name:
		frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)


def _seed_base():
	for doctype, field, value in (
		("STD Form Field Definition", "field_code", "STD-FORM-FIELD-1"),
		("STD Form Definition", "form_code", "STD-FORM-1"),
		("STD Section Definition", "section_code", "STD-SEC-FORMS"),
		("STD Part Definition", "part_code", "STD-PART-2"),
		("STD Template Version", "version_code", "STDTV-WORKS-BUILDING-REV-APR-2022"),
		("STD Template Family", "template_code", "STD-WORKS"),
		("Source Document Registry", "source_document_code", "DOC1_WORKS_BUILDING_REV_APR_2022"),
	):
		_delete_if_exists(doctype, field, value)

	frappe.get_doc(
		{
			"doctype": "Source Document Registry",
			"source_document_code": "DOC1_WORKS_BUILDING_REV_APR_2022",
			"source_document_title": "STD Works Source",
			"issuing_authority": "PPRA",
			"source_revision_label": "Rev April 2022",
			"procurement_category": "Works",
			"legal_use_status": "Approved for Use",
			"status": "Active",
		}
	).insert()
	frappe.get_doc(
		{
			"doctype": "STD Template Family",
			"template_code": "STD-WORKS",
			"template_title": "STD Works Family",
			"issuing_authority": "PPRA",
			"procurement_category": "Works",
			"allowed_procurement_methods": "[\"Open Tender\"]",
			"family_status": "Active",
			"is_active_family": 1,
		}
	).insert()
	frappe.get_doc(
		{
			"doctype": "STD Template Version",
			"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
			"template_code": "STD-WORKS",
			"version_label": "Works Building Rev Apr 2022",
			"revision_label": "Rev April 2022",
			"source_document_code": "DOC1_WORKS_BUILDING_REV_APR_2022",
			"issuing_authority": "PPRA",
			"procurement_category": "Works",
			"version_status": "Active",
			"legal_review_status": "Approved",
			"policy_review_status": "Approved",
			"structure_validation_status": "Pass",
			"is_current_active_version": 1,
		}
	).insert()
	frappe.get_doc(
		{
			"doctype": "STD Part Definition",
			"part_code": "STD-PART-2",
			"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
			"part_number": "II",
			"part_title": "Employer's Requirements",
			"order_index": 2,
		}
	).insert()
	frappe.get_doc(
		{
			"doctype": "STD Section Definition",
			"section_code": "STD-SEC-FORMS",
			"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
			"part_code": "STD-PART-2",
			"section_number": "IV",
			"section_title": "Tendering Forms",
			"section_classification": "Core",
			"editability": "Structured Editable",
			"order_index": 4,
			"source_document_code": "DOC1_WORKS_BUILDING_REV_APR_2022",
		}
	).insert()


class TestSTDForms(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		_seed_base()

	def tearDown(self):
		frappe.set_user("Administrator")
		try:
			for doctype, field, value in (
				("STD Form Field Definition", "field_code", "STD-FORM-FIELD-1"),
				("STD Form Definition", "form_code", "STD-FORM-1"),
				("STD Section Definition", "section_code", "STD-SEC-FORMS"),
				("STD Part Definition", "part_code", "STD-PART-2"),
				("STD Template Version", "version_code", "STDTV-WORKS-BUILDING-REV-APR-2022"),
				("STD Template Family", "template_code", "STD-WORKS"),
				("Source Document Registry", "source_document_code", "DOC1_WORKS_BUILDING_REV_APR_2022"),
			):
				_delete_if_exists(doctype, field, value)
			frappe.db.commit()
		finally:
			super().tearDown()

	def test_form_create_success(self):
		doc = frappe.get_doc(
			{
				"doctype": "STD Form Definition",
				"form_code": "STD-FORM-1",
				"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
				"section_code": "STD-SEC-FORMS",
				"title": "Form of Tender",
				"form_type": "Tendering Form",
				"completed_by": "Tenderer",
				"source_document_code": "DOC1_WORKS_BUILDING_REV_APR_2022",
				"is_required": 1,
				"supplier_submission_requirement": 1,
				"drives_dsm": 1,
			}
		).insert()
		self.assertEqual(doc.form_code, "STD-FORM-1")

	def test_form_code_unique(self):
		self.test_form_create_success()
		with self.assertRaises((frappe.DuplicateEntryError, ValidationError)):
			self.test_form_create_success()

	def test_field_requires_valid_form(self):
		with self.assertRaises(ValidationError):
			frappe.get_doc(
				{
					"doctype": "STD Form Field Definition",
					"field_code": "STD-FORM-FIELD-1",
					"form_code": "UNKNOWN-FORM",
					"field_label": "Tender Number",
					"field_key": "tender_number",
					"data_type": "String",
					"order_index": 1,
				}
			).insert()

	def test_form_field_create_success(self):
		self.test_form_create_success()
		field = frappe.get_doc(
			{
				"doctype": "STD Form Field Definition",
				"field_code": "STD-FORM-FIELD-1",
				"form_code": "STD-FORM-1",
				"field_label": "Tender Number",
				"field_key": "tender_number",
				"data_type": "String",
				"order_index": 1,
				"supplier_editable": 1,
				"required": 1,
			}
		).insert()
		self.assertEqual(field.form_code, "STD-FORM-1")

