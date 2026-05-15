# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SEC-0600 — evidence export authorization controls."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.audit.event_catalog import (
	AuditEventCode,
)
from kentender_procurement.tender_management.security.evidence.export_authorization import (
	EvidenceExportAuthorizationService,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)


class TestSecEvidenceExportAuthorization0600(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")
		upsert_std_template()
		self._created_tenders: list[str] = []
		self._created_users: list[str] = []
		self._created_audits: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for name in self._created_audits:
			if frappe.db.exists("Audit Event", name):
				frappe.delete_doc("Audit Event", name, force=True, ignore_permissions=True)
		for tn in self._created_tenders:
			if frappe.db.exists("Procurement Tender", tn):
				frappe.delete_doc("Procurement Tender", tn, force=True, ignore_permissions=True)
		for user in self._created_users:
			if frappe.db.exists("User", user):
				frappe.delete_doc("User", user, force=True, ignore_permissions=True)

	def _new_user(self, email: str) -> str:
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		u = frappe.new_doc("User")
		u.email = email
		u.first_name = "SEC0600"
		u.user_type = "System User"
		u.enabled = 1
		u.new_password = "Test@1234"
		u.send_welcome_email = 0
		u.insert(ignore_permissions=True)
		self._created_users.append(u.name)
		return u.name

	def _new_tender(self, ref: str) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = f"SEC-0600 {ref}"
		doc.tender_reference = ref
		doc.insert(ignore_permissions=True)
		self._created_tenders.append(doc.name)
		return doc.name

	@staticmethod
	def _meta(value: object) -> dict:
		if isinstance(value, dict):
			return value
		if isinstance(value, str) and value.strip():
			try:
				out = json.loads(value)
			except Exception:
				return {}
			return out if isinstance(out, dict) else {}
		return {}

	def test_sec_0600_auditor_can_export(self) -> None:
		actor = self._new_user("sec0600_auditor@example.com")
		tender = self._new_tender("sec0600-auditor")
		EvidenceExportAuthorizationService.assert_can_export_evidence(
			actor,
			tender,
			context={"security_role_codes": ["ROLE_AUDITOR"]},
		)

	def test_sec_0600_unauthorized_user_denied(self) -> None:
		actor = self._new_user("sec0600_denied@example.com")
		tender = self._new_tender("sec0600-denied")
		with self.assertRaisesRegex(frappe.ValidationError, "not authorized"):
			EvidenceExportAuthorizationService.assert_can_export_evidence(
				actor,
				tender,
				context={"security_role_codes": ["ROLE_PROCUREMENT_ASSISTANT"]},
			)
		rows = frappe.get_all(
			"Audit Event",
			filters={"document_type": "Procurement Tender", "document_name": tender},
			fields=["name", "event_type", "metadata"],
			order_by="timestamp desc",
			limit=1,
		)
		self.assertTrue(rows)
		meta = self._meta(rows[0].get("metadata"))
		self.assertEqual(rows[0].get("event_type"), AuditEventCode.AUDIT_EXPORT_DENIED)
		self.assertEqual(meta.get("denial_code"), "AUDIT_EXPORT_DENIED")
		self.assertEqual(meta.get("action_code"), "EXPORT_EVIDENCE_PACKAGE")

	def test_sec_0600_procurement_officer_assignment_policy(self) -> None:
		actor = self._new_user("sec0600_proc@example.com")
		tender = self._new_tender("sec0600-proc")
		frappe.db.set_value("Procurement Tender", tender, "owner", actor)
		EvidenceExportAuthorizationService.assert_can_export_evidence(
			actor,
			tender,
			context={
				"security_role_codes": ["ROLE_PROCUREMENT_OFFICER"],
				"policy_allow_procurement_officer_export": True,
			},
		)

	def test_sec_0600_every_export_audited_with_format_and_hash(self) -> None:
		actor = self._new_user("sec0600_export@example.com")
		tender = self._new_tender("sec0600-export")
		name = EvidenceExportAuthorizationService.record_evidence_export(
			actor,
			tender,
			"JSON_MANIFEST",
			"hash-0600",
			context={"source": "unit-test"},
		)
		self._created_audits.append(name)
		self.assertTrue(frappe.db.exists("Audit Event", name))
		row = frappe.db.get_value("Audit Event", name, ["event_type", "metadata"], as_dict=True)
		self.assertEqual(row.get("event_type"), AuditEventCode.EVIDENCE_PACKAGE_EXPORTED)
		meta = self._meta(row.get("metadata"))
		self.assertEqual(meta.get("evidence_package_hash"), "hash-0600")
		self.assertEqual((meta.get("details") or {}).get("format"), "JSON_MANIFEST")
