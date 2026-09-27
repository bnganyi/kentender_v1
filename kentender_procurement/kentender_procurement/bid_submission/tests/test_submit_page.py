# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §10.13 BDS-DES-12 (plan Phase 11, slice 11.12): the Submit
page states the consequence, the trusted server time, the submission summary,
the signatory with the certificate, and the final confirmation — offered only
when `SubmitBid`'s own checks pass. The production switch, a signing or
custody outage, a missing certificate, missing portal information, a
definite rejection and an uncertain attempt each have their own state and
none offers Submit. Viewing it changes nothing."""

from __future__ import annotations

from unittest import mock

import frappe

from kentender_procurement.bid_submission import portal
from kentender_procurement.bid_submission.services import reads, simulation
from kentender_procurement.bid_submission.test_services import trust
from kentender_procurement.bid_submission.tests.support import DAVID, MARY, PETER
from kentender_procurement.bid_submission.tests.test_submission import SubmissionCase


def labels(rows):
	return [r["label"] for r in rows]


class SubmitPageCase(SubmissionCase):
	def page(self, user=MARY):
		return reads.get_submit_page(tender_reference=self.reference, user=user)


class TestReadyToSubmit(SubmitPageCase):
	def test_the_signatory_reads_the_final_act(self):
		before = frappe.db.get_value("Bid Workspace", self.bid, ["record_version", "last_saved_at"])
		view = self.page()
		base = f"/tenders/{self.reference}/bid"
		self.assertEqual(
			(view["page"]["title"], view["page"]["description"], view["page"]["back_href"], view["page"]["back_label"]),
			("Submit bid", "Digitally sign and place this bid in the electronic tender box.", f"{base}/review", "Back to review"),
		)
		self.assertEqual(view["consequence"]["tone"], "warning")
		self.assertTrue(view["consequence"]["text"].startswith("After submission, this Version cannot be edited. You may prepare a replacement or withdraw it before "))
		self.assertEqual(labels(view["meta"]), ["Current server time", "Submission deadline"])
		self.assertEqual(labels(view["summary"]), ["Tender", "Bidder", "Bid", "Bid total", "Current deadline", "Addendum acknowledged", "Tender-security physical receipt"])
		self.assertEqual(labels(view["signatory"]), ["Signatory", "Job title", "Authority evidence", "Digital certificate"])
		self.assertEqual(view["signatory"][-1]["status"], {"label": "Ready", "tone": "live"})
		decision = view["decision"]
		self.assertEqual((decision["kind"], decision["submit_label"]), ("confirm", "Submit bid"))
		self.assertTrue(decision["confirmation"].startswith("I confirm that the information, declarations and evidence in this bid are correct"), decision)
		self.assertEqual((view["dialog"]["title"], labels(view["dialog"]["facts"])), ("Submit this bid?", ["Tender", "Bidder", "Bid total", "Deadline"]))
		self.assertIsNone(view["notice"])
		self.assertIsNone(view["action"])
		self.assertNotIn("review_bid", [f.get("fix_id") for f in view["next_step"]["fixes"]])
		self.assertEqual((view["bid"]["reference"], view["bid"]["record_version"], view["replaces"]), (self.bid, self.version(), ""))
		self.assertEqual(frappe.db.get_value("Bid Workspace", self.bid, ["record_version", "last_saved_at"]), before)

	def test_the_route_serves_the_page_and_masks_another_organisation(self):
		mine = portal.resolve(path=f"/tenders/{self.reference}/bid/submit", query={}, user=MARY)
		self.assertEqual((mine["verdict"], mine["payload"]["screen"]), ("OK", "submit"))
		masked = portal.resolve(path=f"/tenders/{self.reference}/bid/submit", query={}, user=PETER)
		self.assertEqual(masked["verdict"], "NOT_FOUND")

	def test_the_representative_is_not_offered_submit(self):
		view = self.page(user=DAVID)
		self.assertIsNone(view["decision"])
		self.assertTrue(view["next_step"]["headline"].endswith("must submit this bid."), view["next_step"])


class TestBlockedSubmit(SubmitPageCase):
	def test_each_operating_state_has_its_own_notice_and_no_submit(self):
		base = f"/tenders/{self.reference}/bid"
		worlds = {
			"gate_closed": ("Electronic bid submission is not available yet", ["Supplier support"], {"label": "Back to bid", "href": base, "tone": "secondary"}),
			"trust_service_down": ("Digital signing is temporarily unavailable", ["Supplier support"], None),
			"custody_service_down": ("Electronic submission is temporarily unavailable", ["View status", "Supplier support"], None),
		}
		for control, (title, links, action) in worlds.items():
			with self.subTest(control=control):
				simulation.set_controls(**{control: 1})
				view = self.page()
				simulation.reset_controls()
				self.assertEqual((view["notice"]["tone"], view["notice"]["title"]), ("critical", title))
				self.assertEqual(labels(view["notice"]["links"]), links)
				self.assertEqual(view["action"], action)
				self.assertIsNone(view["decision"])
				self.assertIsNone(view["consequence"])
				self.assertEqual(view["next_step"]["kind"], "waiting")

	def test_a_missing_certificate_asks_for_one(self):
		trust.revoke_certificate(self.certificate)
		view = self.page()
		self.assertIsNone(view["decision"])
		self.assertEqual(view["signatory"][-1]["status"], {"label": "Not available", "tone": "critical"})
		self.assertEqual([f["label"] for f in view["next_step"]["fixes"]], ["Check certificate"])
		self.assertEqual(view["next_step"]["sentence"], "Your bid remains saved and has not been submitted. Supplier support can explain the process but cannot waive it.")
		self.assertIsNone(view["consequence"])

	def test_missing_portal_information_waits_and_keeps_saved_work(self):
		with mock.patch("kentender_core.services.public_portal.get_public_portal_information", return_value={"status": "Incomplete"}):
			view = self.page()
		self.assertEqual(view["action"], {"label": "Continue saved bid", "href": f"/tenders/{self.reference}/bid", "tone": "secondary"})
		self.assertEqual(view["next_step"]["sentence"], "Saved work and receipts remain available while required supplier portal information is restored.")
		self.assertIsNone(view["decision"])

	def test_a_definite_rejection_offers_a_new_confirmation(self):
		simulation.set_controls(deposit_outcome="Reject", rejection_reference="TBX-REJECT-033-01")
		result = self.submit(self.signed())
		simulation.reset_controls()
		self.assertEqual(result["code"], "BDS_CUSTODY_REJECTED")
		view = self.page()
		self.assertEqual(view["next_step"]["headline"], "The tender box rejected this attempt; no bid was submitted.")
		self.assertEqual(view["next_step"]["sentence"], "Reference TBX-REJECT-033-01. Your bid remains saved and was not submitted.")
		self.assertEqual([f["label"] for f in view["next_step"]["fixes"]], ["Try confirmation again", "Contact support"])
		self.assertIsNone(view["decision"])

	def test_an_uncertain_attempt_is_pending_with_view_status_and_no_new_submit(self):
		simulation.set_controls(deposit_outcome="Uncertain")
		pending = self.submit(self.signed())
		simulation.reset_controls()
		self.assertEqual(pending["code"], "BDS_SUBMISSION_UNCERTAIN")
		view = self.page()
		decision = view["decision"]
		self.assertEqual((decision["kind"], decision["status_href"]), ("pending", f"/tenders/{self.reference}/bid/status"))
		self.assertEqual(decision["text"], "We are checking this submission attempt. You may leave and return through View status. Do not submit again while this attempt is pending.")
		self.assertEqual(view["consequence"]["tone"], "warning")
		headline = view["next_step"]["headline"]
		self.assertTrue(headline.startswith("Technical operator ") and headline.endswith(" is checking the same submission attempt."), headline)
