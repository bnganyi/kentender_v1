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
		("STD Parameter Dependency", "dependency_code", "STD-DEP-SECURITY"),
		("STD Parameter Definition", "parameter_code", "STD-PARAM-TDS-SECURITY"),
		("STD Parameter Definition", "parameter_code", "STD-PARAM-TDS-SECURITY-TYPE"),
		("STD Section Definition", "section_code", "STD-SEC-TDS"),
		("STD Part Definition", "part_code", "STD-PART-1"),
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
			"part_code": "STD-PART-1",
			"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
			"part_number": "I",
			"part_title": "Bidding Procedures",
			"order_index": 1,
		}
	).insert()
	frappe.get_doc(
		{
			"doctype": "STD Section Definition",
			"section_code": "STD-SEC-TDS",
			"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
			"part_code": "STD-PART-1",
			"section_number": "II",
			"section_title": "Tender Data Sheet",
			"section_classification": "Core",
			"editability": "Parameter Only",
			"order_index": 2,
			"source_document_code": "DOC1_WORKS_BUILDING_REV_APR_2022",
		}
	).insert()


class TestSTDParameters(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		_seed_base()

	def tearDown(self):
		frappe.set_user("Administrator")
		try:
			for doctype, field, value in (
				("STD Parameter Dependency", "dependency_code", "STD-DEP-SECURITY"),
				("STD Parameter Definition", "parameter_code", "STD-PARAM-TDS-SECURITY"),
				("STD Parameter Definition", "parameter_code", "STD-PARAM-TDS-SECURITY-TYPE"),
				("STD Section Definition", "section_code", "STD-SEC-TDS"),
				("STD Part Definition", "part_code", "STD-PART-1"),
				("STD Template Version", "version_code", "STDTV-WORKS-BUILDING-REV-APR-2022"),
				("STD Template Family", "template_code", "STD-WORKS"),
				("Source Document Registry", "source_document_code", "DOC1_WORKS_BUILDING_REV_APR_2022"),
			):
				_delete_if_exists(doctype, field, value)
			frappe.db.commit()
		finally:
			super().tearDown()

	def test_parameter_create_success(self):
		doc = frappe.get_doc(
			{
				"doctype": "STD Parameter Definition",
				"parameter_code": "STD-PARAM-TDS-SECURITY",
				"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
				"section_code": "STD-SEC-TDS",
				"label": "Tender Security Required",
				"parameter_group": "Tender Security",
				"data_type": "Boolean",
			}
		).insert()
		self.assertEqual(doc.parameter_code, "STD-PARAM-TDS-SECURITY")

	def test_parameter_code_unique(self):
		self.test_parameter_create_success()
		with self.assertRaises((frappe.DuplicateEntryError, ValidationError)):
			self.test_parameter_create_success()

	def test_dependency_invalid_references_fail(self):
		with self.assertRaises(ValidationError):
			frappe.get_doc(
				{
					"doctype": "STD Parameter Dependency",
					"dependency_code": "STD-DEP-SECURITY",
					"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
					"trigger_parameter_code": "UNKNOWN",
					"trigger_operator": "=",
					"trigger_value": "{\"value\": true}",
					"dependent_parameter_code": "STD-PARAM-TDS-SECURITY",
					"effect": "Required",
					"condition_expression": "trigger=true",
				}
			).insert()

	def test_dependency_create_success(self):
		frappe.get_doc(
			{
				"doctype": "STD Parameter Definition",
				"parameter_code": "STD-PARAM-TDS-SECURITY",
				"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
				"section_code": "STD-SEC-TDS",
				"label": "Tender Security Required",
				"parameter_group": "Tender Security",
				"data_type": "Boolean",
				"required": 1,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Parameter Definition",
				"parameter_code": "STD-PARAM-TDS-SECURITY-TYPE",
				"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
				"section_code": "STD-SEC-TDS",
				"label": "Tender Security Type",
				"parameter_group": "Tender Security",
				"data_type": "Select",
			}
		).insert()
		dep = frappe.get_doc(
			{
				"doctype": "STD Parameter Dependency",
				"dependency_code": "STD-DEP-SECURITY",
				"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
				"trigger_parameter_code": "STD-PARAM-TDS-SECURITY",
				"trigger_operator": "=",
				"trigger_value": "{\"value\": true}",
				"dependent_parameter_code": "STD-PARAM-TDS-SECURITY-TYPE",
				"effect": "Required",
				"condition_expression": "trigger=true",
			}
		).insert()
		self.assertEqual(dep.effect, "Required")

