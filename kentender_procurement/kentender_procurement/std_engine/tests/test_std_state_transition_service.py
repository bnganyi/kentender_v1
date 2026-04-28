from __future__ import annotations

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.services.state_transition_service import transition_std_object


def _delete_if_exists(doctype: str, field: str, value: str):
	name = frappe.db.get_value(doctype, {field: value}, "name")
	if name:
		if doctype == "STD Audit Event":
			frappe.db.delete(doctype, {"name": name})
		else:
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)


class TestSTDStateTransitionService(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		for dt, field, value in (
			("STD Audit Event", "object_code", "STD-WORKS-TXN"),
			("STD Instance", "instance_code", "STDINST-TXN-1"),
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-TXN"),
			("STD Template Version", "version_code", "STDTV-WORKS-TXN"),
			("STD Template Family", "template_code", "STD-WORKS-TXN"),
			("Source Document Registry", "source_document_code", "DOC1_WORKS_TNX"),
		):
			_delete_if_exists(dt, field, value)

		frappe.get_doc(
			{
				"doctype": "Source Document Registry",
				"source_document_code": "DOC1_WORKS_TNX",
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
				"template_code": "STD-WORKS-TXN",
				"template_title": "Transition Test Family",
				"issuing_authority": "PPRA",
				"procurement_category": "Works",
				"allowed_procurement_methods": "[\"Open Tender\"]",
				"family_status": "Draft",
				"is_active_family": 0,
			}
		).insert()

		frappe.get_doc(
			{
				"doctype": "STD Template Version",
				"version_code": "STDTV-WORKS-TXN",
				"template_code": "STD-WORKS-TXN",
				"version_label": "Txn Version",
				"revision_label": "Rev",
				"source_document_code": "DOC1_WORKS_TNX",
				"issuing_authority": "PPRA",
				"procurement_category": "Works",
				"version_status": "Approved",
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
				"profile_code": "WORKS-PROFILE-TXN",
				"version_code": "STDTV-WORKS-TXN",
				"profile_title": "Transition Profile",
				"procurement_category": "Works",
				"allowed_methods": "[\"Open Tender\"]",
				"profile_status": "Approved",
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
				"instance_code": "STDINST-TXN-1",
				"tender_code": "TND-TXN-1",
				"template_version_code": "STDTV-WORKS-TXN",
				"profile_code": "WORKS-PROFILE-TXN",
				"instance_status": "Ready",
				"readiness_status": "Ready",
			}
		).insert()

	def tearDown(self):
		frappe.set_user("Administrator")
		for dt, field, value in (
			("STD Audit Event", "object_code", "STD-WORKS-TXN"),
			("STD Instance", "instance_code", "STDINST-TXN-1"),
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-TXN"),
			("STD Template Version", "version_code", "STDTV-WORKS-TXN"),
			("STD Template Family", "template_code", "STD-WORKS-TXN"),
			("Source Document Registry", "source_document_code", "DOC1_WORKS_TNX"),
		):
			_delete_if_exists(dt, field, value)
		frappe.db.commit()
		super().tearDown()

	def test_invalid_transition_denied_with_stable_code(self):
		resp = transition_std_object(
			object_type="TEMPLATE_FAMILY",
			object_code="STD-WORKS-TXN",
			action_code="STD_FAMILY_ACTIVATE",
			actor="Administrator",
		)
		self.assertFalse(resp["allowed"])
		self.assertEqual("STD_TRANSITION_INVALID_STATE", resp["denial_code"])

	def test_separation_of_duties_denial_code(self):
		resp1 = transition_std_object(
			object_type="TEMPLATE_FAMILY",
			object_code="STD-WORKS-TXN",
			action_code="STD_FAMILY_SUBMIT_REVIEW",
			actor="Administrator",
		)
		self.assertTrue(resp1["allowed"])
		resp2 = transition_std_object(
			object_type="TEMPLATE_FAMILY",
			object_code="STD-WORKS-TXN",
			action_code="STD_FAMILY_APPROVE",
			actor="Administrator",
		)
		self.assertFalse(resp2["allowed"])
		self.assertEqual("STD_SOD_SAME_ACTOR", resp2["denial_code"])

	def test_success_transition_emits_audit_and_returns_next_actions(self):
		resp = transition_std_object(
			object_type="STD_INSTANCE",
			object_code="STDINST-TXN-1",
			action_code="STD_INSTANCE_PUBLISH_LOCK",
			actor="Administrator",
			reason="publish test",
		)
		self.assertTrue(resp["allowed"])
		self.assertEqual("Published Locked", resp["new_state"])
		self.assertIsInstance(resp["allowed_next_actions"], list)
		self.assertTrue(
			frappe.db.exists(
				"STD Audit Event",
				{"event_type": "STD_TRANSITION_SUCCESS", "object_code": "STDINST-TXN-1"},
			)
		)

	def test_direct_status_mutation_blocked(self):
		doc = frappe.get_doc("STD Template Family", {"template_code": "STD-WORKS-TXN"})
		doc.family_status = "Approved"
		with self.assertRaises(ValidationError):
			doc.save(ignore_permissions=True)

