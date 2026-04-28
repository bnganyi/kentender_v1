from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.services.template_query_service import get_eligible_std_templates


def _delete_if_exists(doctype: str, field: str, value: str):
	name = frappe.db.get_value(doctype, {field: value}, "name")
	if name:
		frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)


class TestSTDTemplateQueryService(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		for dt, field, value in (
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-QRY-ACTIVE"),
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-QRY-SUSP"),
			("STD Template Version", "version_code", "STDTV-WORKS-QRY-ACTIVE"),
			("STD Template Version", "version_code", "STDTV-WORKS-QRY-SUSP"),
			("STD Template Family", "template_code", "STD-WORKS-QRY"),
			("Source Document Registry", "source_document_code", "DOC1_WORKS_QRY"),
		):
			_delete_if_exists(dt, field, value)

		frappe.get_doc(
			{
				"doctype": "Source Document Registry",
				"source_document_code": "DOC1_WORKS_QRY",
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
				"template_code": "STD-WORKS-QRY",
				"template_title": "Query Family",
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
				"version_code": "STDTV-WORKS-QRY-ACTIVE",
				"template_code": "STD-WORKS-QRY",
				"version_label": "Active Version",
				"revision_label": "Rev",
				"source_document_code": "DOC1_WORKS_QRY",
				"issuing_authority": "PPRA",
				"procurement_category": "Works",
				"works_profile_type": "Building Civil",
				"version_status": "Active",
				"legal_review_status": "Approved",
				"policy_review_status": "Approved",
				"structure_validation_status": "Pass",
				"is_current_active_version": 1,
				"immutable_after_activation": 1,
			}
		).insert()

		frappe.get_doc(
			{
				"doctype": "STD Template Version",
				"version_code": "STDTV-WORKS-QRY-SUSP",
				"template_code": "STD-WORKS-QRY",
				"version_label": "Suspended Version",
				"revision_label": "Rev",
				"source_document_code": "DOC1_WORKS_QRY",
				"issuing_authority": "PPRA",
				"procurement_category": "Works",
				"works_profile_type": "Building Civil",
				"version_status": "Suspended",
				"legal_review_status": "Approved",
				"policy_review_status": "Approved",
				"structure_validation_status": "Pass",
				"is_current_active_version": 0,
				"immutable_after_activation": 1,
			}
		).insert()

		frappe.get_doc(
			{
				"doctype": "STD Applicability Profile",
				"profile_code": "WORKS-PROFILE-QRY-ACTIVE",
				"version_code": "STDTV-WORKS-QRY-ACTIVE",
				"profile_title": "Works Profile Active",
				"procurement_category": "Works",
				"works_profile_type": "Building Civil",
				"allowed_methods": "[\"Open Tender\"]",
				"allowed_contract_types": "[\"Lump Sum\"]",
				"profile_status": "Active",
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
			}
		).insert()

		frappe.get_doc(
			{
				"doctype": "STD Applicability Profile",
				"profile_code": "WORKS-PROFILE-QRY-SUSP",
				"version_code": "STDTV-WORKS-QRY-SUSP",
				"profile_title": "Works Profile Suspended",
				"procurement_category": "Works",
				"works_profile_type": "Building Civil",
				"allowed_methods": "[\"Open Tender\"]",
				"profile_status": "Suspended",
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
			}
		).insert()

	def tearDown(self):
		frappe.set_user("Administrator")
		for dt, field, value in (
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-QRY-SUSP"),
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-QRY-ACTIVE"),
			("STD Template Version", "version_code", "STDTV-WORKS-QRY-SUSP"),
			("STD Template Version", "version_code", "STDTV-WORKS-QRY-ACTIVE"),
			("STD Template Family", "template_code", "STD-WORKS-QRY"),
			("Source Document Registry", "source_document_code", "DOC1_WORKS_QRY"),
		):
			_delete_if_exists(dt, field, value)
		frappe.db.commit()
		super().tearDown()

	def test_works_query_returns_active_compatible_template_and_profile(self):
		resp = get_eligible_std_templates(
			procurement_category="Works",
			procurement_method="Open Tender",
			works_profile_type="Building Civil",
		)
		self.assertFalse(resp["blocking_reason"])
		self.assertEqual(1, len(resp["eligible_templates"]))
		row = resp["eligible_templates"][0]
		self.assertEqual("STDTV-WORKS-QRY-ACTIVE", row["template_version_code"])
		self.assertEqual("WORKS-PROFILE-QRY-ACTIVE", row["profile_code"])

	def test_non_works_query_does_not_return_works_profile(self):
		resp = get_eligible_std_templates(
			procurement_category="Goods",
			procurement_method="Open Tender",
		)
		self.assertEqual([], resp["eligible_templates"])
		self.assertTrue(resp["blocking_reason"])

	def test_suspended_version_or_profile_not_returned(self):
		resp = get_eligible_std_templates(
			procurement_category="Works",
			procurement_method="Open Tender",
			works_profile_type="Building Civil",
		)
		profile_codes = {row["profile_code"] for row in resp["eligible_templates"]}
		version_codes = {row["template_version_code"] for row in resp["eligible_templates"]}
		self.assertNotIn("WORKS-PROFILE-QRY-SUSP", profile_codes)
		self.assertNotIn("STDTV-WORKS-QRY-SUSP", version_codes)

