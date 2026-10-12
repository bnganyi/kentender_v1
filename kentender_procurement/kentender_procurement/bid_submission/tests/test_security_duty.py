# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The tender-security intake duty (Project Owner, 10 October 2026): explicit,
Tender-scoped, assigned only by the Head of Procurement Function, and
incompatible on the same Tender with opening and evaluation duties in both
directions. Ending an assignment ends access but not exposure."""

from __future__ import annotations

from unittest import mock

import frappe

from kentender_core.services import authorization
from kentender_core.services import responsibility_administration as administration
from kentender_procurement.bid_submission.services import records, security_duty
from kentender_procurement.bid_submission.tests.support import BidCase, key
from kentender_procurement.tenders.tests import fixtures as tender_fx

HEAD, OFFICER, AO, BOTH, NOBODY = tender_fx.HOPF, tender_fx.OFFICER, tender_fx.AO, tender_fx.BOTH, tender_fx.NOBODY


class DutyCase(BidCase):
	def assign(self, officer=OFFICER, **kw):
		return security_duty.assign_intake_officer(tender_reference=self.reference, officer=officer, user=kw.pop("user", HEAD), **kw)

	def expose(self, user, kind=security_duty.VIEWED):
		with records.atomic("test-exposure"):
			security_duty.record_exposure(self.name, self.reference, user, kind)


class TestWhoHoldsTheDuty(DutyCase):
	def test_no_office_status_or_technical_account_holds_it(self):
		for user in (HEAD, AO, BOTH, OFFICER, NOBODY, "Administrator"):
			with self.subTest(user=user):
				self.assertFalse(security_duty.holds_duty(user, self.reference))
				with self.assertRaises(frappe.PermissionError):
					security_duty.require_officer(user, self.reference)

	def test_the_head_assigns_for_one_tender_and_it_stops_when_revoked(self):
		given = self.assign()
		self.assertTrue(given["ok"])
		self.assertTrue(security_duty.holds_duty(OFFICER, self.reference))
		self.assertFalse(security_duty.holds_duty(OFFICER, "TND-OTHER-0000-000"))  # one Tender only
		self.assertEqual(security_duty.officer_tenders(OFFICER), [self.reference])
		row = frappe.db.get_value("User Responsibility Assignment", given["assignment"], ["assigned_by", "scope_reference", "business_role", "organisation_unit"], as_dict=True)
		self.assertEqual((row.assigned_by, row.scope_reference, row.business_role, row.organisation_unit), (HEAD, self.reference, security_duty.ROLE, None))
		self.assertTrue(security_duty.revoke_intake_officer(assignment=given["assignment"], reason="The duty is no longer needed.", user=HEAD)["revoked"])
		self.assertFalse(security_duty.holds_duty(OFFICER, self.reference))

	def test_an_ended_or_future_period_does_not_authorise(self):
		self.assign(effective_to="2020-01-01 00:00:00")
		self.assertFalse(security_duty.holds_duty(OFFICER, self.reference))

	def test_only_the_head_assigns_or_revokes(self):
		for user in (OFFICER, AO, NOBODY, "Administrator"):
			with self.subTest(user=user), self.assertRaises(frappe.PermissionError):
				self.assign(user=user)
		given = self.assign()
		for user in (OFFICER, AO, "Administrator"):
			with self.subTest(revoke=user), self.assertRaises(frappe.PermissionError):
				security_duty.revoke_intake_officer(assignment=given["assignment"], reason="Trying to end it without authority.", user=user)
		# the generic System setup route refuses it as well: the duty is not System Manager's to assign
		with self.assertRaises(Exception):
			administration.grant(user=NOBODY, business_role=security_duty.ROLE, scope_reference=self.reference, actor="Administrator")

	def test_a_technical_account_or_the_head_themselves_cannot_be_assigned(self):
		for officer in ("Administrator", HEAD):
			with self.subTest(officer=officer), self.assertRaises(Exception):
				self.assign(officer=officer)

	def test_the_duty_needs_a_published_tender_and_a_tender_scope(self):
		with self.assertRaises(Exception):
			security_duty.assign_intake_officer(tender_reference="TND-NOPE-0000-000", officer=OFFICER, user=HEAD)
		with self.assertRaises(Exception):
			administration.grant(user=OFFICER, business_role=security_duty.ROLE, actor=HEAD)  # no Tender named
		with self.assertRaises(Exception):
			administration.grant(user=OFFICER, business_role="Procurement Officer", scope_reference=self.reference, actor="Administrator")  # a Tender on a non-Tender role


class TestSeparationBothWays(DutyCase):
	def test_assigning_is_refused_for_someone_on_the_tenders_opening_or_evaluation(self):
		for duty in ("on the opening committee", "on the evaluation committee", "the evaluation secretary"):
			with self.subTest(duty=duty), mock.patch.object(security_duty, "participants", return_value={OFFICER: [duty]}):
				with self.assertRaises(Exception) as caught:
					self.assign()
				self.assertIn(duty, str(caught.exception))
				self.assertIn("cannot also take its tender-security intake", str(caught.exception))

	def test_the_head_office_holder_is_never_eligible_because_the_head_is_every_evaluations_secretary(self):
		with self.assertRaises(Exception) as caught:
			self.assign(officer=BOTH)
		self.assertIn("evaluation secretary of every Tender", str(caught.exception))

	def test_appointing_is_refused_for_a_person_who_holds_the_duty_even_unused(self):
		self.assertIsNone(security_duty.committee_blocker(self.name, OFFICER, "the opening committee", "Opening committee"))
		given = self.assign()
		blocked = security_duty.committee_blocker(self.name, OFFICER, "the opening committee", "Opening committee")
		self.assertIn("holds or has held the tender-security intake duty for this Tender", blocked)
		# an unused assignment may be revoked before appointment, which makes the person eligible again
		security_duty.revoke_intake_officer(assignment=given["assignment"], reason="Assigned to the wrong officer by mistake.", user=HEAD)
		self.assertIsNone(security_duty.committee_blocker(self.name, OFFICER, "the opening committee", "Opening committee"))

	def test_ending_the_duty_does_not_erase_exposure(self):
		given = self.assign()
		self.expose(OFFICER)
		security_duty.revoke_intake_officer(assignment=given["assignment"], reason="The duty ended after the deadline.", user=HEAD)
		self.assertFalse(security_duty.holds_duty(OFFICER, self.reference))
		for duty, kind in (("the opening committee", "Opening committee"), ("the evaluation committee", "Evaluation committee"), ("the evaluation secretary", "Evaluation secretary")):
			with self.subTest(duty=duty):
				self.assertIn("holds or has held", security_duty.committee_blocker(self.name, OFFICER, duty, kind))
		# the same wording for an unused and a used duty: a refusal never tells whether it was used
		other = tender_fx.NOBODY
		self.assertIsNone(security_duty.committee_blocker(self.name, other, "the opening committee", "Opening committee"))

	def test_a_conflict_the_accounting_officer_resolved_no_longer_blocks_that_duty_only(self):
		self.expose(OFFICER)
		with records.atomic("test-conflict"):
			conflict = records.insert(frappe.get_doc({"doctype": security_duty.CONFLICT, "tender": self.name, "tender_reference": self.reference, "user": OFFICER,
				"conflicting_duty": "Opening committee", "basis": "Has viewed intake records", "status": "Open", "detected_at": "2027-05-19 09:00:00", "detected_by": "System"}))
		self.assertTrue(security_duty.committee_blocker(self.name, OFFICER, "the opening committee", "Opening committee"))
		for user in (HEAD, OFFICER):
			with self.subTest(user=user), self.assertRaises(frappe.PermissionError):
				security_duty.resolve_conflict(conflict=conflict.name, reason="Resolved by someone who may not.", user=user)
		self.assertEqual(security_duty.resolve_conflict(conflict=conflict.name, reason="Short", user=AO)["ok"], False)
		self.assertTrue(security_duty.resolve_conflict(conflict=conflict.name, reason="The Accounting Officer accepted this for the demonstration world.", user=AO)["changed"])
		self.assertIsNone(security_duty.committee_blocker(self.name, OFFICER, "the opening committee", "Opening committee"))
		self.assertTrue(security_duty.committee_blocker(self.name, OFFICER, "the evaluation committee", "Evaluation committee"))  # another duty stays blocked

	def test_existing_conflicts_are_flagged_once_and_nothing_is_changed(self):
		self.expose(OFFICER)
		with mock.patch.object(security_duty, "participants", return_value={OFFICER: ["on the opening committee", "the evaluation secretary"]}):
			first = security_duty.detect_conflicts()
			again = security_duty.detect_conflicts()
		self.assertEqual(len(first), 2)
		self.assertEqual(again, [])
		rows = security_duty.list_conflicts(user=AO)["rows"]
		self.assertEqual(sorted((r["user"], r["conflicting_duty"], r["status"]) for r in rows if r["tender_reference"] == self.reference),
			[(OFFICER, "Evaluation secretary", "Open"), (OFFICER, "Opening committee", "Open")])
		# neither the Head nor the Accounting Officer learns whether an intake exists: one generic basis
		self.assertEqual({r["basis"] for r in rows}, {security_duty.GENERIC_BASIS})
		self.assertEqual({r["basis"] for r in security_duty.list_conflicts(user=HEAD)["rows"]}, {security_duty.GENERIC_BASIS})


class TestWhatTheHeadSees(DutyCase):
	def test_the_head_lists_officers_and_reasons_without_any_supplier_or_bid_information(self):
		view = security_duty.eligible_officers(self.reference, user=HEAD)
		by_user = {o["user"]: o for o in view["officers"]}
		self.assertTrue(by_user[OFFICER]["eligible"])
		self.assertFalse(by_user[BOTH]["eligible"])
		self.assertNotIn(HEAD, by_user)  # not themselves
		text = frappe.as_json(view).lower()
		for word in ("supplier", "bid", "afya", "intake record", "instrument"):
			self.assertNotIn(word, text.replace("tender-security intake", ""), word)
		with self.assertRaises(frappe.PermissionError):
			security_duty.eligible_officers(self.reference, user=OFFICER)

	def test_the_head_sees_the_assignments_but_never_whether_any_was_used(self):
		given = self.assign()
		self.expose(OFFICER)
		rows = security_duty.list_duty(self.reference, user=HEAD)["rows"]
		self.assertEqual([r["assignment"] for r in rows], [given["assignment"]])
		self.assertEqual(set(rows[0]), {"assignment", "user", "full_name", "status", "effective_from", "effective_to", "assigned_by", "assigned_at", "revoked_by", "revoked_at", "revocation_reason"})
		with self.assertRaises(frappe.PermissionError):
			security_duty.list_duty(self.reference, user=OFFICER)
