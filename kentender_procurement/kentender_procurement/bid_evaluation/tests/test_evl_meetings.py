# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Procurement meetings register on the real Evaluation world (OVS-CHG-001
v0.6 §11, §13, §15; plan D5 to D8; tracker OVS6-0401 to OVS6-0408; acceptance
OVS-AC-012). The counting rules are proved apart, in
`proceedings/tests/test_ovs_register_counting.py`; here the rows come from
real records: the completed opening's Proceeding (which has no session row)
and each Evaluation discussion session, with the Tender's real department.

Who sees a row is the owner's verdict. A row never carries a session's
subject, notes, a bidder's name, a count of bids or a finding."""

from __future__ import annotations

import json

import frappe

from kentender_procurement.bid_evaluation.services import discussion
from kentender_procurement.bid_evaluation.tests.support import AO, AUDITOR, CHAIR, HOP, MEMBER, MEMBER_2, OUTSIDER, SECRETARY, EvaluationCase
from kentender_procurement.bid_evaluation.tests.test_evl_oversight import BIDDER, HOD, HOD_OTHER
from kentender_procurement.bid_submission.tests.support import key
from kentender_procurement.proceedings.services import register

SUBJECT = "Service-location evidence"


def dump(value) -> str:
	return json.dumps(value, default=str)


class TestMeetingsRegister(EvaluationCase):
	def setUp(self):
		super().setUp()
		self.case = self.reviewing()
		# session 1: the chair starts, one member joins, the chair ends it; session 2 is the chair alone
		discussion.start_discussion(tender=self.name, subject=SUBJECT, idempotency_key=key(), user=CHAIR)
		discussion.join_discussion(tender=self.name, idempotency_key=key(), user=MEMBER)
		discussion.end_discussion(tender=self.name, idempotency_key=key(), user=CHAIR)
		discussion.start_discussion(tender=self.name, subject="Second sitting", idempotency_key=key(), user=CHAIR)
		discussion.end_discussion(tender=self.name, idempotency_key=key(), user=CHAIR)

	def meetings(self, user, **filters):
		return register.list_meetings(user=user, **filters)

	def mine(self, out):
		return [r for r in out["rows"] if r["tender"] == self.reference]

	def test_the_opening_and_each_evaluation_session_are_rows_of_their_tenders_department(self):
		out = self.meetings(AO, query=self.reference)
		rows = self.mine(out)
		self.assertEqual(sorted((r["type"], r["session"]) for r in rows), [("Bid evaluation", 1), ("Bid evaluation", 2), ("Bid opening", 1)])
		tender = frappe.get_doc("Tender", frappe.db.get_value("Tender", {"tender_reference": self.reference}, "name"))
		lead_name = frappe.db.get_value("Organisation Unit", tender.lead_org_unit, "unit_name")
		for r in rows:
			self.assertEqual((r["department"], r["department_name"]), (tender.lead_org_unit, lead_name))
			self.assertTrue(r["held"] and r["started"] and r["state"], r)
		self.assertEqual(out["held_total"], 3)
		self.assertEqual(out["totals"]["by_type"], {"Bid opening": 1, "Bid evaluation": 2})
		self.assertEqual({g["department"]: g["total"] for g in out["totals"]["by_department"]}, {tender.lead_org_unit: 3})
		self.assertFalse(out["incomplete"])

	def test_present_counts_the_people_who_arrived_in_each_session(self):
		sessions = {r["session"]: r for r in self.mine(self.meetings(AO, query=self.reference)) if r["type"] == "Bid evaluation"}
		self.assertEqual(sessions[1]["present"], 2)  # the chair who started it and the member who joined
		self.assertEqual(sessions[2]["present"], 1)  # the chair alone

	def test_a_row_never_carries_a_subject_a_bidder_or_a_bid_count(self):
		for user in (AO, HOP, AUDITOR, HOD, "Administrator"):
			out = self.meetings(user, query=self.reference)
			text = dump(out)
			self.assertNotIn(SUBJECT, text, user)
			self.assertNotIn("Second sitting", text, user)
			self.assertNotIn(BIDDER, text, user)
			for forbidden in ("subject", "bids_opened", "findings", "notes"):
				self.assertNotIn(f'"{forbidden}"', text, f"{user} {forbidden}")

	def test_each_reader_sees_the_rows_their_owner_allows(self):
		for user in (AO, HOP, AUDITOR, HOD, "Administrator", SECRETARY):
			self.assertEqual(self.meetings(user, query=self.reference)["held_total"], 3, user)
		# an evaluation committee member keeps the owner's own access: the evaluation's sessions, not the opening committee's
		for user in (CHAIR, MEMBER):
			out = self.meetings(user, query=self.reference)
			self.assertEqual((out["held_total"], out["totals"]["by_type"]), (2, {"Bid opening": 0, "Bid evaluation": 2}), user)
		for user in (HOD_OTHER, OUTSIDER):
			self.assertEqual(self.mine(self.meetings(user, query=self.reference)), [], user)

	def test_a_reader_with_no_responsibility_and_no_row_gets_the_forbidden_verdict_and_a_department_head_does_not(self):
		self.assertTrue(self.meetings(OUTSIDER)["forbidden"])
		self.assertFalse(self.meetings(HOD_OTHER)["forbidden"])  # a department head may open the page; none of these rows is theirs
		self.assertFalse(self.meetings(AO)["forbidden"])

	def test_the_department_filter_matches_the_lead_and_totals_do_not_change_with_pagination(self):
		out = self.meetings(AO, query=self.reference)
		unit = self.mine(out)[0]["department"]
		by_unit = self.meetings(AO, query=self.reference, department=unit)
		self.assertEqual(by_unit["held_total"], out["held_total"])
		paged = self.meetings(AO, query=self.reference, start=0, limit=1)
		self.assertEqual((len(paged["rows"]), paged["held_total"], paged["totals"]), (1, out["held_total"], out["totals"]))
		self.assertEqual(self.meetings(AO, query=self.reference, department="OU-NO-SUCH")["held_total"], 0)

	def test_filters_by_type_and_state(self):
		self.assertEqual(self.meetings(AO, query=self.reference, type="Bid evaluation")["held_total"], 2)
		self.assertEqual(self.meetings(AO, query=self.reference, type="Bid opening")["held_total"], 1)
		self.assertEqual(self.meetings(AO, query=self.reference, state="Session ended")["held_total"], 2)

	def test_reading_the_register_changes_nothing(self):
		before = frappe.db.count("Proceeding Session"), frappe.db.count("Proceeding Attendance"), frappe.db.count("Notification Log")
		for user in (AO, HOD, "Administrator"):
			self.meetings(user)
		self.assertEqual((frappe.db.count("Proceeding Session"), frappe.db.count("Proceeding Attendance"), frappe.db.count("Notification Log")), before)
