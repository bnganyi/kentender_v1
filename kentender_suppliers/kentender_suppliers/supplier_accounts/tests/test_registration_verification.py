# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §4.1, §5.1–5.2, §7.2, §10.4, §11.3 — registering a
supplier organisation and verifying its email (BDS01-IMP-004/005,
BDS03-IMP-009; BDS01-AC-004/005, BDS03-AC-009)."""

from __future__ import annotations

from unittest import mock

import frappe

from kentender_suppliers.supplier_accounts.services import registration, verification
from kentender_suppliers.supplier_accounts.services.errors import AccountError
from kentender_suppliers.supplier_accounts.tests.support import AFYA, DAVID, MARY, PDF, PETER, STAFF, AccountsCase, key


class TestRegistration(AccountsCase):
	def test_registration_creates_a_pending_account_with_the_signatory_and_one_link(self):
		result = self.register()
		self.assertEqual((result["ok"], result["account_status"], result["verification_sent_to"]), (True, "Pending verification", "tenders@afyadigital.example"))
		org = frappe.get_doc("Supplier Organisation", result["organisation"])
		self.assertEqual((org.legal_name, org.registration_number, org.tax_identifier, org.registered_by, str(org.status_since)), (AFYA["legal_name"], AFYA["registration_number"], "P051234567X", MARY, "2027-05-18 09:00:00"))
		self.assertEqual([(c.channel, c.value, c.verification_status) for c in org.contacts], [("Email", "tenders@afyadigital.example", "Unverified"), ("Phone", "+254 709 555 014", "Unverified")])
		assignment = frappe.get_all("Supplier User Assignment", filters={"organisation": org.name}, fields=["user", "responsibility", "job_title", "authority_evidence", "assigned_by"])
		self.assertEqual([(a.user, a.responsibility, a.job_title, a.assigned_by) for a in assignment], [(MARY, "Authorised Signatory", "Managing Director", MARY)])
		evidence = frappe.get_doc("Supplier Account Evidence", assignment[0].authority_evidence)
		self.assertEqual((evidence.evidence_type, evidence.status, evidence.file_name, len(evidence.file_digest)), ("Signatory authority", "Available", "mary-wanjiku-signing-authority.pdf", 64))
		self.assertTrue(frappe.db.get_value("File", evidence.file, "is_private"))
		self.assertEqual([m["to"] for m in self.sent], ["tenders@afyadigital.example"])
		self.assertIn("/account/verify?token=", self.sent[0]["link"])
		# the stored challenge keeps only a hash of the link token
		self.assertFalse(frappe.db.exists("Supplier Account Verification", {"token_hash": self.token()}))
		self.assertTrue(frappe.db.exists("Supplier Account Verification", {"token_hash": verification.token_hash(self.token()), "status": "Sent"}))

	def test_repeating_your_own_registration_returns_it_and_another_person_is_told_to_ask(self):
		first = self.register()
		again = self.register()
		self.assertEqual((again["organisation"], again["idempotent"]), (first["organisation"], True))
		other = self.register(user=PETER)
		self.assertEqual((other["ok"], other["errors"]), (False, {"registration_number": "This organisation already has a supplier account. Ask its Authorised Signatory to add you."}))
		self.assertEqual(frappe.db.count("Supplier Organisation", {"registration_number": AFYA["registration_number"]}), 1)

	def test_each_invalid_fact_is_named_and_nothing_is_saved(self):
		result = self.register(legal_name="Af", tax_identifier="0512", official_email="not-an-email", official_phone="call us", job_title="", authority_content=b"")
		self.assertFalse(result["ok"])
		self.assertEqual(set(result["errors"]), {"legal_name", "tax_identifier", "official_email", "official_phone", "job_title", "authority_evidence"})
		self.assertEqual(result["errors"]["tax_identifier"], "Enter a KRA PIN such as P051234567X.")
		self.assertEqual(frappe.db.count("Supplier Organisation", {"fixture_namespace": "BDS_ACC_TEST"}), 0)
		self.assertEqual(self.sent, [])

	def test_a_rejected_authority_file_creates_nothing(self):
		result = self.register(authority_filename="authority.pdf", authority_content=b"MZ\x90\x00 not a pdf")
		self.assertEqual((result["ok"], result["code"], result["errors"]), (False, "BDS_EVIDENCE_REJECTED", {"authority_evidence": "Upload a PDF, PNG or JPEG file."}))
		with mock.patch("kentender_core.services.file_integrity.scanner_result", return_value="Infected — test signature"):
			infected = self.register()
		self.assertEqual(infected["errors"], {"authority_evidence": "The file did not pass the malware check."})
		# a truncated PDF is refused by name, never a server error (found in the browser, 27 Sep 2026)
		broken = self.register(authority_filename="authority.pdf", authority_content=b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF\n")
		self.assertEqual(broken["errors"], {"authority_evidence": "The file could not be read. Upload a complete PDF, PNG or JPEG file."})
		self.assertEqual(frappe.db.count("Supplier Organisation", {"fixture_namespace": "BDS_ACC_TEST"}), 0)
		self.assertEqual(frappe.db.count("Supplier Account Evidence", {"fixture_namespace": "BDS_ACC_TEST"}), 0)

	def test_guests_and_internal_users_cannot_register(self):
		with self.assertRaises(AccountError) as ctx:
			self.register(user="Guest")
		self.assertEqual(ctx.exception.code, "BDS_SIGN_IN_REQUIRED")
		with self.assertRaises(AccountError) as ctx:
			self.register(user=STAFF)
		self.assertEqual(ctx.exception.code, "BDS_RESPONSIBILITY_REQUIRED")

	def test_the_same_key_with_different_facts_is_refused(self):
		k = key()
		registration.register_supplier_organisation(**AFYA, authority_filename="a.pdf", authority_content=PDF, idempotency_key=k, user=MARY)
		with self.assertRaises(AccountError) as ctx:
			registration.register_supplier_organisation(**{**AFYA, "legal_name": "Another name Limited"}, authority_filename="a.pdf", authority_content=PDF, idempotency_key=k, user=MARY)
		self.assertEqual(ctx.exception.code, "BDS_IDEMPOTENCY_CONFLICT")


class TestVerification(AccountsCase):
	def test_the_link_activates_the_account_and_proves_the_channel_only(self):
		org = self.register()["organisation"]
		self.at("2027-05-18 09:05:00")
		result = verification.verify_account_communication(token=self.token(), user=MARY)
		self.assertEqual((result["ok"], result["account_status"]), (True, "Active"))
		doc = frappe.get_doc("Supplier Organisation", org)
		self.assertEqual((doc.contacts[0].verification_status, str(doc.contacts[0].verified_at), doc.contacts[0].verified_by), ("Verified", "2027-05-18 09:05:00", MARY))
		self.assertEqual(doc.contacts[1].verification_status, "Unverified")  # the phone is not the configured channel
		self.assertEqual(str(doc.status_since), "2027-05-18 09:05:00")
		again = verification.verify_account_communication(token=self.token(), user=MARY)
		self.assertEqual((again["ok"], again["already_verified"]), (True, True))

	def test_an_expired_superseded_or_foreign_link_does_not_activate(self):
		org = self.register()["organisation"]
		first = self.token()
		self.at("2027-05-18 09:10:00")
		verification.send_account_verification(organisation=org, idempotency_key=key(), user=MARY)
		self.assertEqual(verification.verify_account_communication(token=first, user=MARY)["reason"], "superseded")
		self.assertEqual(verification.verify_account_communication(token=self.token(), user=PETER)["reason"], "invalid")  # not his organisation: no disclosure
		self.assertEqual(verification.verify_account_communication(token="made-up", user=MARY)["reason"], "invalid")
		self.at("2027-05-19 09:10:00")  # 24 hours later
		self.assertEqual(verification.verify_account_communication(token=self.token(), user=MARY)["reason"], "expired")
		self.assertEqual(frappe.db.get_value("Supplier Organisation", org, "account_status"), "Pending verification")

	def test_resending_is_limited_to_three_links_an_hour_without_saying_more(self):
		org = self.register()["organisation"]  # link 1
		for minute in ("09:10", "09:20"):
			self.at(f"2027-05-18 {minute}:00")
			self.assertTrue(verification.send_account_verification(organisation=org, idempotency_key=key(), user=MARY)["sent"])
		self.at("2027-05-18 09:30:00")
		limited = verification.send_account_verification(organisation=org, idempotency_key=key(), user=MARY)
		self.assertEqual((limited["ok"], limited["sent"], limited["limited"], limited["message"]), (True, False, True, "A verification link was sent recently. Check your inbox, or try again later."))
		self.assertEqual(len(self.sent), 3)
		self.at("2027-05-18 10:00:01")
		self.assertTrue(verification.send_account_verification(organisation=org, idempotency_key=key(), user=MARY)["sent"])

	def test_only_the_organisations_people_can_resend_and_an_active_account_needs_none(self):
		org = self.register()["organisation"]
		with self.assertRaises(frappe.DoesNotExistError):
			verification.send_account_verification(organisation=org, idempotency_key=key(), user=DAVID)
		verification.verify_account_communication(token=self.token(), user=MARY)
		result = verification.send_account_verification(organisation=org, idempotency_key=key(), user=MARY)
		self.assertEqual((result["sent"], result["already_verified"]), (False, True))
