# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Evaluation and the tender-security intake duty (Project Owner, 10 October
2026): on the same Tender they exclude each other, in both directions — the
committee, the secretary by office and a delegated secretary."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_evaluation.services import picker_sources, roster, secretary
from kentender_procurement.bid_evaluation.tests.support import AO, CHAIR, HOP, MEMBER, MEMBER_2, REPLACEMENT, SECRETARY
from kentender_procurement.bid_evaluation.tests.test_evl_committee import ROSTER, CommitteeCase
from kentender_procurement.bid_submission.services import records, security_duty
from kentender_procurement.tenders.tests import fixtures as tender_fx

NEW_ROSTER = [{"user": CHAIR, "capacity": "Chair"}, {"user": MEMBER, "capacity": "Member"}, {"user": REPLACEMENT, "capacity": "Member"}]


class TestEvaluationAndIntakeDuty(CommitteeCase):
	def assign(self, officer=REPLACEMENT):
		return security_duty.assign_intake_officer(tender_reference=self.reference, officer=officer, user=tender_fx.HOPF)

	def test_an_evaluation_member_cannot_be_assigned_the_duty(self):
		self.evl_appoint()
		with self.assertRaises(Exception) as caught:
			self.assign(MEMBER)
		self.assertIn("is on the evaluation committee for this Tender, so cannot also take its tender-security intake", str(caught.exception))

	def test_the_secretary_cannot_be_assigned_the_duty(self):
		self.evl_appoint()
		self.assertTrue(secretary.delegate_secretary(tender=self.name, secretary=SECRETARY, expected_version=self.evl_version(), idempotency_key=records.uuid4().hex, user=HOP)["ok"])
		with self.assertRaises(Exception) as caught:
			self.assign(SECRETARY)
		self.assertIn("the evaluation secretary for this Tender, so cannot also take its tender-security intake", str(caught.exception))
		# the Head is the secretary by office on every Tender, so the Head's office is never eligible
		with self.assertRaises(Exception) as caught:
			self.assign(tender_fx.BOTH)
		self.assertIn("evaluation secretary of every Tender", str(caught.exception))

	def test_an_officer_who_holds_the_duty_cannot_be_appointed_and_the_reason_is_reported_with_the_person(self):
		given = self.assign()
		error = self.refused(self.evl_appoint, members=NEW_ROSTER)
		by_person = {r["detail"].get("person"): r["detail"].get("reason") for r in error.reasons}
		self.assertEqual(by_person, {REPLACEMENT: "security_intake"})
		self.assertIn("holds or has held the tender-security intake duty for this tender", [r["detail"].get("explanation") for r in error.reasons][0])
		self.assertFalse(roster.current_appointment(self.evaluation))  # nothing appointed in part
		# the picker lists the same person unavailable, in the command's words, rather than leaving them out without a word
		listed = {r["id"]: r for r in picker_sources.committee_members(query="", context={"tender_reference": self.reference, "mode": "appoint"}, actor=AO, limit=20)}
		self.assertEqual(listed[REPLACEMENT]["disabled_reason"], [r["detail"].get("explanation") for r in error.reasons][0])
		security_duty.revoke_intake_officer(assignment=given["assignment"], reason="Assigned in error before the committee was named.", user=tender_fx.HOPF)
		again = {r["id"]: r for r in picker_sources.committee_members(query="", context={"tender_reference": self.reference, "mode": "appoint"}, actor=AO, limit=20)}
		self.assertIsNone(again[REPLACEMENT]["disabled_reason"])
		self.assertTrue(self.evl_appoint(members=NEW_ROSTER)["ok"])

	def test_an_officer_who_viewed_the_intake_stays_ineligible_after_the_duty_ends(self):
		given = self.assign()
		with records.atomic("exposure"):
			security_duty.record_exposure(self.name, self.reference, REPLACEMENT, security_duty.RECORDED, "TSI-0000000000")
		security_duty.revoke_intake_officer(assignment=given["assignment"], reason="The duty ended once the deadline had passed.", user=tender_fx.HOPF)
		error = self.refused(self.evl_appoint, members=NEW_ROSTER)
		self.assertEqual({r["detail"].get("person"): r["detail"].get("reason") for r in error.reasons}, {REPLACEMENT: "security_intake"})

	def test_a_head_who_exercised_the_duty_cannot_be_secretary_until_the_accounting_officer_resolves_it(self):
		from kentender_procurement.bid_evaluation.services import people

		head = people.head_holders()[0]
		with records.atomic("exposure"):
			security_duty.record_exposure(self.name, self.reference, head, security_duty.RECORDED, "TSI-0000000000")
			conflict = records.insert(frappe.get_doc({"doctype": security_duty.CONFLICT, "tender": self.name, "tender_reference": self.reference, "user": head, "conflicting_duty": "Evaluation secretary",
				"basis": "Has recorded intake", "status": "Open", "detected_at": "2027-05-19 09:00:00", "detected_by": "System"}))
		error = self.refused(self.evl_appoint)
		self.assertEqual(error.code, "EVL_SECRETARY_INELIGIBLE", error.detail)
		self.assertFalse(roster.current_appointment(self.evaluation))
		self.assertTrue(security_duty.resolve_conflict(conflict=conflict.name, reason="The Accounting Officer accepted this historic demonstration record.", user=AO)["changed"])
		self.assertTrue(self.evl_appoint()["ok"])  # explicit resolution lets the appointment proceed

	def test_a_delegated_secretary_with_the_duty_is_refused(self):
		self.evl_appoint()
		self.assign(REPLACEMENT)
		error = self.refused(secretary.delegate_secretary, tender=self.name, secretary=REPLACEMENT, expected_version=self.evl_version(), idempotency_key=records.uuid4().hex if hasattr(records, "uuid4") else "k1", user=HOP)
		self.assertEqual(error.code, "EVL_SECRETARY_INELIGIBLE", error.detail)

	def test_the_secretary_picker_lists_a_procurement_officer_who_holds_the_duty_in_the_commands_words(self):
		self.evl_appoint()
		with records.atomic("exposure"):  # a procurement officer, not yet the secretary, who has recorded intake
			security_duty.record_exposure(self.name, self.reference, SECRETARY, security_duty.RECORDED, "TSI-0000000000")
		error = self.refused(secretary.delegate_secretary, tender=self.name, secretary=SECRETARY, expected_version=self.evl_version(), idempotency_key="duty-picker-1", user=HOP)
		self.assertEqual(error.reasons[0]["detail"].get("reason"), "security_intake")
		listed = {r["id"]: r for r in picker_sources.secretaries(query="", context={"tender_reference": self.reference}, actor=HOP, limit=20)}
		self.assertEqual(listed[SECRETARY]["disabled_reason"], error.reasons[0]["detail"].get("explanation"))
