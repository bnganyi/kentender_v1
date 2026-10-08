# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RG-15 / AUD-AWD-001 — same-tender separation (owner decision 7 Oct 2026).

Evaluators assess and recommend; the secretary manages the proceedings; the Head
of Procurement issues the professional opinion; the Accounting Officer decides the
award. The Head may be the evaluation secretary but not a member or chair of the same
tender's evaluation; the Accounting Officer may not be on the panel at all (member,
chair or secretary). The rule holds at appointment and at every command that exercises
the role, so a person appointed earlier who later gets the other role is refused."""

from __future__ import annotations

import frappe

from kentender_core.services import responsibility_administration as administration
from kentender_procurement.bid_evaluation.services import appointment, records, roster, secretary
from kentender_procurement.bid_evaluation.tests.support import AO, CHAIR, HOP, MEMBER, MEMBER_2, NS, SECRETARY
from kentender_procurement.bid_evaluation.tests.test_evl_committee import ROSTER, CommitteeCase
from kentender_procurement.bid_submission.tests.support import key

HEAD = "Head of Procurement Function"
OFFICER = "Accounting Officer"


def _with(roster_rows, user, capacity):
	return [r if r["capacity"] != capacity else {**r, "user": user} for r in roster_rows]


class TestSeparationAtAppointment(CommitteeCase):
	def reasons(self, error):
		return {r["detail"].get("person"): r["detail"].get("reason") for r in error.reasons}

	def test_the_accounting_officer_cannot_be_chair_or_member(self):
		as_chair = self.refused(self.evl_appoint, [{**ROSTER[0], "user": AO}, ROSTER[1], ROSTER[2]])
		self.assertEqual((as_chair.code, self.reasons(as_chair)), ("EVL_MEMBER_INELIGIBLE", {AO: "accounting_officer"}))
		as_member = self.refused(self.evl_appoint, [ROSTER[0], ROSTER[1], {**ROSTER[2], "user": AO}])
		self.assertEqual(self.reasons(as_member), {AO: "accounting_officer"})
		self.assertFalse(roster.current_appointment(self.evaluation))

	def test_the_head_of_procurement_cannot_be_chair_or_member(self):
		as_chair = self.refused(self.evl_appoint, [{**ROSTER[0], "user": HOP}, ROSTER[1], ROSTER[2]])
		self.assertEqual(self.reasons(as_chair), {HOP: "head_of_procurement"})
		as_member = self.refused(self.evl_appoint, [ROSTER[0], ROSTER[1], {**ROSTER[2], "user": HOP}])
		self.assertEqual(self.reasons(as_member), {HOP: "head_of_procurement"})

	def test_the_accounting_officer_cannot_be_the_secretary_and_the_head_is_by_office(self):
		self.evl_appoint()
		self.assertEqual(roster.secretary(self.evaluation), HOP)  # the Head may be the secretary: by office
		error = self.refused(secretary.delegate_secretary, tender=self.name, secretary=AO, expected_version=self.evl_version(), idempotency_key=key(), user=HOP)
		self.assertEqual(error.code, "EVL_SECRETARY_INELIGIBLE")
		self.assertIn("accounting_officer", {r["detail"].get("reason") for r in error.reasons})
		self.assertEqual(roster.secretary(self.evaluation), HOP)

	def test_a_replacement_cannot_bring_in_either_officer(self):
		self.evl_appoint()
		for who, reason in ((AO, "accounting_officer"), (HOP, "head_of_procurement")):
			error = self.refused(
				appointment.replace_member, tender=self.name, outgoing=MEMBER_2, incoming={"user": who, "capacity": "Member"},
				reason="The member is unavailable for the whole evaluation period.", expected_version=self.evl_version(),
				idempotency_key=key(), user=AO,
			)
			self.assertEqual(self.reasons(error), {who: reason})


class TestSeparationAtEveryCommand(CommitteeCase):
	def grant(self, user, role):
		outcome = administration.grant(user=user, business_role=role, organisation_unit="", fixture_namespace=NS, actor="Administrator")
		self.addCleanup(lambda: administration.revoke(outcome["assignment"], reason="Revoked inside the separation test.", actor="Administrator"))
		frappe.db.commit()

	def probe(self, user):
		return records.command("Probe", tender=self.name, idempotency_key=key(), actor=user, payload={}, body=lambda: {"ok": True})

	def test_a_member_who_later_becomes_the_accounting_officer_is_refused(self):
		self.evl_appoint()
		self.assertTrue(self.probe(MEMBER)["ok"])
		self.grant(MEMBER, OFFICER)
		error = self.refused(self.probe, MEMBER)
		self.assertEqual((error.code, error.detail["reason"]), ("EVL_MEMBER_INELIGIBLE", "accounting_officer"))
		self.assertEqual(self.refused(self.evl_declare, MEMBER).detail["reason"], "accounting_officer")

	def test_a_member_who_later_becomes_the_head_of_procurement_is_refused(self):
		self.evl_appoint()
		self.grant(CHAIR, HEAD)
		self.assertEqual(self.refused(self.probe, CHAIR).detail["reason"], "head_of_procurement")
		self.assertEqual(self.refused(self.evl_declare, CHAIR).detail["reason"], "head_of_procurement")

	def test_a_secretary_who_later_becomes_the_accounting_officer_is_refused_but_a_head_secretary_is_not(self):
		self.evl_appoint()
		self.assertTrue(self.probe(HOP)["ok"])  # the Head is the secretary by office and holds no member seat
		self.assertTrue(secretary.delegate_secretary(tender=self.name, secretary=SECRETARY, expected_version=self.evl_version(), idempotency_key=key(), user=HOP)["ok"])
		self.assertTrue(self.probe(SECRETARY)["ok"])
		self.grant(SECRETARY, OFFICER)
		self.assertEqual(self.refused(self.probe, SECRETARY).detail["reason"], "accounting_officer")

	def test_the_offices_themselves_still_act_in_office(self):
		self.evl_appoint()
		self.assertTrue(self.probe(AO)["ok"])
		self.assertTrue(self.probe(HOP)["ok"])
