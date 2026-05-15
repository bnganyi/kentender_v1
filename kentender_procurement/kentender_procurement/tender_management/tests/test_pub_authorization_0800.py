# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0800 — ``PublicationAuthorizationService``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_pub_authorization_0800
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.tender_publication.authorization.publication_authorization import (
	PublicationAuthorizationService,
	TITLE_APPROVAL_DECISION_PERMISSION_DENIED,
	TITLE_PUBLICATION_READINESS_PERMISSION_DENIED,
	TITLE_PUBLISH_PERMISSION_DENIED,
	TITLE_SUBMIT_FOR_APPROVAL_PERMISSION_DENIED,
)


def _last_msg_title() -> str | None:
	log = frappe.get_message_log()
	return (log[-1].get("title") or "").strip() if log else None


class TestPubAuthorization0800(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _ensure_role(self, role: str) -> None:
		if not frappe.db.exists("Role", role):
			doc = frappe.new_doc("Role")
			doc.role_name = role
			doc.insert(ignore_permissions=True)

	def _ensure_user(self, email: str, roles: list[str]) -> None:
		for r in roles:
			self._ensure_role(r)
		if not frappe.db.exists("User", email):
			u = frappe.new_doc("User")
			u.email = email
			u.first_name = "PUB0800"
			u.user_type = "System User"
			u.enabled = 1
			u.new_password = "Test@1234"
			u.send_welcome_email = 0
			u.insert(ignore_permissions=True)
		frappe.get_doc("User", email).add_roles(*roles)

	def _cleanup_user(self, email: str) -> None:
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)

	def test_pub_0800_officer_may_submit_not_approve(self) -> None:
		email = "pub0800_officer@example.com"
		self._ensure_user(email, ["Procurement Officer"])
		try:
			self.assertTrue(PublicationAuthorizationService.actorMaySubmitForApproval(email))
			self.assertFalse(PublicationAuthorizationService.actorMayApproveOrReturn(email))
			frappe.set_user(email)
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				PublicationAuthorizationService.assertCanApproveForPublication(email)
			self.assertEqual(_last_msg_title(), TITLE_APPROVAL_DECISION_PERMISSION_DENIED)
		finally:
			self._cleanup_user(email)

	def test_pub_0800_purchase_manager_may_approve_not_submit(self) -> None:
		email = "pub0800_pm@example.com"
		self._ensure_user(email, ["Purchase Manager"])
		try:
			self.assertTrue(PublicationAuthorizationService.actorMayApproveOrReturn(email))
			self.assertFalse(PublicationAuthorizationService.actorMaySubmitForApproval(email))
			frappe.set_user(email)
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				PublicationAuthorizationService.assertCanSubmitForApproval(email)
			self.assertEqual(_last_msg_title(), TITLE_SUBMIT_FOR_APPROVAL_PERMISSION_DENIED)
		finally:
			self._cleanup_user(email)

	def test_pub_0800_officer_may_publish_auditor_may_export_not_publish(self) -> None:
		officer = "pub0800_po_pub@example.com"
		auditor = "pub0800_aud@example.com"
		self._ensure_user(officer, ["Procurement Officer"])
		self._ensure_user(auditor, ["Auditor"])
		try:
			self.assertTrue(PublicationAuthorizationService.actorMayPublishTender(officer))
			self.assertTrue(PublicationAuthorizationService.actorMayExportPublicationEvidence(auditor))
			self.assertFalse(PublicationAuthorizationService.actorMayPublishTender(auditor))
			frappe.set_user(auditor)
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				PublicationAuthorizationService.assertCanPublishTender(auditor)
			self.assertEqual(_last_msg_title(), TITLE_PUBLISH_PERMISSION_DENIED)
		finally:
			self._cleanup_user(officer)
			self._cleanup_user(auditor)

	def test_pub_0800_assistant_denied_publication_readiness(self) -> None:
		email = "pub0800_asst@example.com"
		self._ensure_user(email, ["Procurement Assistant"])
		try:
			self.assertFalse(PublicationAuthorizationService.actorMayRunPublicationReadiness(email))
			frappe.set_user(email)
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				PublicationAuthorizationService.assertCanRunPublicationReadiness(email)
			self.assertEqual(_last_msg_title(), TITLE_PUBLICATION_READINESS_PERMISSION_DENIED)
		finally:
			self._cleanup_user(email)

	def test_pub_0800_denial_emits_audit_for_non_admin(self) -> None:
		email = "pub0800_audit@example.com"
		self._ensure_user(email, ["Desk User"])
		try:
			before = frappe.db.count(
				"Audit Event",
				{
					"event_type": "TENDER_PUBLICATION_AUTHORIZATION_DENIED",
					"document_name": email,
				},
			)
			frappe.set_user(email)
			with self.assertRaises(frappe.ValidationError):
				PublicationAuthorizationService.assertCanPublishTender(email)
			after = frappe.db.count(
				"Audit Event",
				{
					"event_type": "TENDER_PUBLICATION_AUTHORIZATION_DENIED",
					"document_name": email,
				},
			)
			self.assertGreater(after, before)
		finally:
			self._cleanup_user(email)
