# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The closed Tender page says what Bid Opening needs next from this reader (owner instruction,
10 October 2026). Tenders reads one published answer through `kt_tender_stage_summaries`: Bid
Opening's own next step, the one its page uses. A reader with no step keeps the Tender's status;
no bid count or name appears before the opening starts."""

from __future__ import annotations

import json

import frappe

from kentender_core.services import home_support
from kentender_core.services import next_step as ns
from kentender_procurement.bid_opening.services import next_steps, records
from kentender_procurement.bid_opening.tests.support import AO, CHAIR, MEMBER, OpeningCase
from kentender_procurement.bid_submission.tests.support import AFYA
from kentender_procurement.bid_submission.tests.test_submission import SubmissionCase
from kentender_procurement.bid_submission.services import supplier_gateway
from kentender_procurement.tenders.services import guidance as guide
from kentender_procurement.tenders.services import read

CORE = ("kind", "label", "headline", "sentence", "stage", "holder", "since", "blockers")


def core(step: dict) -> dict:
	return {k: step[k] for k in CORE}


class TenderPageMixin:
	def closed(self, *, appoint: bool = False, publish: bool = False) -> None:
		self.prepare_case()
		if appoint:
			self.assertTrue(self.appoint()["ok"])
		if publish:
			self.assertTrue(self.publish()["ok"])
		self.close_box()
		self.assertEqual(frappe.db.get_value("Tender", self.name, "overall_status"), "Submission period ended")

	def owner_answer(self, user: str) -> dict:
		return next_steps.answer_for(frappe.get_doc(records.CASE, records.case_for(self.name)), user)

	def page(self, user: str) -> dict:
		frappe.set_user(user)
		try:
			return read.get_tender(tender=self.name, user=user)["guidance"]
		finally:
			frappe.set_user("Administrator")



class TestTenderPageStep(TenderPageMixin, OpeningCase):
	def test_the_accounting_officer_is_told_to_appoint_then_to_publish_with_a_button_into_the_opening_record(self):
		self.closed()
		step = self.page(AO)["next_step"]
		self.assertEqual(core(step), core(self.owner_answer(AO)))
		self.assertEqual((step["kind"], step["headline"]), (ns.KIND_YOUR_TURN, "Appoint opening committee"))
		self.assertEqual([(f["kind"], f["target"], f["primary"]) for f in step["fixes"]], [(ns.FIX_ROUTE, ["tenders", self.reference, "opening"], True)])
		self.assertEqual(ns.problems(step), [])
		self.assertTrue(self.appoint()["ok"])
		later = self.page(AO)["next_step"]
		self.assertEqual((later["headline"], core(later)), ("Publish how to attend", core(self.owner_answer(AO))))
		self.assertTrue(self.publish()["ok"])
		done = self.page(AO)["next_step"]
		self.assertEqual(core(done), core(self.owner_answer(AO)))
		self.assertTrue(done["headline"].startswith("You published how to attend on "))

	def test_the_head_of_procurement_waits_for_the_accounting_officer_with_no_button(self):
		self.closed()
		step = self.page(CHAIR)["next_step"]
		self.assertEqual(core(step), core(self.owner_answer(CHAIR)))
		self.assertEqual(step["kind"], ns.KIND_WAITING)
		self.assertEqual(step["fixes"], [])

	def test_a_committee_member_sees_exactly_the_openings_own_step(self):
		self.closed(appoint=True, publish=True)
		for user in (CHAIR, MEMBER):
			step = self.page(user)["next_step"]
			self.assertEqual(core(step), core(self.owner_answer(user)), user)
			self.assertNotEqual(step["kind"], ns.KIND_NOT_INVOLVED, user)

	def test_a_reader_with_no_step_keeps_the_tenders_own_status(self):
		self.closed()
		answer = self.owner_answer(MEMBER)
		self.assertEqual(answer["kind"], ns.KIND_NOT_INVOLVED)
		step = self.page(MEMBER)["next_step"]
		self.assertEqual((step["kind"], step["stage"]), (ns.KIND_DONE, guide.OPEN_MANAGEMENT))
		self.assertTrue(step["headline"].startswith("The system closed supplier submission at "))

	def test_the_finished_tender_row_is_captioned_and_sits_below_the_opening_step(self):
		self.closed()
		with_step, without = self.page(AO)["journey"], self.page(MEMBER)["journey"]
		self.assertEqual((with_step["caption"], with_step["step_first"]), ("Tender preparation is complete", True))
		self.assertEqual((without["caption"], without["step_first"]), ("Tender preparation is complete", False))
		self.assertTrue(all(s["marker"] == "done" for s in with_step["stages"]))

	def test_an_open_tender_page_is_unchanged(self):
		self.prepare_case()
		self.assertEqual(frappe.db.get_value("Tender", self.name, "overall_status"), "Published — open")
		step = self.page(AO)["next_step"]
		self.assertNotEqual(step["headline"], "Appoint opening committee")

	def test_home_words_the_accounting_officers_step_as_the_tender_page_does(self):
		from kentender_procurement.bid_opening.services.home_provider import entries
		self.closed()
		home_support.reset()
		rows = entries(user=AO, region="my_work")
		appoint = [r for r in rows if r["action"] == self.page(AO)["next_step"]["headline"]]
		self.assertEqual(len(appoint), 1)
		self.assertEqual(appoint[0]["destination"]["route"], ["tenders", self.reference, "opening"])
		# the Head of Procurement Function's wait reads the same on Home as on the Tender page
		home_support.reset()
		waits = [r["action"] for r in entries(user=CHAIR, region="waiting")]
		step = self.page(CHAIR)["next_step"]
		self.assertEqual(waits, [step["headline"]])  # one wording on Home, the Tender page and the opening page, however many hold the role


class TestTenderPageLeakage(TenderPageMixin, OpeningCase, SubmissionCase):
	"""With a real, submitted bid in the box: before Start the Tender page carries no bid count and no bidder name."""

	def test_before_start_no_bid_count_or_name_reaches_the_tender_page(self):
		self.assertTrue(self.submit(self.signed())["ok"])
		self.prepared()
		self.close_box()
		bidder = (supplier_gateway.organisation(organisation_id=AFYA) or {}).get("legal_name")
		self.assertTrue(bidder)
		for user in (AO, CHAIR, MEMBER):
			frappe.set_user(user)
			try:
				record = read.get_tender(tender=self.name, user=user)
			finally:
				frappe.set_user("Administrator")
			text = json.dumps({"guidance": record["guidance"], "stages": record.get("stage_summaries")}, default=str)
			self.assertNotIn(bidder, text, user)
			self.assertNotIn("Bids opened", text, user)
			self.assertNotIn("bids opened", text.lower(), user)
			opening = [s for s in record.get("stage_summaries") or [] if s["key"] == "bid-opening"][0]
			self.assertEqual([f["label"] for f in opening["facts"] if "bid" in f["label"].lower()], [], user)


class TestWhoAWaitIsOn(OpeningCase):
	"""One rule for naming who a wait is on, on every surface: up to two names, otherwise the responsibility."""

	def test_up_to_two_names_otherwise_the_role(self):
		self.assertEqual(next_steps.someone(["Amina Hassan"], "Accounting Officer"), "Amina Hassan")
		self.assertEqual(next_steps.someone(["Amina Hassan", "Brian Wafula"], "Accounting Officer"), "Amina Hassan or Brian Wafula")
		self.assertEqual(next_steps.someone(["A", "B", "C"], "Accounting Officer"), "an Accounting Officer")
		self.assertEqual(next_steps.someone(["A", "B", "C"], "Committee member"), "a Committee member")
		self.assertEqual(next_steps.someone([], "Accounting Officer"), "an Accounting Officer")
