# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §5.4, §7.2 `SubmitTenderClarification` and §8 (plan
Phase 5, BDS8-502): only a registered candidate asks, only before the
clarification deadline by trusted time, and the question lives in Tenders
alone."""

from __future__ import annotations

import frappe
from frappe.utils import add_to_date, get_datetime

from kentender_procurement.bid_submission.services import clarification, errors, start_bid
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, BidCase, key
from kentender_procurement.tenders.tests import fixtures as tender_fx

QUESTION = "Please confirm whether the 3-year warranty must include on-site battery replacement."


class TestSubmitClarification(BidCase):
	def setUp(self):
		super().setUp()
		self._flag("kt_bds_clarification_producer", tender_fx.PRODUCER)

	def ask(self, text=QUESTION, idempotency_key=None):
		return clarification.submit_tender_clarification(tender_reference=self.reference, question=text, organisation=AFYA, idempotency_key=idempotency_key or key(), user=DAVID)

	def test_a_candidate_asks_through_tenders_and_nothing_is_kept_here(self):
		start_bid.start_bid(tender_reference=self.reference, organisation=AFYA, arrangement=self.single(), notice_contact_id=f"{AFYA}-C1", idempotency_key=key(), user=DAVID)
		self.at("2027-05-20 08:50:00")
		request = key()
		asked = self.ask(idempotency_key=request)
		row = frappe.db.get_value("Tender Clarification", asked["clarification_id"], ["tender", "candidate_registration_id", "question", "received_at"], as_dict=True)
		arrangement = frappe.db.get_value("Bidder Arrangement", {"tender": self.name}, "name")
		self.assertEqual((row.tender, row.candidate_registration_id, row.question, str(row.received_at)), (self.name, arrangement, QUESTION, "2027-05-20 08:50:00"))
		self.assertEqual(self.ask(idempotency_key=request), asked)
		self.assertEqual(frappe.db.count("Tender Clarification", {"tender": self.name}), 1)
		short = self.ask(text="Why?")
		self.assertEqual((short["ok"], list(short["errors"])), (False, ["question"]))

	def test_no_question_without_a_bid_or_after_the_deadline(self):
		with self.assertRaises(errors.BidSubmissionError) as unregistered:
			self.ask()
		self.assertEqual(unregistered.exception.code, "BDS_CLARIFICATION_NOT_REGISTERED")
		start_bid.start_bid(tender_reference=self.reference, organisation=AFYA, arrangement=self.single(), notice_contact_id=f"{AFYA}-C1", idempotency_key=key(), user=DAVID)
		deadline = get_datetime(frappe.db.get_value("Tender", self.name, "clarification_deadline"))
		self.at(str(deadline))
		with self.assertRaises(errors.BidSubmissionError) as late:
			self.ask()
		self.assertEqual(late.exception.code, "BDS_CLARIFICATION_DEADLINE_PASSED")
		self.at(str(add_to_date(deadline, seconds=-1)))
		self.assertTrue(self.ask()["ok"])
		self.assertEqual(frappe.db.count("Tender Clarification", {"tender": self.name}), 1)
