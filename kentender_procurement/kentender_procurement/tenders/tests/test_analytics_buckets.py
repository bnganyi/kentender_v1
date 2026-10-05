# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ANL-CHG-001 v0.8 §5.2 — the Tender bucket classifier (`tenders/services/analytics_buckets.py`).

A pure function over a facts dict, so there is no world, no database and nothing to clean up. Every bucket and the edges the
plan names (D5; FU-ANL-05, 15): a deadline that has passed before the hourly job closed the Tender, a cancellation over a
retained report or decision, an empty opening, a report delivered but not yet received, a decided Tender with notices still
to go, a hand-off to Contract Management, and a stage read that failed.

Run:
  bench --site kentender-test.local run-tests --app kentender_procurement \\
    --module kentender_procurement.tenders.tests.test_analytics_buckets
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from kentender_core.services.analytics_contract import AWARD, BUCKETS, CLOSED, CONTRACT, EVALUATION, OPEN, OPENING, PREPARATION, UNAVAILABLE
from kentender_procurement.tenders.services.analytics_buckets import FAILED, classify, needs_stage_reads

AT = datetime(2027, 6, 18, 10, 0)
PAST = AT - timedelta(days=2)
FUTURE = AT + timedelta(days=3)
DONE_AT = datetime(2027, 6, 10, 9, 0)


def facts(status: str = "Submission period ended", **over) -> dict:
	"""A Tender whose submission closed two days ago, with no stage case yet."""
	base = {"status": status, "at": AT, "submission_deadline": PAST, "cancelled": False, "cancellation_complete": None, "note": "", "opening": None, "evaluation": None, "award": None}
	return {**base, **over}


def opening(**over) -> dict:
	return {"opening_complete_at": DONE_AT, "outcome": "Bids opened", "status": "Complete", **over}


def evaluation(**over) -> dict:
	return {"case_state": "Reviewing", "no_evaluation_required": False, "report_sent_at": None, "opening_completed_at": DONE_AT, "outstanding": None, **over}


def award(**over) -> dict:
	return {"stage": "Opinion", "received_at": datetime(2027, 6, 15, 9, 0), "decision_at": None, "decision_outcome": None, "decision_events": [], "award_amount": None,
		"award_amount_visible": True, "sent_to_contracting": False, "closed": False, "outstanding": None, "cancelled": False, **over}


def sentence(text: str) -> dict:
	return {"text": text, "holder": "Grace Wambui", "since": DONE_AT}


