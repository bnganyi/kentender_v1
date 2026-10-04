# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §4.2, §5.2, §6 and plan OD-D — people, authority windows,
organisation isolation, several organisations per person, and suspending
or restoring access (BDS01-IMP-007/008/010, BDS03-IMP-010; BDS01-AC-006…010,
BDS03-AC-010)."""

from __future__ import annotations

from unittest import mock

import frappe

from kentender_suppliers.supplier_accounts.services import access, assignments, authorization as authz, evidence, my_work_provider, organisation, read, verification
from kentender_suppliers.supplier_accounts.services.errors import AccountError
from kentender_suppliers.supplier_accounts.tests.support import AMINA, DAVID, DOMAIN, GRACE, MARY, PDF, PETER, STAFF, AccountsCase, key

KISIWA = {"legal_name": "Kisiwa Digital Limited", "registration_number": "PVT-KISIWA-01", "tax_identifier": "P051234568X", "official_email": "tenders@kisiwadigital.example", "job_title": "Director"}


class TestPeople(AccountsCase):
	def test_a_signatory_adds_a_representative_who_becomes_a_portal_user(self):
		org = self.active_account()
		self.at("2027-05-18 09:20:00")
		result = assignments.assign_supplier_representative(organisation=org, email=DAVID, full_name="David Ouma", job_title="Bid Coordinator", idempotency_key=key(), user=MARY)
		self.assertTrue(result["ok"])
		row = frappe.get_doc("Supplier User Assignment", result["assignment"])
		self.assertEqual((row.user, row.responsibility, row.job_title, str(row.effective_from), row.assigned_by), (DAVID, "Supplier Representative", "Bid Coordinator", "2027-05-18 09:20:00", MARY))
		fresh = f"new.person@{DOMAIN}"
		made = assignments.assign_supplier_representative(organisation=org, email=fresh, full_name="New Person", idempotency_key=key(), user=MARY)
		self.assertEqual(frappe.db.get_value("User", made["user"], "user_type"), "Website User")
		self.assertEqual(authz.responsibility_of(org, DAVID), "Supplier Representative")

	def test_a_representative_cannot_add_people_or_act_as_signatory(self):
		org = self.active_account()
		assignments.assign_supplier_representative(organisation=org, email=DAVID, full_name="David Ouma", idempotency_key=key(), user=MARY)
		with self.assertRaises(AccountError) as ctx:
			assignments.assign_supplier_representative(organisation=org, email=GRACE, full_name="Grace Njeri", idempotency_key=key(), user=DAVID)
		self.assertEqual(ctx.exception.code, "BDS_RESPONSIBILITY_REQUIRED")
		with self.assertRaises(AccountError):
			authz.require_signatory(org, DAVID)

	def test_a_signatory_needs_authority_evidence_and_internal_staff_are_never_assigned(self):
		org = self.active_account()
		missing = assignments.assign_authorised_signatory(organisation=org, email=GRACE, full_name="Grace Njeri", idempotency_key=key(), user=MARY)
		self.assertEqual(missing["errors"], {"authority_evidence": "Upload the evidence of this person's authority to sign."})
		staff = assignments.assign_supplier_representative(organisation=org, email=STAFF, full_name="Internal Staff", idempotency_key=key(), user=MARY)
		self.assertEqual(staff["errors"], {"email": "Internal KenTender users cannot hold supplier responsibilities."})
		ok = assignments.assign_authorised_signatory(organisation=org, email=GRACE, full_name="Grace Njeri", authority_filename="grace.pdf", authority_content=PDF, idempotency_key=key(), user=MARY)
		self.assertEqual(authz.require_signatory(org, GRACE)["name"], ok["assignment"])
		dup = assignments.assign_authorised_signatory(organisation=org, email=GRACE, full_name="Grace Njeri", authority_filename="grace.pdf", authority_content=PDF, idempotency_key=key(), user=MARY)
		self.assertEqual(dup["errors"], {"email": "This person already holds this responsibility for the organisation."})

	def test_authority_holds_only_inside_its_window_and_with_available_evidence(self):
		org = self.active_account()
		assignments.assign_authorised_signatory(organisation=org, email=GRACE, full_name="Grace Njeri", authority_filename="g.pdf", authority_content=PDF, effective_from="2027-05-20 10:00:00", effective_to="2027-06-12 11:00:00", idempotency_key=key(), user=MARY)
		for instant, expected in (("2027-05-20 09:59:59", False), ("2027-05-20 10:00:00", True), ("2027-06-12 10:59:59", True), ("2027-06-12 11:00:00", False)):
			self.at(instant)
			self.assertEqual(authz.responsibility_of(org, GRACE) == authz.SIGNATORY, expected, instant)
		# a signatory whose evidence was never scanned clean cannot sign
		self.at("2027-05-21 09:00:00")
		with mock.patch("kentender_core.services.file_integrity.scanner_result", return_value="Not scanned — no scanner configured"):
			assignments.assign_authorised_signatory(organisation=org, email=PETER, full_name="Peter Mwangi", authority_filename="p.pdf", authority_content=PDF, idempotency_key=key(), user=MARY)
		self.assertEqual(authz.responsibility_of(org, PETER), authz.REPRESENTATIVE)
		with self.assertRaises(AccountError):
			authz.require_signatory(org, PETER)


class TestIsolation(AccountsCase):
	def test_another_organisation_is_not_found_to_read_or_change(self):
		afya = self.active_account()
		self.at("2027-05-18 10:00:00")
		kisiwa = self.active_account(PETER, **KISIWA)
		version = frappe.db.get_value("Supplier Organisation", afya, "record_version")
		for call in (
			lambda: read.get_supplier_account(organisation=afya, user=PETER),
			lambda: organisation.update_supplier_organisation(organisation=afya, values={"registered_address": "Elsewhere"}, expected_version=version, idempotency_key=key(), user=PETER),
			lambda: evidence.upload_account_evidence(organisation=afya, evidence_type="Other", filename="x.pdf", content=PDF, idempotency_key=key(), user=PETER),
			lambda: verification.send_account_verification(organisation=afya, idempotency_key=key(), user=PETER),
		):
			with self.assertRaises(frappe.DoesNotExistError):
				call()
		self.assertEqual(read.get_supplier_account(user=PETER)["organisation"]["organisation"], kisiwa)

	def test_a_person_in_two_organisations_names_one_per_request(self):
		afya = self.active_account()
		self.at("2027-05-18 10:00:00")
		kisiwa = self.active_account(PETER, **KISIWA)
		assignments.assign_supplier_representative(organisation=kisiwa, email=DAVID, full_name="David Ouma", idempotency_key=key(), user=PETER)
		assignments.assign_supplier_representative(organisation=afya, email=DAVID, full_name="David Ouma", idempotency_key=key(), user=MARY)
		choose = read.get_supplier_account(user=DAVID)
		self.assertEqual((choose["state"], sorted(o["organisation"] for o in choose["organisations"])), ("choose_organisation", sorted([afya, kisiwa])))
		self.assertNotIn("organisation", choose)
		one = read.get_supplier_account(organisation=kisiwa, user=DAVID)
		self.assertEqual((one["organisation"]["legal_name"], one["viewer"]["responsibility"]), ("Kisiwa Digital Limited", "Supplier Representative"))


class TestSuspension(AccountsCase):
	def _version(self, org):
		return frappe.db.get_value("Supplier Organisation", org, "record_version")

	def test_only_the_support_officer_suspends_and_restores_with_a_reason(self):
		org = self.active_account()
		for user in (MARY, STAFF, "Administrator"):
			with self.assertRaises(AccountError) as ctx:
				access.suspend_supplier_account(organisation=org, reason="Reported misuse of the account.", expected_version=self._version(org), idempotency_key=key(), user=user)
			self.assertEqual(ctx.exception.code, "BDS_RESPONSIBILITY_REQUIRED", user)
		short = access.suspend_supplier_account(organisation=org, reason="misuse", expected_version=self._version(org), idempotency_key=key(), user=AMINA)
		self.assertEqual(short["errors"], {"reason": "Enter a reason of 10 to 500 characters."})
		self.at("2027-05-19 08:00:00")
		done = access.suspend_supplier_account(organisation=org, reason="Reported misuse of the account.", expected_version=self._version(org), idempotency_key=key(), user=AMINA)
		self.assertEqual(done["account_status"], "Suspended")
		decision = frappe.get_doc("Supplier Account Access Decision", done["decision"])
		self.assertEqual((decision.decision, decision.previous_status, decision.resulting_status, decision.decided_by), ("Suspend", "Active", "Suspended", AMINA))
		rows = my_work_provider.my_work_rows(user=AMINA)["assigned"]
		self.assertEqual([(r["title"], r["reference"], r["route"]) for r in rows if r["route"][-1] == org], [("Review suspended supplier account access", "Afya Digital Supplies Limited", ["Form", "Supplier Organisation", org])])
		self.assertEqual(my_work_provider.my_work_rows(user=MARY)["assigned"], [])
		restored = access.restore_supplier_account(organisation=org, reason="Misuse report was withdrawn by the reporter.", expected_version=self._version(org), idempotency_key=key(), user=AMINA)
		self.assertEqual(restored["account_status"], "Active")  # the official email is verified
		self.assertFalse([r for r in my_work_provider.my_work_rows(user=AMINA)["assigned"] if r["route"][-1] == org])

	def test_a_suspended_account_blocks_every_change_but_keeps_its_read(self):
		org = self.active_account()
		access.suspend_supplier_account(organisation=org, reason="Reported misuse of the account.", expected_version=self._version(org), idempotency_key=key(), user=AMINA)
		for call in (
			lambda: organisation.update_supplier_organisation(organisation=org, values={"registered_address": "Elsewhere"}, expected_version=self._version(org), idempotency_key=key(), user=MARY),
			lambda: evidence.upload_account_evidence(organisation=org, evidence_type="Other", filename="x.pdf", content=PDF, idempotency_key=key(), user=MARY),
			lambda: assignments.assign_supplier_representative(organisation=org, email=DAVID, full_name="David Ouma", idempotency_key=key(), user=MARY),
			lambda: verification.send_account_verification(organisation=org, idempotency_key=key(), user=MARY),
		):
			with self.assertRaises(AccountError) as ctx:
				call()
			self.assertEqual(ctx.exception.code, "BDS_ACCOUNT_SUSPENDED")
		account = read.get_supplier_account(user=MARY)
		self.assertEqual((account["organisation"]["account_status"], account["allowed_actions"], account["organisation"]["legal_name"]), ("Suspended", ["view_receipts"], "Afya Digital Supplies Limited"))

	def test_restoring_an_unverified_account_returns_it_to_pending_verification(self):
		org = self.register()["organisation"]
		access.suspend_supplier_account(organisation=org, reason="Registration reported as impersonation.", expected_version=self._version(org), idempotency_key=key(), user=AMINA)
		with self.assertRaises(AccountError):
			verification.verify_account_communication(token=self.token(), user=MARY)  # verification never reactivates
		restored = access.restore_supplier_account(organisation=org, reason="Identity confirmed by telephone call.", expected_version=self._version(org), idempotency_key=key(), user=AMINA)
		self.assertEqual(restored["account_status"], "Pending verification")
