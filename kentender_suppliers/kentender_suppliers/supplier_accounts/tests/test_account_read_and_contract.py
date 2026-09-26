# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §4.1, §5.12, §7.1, §10.5, §11.3 and plan D1/D12 — the
record rules, the Account read and its next step and journey, Account
evidence, the Account editor, and the published provider contract Bid
Submission uses (BDS01-IMP-006/011; BDS01-AC-004/005)."""

from __future__ import annotations

import json
from unittest import mock

import frappe

from kentender_core.services import supplier_account_contract as contract
from kentender_suppliers.supplier_accounts.services import access, evidence, organisation, provider, read
from kentender_suppliers.supplier_accounts.tests.support import AFYA, AMINA, DAVID, MARY, PDF, PETER, AccountsCase, key

ACCOUNT_KEYS = {"state", "organisations", "organisation", "viewer", "people", "evidence", "notice_contacts", "missing", "allowed_actions", "next_step", "journey"}
FORBIDDEN_WORDS = ("approved", "qualified", "prequalified", "verified supplier", "eligible")


def markers(account):
	return [s["marker"] for s in account["journey"]["stages"]]


class TestRecordRules(AccountsCase):
	def test_account_records_change_only_through_commands_and_are_kept(self):
		org = self.active_account()
		doc = frappe.get_doc("Supplier Organisation", org)
		doc.legal_name = "Renamed outside the command"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc("Supplier Organisation", org).delete(ignore_permissions=True)

	def test_suppliers_have_no_desk_permission_on_any_account_record(self):
		for doctype in ("Supplier Organisation", "Supplier User Assignment", "Supplier Account Evidence", "Supplier Account Verification", "Supplier Account Access Decision", "Supplier Account Command Journal"):
			roles = {p.role for p in frappe.get_meta(doctype).permissions}
			self.assertTrue(roles <= {"System Manager", "Supplier Account Support Officer"}, doctype)
			self.assertFalse([p for p in frappe.get_meta(doctype).permissions if p.write or p.create or p.delete], doctype)


class TestAccountRead(AccountsCase):
	def test_a_new_person_is_asked_for_the_organisation_details(self):
		account = read.get_supplier_account(user=PETER)
		self.assertEqual((account["state"], account["next_step"]["kind"], account["next_step"]["headline"]), ("no_account", "your_turn", "Enter the supplier organisation details."))
		self.assertEqual(markers(account), ["current", "not_started", "not_started"])

	def test_pending_verification_then_active(self):
		org = self.register()["organisation"]
		pending = read.get_supplier_account(user=MARY)
		self.assertEqual(set(pending), ACCOUNT_KEYS)
		self.assertEqual((pending["next_step"]["headline"], markers(pending), pending["next_step"]["primary_action"]), ("Verify your email to finish setting up the supplier account.", ["done", "current", "not_started"], "send_account_verification"))
		self.assertIn("send_account_verification", pending["allowed_actions"])
		self.assertEqual(pending["notice_contacts"], [])
		from kentender_suppliers.supplier_accounts.services import verification

		verification.verify_account_communication(token=self.token(), user=MARY)
		active = read.get_supplier_account(organisation=org, user=MARY)
		self.assertEqual((active["next_step"]["kind"], active["next_step"]["headline"], markers(active)), ("done", "The supplier account is ready.", ["done", "done", "done"]))
		self.assertEqual(active["notice_contacts"], [{"email": "tenders@afyadigital.example", "status": "Verified"}])
		self.assertEqual([(p["person"], p["responsibility"], p["effective_period"]) for p in active["people"]], [("Mary Wanjiku", "Authorised Signatory", "From 18 May 2027")])
		self.assertEqual(active["allowed_actions"], ["edit_organisation", "add_evidence", "add_person"])
		text = json.dumps(active).lower()
		for word in FORBIDDEN_WORDS:
			self.assertNotIn(word, text, word)

	def test_a_missing_official_phone_blocks_at_account_setup(self):
		org = self.active_account()
		frappe.db.set_value("Supplier Organisation", org, "official_phone", "", update_modified=False)  # the isolated legacy-record fixture
		account = read.get_supplier_account(user=MARY)
		self.assertEqual((account["next_step"]["kind"], account["next_step"]["headline"], markers(account)), ("your_turn_blocked", "Add the missing official phone before continuing.", ["blocked", "not_started", "not_started"]))
		self.assertEqual(account["missing"], [{"field": "official_phone", "text": "Enter the official phone number"}])
		self.assertEqual(account["next_step"]["fixes"][0]["label"], "Edit organisation")

	def test_suspended_waits_on_the_named_support_officer_with_no_self_activation(self):
		org = self.active_account()
		self.at("2027-05-19 08:00:00")
		access.suspend_supplier_account(organisation=org, reason="Reported misuse of the account.", expected_version=frappe.db.get_value("Supplier Organisation", org, "record_version"), idempotency_key=key(), user=AMINA)
		account = read.get_supplier_account(user=MARY)
		step = account["next_step"]
		self.assertEqual((step["kind"], step["headline"], step["holder"]["people"], step["since"]["display"]), ("waiting", "Supplier Account support officer Amina Yusuf is reviewing suspended access.", ["Amina Yusuf"], "19 May 2027, 08:00 EAT"))
		self.assertEqual((markers(account), step["fixes"], step["primary_action"]), (["done", "done", "blocked"], [], ""))


class TestEvidenceAndEditor(AccountsCase):
	def test_evidence_is_account_only_and_shows_expiry_and_scan_state(self):
		org = self.active_account()
		ok = evidence.upload_account_evidence(organisation=org, evidence_type="Reservation evidence", filename="agpo-youth.pdf", content=PDF, reference="AGPO-Y-2026-04172", valid_until="2027-06-30", title="Youth reservation evidence", idempotency_key=key(), user=MARY)
		self.assertEqual(ok["status"], "Available")
		with mock.patch("kentender_core.services.file_integrity.scanner_result", return_value="Not scanned — no scanner configured"):
			unscanned = evidence.upload_account_evidence(organisation=org, evidence_type="Tax compliance certificate", filename="tcc.pdf", content=PDF, reference="P051234567X", valid_until="2027-12-31", idempotency_key=key(), user=MARY)
		self.assertEqual(unscanned["status"], "Not scanned")
		bad = evidence.upload_account_evidence(organisation=org, evidence_type="Other", filename="notes.docx", content=b"PK\x03\x04", idempotency_key=key(), user=MARY)
		self.assertEqual((bad["code"], bad["errors"]), ("BDS_EVIDENCE_REJECTED", {"file": "Upload a PDF, PNG or JPEG file."}))
		self.at("2027-07-01 09:00:00")
		rows = {r["reference"]: r for r in read.get_supplier_account(user=MARY)["evidence"]}
		self.assertEqual((rows["AGPO-Y-2026-04172"]["label"], rows["AGPO-Y-2026-04172"]["valid_until"], rows["AGPO-Y-2026-04172"]["status"]), ("Youth reservation evidence", "30 Jun 2027", "Expired"))
		self.assertEqual(rows["P051234567X"]["status"], "Not scanned")
		download = evidence.get_account_evidence_file(organisation=org, evidence=ok["evidence"], user=MARY)
		self.assertEqual((download["file_name"], download["content"]), ("agpo-youth.pdf", PDF))
		with self.assertRaises(frappe.DoesNotExistError):
			evidence.get_account_evidence_file(organisation=org, evidence=ok["evidence"], user=PETER)

	def test_the_editor_checks_the_version_and_keeps_identity_after_activation(self):
		org = self.active_account()
		version = frappe.db.get_value("Supplier Organisation", org, "record_version")
		locked = organisation.update_supplier_organisation(organisation=org, values={"legal_name": "Afya Digital Supplies (Kenya) Limited", "registered_address": "Afya Plaza, Nairobi"}, expected_version=version, idempotency_key=key(), user=MARY)
		self.assertEqual(locked["errors"], {"legal_name": "Contact Supplier support to change the registered identity."})
		saved = organisation.update_supplier_organisation(organisation=org, values={"registered_address": "Afya Plaza, Nairobi", "official_email": "bids@afyadigital.example"}, expected_version=version, idempotency_key=key(), user=MARY)
		self.assertEqual((saved["record_version"], saved["verification_sent_to"]), (version + 1, "bids@afyadigital.example"))
		doc = frappe.get_doc("Supplier Organisation", org)
		self.assertEqual((doc.account_status, [(c.value, c.is_official, c.verification_status) for c in doc.contacts if c.channel == "Email"]), ("Active", [("tenders@afyadigital.example", 0, "Verified"), ("bids@afyadigital.example", 1, "Unverified")]))
		from kentender_suppliers.supplier_accounts.services.errors import AccountError

		with self.assertRaises(AccountError) as ctx:
			organisation.update_supplier_organisation(organisation=org, values={"registered_address": "Stale"}, expected_version=version, idempotency_key=key(), user=MARY)
		self.assertEqual(ctx.exception.code, "BDS_STALE_VERSION")


class TestProviderContract(AccountsCase):
	def test_the_registered_provider_meets_the_core_contract(self):
		self.assertIs(contract.provider(), provider)
		self.assertEqual(contract.missing_functions(provider), [])

	def test_the_provider_answers_identity_and_access_facts_only(self):
		org = self.active_account()
		from kentender_suppliers.supplier_accounts.services import assignments

		assignments.assign_supplier_representative(organisation=org, email=DAVID, full_name="David Ouma", idempotency_key=key(), user=MARY)
		mine = provider.active_assignments(user=MARY)
		self.assertEqual([(a["organisation_id"], a["responsibility"], a["signatory_ready"]) for a in mine], [(org, "Authorised Signatory", True)])
		self.assertEqual([(a["responsibility"], a["signatory_ready"]) for a in provider.active_assignments(user=DAVID)], [("Supplier Representative", False)])
		self.assertEqual(provider.active_assignments(user="Administrator"), [])
		self.assertEqual(provider.organisation(organisation_id=org)["account_status"], "Active")
		self.assertEqual([c["value"] for c in provider.verified_contacts(organisation_id=org)], ["tenders@afyadigital.example"])
		self.assertEqual(provider.find_active_account(country="Kenya", registration_number=AFYA["registration_number"]), {"organisation_id": org, "legal_name": "Afya Digital Supplies Limited"})
		self.assertIsNone(provider.find_active_account(country="Kenya", registration_number="PVT-NOPE"))
		proof = provider.account_evidence(organisation_id=org)[0]
		self.assertEqual(provider.evidence_file(organisation_id=org, evidence_id=proof["evidence_id"])["digest"], proof["file_digest"])
		self.assertIsNone(provider.evidence_file(organisation_id="another", evidence_id=proof["evidence_id"]))
