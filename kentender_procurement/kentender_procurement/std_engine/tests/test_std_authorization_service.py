from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.services.authorization_service import check_std_permission


def _delete_if_exists(doctype: str, field: str, value: str):
	name = frappe.db.get_value(doctype, {field: value}, "name")
	if name:
		if doctype == "STD Audit Event":
			frappe.db.delete(doctype, {"name": name})
		else:
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)


class TestSTDAuthorizationService(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		for dt, field, value in (
			("STD Instance", "instance_code", "STDINST-AUTH-1"),
			("STD Generated Output", "output_code", "STDOUT-AUTH-1"),
			("STD Audit Event", "audit_event_code", "STDAUD-AUTH-1"),
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-AUTH"),
			("STD Template Version", "version_code", "STDTV-WORKS-AUTH"),
			("STD Template Family", "template_code", "STD-WORKS-AUTH"),
			("Source Document Registry", "source_document_code", "DOC1_WORKS_AUTH"),
		):
			_delete_if_exists(dt, field, value)

		frappe.get_doc(
			{
				"doctype": "Source Document Registry",
				"source_document_code": "DOC1_WORKS_AUTH",
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
				"template_code": "STD-WORKS-AUTH",
				"template_title": "Auth Family",
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
				"version_code": "STDTV-WORKS-AUTH",
				"template_code": "STD-WORKS-AUTH",
				"version_label": "Auth Version",
				"revision_label": "Rev",
				"source_document_code": "DOC1_WORKS_AUTH",
				"issuing_authority": "PPRA",
				"procurement_category": "Works",
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
				"doctype": "STD Applicability Profile",
				"profile_code": "WORKS-PROFILE-AUTH",
				"version_code": "STDTV-WORKS-AUTH",
				"profile_title": "Auth Profile",
				"procurement_category": "Works",
				"allowed_methods": "[\"Open Tender\"]",
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
				"doctype": "STD Instance",
				"instance_code": "STDINST-AUTH-1",
				"tender_code": "TND-AUTH",
				"template_version_code": "STDTV-WORKS-AUTH",
				"profile_code": "WORKS-PROFILE-AUTH",
				"instance_status": "Published Locked",
				"readiness_status": "Ready",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Generated Output",
				"output_code": "STDOUT-AUTH-1",
				"instance_code": "STDINST-AUTH-1",
				"output_type": "Bundle",
				"version_number": 1,
				"status": "Published",
				"source_template_version_code": "STDTV-WORKS-AUTH",
				"source_profile_code": "WORKS-PROFILE-AUTH",
				"generated_by_job_code": "JOB-AUTH-1",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Audit Event",
				"audit_event_code": "STDAUD-AUTH-1",
				"event_type": "TEST",
				"object_type": "STD_INSTANCE",
				"object_code": "STDINST-AUTH-1",
				"timestamp": frappe.utils.now_datetime(),
			}
		).insert()

	def tearDown(self):
		frappe.set_user("Administrator")
		for dt, field, value in (
			("STD Generated Output", "output_code", "STDOUT-AUTH-1"),
			("STD Audit Event", "audit_event_code", "STDAUD-AUTH-1"),
			("STD Instance", "instance_code", "STDINST-AUTH-1"),
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-AUTH"),
			("STD Template Version", "version_code", "STDTV-WORKS-AUTH"),
			("STD Template Family", "template_code", "STD-WORKS-AUTH"),
			("Source Document Registry", "source_document_code", "DOC1_WORKS_AUTH"),
		):
			_delete_if_exists(dt, field, value)
		frappe.db.commit()
		super().tearDown()

	def test_active_template_immutability_denied(self):
		resp = check_std_permission(
			actor="Administrator",
			action_code="STD_VERSION_EDIT_CONTENT",
			object_type="TEMPLATE_VERSION",
			object_code="STDTV-WORKS-AUTH",
		)
		self.assertFalse(resp["allowed"])
		self.assertEqual("STD_AUTH_ACTIVE_IMMUTABLE", resp["denial_code"])

	def test_published_instance_immutability_denied(self):
		resp = check_std_permission(
			actor="Administrator",
			action_code="STD_INSTANCE_EDIT_CONTENT",
			object_type="STD_INSTANCE",
			object_code="STDINST-AUTH-1",
		)
		self.assertFalse(resp["allowed"])
		self.assertEqual("STD_AUTH_INSTANCE_IMMUTABLE", resp["denial_code"])

	def test_output_immutability_denied(self):
		resp = check_std_permission(
			actor="Administrator",
			action_code="STD_OUTPUT_EDIT_CONTENT",
			object_type="GENERATED_OUTPUT",
			object_code="STDOUT-AUTH-1",
		)
		self.assertFalse(resp["allowed"])
		self.assertEqual("STD_AUTH_OUTPUT_IMMUTABLE", resp["denial_code"])

	def test_audit_immutability_denied(self):
		resp = check_std_permission(
			actor="Administrator",
			action_code="STD_AUDIT_EDIT",
			object_type="AUDIT_EVENT",
			object_code="STDAUD-AUTH-1",
		)
		self.assertFalse(resp["allowed"])
		self.assertEqual("STD_AUTH_AUDIT_IMMUTABLE", resp["denial_code"])

	def test_template_profile_active_and_generation_requirements(self):
		resp = check_std_permission(
			actor="Administrator",
			action_code="STD_INSTANCE_CREATE_FROM_TEMPLATE",
			object_type="STD_INSTANCE",
			context={"template_version_code": "STDTV-WORKS-AUTH", "profile_code": "WORKS-PROFILE-AUTH"},
		)
		self.assertTrue(resp["allowed"])

		resp2 = check_std_permission(
			actor="Administrator",
			action_code="STD_INSTANCE_PUBLISH_LOCK",
			object_type="STD_INSTANCE",
			object_code="STDINST-AUTH-1",
			context={"requires_addendum": True, "addendum_completed": False},
		)
		self.assertFalse(resp2["allowed"])
		self.assertEqual("STD_AUTH_ADDENDUM_REQUIRED", resp2["denial_code"])

		resp3 = check_std_permission(
			actor="Administrator",
			action_code="STD_INSTANCE_PUBLISH_LOCK",
			object_type="STD_INSTANCE",
			object_code="STDINST-AUTH-1",
			context={"requires_generated_models": True, "generated_models_ready": False},
		)
		self.assertFalse(resp3["allowed"])
		self.assertEqual("STD_AUTH_MODEL_GENERATION_REQUIRED", resp3["denial_code"])

