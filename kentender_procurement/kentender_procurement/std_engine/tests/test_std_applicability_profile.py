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


def _minimal_profile(code: str) -> dict[str, object]:
	return {
		"doctype": "STD Applicability Profile",
		"profile_code": code,
		"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
		"profile_title": "Works Building/Civil",
		"procurement_category": "Works",
		"works_profile_type": "Building and Associated Civil Engineering Works",
		"allowed_methods": "[\"Open Tender\"]",
		"requires_boq": 0,
		"requires_drawings": 0,
		"requires_specifications": 0,
		"requires_site_information": 0,
		"requires_hse_requirements": 0,
		"requires_environmental_social_requirements": 0,
		"supports_lots": 0,
		"supports_alternative_tenders": 0,
		"supports_margin_of_preference": 0,
		"supports_reservations": 0,
		"profile_status": "Active",
	}


def _delete_if_exists(doctype: str, field: str, value: str):
	name = frappe.db.get_value(doctype, {field: value}, "name")
	if name:
		frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)


class TestSTDApplicabilityProfile(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		_delete_if_exists("STD Applicability Profile", "profile_code", "WORKS-PROFILE-BUILDING-CIVIL")
		_delete_if_exists("STD Applicability Profile", "profile_code", "WORKS-PROFILE-BUILDING-CIVIL-2")
		_delete_if_exists("STD Template Version", "version_code", "STDTV-WORKS-BUILDING-REV-APR-2022")
		_delete_if_exists("STD Template Family", "template_code", "STD-WORKS")
		_delete_if_exists("Source Document Registry", "source_document_code", "DOC1_WORKS_BUILDING_REV_APR_2022")

		frappe.get_doc(_minimal_source_doc("DOC1_WORKS_BUILDING_REV_APR_2022")).insert()
		frappe.get_doc(_minimal_template_family("STD-WORKS")).insert()
		frappe.get_doc(_minimal_template_version("STDTV-WORKS-BUILDING-REV-APR-2022")).insert()

	def tearDown(self):
		frappe.set_user("Administrator")
		try:
			_delete_if_exists("STD Applicability Profile", "profile_code", "WORKS-PROFILE-BUILDING-CIVIL")
			_delete_if_exists("STD Applicability Profile", "profile_code", "WORKS-PROFILE-BUILDING-CIVIL-2")
			_delete_if_exists("STD Template Version", "version_code", "STDTV-WORKS-BUILDING-REV-APR-2022")
			_delete_if_exists("STD Template Family", "template_code", "STD-WORKS")
			_delete_if_exists("Source Document Registry", "source_document_code", "DOC1_WORKS_BUILDING_REV_APR_2022")
			frappe.db.commit()
		finally:
			super().tearDown()

	def test_create_profile_success(self):
		doc = frappe.get_doc(_minimal_profile("WORKS-PROFILE-BUILDING-CIVIL")).insert()
		self.assertEqual(doc.profile_code, "WORKS-PROFILE-BUILDING-CIVIL")
		self.assertEqual(doc.procurement_category, "Works")

	def test_profile_code_unique(self):
		frappe.get_doc(_minimal_profile("WORKS-PROFILE-BUILDING-CIVIL")).insert()
		with self.assertRaises((frappe.DuplicateEntryError, ValidationError)):
			frappe.get_doc(_minimal_profile("WORKS-PROFILE-BUILDING-CIVIL")).insert()

	def test_incompatible_category_rejected(self):
		payload = _minimal_profile("WORKS-PROFILE-BUILDING-CIVIL")
		payload["procurement_category"] = "Goods"
		with self.assertRaises(ValidationError):
			frappe.get_doc(payload).insert()

	def test_active_profile_direct_edit_rejected(self):
		doc = frappe.get_doc(_minimal_profile("WORKS-PROFILE-BUILDING-CIVIL")).insert()
		doc.profile_title = "Changed"
		with self.assertRaises(ValidationError):
			doc.save()

