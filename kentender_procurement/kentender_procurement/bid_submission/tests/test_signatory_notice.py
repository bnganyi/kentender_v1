# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Notify the Authorised Signatory (owner request, 2 Oct 2026). The person who
prepared the bid (David) cannot submit it, so he can tell the signatory (Mary)
that it is ready: a message by the supplier message transport with a link and
an optional note, recorded as an event, not more often than every ten minutes,
and only while the bid is ready and open. The signatory herself never needs it."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest import TestCase

import frappe

from kentender_procurement.bid_submission.services import reads, signatory_notice
from kentender_procurement.bid_submission.tests.support import DAVID, MARY, key
from kentender_procurement.bid_submission.tests.test_submission import SubmissionCase


class TestComposition(TestCase):
	def test_the_message_names_who_prepared_the_bid_what_it_is_and_where_to_open_it(self):
		subject, body = signatory_notice.compose(sender="David Ouma", tender_title="Supply of laptops", bid="BID-1", deadline_label="5 Jun 2027, 11:00 EAT", url="https://x.example/tenders/T/bid/review", note="")
		self.assertEqual(subject, "Bid ready for your signature: Supply of laptops")
		self.assertIn("David Ouma has finished preparing the bid BID-1 for Supply of laptops", body)
		self.assertIn("Submissions close 5 Jun 2027, 11:00 EAT.", body)
		self.assertIn('href="https://x.example/tenders/T/bid/review"', body)
		self.assertNotIn("<blockquote", body)

	def test_a_note_is_quoted_and_everything_typed_is_escaped(self):
		_subject, body = signatory_notice.compose(sender="<b>D</b>", tender_title="T & Co", bid="BID-1", deadline_label="d", url="u", note="Please sign <script>alert(1)</script> today")
		self.assertIn("<blockquote>Please sign &lt;script&gt;alert(1)&lt;/script&gt; today</blockquote>", body)
		self.assertIn("&lt;b&gt;D&lt;/b&gt;", body)
		self.assertNotIn("<script>", body)
		self.assertIn("T &amp; Co", body)

	def test_another_notice_is_allowed_ten_minutes_after_the_last(self):
		last = datetime(2027, 5, 20, 11, 0)
		self.assertEqual(signatory_notice.next_allowed(last), last + timedelta(minutes=10))
		self.assertIsNone(signatory_notice.next_allowed(None))


class TestNotifyTheSignatory(SubmissionCase):
	def setUp(self):
		super().setUp()
		self.sent: list[dict] = []
		self._flag("kt_bds_message_transport", lambda message: self.sent.append(message) or {"result": "Sent"})
		self.at("2027-05-20 11:00:00")

	def notify(self, user=DAVID, note="", **kw):
		return signatory_notice.notify_signatory(bid_reference=self.bid, note=note, idempotency_key=kw.pop("request_key", key()), user=user, **kw)

	def events(self):
		return frappe.get_all("Bid Submission Event", filters={"bid_workspace": self.bid, "event_type": "SignatoryNotified"}, fields=["actor", "payload_json"], order_by="creation asc")

	def test_the_preparer_notifies_the_signatory_with_a_link_and_a_note(self):
		result = self.notify(note="Please sign before Friday.")
		self.assertEqual((result["ok"], result["recipients"]), (True, ["Mary Wanjiku"]))
		self.assertEqual([m["to"] for m in self.sent], [MARY])
		message = self.sent[0]
		self.assertTrue(message["subject"].startswith("Bid ready for your signature: "))
		self.assertIn("David Ouma has finished preparing the bid", message["body"])
		self.assertIn("Please sign before Friday.", message["body"])
		self.assertIn(f"/tenders/{self.reference}/bid/review", message["body"])
		self.assertEqual([e.actor for e in self.events()], [DAVID])
		self.assertIn("Please sign before Friday.", self.events()[0].payload_json)

	def test_the_workspace_read_says_who_can_be_notified_and_when_they_last_were(self):
		before = reads.get_bid_workspace(bid_reference=self.bid, user=DAVID)["handover"]
		self.assertEqual((before["signatories"], before["can_notify"], before["last"]), (["Mary Wanjiku"], True, None))
		self.notify()
		after = reads.get_bid_workspace(bid_reference=self.bid, user=DAVID)["handover"]
		self.assertEqual(after["last"]["by"], "David Ouma")
		self.assertTrue(after["last"]["at_label"])
		self.assertFalse(after["can_notify"])  # not again within ten minutes
		self.assertIn("after", after["wait_text"])
		self.assertNotIn("handover", reads.get_bid_workspace(bid_reference=self.bid, user=MARY))  # she is the one it is for

	def test_a_second_notice_within_ten_minutes_is_refused_and_after_ten_it_goes(self):
		self.notify()
		again = self.notify()
		self.assertFalse(again["ok"])
		self.assertIn("You can send another reminder after", again["errors"]["notify"])
		self.assertEqual(len(self.sent), 1)
		self.at("2027-05-20 11:11:00")
		self.assertTrue(self.notify()["ok"])
		self.assertEqual(len(self.sent), 2)

	def test_the_same_request_is_not_sent_twice(self):
		request = key()
		first = self.notify(request_key=request)
		second = self.notify(request_key=request)
		self.assertEqual(first, second)
		self.assertEqual(len(self.sent), 1)

	def test_every_task_page_carries_the_hand_over_wherever_the_waiting_line_shows(self):
		for task in ("documents", "company", "requirements", "price", "review"):
			page = reads.get_bid_task(bid_reference=self.bid, task=task, user=DAVID)
			self.assertEqual(page["handover"]["signatories"], ["Mary Wanjiku"], task)
			self.assertNotIn("handover", reads.get_bid_task(bid_reference=self.bid, task=task, user=MARY), task)

	def test_the_signatory_has_no_need_to_notify_herself(self):
		result = self.notify(user=MARY)
		self.assertFalse(result["ok"])
		self.assertIn("You are the Authorised Signatory", result["errors"]["notify"])
		self.assertEqual(self.sent, [])

	def test_a_bid_that_is_not_ready_cannot_be_handed_over(self):
		frappe.db.set_value("Bid Workspace", self.bid, "status", "Draft")
		result = self.notify()
		self.assertFalse(result["ok"])
		self.assertIn("Finish the bid first", result["errors"]["notify"])
		self.assertNotIn("handover", reads.get_bid_workspace(bid_reference=self.bid, user=DAVID))

	def test_a_note_longer_than_five_hundred_characters_is_refused(self):
		result = self.notify(note="x" * 501)
		self.assertFalse(result["ok"])
		self.assertIn("500", result["errors"]["note"])
		self.assertEqual(self.sent, [])

	def test_after_the_deadline_nothing_is_sent(self):
		self.at("2027-07-01 12:00:00")
		with self.assertRaises(Exception):
			self.notify()
		self.assertEqual(self.sent, [])
