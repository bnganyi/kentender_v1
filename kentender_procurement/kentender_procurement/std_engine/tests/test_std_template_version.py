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
		"procurement_category": "Works",
		"legal_use_status": "Approved for Use",
		"status": "Active",
	}


def _minimal_template_family(template_code: str) -> dict[str, object]:
	return {
		"doctype": "STD Template Family",
		"template_code": template_code,
		"template_title": "PPRA Works STD Template Family",
		"issuing_authority": "PPRA",
		"procurement_category": "Works",
		"allowed_procurement_methods": "[\"Open Tender\", \"Restricted Tender\"]",
		"family_status": "Active",
		"is_active_family": 1,
	}


def _minimal_template_version(version_code: str) -> dict[str, object]:
	return {
		"doctype": "STD Template Version",
		"version_code": version_code,
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


def _cleanup_template_version(version_code: str) -> None:
	name = frappe.db.get_value("STD Template Version", {"version_code": version_code}, "name")
	if name:
		frappe.delete_doc("STD Template Version", name, force=True, ignore_permissions=True)


def _cleanup_template_family(template_code: str) -> None:
	name = frappe.db.get_value("STD Template Family", {"template_code": template_code}, "name")
	if name:
		frappe.delete_doc("STD Template Family", name, force=True, ignore_permissions=True)


def _cleanup_source_doc(source_document_code: str) -> None:
	name = frappe.db.get_value(
		"Source Document Registry", {"source_document_code": source_document_code}, "name"
	)
	if name:
		frappe.delete_doc("Source Document Registry", name, force=True, ignore_permissions=True)


class TestSTDTemplateVersion(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		for code in ("STDTV-WORKS-BUILDING-REV-APR-2022", "STDTV-WORKS-BUILDING-REV-APR-2022-2"):
			_cleanup_template_version(code)
		_cleanup_template_family("STD-WORKS")
		_cleanup_source_doc("DOC1_WORKS_BUILDING_REV_APR_2022")
		frappe.get_doc(_minimal_source_doc("DOC1_WORKS_BUILDING_REV_APR_2022")).insert()
		frappe.get_doc(_minimal_template_family("STD-WORKS")).insert()

	def tearDown(self):
		frappe.set_user("Administrator")
		try:
			for code in ("STDTV-WORKS-BUILDING-REV-APR-2022", "STDTV-WORKS-BUILDING-REV-APR-2022-2"):
				_cleanup_template_version(code)
			_cleanup_template_family("STD-WORKS")
			_cleanup_source_doc("DOC1_WORKS_BUILDING_REV_APR_2022")
			frappe.db.commit()
		finally:
			super().tearDown()

	def test_create_template_version_success(self):
		doc = frappe.get_doc(_minimal_template_version("STDTV-WORKS-BUILDING-REV-APR-2022")).insert()
		self.assertEqual(doc.version_code, "STDTV-WORKS-BUILDING-REV-APR-2022")
		self.assertEqual(doc.version_status, "Active")
		self.assertEqual(doc.immutable_after_activation, 1)

	def test_version_code_unique(self):
		frappe.get_doc(_minimal_template_version("STDTV-WORKS-BUILDING-REV-APR-2022")).insert()
		with self.assertRaises((frappe.DuplicateEntryError, ValidationError)):
			frappe.get_doc(_minimal_template_version("STDTV-WORKS-BUILDING-REV-APR-2022")).insert()

	def test_current_active_requires_active_status(self):
		payload = _minimal_template_version("STDTV-WORKS-BUILDING-REV-APR-2022")
		payload["version_status"] = "Draft"
		with self.assertRaises(ValidationError):
			frappe.get_doc(payload).insert()

	def test_active_immutable_version_blocks_direct_edit(self):
		doc = frappe.get_doc(_minimal_template_version("STDTV-WORKS-BUILDING-REV-APR-2022")).insert()
		doc.version_label = "Changed Label"
		with self.assertRaises(ValidationError):
			doc.save()

	def test_delete_blocked_when_referenced_by_std_instance(self):
		doc = frappe.get_doc(_minimal_template_version("STDTV-WORKS-BUILDING-REV-APR-2022")).insert()
		with patch(
			"kentender_procurement.procurement_planning.doctype.std_template_version.std_template_version."
			"STDTemplateVersion._is_referenced_by_std_instance",
			return_value=True,
		):
			with self.assertRaises(ValidationError):
				frappe.delete_doc("STD Template Version", doc.name, ignore_permissions=True)

	def test_supersession_fields_accept_lineage_links(self):
		base = frappe.get_doc(_minimal_template_version("STDTV-WORKS-BUILDING-REV-APR-2022")).insert()
		next_payload = _minimal_template_version("STDTV-WORKS-BUILDING-REV-APR-2022-2")
		next_payload["is_current_active_version"] = 0
		next_payload["version_status"] = "Approved"
		next_payload["supersedes_version_code"] = base.version_code
		next_doc = frappe.get_doc(next_payload).insert()
		self.assertEqual(next_doc.supersedes_version_code, base.version_code)

