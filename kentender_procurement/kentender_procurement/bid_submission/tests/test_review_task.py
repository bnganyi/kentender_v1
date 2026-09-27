# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §10.12 BDS-DES-11 (plan Phase 11, slice 11.11): the review
page states the computed result and the physical-original fact, the summary
of the bid, the five tasks with their exact issue links, what is offered, the
declarations and evidence, and the price summary. Submit bid is offered only
to the Authorised Signatory on a Ready bid while supplier portal information
is complete; the representative, a bid with something to fix and a bid
waiting on portal information see no Submit. Viewing it changes nothing."""

from __future__ import annotations

from unittest import mock

import frappe

from kentender_procurement.bid_submission.services import evidence, reads, security_intake, tender_security
from kentender_procurement.bid_submission.services.bid_context import load
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, MARY, fill_everything, key
from kentender_procurement.bid_submission.tests.test_addendum_refresh import AddendumCase
from kentender_procurement.bid_submission.tests.test_evidence import EICAR_PDF
from kentender_procurement.bid_submission.tests.test_submission import SubmissionCase
from kentender_procurement.tenders.tests import fixtures as tender_fx


def review(bid, user=MARY):
	return reads.get_bid_task(bid_reference=bid, task="review", user=user)


def facts(region):
	return {row["label"]: row["value"] for row in region}


class TestReadyReview(SubmissionCase):
	def test_the_signatory_reads_a_ready_bid_and_may_submit_it(self):
		before = frappe.db.get_value("Bid Workspace", self.bid, ["record_version", "last_saved_at"])
		view = review(self.bid)
		base = f"/tenders/{self.reference}/bid"
		self.assertEqual((view["page"]["title"], view["page"]["description"]), ("Review bid", "Check the complete bid before submitting it to the electronic tender box."))
		self.assertEqual(view["page"]["action"], {"label": "Submit bid", "href": f"{base}/submit", "tone": "primary"})
		self.assertEqual(view["result"], {"tone": "live", "text": "All required bid information is complete."})
		self.assertEqual([r["label"] for r in view["summary"]], ["Tender", "Bidder", "Bid", "Current deadline", "Signatory", "Bid total"])
		summary = facts(view["summary"])
		self.assertEqual(summary["Bid"], f"{self.bid} · Draft Version {frappe.db.get_value('Bid Workspace', self.bid, 'current_draft_version')}")
		self.assertTrue(summary["Bidder"].endswith(" · Single organisation"), summary["Bidder"])
		self.assertTrue(summary["Signatory"].startswith("Mary Wanjiku"), summary["Signatory"])
		self.assertTrue(summary["Bid total"].startswith("KES "))
		# the five tasks, each preparation task offering Review; nothing to fix
		self.assertEqual([r["key"] for r in view["task_rows"]], ["documents", "company", "requirements", "price", "review"])
		self.assertTrue(all(r["status"] == "Complete" and not r["issues"] for r in view["task_rows"]), view["task_rows"])
		self.assertEqual([r["href"] for r in view["task_rows"]], [f"{base}/{k}" for k in ("documents", "company", "requirements", "price")] + [""])
		# what is offered, from the definition's goods and warranty obligations
		offering = facts(view["offering"])
		self.assertEqual(list(offering), ["Offered model", "Quantity", "Delivery", "Warranty", "Support response"])
		self.assertTrue(all(offering.values()), offering)
		self.assertTrue(offering["Warranty"].endswith(" months") and offering["Support response"].endswith(" hours"), offering)
		declared = facts(view["declarations"])
		self.assertEqual(list(declared), ["Declarations", "Evidence items", "Tender security reference", "Physical receipt"])
		self.assertIn("confirmed", declared["Declarations"])
		self.assertTrue(declared["Evidence items"].endswith(" accepted"), declared["Evidence items"])
		self.assertEqual(declared["Physical receipt"], "Not yet recorded")
		# an outstanding original is the amber fact from the company task, not a Must fix
		self.assertEqual((view["security_notice"]["tone"], view["security_notice"]["title"]), ("warning", "Physical original not yet recorded"))
		self.assertEqual([r["label"] for r in view["price_summary"]], ["Subtotal excluding tax", "Tax", "Bid total"])
		self.assertEqual(view["footer"], {"back_href": base, "submit": {"label": "Submit bid", "href": f"{base}/submit"}})
		self.assertNotIn("review_bid", [f.get("fix_id") for f in view["next_step"]["fixes"]])
		self.assertEqual(frappe.db.get_value("Bid Workspace", self.bid, ["record_version", "last_saved_at"]), before)

	def test_a_recorded_original_is_a_green_fact(self):
		ctx = load(self.bid, actor=MARY, organisation="", at=frappe.utils.now_datetime())
		security = tender_security.response(ctx)
		recorded = security_intake.record_physical_tender_security_receipt(
			tender_reference=self.reference, instrument_type=security["security_type"], issuer=security["issuer"], instrument_reference=security["reference"],
			amount=security["amount"], currency=security["currency"], received_at="2027-05-19 09:00:00", notes="", confirmed=True, idempotency_key=key(), user=tender_fx.HOPF,
		)
		self.assertTrue(recorded["ok"], recorded)
		view = review(self.bid)
		self.assertEqual(view["security_notice"]["tone"], "live")
		self.assertTrue(view["security_notice"]["text"].startswith("Physical tender-security original recorded as received on 19 May 2027"), view["security_notice"])
		self.assertEqual(facts(view["declarations"])["Physical receipt"], recorded["intake_reference"])

	def test_the_representative_sees_the_same_review_without_submit(self):
		view = review(self.bid, user=DAVID)
		self.assertIsNone(view["page"]["action"])
		self.assertIsNone(view["footer"]["submit"])
		self.assertEqual(view["result"]["text"], "All required bid information is complete.")
		self.assertTrue(view["next_step"]["headline"].endswith("must submit this bid."), view["next_step"])

	def test_a_rejected_file_is_linked_at_its_task_and_submit_is_absent(self):
		requirements = reads.get_bid_task(bid_reference=self.bid, task="requirements", user=DAVID)
		# the Evidence rejected fixture: the datasheet's only file was rejected
		group, field = next((g, f) for g in requirements["groups"] for f in g["fields"] if f["kind"] == "evidence" and f["required"] and len(f["evidence"]["files"]) == 1)
		removed = evidence.remove_bid_evidence(bid_reference=self.bid, evidence_id=field["evidence"]["files"][0]["id"], expected_record_version=self.version(), idempotency_key=key(), user=DAVID)
		self.assertTrue(removed["ok"], removed)
		refused = evidence.upload_bid_evidence(bid_reference=self.bid, handle=field["handle"], filename="datasheet.pdf", content=EICAR_PDF, expected_record_version=self.version(), idempotency_key=key(), user=DAVID)
		self.assertFalse(refused["ok"])
		view = review(self.bid)
		self.assertIsNone(view["page"]["action"])
		self.assertIsNone(view["result"])
		self.assertIsNone(view["footer"]["submit"])
		row = next(r for r in view["task_rows"] if r["key"] == "requirements")
		label = field["label"][:1].lower() + field["label"][1:]
		self.assertEqual((row["status"], row["issues"]), ("Needs attention", [{"label": f"Replace the rejected {label}", "href": f"/tenders/{self.reference}/bid/requirements?item={group['key']}"}]))
		self.assertIn("1 rejected", facts(view["declarations"])["Evidence items"])
		self.assertEqual([f["label"] for f in view["next_step"]["fixes"]], ["Fix item"])

	def test_submit_is_absent_while_the_operating_conditions_are_not_met(self):
		# §5.10 / BDS01-IMP-051: the production switch off, signing or custody down,
		# or an uncertain attempt — Submit is absent and the next step names who acts
		for code in ("BDS_PRODUCTION_SUBMISSION_NOT_ENABLED", "BDS_SIGNATURE_UNAVAILABLE", "BDS_SUBMISSION_SERVICE_UNAVAILABLE"):
			with self.subTest(code=code), mock.patch("kentender_procurement.bid_submission.services.availability.get_submission_availability", return_value={"available": False, "code": code, "message": ""}):
				view = review(self.bid)
				self.assertEqual((view["page"]["action"], view["footer"]["submit"]), (None, None))
				self.assertEqual(view["result"]["text"], "All required bid information is complete.")
				self.assertEqual(view["next_step"]["kind"], "waiting")
		# a missing certificate is the signatory's own to fix on the Submit page
		from kentender_procurement.bid_submission.test_services import trust

		trust.revoke_certificate(self.certificate)
		view = review(self.bid)
		self.assertEqual(view["page"]["action"]["label"], "Submit bid")
		self.assertEqual(view["next_step"]["headline"], "Obtain a valid digital signature certificate from an approved licensed certifying agency before submitting.")

	def test_waiting_on_portal_information_keeps_the_ready_draft_without_submit(self):
		with mock.patch("kentender_core.services.public_portal.get_public_portal_information", return_value={"status": "Incomplete"}):
			view = review(self.bid)
		self.assertEqual(view["page"]["action"]["label"], "Continue saved bid")
		self.assertEqual(view["page"]["action"]["tone"], "secondary")
		self.assertIsNone(view["footer"]["submit"])
		self.assertEqual(view["result"]["text"], "All required bid information is complete.")


class TestAddendumReview(AddendumCase):
	def test_an_addendum_links_the_changed_response_at_its_task(self):
		fill_everything(self.bid)
		self.issue_addendum()
		self.at("2027-06-01 12:10:00")
		price = reads.get_bid_task(bid_reference=self.bid, task="price", user=DAVID)
		unit = next(f for g in price["groups"] for f in g["fields"] if f["kind"] == "money")
		refreshed = self.save("price", {unit["handle"]: unit["value"]})
		self.assertTrue(refreshed.get("refreshed"), refreshed)
		view = review(self.bid, user=MARY)
		changed = [r for r in view["task_rows"] if r["issues"]]
		self.assertTrue(changed, view["task_rows"])
		documents = next(r for r in view["task_rows"] if r["key"] == "documents")
		self.assertEqual((documents["status"], documents["issues"]), ("Needs attention", []))
		for row in changed:
			self.assertEqual(row["status"], "Needs attention")
			self.assertTrue(row["issues"][0]["label"].startswith("Confirm the current "), row)
			self.assertEqual(row["issues"][0]["href"], f"/tenders/{self.reference}/bid/{row['key']}")
		self.assertIsNone(view["page"]["action"])
		self.assertEqual([f["label"] for f in view["next_step"]["fixes"]][:1], ["Review addendum"])