class TestBuckets(unittest.TestCase):
	def bucket(self, f: dict) -> str:
		return classify(f)["bucket"]

	def position(self, f: dict) -> str:
		return classify(f)["position"]

	# ----- preparation and open -----

	def test_every_preparation_status_is_preparation(self):
		for status in ("Draft", "Awaiting procurement approval", "Approved", "Publication authorised", "Requisition correction requested"):
			got = classify(facts(status, submission_deadline=FUTURE))
			self.assertEqual(got["bucket"], PREPARATION, status)
			self.assertTrue(got["position"].startswith("Tender preparation — "), got["position"])

	def test_the_owners_note_words_a_preparation_position_and_a_status_alone_does_not_invent_one(self):
		self.assertEqual(self.position(facts("Draft", note="supplier and contract requirements returned for correction")), "Tender preparation — supplier and contract requirements returned for correction")
		self.assertEqual(self.position(facts("Draft")), "Tender preparation — draft")
		self.assertEqual(self.position(facts("Publication authorised")), "Tender preparation — publication confirmation required")

	def test_published_open_before_the_deadline_is_open_for_bids(self):
		got = classify(facts("Published — open", submission_deadline=FUTURE))
		self.assertEqual((got["bucket"], got["position"]), (OPEN, "Open for bids"))

	def test_a_published_tender_with_no_recorded_deadline_stays_open(self):
		self.assertEqual(self.bucket(facts("Published — open", submission_deadline=None)), OPEN)

	def test_a_deadline_that_passed_before_the_hourly_job_closed_the_tender_is_not_open_for_bids(self):
		# overall_status still reads Published — open: the job lags (FU-ANL-15)
		got = classify(facts("Published — open"))
		self.assertEqual(got["bucket"], OPENING)
		self.assertTrue(got["position"].startswith("Opening — "), got["position"])

	def test_the_deadline_instant_itself_has_closed_the_tender(self):
		self.assertEqual(self.bucket(facts("Published — open", submission_deadline=AT)), OPENING)
		self.assertEqual(self.bucket(facts("Published — open", submission_deadline=AT + timedelta(seconds=1))), OPEN)

	# ----- opening -----

	def test_submission_closed_with_no_opening_case_yet_is_opening(self):
		self.assertEqual(self.bucket(facts()), OPENING)

	def test_opening_in_every_unfinished_state_is_opening_in_the_owners_words(self):
		# the owner's own status texts (`bid_opening.stage_summary.STATUS`); an unfinished opening has no outcome
		for state, phrase in (("Awaiting deadline", "awaiting deadline"), ("Ready to open", "ready to open"), ("In session", "in session"), ("Paused", "paused"), ("Awaiting attestations", "awaiting attestations"), ("Did not take place", "did not take place")):
			got = classify(facts(opening={"opening_complete_at": None, "outcome": None, "status": state}))
			self.assertEqual((got["bucket"], got["position"]), (OPENING, f"Opening — {phrase}"), state)

	def test_a_completed_package_awaiting_evaluation_receipt_is_opening(self):
		got = classify(facts(opening=opening()))
		self.assertEqual((got["bucket"], got["position"]), (OPENING, "Opening — complete; awaiting Evaluation receipt"))

	def test_an_evaluation_case_that_exists_before_the_opening_is_not_evaluation(self):
		# the case is prepared from the publication; it has no Opening receipt yet
		pending = facts(opening={"opening_complete_at": None, "outcome": None, "status": "In session"}, evaluation=evaluation(case_state="Preparing", opening_completed_at=None))
		self.assertEqual(self.bucket(pending), OPENING)
		complete_not_received = facts(opening=opening(), evaluation=evaluation(case_state="Preparing", opening_completed_at=None))
		self.assertEqual(self.bucket(complete_not_received), OPENING)

	# ----- closed without a decision -----

	def test_an_empty_opening_closes_the_tender_with_no_evaluation_required(self):
		got = classify(facts(opening={"opening_complete_at": None, "outcome": "No bids", "status": "Complete"}))
		self.assertEqual((got["bucket"], got["outcome"]), (CLOSED, "no_bids"))
		self.assertEqual(got["position"], "Closed — no bids received; no evaluation required")

	def test_an_opening_with_no_outcome_yet_is_still_opening_even_if_it_will_be_empty(self):
		self.assertEqual(self.bucket(facts(opening={"opening_complete_at": None, "outcome": None, "status": "Readout complete"})), OPENING)

	def test_evaluation_saying_no_evaluation_required_closes_the_tender(self):
		got = classify(facts(opening=opening(), evaluation=evaluation(case_state="No evaluation required", no_evaluation_required=True)))
		self.assertEqual((got["bucket"], got["outcome"]), (CLOSED, "no_evaluation"))

	# ----- evaluation -----

	def test_evaluation_confirming_the_opening_receipt_is_evaluation_in_its_own_words(self):
		got = classify(facts(opening=opening(), evaluation=evaluation(outstanding=sentence("Automatic checks complete; committee review outstanding. Grace Wambui chairs the appointed committee."))))
		self.assertEqual((got["bucket"], got["position"]), (EVALUATION, "Evaluation — automatic checks complete; committee review outstanding"))

	def test_an_owner_supplied_position_is_used_as_given(self):
		got = classify(facts(opening=opening(), evaluation=evaluation(position="Review and signing under way", outstanding=sentence("Something else."))))
		self.assertEqual(got["position"], "Evaluation — review and signing under way")

	def test_evaluation_without_owner_text_falls_back_to_its_case_state_only(self):
		self.assertEqual(self.position(facts(opening=opening(), evaluation=evaluation(case_state="Signing"))), "Evaluation — signing")

	def test_a_delivered_report_awaiting_award_receipt_is_shown_as_such_and_stays_in_evaluation(self):
		for award_facts in (None, award(received_at=None)):
			got = classify(facts(opening=opening(), evaluation=evaluation(case_state="Report sent", report_sent_at=DONE_AT), award=award_facts))
			self.assertEqual((got["bucket"], got["position"]), (EVALUATION, "Evaluation report delivered — Award receipt pending"))

	# ----- award and contract -----

	def test_award_confirming_receipt_is_award_at_each_working_stage(self):
		for stage in ("Opinion", "Decision", "Notices", "Waiting to proceed"):
			f = facts(opening=opening(), evaluation=evaluation(case_state="Report sent", report_sent_at=DONE_AT), award=award(stage=stage))
			self.assertEqual(self.bucket(f), AWARD, stage)

	def test_award_uses_the_owners_wording_for_its_outstanding_matter(self):
		f = facts(opening=opening(), evaluation=evaluation(case_state="Report sent", report_sent_at=DONE_AT), award=award(stage="Opinion", outstanding=sentence("Awaiting professional opinion by Charles Mutiso.")))
		self.assertEqual(self.position(f), "Award — awaiting professional opinion by Charles Mutiso")

	def test_a_decided_tender_with_notices_still_to_go_stays_in_award(self):
		f = facts(opening=opening(), evaluation=evaluation(case_state="Report sent", report_sent_at=DONE_AT), award=award(
			stage="Notices", decision_at=datetime(2027, 6, 17, 11, 0), decision_outcome="Award", award_amount="7185000",
			outstanding=sentence("Award decision recorded. Required bidder notices are awaiting delivery.")))
		got = classify(f)
		self.assertEqual((got["bucket"], got["position"]), (AWARD, "Award — required bidder notices are awaiting delivery"))

	def test_a_department_reader_gets_no_award_working_wording_only_the_recorded_decision(self):
		# OVS-CHG-001 v0.6 §4.1: no professional opinion, no unissued notices
		delivered = dict(opening=opening(), evaluation=evaluation(case_state="Report sent", report_sent_at=DONE_AT))
		pending = facts(**delivered, department=True, award=award(stage="Opinion", outstanding=sentence("Awaiting professional opinion by Charles Mutiso.")))
		self.assertEqual(classify(pending)["position"], "Award")
		decided = facts(**delivered, department=True, award=award(
			stage="Notices", decision_at=datetime(2027, 6, 17, 11, 0), decision_outcome="Award", outstanding=sentence("Award decision recorded. Required bidder notices are awaiting delivery.")))
		got = classify(decided)
		self.assertEqual((got["bucket"], got["position"]), (AWARD, "Award — decision recorded"))
		# the same facts for a site-wide reader keep the owner's wording
		self.assertEqual(classify({**decided, "department": False})["position"], "Award — required bidder notices are awaiting delivery")
		# Evaluation's administrative progress is unchanged for a department reader
		reviewing = facts(opening=opening(), department=True, evaluation=evaluation(outstanding=sentence("Automatic checks complete; committee review outstanding. Grace Wambui chairs the appointed committee.")))
		self.assertEqual(classify(reviewing)["position"], "Evaluation — automatic checks complete; committee review outstanding")

	def test_award_receipt_places_the_tender_in_award_even_if_the_evaluation_row_has_not_caught_up(self):
		f = facts(opening=opening(), evaluation=evaluation(case_state="Signing", report_sent_at=None), award=award(stage="Decision"))
		self.assertEqual(self.bucket(f), AWARD)

	def test_delivery_to_contract_management_is_the_contract_bucket(self):
		for stage_facts in (award(stage="Sent to Contracting"), award(stage="Waiting to proceed", sent_to_contracting=True)):
			f = facts(opening=opening(), evaluation=evaluation(case_state="Report sent", report_sent_at=DONE_AT), award=stage_facts)
			got = classify(f)
			self.assertEqual((got["bucket"], got["position"]), (CONTRACT, "Sent to Contract Management"))

	# ----- closed -----

	def test_a_closed_no_award_cycle_keeps_its_exact_outcome(self):
		f = facts(opening=opening(), evaluation=evaluation(case_state="Report sent", report_sent_at=DONE_AT), award=award(stage="Closed", closed=True, decision_outcome="No award"))
		got = classify(f)
		self.assertEqual((got["bucket"], got["outcome"], got["position"]), (CLOSED, "no_award", "Closed — No award recorded"))

	def test_a_closed_decision_under_correction_keeps_the_recorded_outcome(self):
		f = facts(opening=opening(), evaluation=evaluation(case_state="Report sent", report_sent_at=DONE_AT), award=award(stage="Closed", closed=True, decision_outcome="Award"))
		self.assertEqual(self.position(f), "Closed — Award decision recorded")

	def test_an_award_case_closed_by_cancellation_is_closed(self):
		f = facts(opening=opening(), evaluation=evaluation(case_state="Report sent", report_sent_at=DONE_AT), award=award(stage="Closed", closed=True, cancelled=True))
		self.assertEqual(classify(f)["outcome"], "cancelled")

	def test_cancellation_takes_precedence_over_a_retained_report_and_decision(self):
		retained = facts("Cancelled", cancelled=True, opening=opening(), evaluation=evaluation(case_state="Report sent", report_sent_at=DONE_AT),
			award=award(stage="Notices", decision_outcome="Award", decision_at=DONE_AT))
		got = classify(retained)
		self.assertEqual((got["bucket"], got["outcome"]), (CLOSED, "cancelled"))
		self.assertEqual(got["position"], "Closed — cancelled")

	def test_a_cancellation_recorded_before_the_status_caught_up_still_wins(self):
		self.assertEqual(self.bucket(facts("Published — open", submission_deadline=FUTURE, cancelled=True)), CLOSED)

	def test_cancellation_wording_states_the_compliance_evidence_only_when_known(self):
		self.assertEqual(self.position(facts("Cancelled", cancellation_complete=True)), "Closed — cancelled; cancellation compliance evidence complete")
		self.assertEqual(self.position(facts("Cancelled", cancellation_complete=False)), "Closed — cancelled; cancellation compliance evidence outstanding")
		self.assertEqual(self.position(facts("Cancelled")), "Closed — cancelled")

	def test_a_failed_stage_read_does_not_unclose_a_cancelled_tender(self):
		self.assertEqual(self.bucket(facts("Cancelled", opening=FAILED, evaluation=FAILED, award=FAILED)), CLOSED)

	# ----- unavailable -----

	def test_a_failed_opening_read_is_status_unavailable(self):
		got = classify(facts(opening=FAILED))
		self.assertEqual((got["bucket"], got["position"]), (UNAVAILABLE, "Status unavailable"))

	def test_a_failed_evaluation_read_is_unavailable_once_the_opening_is_complete(self):
		self.assertEqual(self.bucket(facts(opening=opening(), evaluation=FAILED)), UNAVAILABLE)

	def test_a_failed_award_read_is_unavailable_once_the_report_is_delivered(self):
		f = facts(opening=opening(), evaluation=evaluation(case_state="Report sent", report_sent_at=DONE_AT), award=FAILED)
		self.assertEqual(self.bucket(f), UNAVAILABLE)

	def test_a_failed_read_that_the_classification_does_not_need_is_ignored(self):
		# no award can have been received before a report is delivered; an empty opening needs no evaluation or award
		self.assertEqual(self.bucket(facts(opening=opening(), evaluation=evaluation(), award=FAILED)), EVALUATION)
		self.assertEqual(self.bucket(facts(opening={"opening_complete_at": None, "outcome": "No bids", "status": "Complete"}, evaluation=FAILED, award=FAILED)), CLOSED)
		self.assertEqual(self.bucket(facts(opening={"opening_complete_at": None, "outcome": None, "status": "In session"}, evaluation=FAILED, award=FAILED)), OPENING)

	def test_an_evaluation_cancelled_under_a_live_tender_cannot_be_explained_so_it_is_unavailable(self):
		self.assertEqual(self.bucket(facts(opening=opening(), evaluation=evaluation(case_state="Cancelled"))), UNAVAILABLE)

	def test_an_unknown_tender_status_is_unavailable_and_never_guessed(self):
		self.assertEqual(self.bucket(facts("Something new")), UNAVAILABLE)
		self.assertEqual(self.bucket(facts("")), UNAVAILABLE)

	# ----- one bucket, always -----

	def test_every_classification_lands_in_exactly_one_known_bucket(self):
		stage_pairs = [
			facts("Draft"), facts("Published — open", submission_deadline=FUTURE), facts(), facts(opening=FAILED), facts(opening=opening()), facts(opening=opening(), evaluation=evaluation()),
			facts(opening=opening(), evaluation=evaluation(case_state="Report sent", report_sent_at=DONE_AT)),
			facts(opening=opening(), evaluation=evaluation(case_state="Report sent", report_sent_at=DONE_AT), award=award()),
			facts(opening=opening(), evaluation=evaluation(case_state="Report sent", report_sent_at=DONE_AT), award=award(stage="Sent to Contracting")),
			facts(opening=opening(), evaluation=evaluation(case_state="Report sent", report_sent_at=DONE_AT), award=award(stage="Closed", closed=True)),
			facts("Cancelled"),
		]
		seen = {self.bucket(f) for f in stage_pairs}
		self.assertTrue(seen <= set(BUCKETS))
		self.assertEqual(seen, {PREPARATION, OPEN, OPENING, EVALUATION, AWARD, CONTRACT, CLOSED, UNAVAILABLE})
		for f in stage_pairs:
			got = classify(f)
			self.assertEqual(set(got), {"bucket", "position", "outcome"})
			self.assertTrue(got["position"])

	# ----- which tenders the owners are asked about -----

	def test_stage_owners_are_asked_only_once_submission_has_closed_or_the_tender_is_cancelled(self):
		self.assertFalse(needs_stage_reads(facts("Draft")))
		self.assertFalse(needs_stage_reads(facts("Publication authorised")))
		self.assertFalse(needs_stage_reads(facts("Published — open", submission_deadline=FUTURE)))
		self.assertTrue(needs_stage_reads(facts("Published — open")))
		self.assertTrue(needs_stage_reads(facts("Submission period ended")))
		self.assertTrue(needs_stage_reads(facts("Cancelled")))
		self.assertTrue(needs_stage_reads(facts("Approved", cancelled=True)))
