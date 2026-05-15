# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0900 — Publication whitelist API (pack §17).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_pub_api_0900
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.tender_publication.api.handlers import (
	PUB_API_NOT_FOUND,
	PUB_API_PAYLOAD_INVALID,
	PUB_API_TENDER_AMBIGUOUS,
	PUB_API_TENDER_CODE_REQUIRED,
	pub_api_export_evidence_package,
	pub_api_get_latest_publication_readiness,
	pub_api_reject_publication,
	pub_api_run_publication_readiness,
	pub_api_validate_evidence_package,
)
from kentender_procurement.tender_management.tender_publication.authorization.publication_authorization import (
	TITLE_PUBLICATION_READINESS_PERMISSION_DENIED,
)


class TestPubApi0900(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _ensure_role(self, role: str) -> None:
		if not frappe.db.exists("Role", role):
			doc = frappe.new_doc("Role")
			doc.role_name = role
			doc.insert(ignore_permissions=True)

	def _cleanup_user(self, email: str) -> None:
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)

	def _minimal_tender(self, *, ref: str) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = f"PUB-0900 {ref}"
		doc.tender_reference = ref
		doc.insert(ignore_permissions=True)
		return doc.name

	def _cleanup_tender(self, tender_name: str) -> None:
		if frappe.db.exists("Procurement Tender", tender_name):
			frappe.delete_doc("Procurement Tender", tender_name, force=True, ignore_permissions=True)

	def test_pub_0900_tender_not_found_envelope(self) -> None:
		r = pub_api_run_publication_readiness("NO-SUCH-TENDER-REF-999")
		self.assertFalse(r["success"])
		self.assertEqual(r["error_code"], PUB_API_NOT_FOUND)

	def test_pub_0900_tender_code_required(self) -> None:
		r = pub_api_run_publication_readiness("")
		self.assertFalse(r["success"])
		self.assertEqual(r["error_code"], PUB_API_TENDER_CODE_REQUIRED)

	def test_pub_0900_resolve_by_tender_reference(self) -> None:
		ref = f"PUB0900-REF-{frappe.generate_hash(length=6)}"
		tn = self._minimal_tender(ref=ref)
		try:
			r = pub_api_run_publication_readiness(ref)
			self.assertTrue(r["success"])
			self.assertEqual(r["readiness"]["tender_code"], tn)
			self.assertIn("status", r["readiness"])
		finally:
			self._cleanup_tender(tn)

	def test_pub_0900_ambiguous_tender_reference(self) -> None:
		ref = f"PUB0900-DUP-{frappe.generate_hash(length=6)}"
		t1 = self._minimal_tender(ref=ref)
		t2 = self._minimal_tender(ref=ref)
		try:
			r = pub_api_run_publication_readiness(ref)
			self.assertFalse(r["success"])
			self.assertEqual(r["error_code"], PUB_API_TENDER_AMBIGUOUS)
		finally:
			self._cleanup_tender(t1)
			self._cleanup_tender(t2)

	def test_pub_0900_readiness_permission_denied_envelope(self) -> None:
		email = "pub0900_desk@example.com"
		self._ensure_role("Desk User")
		ref = f"PUB0900-DESK-{frappe.generate_hash(length=6)}"
		tn = self._minimal_tender(ref=ref)
		try:
			if not frappe.db.exists("User", email):
				u = frappe.new_doc("User")
				u.email = email
				u.first_name = "Desk"
				u.user_type = "System User"
				u.enabled = 1
				u.new_password = "Test@1234"
				u.send_welcome_email = 0
				u.insert(ignore_permissions=True)
			frappe.get_doc("User", email).add_roles("Desk User")
			frappe.set_user(email)
			r = pub_api_run_publication_readiness(tn)
			self.assertFalse(r["success"])
			self.assertEqual(r["error_code"], TITLE_PUBLICATION_READINESS_PERMISSION_DENIED)
		finally:
			frappe.set_user("Administrator")
			self._cleanup_tender(tn)
			self._cleanup_user(email)

	def test_pub_0900_validate_evidence_success_wraps_service_payload(self) -> None:
		ref = f"PUB0900-EV-{frappe.generate_hash(length=6)}"
		tn = self._minimal_tender(ref=ref)
		try:
			r = pub_api_validate_evidence_package(tn)
			self.assertTrue(r["success"])
			self.assertIn("validation", r)
			self.assertIn("ok", r["validation"])
			self.assertFalse(r["validation"]["ok"])
		finally:
			self._cleanup_tender(tn)

	def test_pub_0900_get_latest_readiness_after_run(self) -> None:
		ref = f"PUB0900-LAT-{frappe.generate_hash(length=6)}"
		tn = self._minimal_tender(ref=ref)
		try:
			pub_api_run_publication_readiness(tn)
			r = pub_api_get_latest_publication_readiness(tn)
			self.assertTrue(r["success"])
			self.assertEqual(r["readiness"]["tender_code"], tn)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0900_reject_invalid_json_payload(self) -> None:
		ref = f"PUB0900-RJ-{frappe.generate_hash(length=6)}"
		tn = self._minimal_tender(ref=ref)
		try:
			r = pub_api_reject_publication(tn, decision_payload="{not json")
			self.assertFalse(r["success"])
			self.assertEqual(r["error_code"], PUB_API_PAYLOAD_INVALID)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0900_export_requires_format(self) -> None:
		ref = f"PUB0900-EX-{frappe.generate_hash(length=6)}"
		tn = self._minimal_tender(ref=ref)
		try:
			r = pub_api_export_evidence_package(tn, export_format="")
			self.assertFalse(r["success"])
			self.assertEqual(r["error_code"], PUB_API_PAYLOAD_INVALID)
		finally:
			self._cleanup_tender(tn)
