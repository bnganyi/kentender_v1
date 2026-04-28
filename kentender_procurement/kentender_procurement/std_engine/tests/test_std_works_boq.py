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
		("STD BOQ Item Schema Definition", "schema_field_code", "STD-BOQ-SCHEMA-1"),
		("STD BOQ Bill Definition", "bill_code", "STD-BOQ-BILL-1"),
		("STD BOQ Definition", "boq_definition_code", "STD-BOQ-DEF-1"),
		("STD Works Requirement Component Definition", "component_code", "STD-WRC-1"),
		("STD Section Definition", "section_code", "STD-SEC-WORKS"),
		("STD Part Definition", "part_code", "STD-PART-3"),
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
			"part_code": "STD-PART-3",
			"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
			"part_number": "III",
			"part_title": "Technical Requirements",
			"order_index": 3,
		}
	).insert()
	frappe.get_doc(
		{
			"doctype": "STD Section Definition",
			"section_code": "STD-SEC-WORKS",
			"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
			"part_code": "STD-PART-3",
			"section_number": "V",
			"section_title": "Bills of Quantities",
			"section_classification": "Core",
			"editability": "Structured Editable",
			"order_index": 5,
			"source_document_code": "DOC1_WORKS_BUILDING_REV_APR_2022",
		}
	).insert()


class TestSTDWorksBOQ(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		_seed_base()

	def tearDown(self):
		frappe.set_user("Administrator")
		try:
			for doctype, field, value in (
				("STD BOQ Item Schema Definition", "schema_field_code", "STD-BOQ-SCHEMA-1"),
				("STD BOQ Bill Definition", "bill_code", "STD-BOQ-BILL-1"),
				("STD BOQ Definition", "boq_definition_code", "STD-BOQ-DEF-1"),
				("STD Works Requirement Component Definition", "component_code", "STD-WRC-1"),
				("STD Section Definition", "section_code", "STD-SEC-WORKS"),
				("STD Part Definition", "part_code", "STD-PART-3"),
				("STD Template Version", "version_code", "STDTV-WORKS-BUILDING-REV-APR-2022"),
				("STD Template Family", "template_code", "STD-WORKS"),
				("Source Document Registry", "source_document_code", "DOC1_WORKS_BUILDING_REV_APR_2022"),
			):
				_delete_if_exists(doctype, field, value)
			frappe.db.commit()
		finally:
			super().tearDown()

	def test_works_requirement_component_create(self):
		doc = frappe.get_doc(
			{
				"doctype": "STD Works Requirement Component Definition",
				"component_code": "STD-WRC-1",
				"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
				"section_code": "STD-SEC-WORKS",
				"component_title": "Specifications",
				"component_type": "Specifications",
				"supports_attachments": 1,
				"attachment_required": 1,
			}
		).insert()
		self.assertEqual(doc.component_code, "STD-WRC-1")

	def test_boq_definition_and_children_create(self):
		boq = frappe.get_doc(
			{
				"doctype": "STD BOQ Definition",
				"boq_definition_code": "STD-BOQ-DEF-1",
				"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
				"section_code": "STD-SEC-WORKS",
				"pricing_model": "Item Rate",
				"quantity_owner": "Procuring Entity",
				"supplier_input_mode": "Rate Only",
				"amount_computation_rule": "qty * rate",
				"total_computation_rule": "sum(amount)",
				"arithmetic_correction_stage": "Evaluation",
			}
		).insert()
		bill = frappe.get_doc(
			{
				"doctype": "STD BOQ Bill Definition",
				"bill_code": "STD-BOQ-BILL-1",
				"boq_definition_code": boq.boq_definition_code,
				"bill_number": "Bill 1",
				"bill_title": "Preliminaries",
				"bill_type": "General",
				"supplier_input_mode": "Rate Only",
				"order_index": 1,
			}
		).insert()
		schema = frappe.get_doc(
			{
				"doctype": "STD BOQ Item Schema Definition",
				"schema_field_code": "STD-BOQ-SCHEMA-1",
				"boq_definition_code": boq.boq_definition_code,
				"field_key": "quantity",
				"label": "Quantity",
				"item_owner": "Procuring Entity",
				"supplier_editable": 0,
				"required": 1,
			}
		).insert()
		self.assertEqual(bill.bill_code, "STD-BOQ-BILL-1")
		self.assertEqual(schema.supplier_editable, 0)

	def test_boq_quantity_owner_enforced(self):
		with self.assertRaises(ValidationError):
			frappe.get_doc(
				{
					"doctype": "STD BOQ Definition",
					"boq_definition_code": "STD-BOQ-DEF-1",
					"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
					"section_code": "STD-SEC-WORKS",
					"pricing_model": "Item Rate",
					"quantity_owner": "Tenderer",
					"supplier_input_mode": "Rate Only",
					"amount_computation_rule": "qty * rate",
					"total_computation_rule": "sum(amount)",
					"arithmetic_correction_stage": "Evaluation",
				}
			).insert()

