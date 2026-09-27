# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §10.9 BDS-DES-08 (plan Phase 11, slice 11.8): the company
task read gives the bidding organisation as copied to the bid (and the two
choices once the Account has changed), the bid's Tender contact, one row per
form of the task in the definition's order with its state and who confirmed
it, the tender security with the physical original as this bid knows it, and
the Authorised Signatory with their certificate. A read saves nothing."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_submission.services import reads, start_bid
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, BidCase, key
from kentender_procurement.bid_submission.tests.test_submission import SubmissionCase


def company(bid, user=DAVID):
	return reads.get_bid_task(bid_reference=bid, task="company", user=user)


class TestCompleteCompanyTask(SubmissionCase):
	def test_the_complete_task_as_the_board_draws_it(self):
		view = company(self.bid)
		self.assertEqual((view["page"]["title"], view["badge"]), ("Company, declarations and tender security", {"label": "Complete", "tone": "live"}))
		org = view["organisation"]
		self.assertEqual([f["label"] for f in org["facts"]], ["Legal name", "Registration number", "KRA PIN", "Address", "Arrangement"])
		self.assertEqual((org["kind"], org["update"], org["current_text"]), ("single", None, "This bid is using your current Account details."))
		self.assertTrue(org["snapshot_text"].startswith("From your Account · copied to this bid on "))
		self.assertEqual((view["contact"]["phone"], view["contact"]["note"]), ("+254 709 555 015", "These values apply only to this bid."))
		rows = view["declarations"]
		self.assertTrue(rows and all(r["status"] in ("Complete", "Confirmed") for r in rows), [(r["label"], r["status"]) for r in rows])
		confirmed = [r for r in rows if r["status"] == "Confirmed"]
		self.assertTrue(confirmed and all(r["confirmed_text"] == "Confirmed by David Ouma" for r in confirmed))
		self.assertTrue(all(r["fields"] for r in rows))
		# each form by its own name (the product profile's names for the definition's form ids)
		labels = [r["label"] for r in rows]
		for name in ("Tenderer information", "Form of Tender", "Independent tender determination", "Self-declaration — not debarred", "Self-declaration — no corrupt or fraudulent practice", "Code of ethics commitment"):
			self.assertIn(name, labels)
		self.assertNotIn("Declaration", labels)
		self.assertEqual(view["contact"]["assigned"], "David Ouma")
		notice = view["contact"]["notice"]
		self.assertIn(notice["current"], [o["contact_id"] for o in notice["options"]])  # verified Account emails only
		security = view["tender_security"]
		self.assertEqual((security["entered"], security["physical"]["tone"], security["physical"]["title"]), (True, "warning", "Physical original not yet recorded"))
		self.assertIn("You may submit electronically, but failure to deliver the original before closing may disqualify the bid.", security["physical"]["text"])
		self.assertEqual(view["signatory"]["name"], "Mary Wanjiku")
		self.assertEqual(view["signatory"]["certificate"]["status"], "Ready")
		self.assertEqual(view["footer"]["next_href"], f"/tenders/{self.reference}/bid/requirements")

	def test_a_changed_account_offers_its_two_choices_and_changes_nothing(self):
		self.accounts.orgs[AFYA]["registered_address"] = "Riverside Drive, Nairobi"
		events = frappe.db.count("Bid Submission Event")
		org = company(self.bid)["organisation"]
		self.assertEqual([r["label"] for r in org["update"]["rows"]], ["This bid", "Current Account"])
		self.assertEqual(org["update"]["rows"][1]["value"], "Riverside Drive, Nairobi")
		self.assertEqual((org["update"]["fact"], org["current_text"]), ("Address", ""))
		self.assertEqual(frappe.db.count("Bid Submission Event"), events)


class TestNewCompanyTask(BidCase):
	def test_a_new_bid_lists_every_form_not_started_and_no_security_yet(self):
		bid = start_bid.start_bid(tender_reference=self.reference, organisation=AFYA, arrangement=self.single(), notice_contact_id=f"{AFYA}-C1", idempotency_key=key(), user=DAVID)["bid_reference"]
		view = company(bid)
		self.assertNotEqual(view["badge"]["label"], "Complete")
		self.assertTrue(all(r["status"] in ("Not started", "In progress") for r in view["declarations"]), [(r["label"], r["status"]) for r in view["declarations"]])
		self.assertFalse(view["tender_security"]["entered"])
		self.assertEqual(view["contact"]["notice_email"] != "", True)
