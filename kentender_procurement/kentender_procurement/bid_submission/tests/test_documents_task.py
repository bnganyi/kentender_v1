# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §10.8 BDS-DES-07 (plan Phase 11, slice 11.7): the
documents task read gives the official documents, each effective addendum
with this bid's acknowledgement and — while it is not delivered — the
notice to the candidate's Tender notice email, the public answers with their
notice result, whether a question may still be asked, the badge only while
there is something to acknowledge, and whether Save and continue waits. The
acknowledgement is saved through `SaveBidTask`; a read acknowledges nothing."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_submission.services import reads, start_bid
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, BidCase, key
from kentender_procurement.bid_submission.tests.test_addendum_refresh import AddendumCase

BLOCKED = "Acknowledge the addendum to continue."


def documents(bid):
	return reads.get_bid_task(bid_reference=bid, task="documents", user=DAVID)


class TestWithoutAddendum(BidCase):
	def test_nothing_to_acknowledge_means_no_badge_and_an_open_footer(self):
		bid = start_bid.start_bid(tender_reference=self.reference, organisation=AFYA, arrangement=self.single(), notice_contact_id=f"{AFYA}-C1", idempotency_key=key(), user=DAVID)["bid_reference"]
		view = documents(bid)
		self.assertEqual(view["page"]["title"], "Tender documents, clarifications and addenda")
		self.assertEqual((view["badge"], view["addenda"], view["footer"]["blocked_text"]), (None, [], ""))
		self.assertEqual(view["footer"]["next_href"], f"/tenders/{self.reference}/bid/company")
		self.assertTrue(view["documents"] and all(d["view_href"].endswith("&inline=1") and "inline" not in d["download_href"] for d in view["documents"]), view["documents"])
		self.assertEqual(view["page"]["back_href"], f"/tenders/{self.reference}/bid")
		self.assertIn(view["notice_contact"]["current"], [o["contact_id"] for o in view["notice_contact"]["options"]])


class TestWithAddendum(AddendumCase):
	def test_an_effective_addendum_waits_for_this_bids_acknowledgement(self):
		name = self.issue_addendum()
		reference = frappe.db.get_value("Tender Addendum", name, "addendum_reference")
		self.at("2027-06-01 12:05:00")
		view = documents(self.bid)
		addendum = next(a for a in view["addenda"] if a["reference"] == reference)
		self.assertEqual((view["badge"], view["footer"]["blocked_text"]), ({"label": "Needs attention", "tone": "attention"}, BLOCKED))
		self.assertIsNone(addendum["notice"])  # delivered: nothing to warn about
		self.assertEqual(addendum["revised_deadline"], "12 Jun 2027, 11:00 EAT")
		ack = addendum["acknowledgement"]
		self.assertFalse(ack["value"])
		self.assertIn(reference, ack["label"])
		self.assertTrue(addendum["view_href"] and addendum["download_href"])

		self.assertEqual((ack["handle"], ack["moves_bid"]), ("", True))  # the Draft is still bound to the earlier definition

		# the first save moves the bid to the current definition; then the acknowledgement saves
		self.at("2027-06-01 12:10:00")
		moved = self.save("documents", {})
		self.assertEqual((moved["ok"], moved["code"], moved["refreshed"]), (False, "BDS_ADDENDUM_REVIEW_REQUIRED", True))
		ack = next(a for a in documents(self.bid)["addenda"] if a["reference"] == reference)["acknowledgement"]
		self.assertEqual((bool(ack["handle"]), ack["moves_bid"], ack["value"]), (True, False, False))
		saved = self.save("documents", {ack["handle"]: True})
		self.assertTrue(saved["ok"], saved)
		after = documents(self.bid)
		ack = next(a for a in after["addenda"] if a["reference"] == reference)["acknowledgement"]
		self.assertEqual((ack["value"], ack["acknowledged_text"]), (True, "Acknowledged by David Ouma on 1 Jun 2027, 12:10 EAT"))
		self.assertEqual((after["badge"]["label"], after["footer"]["blocked_text"]), ("Complete", ""))

	def test_a_failed_notice_is_named_and_offers_only_a_verified_email(self):
		self._flag("kt_tenders_notice_transport", lambda notice: {"result": "Failed", "provider_reference": "", "failure_reason": "Mailbox unavailable"})
		name = self.issue_addendum()
		reference = frappe.db.get_value("Tender Addendum", name, "addendum_reference")
		self.at("2027-05-31 09:15:00")
		view = documents(self.bid)
		notice = next(a for a in view["addenda"] if a["reference"] == reference)["notice"]
		self.assertEqual((notice["status"], notice["tone"], notice["can_update_contact"]), ("Delivery problem", "attention", True))
		self.assertEqual(notice["text"], "The notice could not be delivered to your selected Tender notice email. The current Tender information remains available here.")
		self.assertTrue(notice["destination"].startswith("Notice to "))
		self.assertNotIn("Mailbox unavailable", frappe.as_json(view))  # delivery internals stay with Tenders
		events = frappe.db.count("Bid Submission Event")
		documents(self.bid)
		self.assertEqual(frappe.db.count("Bid Submission Event"), events)


class TestDocumentsAddress(BidCase):
	def test_the_documents_address_is_the_organisations_own_bid(self):
		from kentender_procurement.bid_submission import portal
		from kentender_procurement.bid_submission.tests.support import PETER

		bid = start_bid.start_bid(tender_reference=self.reference, organisation=AFYA, arrangement=self.single(), notice_contact_id=f"{AFYA}-C1", idempotency_key=key(), user=DAVID)["bid_reference"]
		path = f"/tenders/{self.reference}/bid/documents"
		self.assertEqual(portal.resolve(path=path, query={}, user="Guest")["verdict"], "SIGN_IN")
		mine = portal.resolve(path=path, query={}, user=DAVID)
		self.assertEqual((mine["payload"]["screen"], mine["payload"]["data"]["bid"]["reference"]), ("documents-task", bid))
		masked = portal.resolve(path=path, query={}, user=PETER)
		self.assertEqual((masked["verdict"], masked["payload"]["screen"]), ("NOT_FOUND", "not-found"))
		self.assertEqual(portal.resolve(path=f"/tenders/{self.reference}/bid/price", query={}, user=DAVID)["verdict"], "NOT_FOUND")  # a later slice
