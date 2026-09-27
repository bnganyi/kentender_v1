# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §10.3, §11.2 (plan Phase 11, slice 11.2): the Tender
overview gives each viewer the one action that fits — Sign in to start bid,
Start bid (with the "Who is bidding?" choices), Continue bid, View receipt —
from the server; another organisation's bid is never visible; the production
gate's notice promises nothing; a read creates nothing."""

from __future__ import annotations

import json

import frappe

from kentender_procurement.bid_submission.services import overview, start_bid
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, MARY, PETER, key
from kentender_procurement.bid_submission.tests.test_changes_and_close import ChangeCase


class TestTenderOverview(ChangeCase):
	def view(self, user, **kw):
		return overview.get_tender_overview(tender_reference=self.reference, user=user, **kw)

	def test_each_viewer_gets_the_action_that_fits_and_no_other_bid(self):
		# the submission case world: Afya (David, Mary) holds a ready Draft
		guest = self.view("Guest")
		self.assertEqual((guest["action"]["kind"], guest["bid"], guest["organisation"]), ("sign_in", None, None))
		self.assertEqual(guest["action"]["href"], f"/login?redirect-to=/tenders/{self.reference}")
		self.assertTrue(guest["documents"] and all(d["view_href"].startswith("/api/method/") for d in guest["documents"]))
		david = self.view(DAVID)
		self.assertEqual((david["action"]["kind"], david["bid"]["bid_reference"], david["bid"]["status_text"]), ("continue_bid", self.bid, "Ready to submit"))
		self.assertTrue(david["clarification"]["can_ask"] if david["tender"]["clarifications_open"] else True)
		peter = self.view(PETER)
		self.assertEqual((peter["action"]["kind"], peter["bid"]), ("start_bid", None))
		self.assertNotIn(self.bid, json.dumps(peter))
		self.assertNotIn("Afya", json.dumps(peter))
		self.assertEqual(peter["start"]["notice_contacts"][0]["value"], "tenders@kisiwadigital.example")
		self.assertIn("Single organisation", peter["start"]["arrangements"])
		# submitted: View receipt with the accepted time
		receipt = self.submitted()
		mary = self.view(MARY)
		self.assertEqual((mary["action"]["kind"], mary["bid"]["receipt_reference"]), ("view_receipt", receipt))
		self.assertTrue(mary["bid"]["status_text"].startswith("Submitted "))

	def test_the_gate_notice_and_a_read_that_creates_nothing(self):
		frappe.conf["production_bid_submission_enabled"] = 0
		notice = self.view(PETER)["notice"]
		self.assertEqual(notice["title"], "Electronic bid submission is not available yet")
		self.assertNotIn("temporar", notice["text"].lower())
		counts = {d: frappe.db.count(d) for d in ("Bidder Arrangement", "Bid Workspace", "Bid Submission Event")}
		self.view(PETER)
		self.view("Guest")
		self.assertEqual({d: frappe.db.count(d) for d in counts}, counts)
		with self.assertRaises(frappe.DoesNotExistError):
			overview.get_tender_overview(tender_reference="TND-NOPE-0000-000", user=PETER)
