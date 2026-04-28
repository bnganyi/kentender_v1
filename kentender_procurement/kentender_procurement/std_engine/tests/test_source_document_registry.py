# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase


def _minimal_source_doc(source_document_code: str) -> dict[str, object]:
	return {
		"doctype": "Source Document Registry",
		"source_document_code": source_document_code,
		"source_document_title": "STD for Works Building and Associated Civil Engineering Works",
		"issuing_authority": "PPRA",
		"country": "UG",
		"source_revision_label": "Rev April 2022",
		"issued_date_text": "April 2022",
		"procurement_category": "Works",
		"works_profile_type": "Building and Associated Civil Engineering Works",
		"legal_use_status": "Approved for Use",
		"status": "Active",
	}


def _cleanup_source_doc(source_document_code: str) -> None:
	name = frappe.db.get_value(
		"Source Document Registry", {"source_document_code": source_document_code}, "name"
	)
	if name:
		frappe.delete_doc("Source Document Registry", name, force=True, ignore_permissions=True)


class TestSourceDocumentRegistry(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		_cleanup_source_doc("DOC1_WORKS_BUILDING_REV_APR_2022")
		_cleanup_source_doc("DOC1_WORKS_BUILDING_REV_APR_2022_DUP")

	def tearDown(self):
		frappe.set_user("Administrator")
		try:
			_cleanup_source_doc("DOC1_WORKS_BUILDING_REV_APR_2022")
			_cleanup_source_doc("DOC1_WORKS_BUILDING_REV_APR_2022_DUP")
			frappe.db.commit()
		finally:
			super().tearDown()

	def test_create_source_document_registry(self):
		doc = frappe.get_doc(_minimal_source_doc("DOC1_WORKS_BUILDING_REV_APR_2022")).insert()
		self.assertEqual(doc.source_document_code, "DOC1_WORKS_BUILDING_REV_APR_2022")
		self.assertEqual(doc.procurement_category, "Works")
		self.assertEqual(doc.status, "Active")

	def test_source_document_code_must_be_unique(self):
		frappe.get_doc(_minimal_source_doc("DOC1_WORKS_BUILDING_REV_APR_2022")).insert()
		with self.assertRaises((frappe.DuplicateEntryError, ValidationError)):
			frappe.get_doc(_minimal_source_doc("DOC1_WORKS_BUILDING_REV_APR_2022")).insert()

	def test_delete_blocked_when_referenced_by_template_version(self):
		doc = frappe.get_doc(_minimal_source_doc("DOC1_WORKS_BUILDING_REV_APR_2022_DUP")).insert()
		with patch(
			"kentender_procurement.procurement_planning.doctype.source_document_registry.source_document_registry."
			"SourceDocumentRegistry._is_referenced_by_template_version",
			return_value=True,
		):
			with self.assertRaises(ValidationError):
				frappe.delete_doc("Source Document Registry", doc.name, ignore_permissions=True)

