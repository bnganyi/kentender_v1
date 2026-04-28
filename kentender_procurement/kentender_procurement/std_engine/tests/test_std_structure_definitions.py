# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase


def _minimal_source_doc(code: str) -> dict[str, object]:
	return {
		"doctype": "Source Document Registry",
		"source_document_code": code,
		"source_document_title": "STD Works Source",
		"issuing_authority": "PPRA",
		"source_revision_label": "Rev April 2022",
		"procurement_category": "Works",
		"legal_use_status": "Approved for Use",
		"status": "Active",
	}


def _minimal_template_family(code: str) -> dict[str, object]:
	return {
		"doctype": "STD Template Family",
		"template_code": code,
		"template_title": "STD Works Family",
		"issuing_authority": "PPRA",
		"procurement_category": "Works",
		"allowed_procurement_methods": "[\"Open Tender\", \"Restricted Tender\"]",
		"family_status": "Active",
		"is_active_family": 1,
	}


def _minimal_template_version(code: str) -> dict[str, object]:
	return {
		"doctype": "STD Template Version",
		"version_code": code,
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


def _minimal_part(code: str) -> dict[str, object]:
	return {
		"doctype": "STD Part Definition",
		"part_code": code,
		"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
		"part_number": "I",
		"part_title": "Bidding Procedures",
		"order_index": 1,
	}


def _minimal_section(code: str) -> dict[str, object]:
	return {
		"doctype": "STD Section Definition",
		"section_code": code,
		"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
		"part_code": "STD-PART-1",
		"section_number": "I",
		"section_title": "Instructions to Tenderers",
		"section_classification": "Core",
		"editability": "Locked",
		"order_index": 1,
		"source_document_code": "DOC1_WORKS_BUILDING_REV_APR_2022",
	}


def _minimal_clause(code: str) -> dict[str, object]:
	return {
		"doctype": "STD Clause Definition",
		"clause_code": code,
		"section_code": "STD-SEC-ITT",
		"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
		"clause_number": "1.1",
		"clause_title": "Scope of Tender",
		"editability": "Locked",
		"order_index": 1,
		"source_document_code": "DOC1_WORKS_BUILDING_REV_APR_2022",
		"source_page_start": 12,
		"source_page_end": 12,
	}


def _delete_if_exists(doctype: str, field: str, value: str):
	name = frappe.db.get_value(doctype, {field: value}, "name")
	if name:
		frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)


class TestSTDStructureDefinitions(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		for doctype, field, val in (
			("STD Clause Definition", "clause_code", "STD-CL-1"),
			("STD Section Definition", "section_code", "STD-SEC-ITT"),
			("STD Part Definition", "part_code", "STD-PART-1"),
			("STD Template Version", "version_code", "STDTV-WORKS-BUILDING-REV-APR-2022"),
			("STD Template Family", "template_code", "STD-WORKS"),
			("Source Document Registry", "source_document_code", "DOC1_WORKS_BUILDING_REV_APR_2022"),
		):
			_delete_if_exists(doctype, field, val)
		frappe.get_doc(_minimal_source_doc("DOC1_WORKS_BUILDING_REV_APR_2022")).insert()
		frappe.get_doc(_minimal_template_family("STD-WORKS")).insert()
		frappe.get_doc(_minimal_template_version("STDTV-WORKS-BUILDING-REV-APR-2022")).insert()

	def tearDown(self):
		frappe.set_user("Administrator")
		try:
			for doctype, field, val in (
				("STD Clause Definition", "clause_code", "STD-CL-1"),
				("STD Section Definition", "section_code", "STD-SEC-ITT"),
				("STD Part Definition", "part_code", "STD-PART-1"),
				("STD Template Version", "version_code", "STDTV-WORKS-BUILDING-REV-APR-2022"),
				("STD Template Family", "template_code", "STD-WORKS"),
				("Source Document Registry", "source_document_code", "DOC1_WORKS_BUILDING_REV_APR_2022"),
			):
				_delete_if_exists(doctype, field, val)
			frappe.db.commit()
		finally:
			super().tearDown()

	def test_hierarchy_creation_success(self):
		part = frappe.get_doc(_minimal_part("STD-PART-1")).insert()
		section = frappe.get_doc(_minimal_section("STD-SEC-ITT")).insert()
		clause = frappe.get_doc(_minimal_clause("STD-CL-1")).insert()
		self.assertEqual(part.part_code, "STD-PART-1")
		self.assertEqual(section.editability, "Locked")
		self.assertEqual(clause.clause_code, "STD-CL-1")

	def test_invalid_parent_link_fails(self):
		frappe.get_doc(_minimal_part("STD-PART-1")).insert()
		payload = _minimal_section("STD-SEC-ITT")
		payload["part_code"] = "UNKNOWN-PART"
		with self.assertRaises(ValidationError):
			frappe.get_doc(payload).insert()

	def test_locked_clause_cannot_be_marked_instance_editable(self):
		frappe.get_doc(_minimal_part("STD-PART-1")).insert()
		frappe.get_doc(_minimal_section("STD-SEC-ITT")).insert()
		payload = _minimal_clause("STD-CL-1")
		payload["instance_edit_allowed"] = 1
		with self.assertRaises(ValidationError):
			frappe.get_doc(payload).insert()

	def test_clause_source_trace_required(self):
		frappe.get_doc(_minimal_part("STD-PART-1")).insert()
		frappe.get_doc(_minimal_section("STD-SEC-ITT")).insert()
		payload = _minimal_clause("STD-CL-1")
		payload["source_page_start"] = None
		payload["source_page_end"] = None
		payload["source_text_hash"] = None
		with self.assertRaises(ValidationError):
			frappe.get_doc(payload).insert()

