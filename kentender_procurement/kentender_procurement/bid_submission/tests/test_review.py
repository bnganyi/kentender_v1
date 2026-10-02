# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §5.3, §5.7 items 1–2 and §7.1 `GetBidReview` (plan
Phase 6, BDS8-601): the review states the result first and lists every Must
fix and Review note with its task and field; a bidder's own non-compliance
is a note, not a blocker; viewing it changes nothing."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_submission.services import reads, save, start_bid
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, BidCase, fill_everything, key, simulation_on


class TestBidReview(BidCase):
	def setUp(self):
		super().setUp()
		simulation_on(self)
		self.bid = start_bid.start_bid(tender_reference=self.reference, organisation=AFYA, arrangement=self.single(), notice_contact_id=f"{AFYA}-C1", idempotency_key=key(), user=DAVID)["bid_reference"]

	def test_a_new_bid_lists_what_to_fix_by_task_and_field(self):
		before = frappe.db.get_value("Bid Workspace", self.bid, ["record_version", "last_saved_at"])
		review = reads.get_bid_review(bid_reference=self.bid, user=DAVID)
		self.assertEqual(review["ready"], False)
		self.assertEqual({i["task"] for i in review["must_fix"]}, {"company", "requirements", "price"})
		first = review["must_fix"][0]
		view = reads.get_bid_task(bid_reference=self.bid, task=first["task"], user=DAVID)
		self.assertIn(first["handle"], {f["handle"] for g in view["groups"] for f in g["fields"]})
		self.assertEqual(frappe.db.get_value("Bid Workspace", self.bid, ["record_version", "last_saved_at"]), before)

	def test_a_complete_bid_is_ready_and_a_non_compliance_is_only_a_note(self):
		fill_everything(self.bid)
		self.assertEqual((reads.get_bid_review(bid_reference=self.bid, user=DAVID)["ready"], reads.get_bid_review(bid_reference=self.bid, user=DAVID)["must_fix"]), (True, []))
		view = reads.get_bid_task(bid_reference=self.bid, task="requirements", user=DAVID)
		# a truthful non-compliance: "Do not comply" beside a value that really falls short (beside one that meets the
		# requirement it would contradict itself and be a Must fix: test_compliance_consistency)
		group = next(g for g in view["groups"] if any(f["label"] == "Compliance" for f in g["fields"]))
		compliance = next(f for f in group["fields"] if f["label"] == "Compliance")
		offered = next(f for f in group["fields"] if f["label"] == "Offered value")
		self.assertEqual(offered["kind"], "yes_no")  # the first row (electrical compatibility) requires Yes
		version = frappe.db.get_value("Bid Workspace", self.bid, "record_version")
		self.assertTrue(save.save_bid_task(bid_reference=self.bid, task="requirements", values={compliance["handle"]: "Do not comply", offered["handle"]: "No"}, expected_record_version=version, idempotency_key=key(), user=DAVID)["ok"])
		review = reads.get_bid_review(bid_reference=self.bid, user=DAVID)
		self.assertEqual((review["ready"], review["must_fix"], [n["text"] for n in review["review_notes"]]), (True, [], ["You state that the offer does not meet this requirement.", "The physical tender-security original has not been recorded as received."]))
