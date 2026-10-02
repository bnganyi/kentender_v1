# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §10.10 BDS-DES-09 (plan Phase 11, slice 11.9): the
requirements task read gives one link per region with its state, the offered
goods form beside the published facts, one row per technical and warranty
requirement with the published requirement, this bid's response, its files
and state, the comparable contracts, the supporting evidence with each
file's check, and what must be fixed — a rejected file names its row."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_submission.services import evidence, reads, start_bid
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, BidCase, key
from kentender_procurement.bid_submission.tests.test_evidence import EICAR_PDF
from kentender_procurement.bid_submission.tests.test_submission import SubmissionCase


def requirements(bid):
	return reads.get_bid_task(bid_reference=bid, task="requirements", user=DAVID)


class TestCompleteRequirements(SubmissionCase):
	def test_a_filled_bid_reads_region_by_region(self):
		view = requirements(self.bid)
		self.assertEqual((view["page"]["title"], view["badge"]["label"]), ("Requirements and supporting evidence", "Complete"))
		labels = [s["label"] for s in view["sections"]]
		for name in ("Offered goods", "Technical requirements", "Warranty and support", "Experience", "Evidence"):
			self.assertIn(name, labels)
		# every section is complete; the acceptance terms say "Accepted" in their own words
		self.assertTrue(all(s["status"] == ("Accepted" if s["key"] == "acceptance" else "Complete") for s in view["sections"]), view["sections"])
		self.assertIsNone(view["attention"])
		self.assertTrue(view["goods"]["fields"])
		self.assertIn("Quantity · published", [f["label"] for f in view["goods"]["published"]])
		for row in view["technical"] + view["warranty"]:
			self.assertEqual(row["status"], "Complete", row["label"])
			self.assertTrue(row["response"], row["label"])
		with_required_file = [r for r in view["technical"] + view["warranty"] if any(f["kind"] == "evidence" and f["required"] for f in r["fields"])]
		self.assertTrue(with_required_file)
		for row in with_required_file:
			self.assertNotEqual(row["evidence"], "—", row["label"])  # a required file is there
			# the table shows how many files a row holds, never their names (which can be any length)
			self.assertGreaterEqual(row["evidence_count"], 1, row["label"])
			self.assertEqual(row["evidence_count"], len(row["evidence_names"]), row["label"])
		# requirements read as the Tender states them, from the definition's comparison, value and unit
		minimums = [r for r in view["technical"] if r["requirement"].startswith("Minimum ")]
		self.assertTrue(minimums, [r["requirement"] for r in view["technical"]])
		self.assertTrue(all(any(ch.isdigit() for ch in r["requirement"]) for r in minimums))
		self.assertEqual([r["label"] for r in view["experience"]["rows"]][:2], ["Contract 1", "Contract 2"])
		self.assertTrue(all(r["label"] != "Acceptance" for r in view["acceptance"]))
		# acceptance rows read as contract terms the bidder has accepted, not as answers
		self.assertTrue(view["acceptance"] and all((r["accepted"], r["accept_status"], r["accept_tone"]) == (True, "Accepted", "live") for r in view["acceptance"]))
		self.assertEqual(next(s for s in view["sections"] if s["key"] == "acceptance"), {"key": "acceptance", "label": "Acceptance terms", "status": "Accepted", "tone": "live"})
		self.assertTrue(view["experience"]["rows"])
		self.assertTrue(view["experience"]["text"].startswith("Provide at least "))
		self.assertTrue(view["evidence"] and all(r["file_status"] == "Accepted" for r in view["evidence"]))
		# the evidence table's File column counts the files too, and its status reads the whole row
		self.assertTrue(all(r["evidence_count"] >= 1 and r["evidence_count"] == len(r["evidence_names"]) for r in view["evidence"]))
		# the other tasks are done too, so the way on is Review (not through the finished Price task)
		self.assertEqual(view["footer"], {"save_label": "Save and finish", "next_href": f"/tenders/{self.reference}/bid"})  # David's part is done; Mary signs

	def test_a_rejected_file_names_its_row_and_asks_for_it_to_be_fixed(self):
		row = requirements(self.bid)["technical"][0]
		handle = next(f["handle"] for f in row["fields"] if f["kind"] == "evidence")
		refused = evidence.upload_bid_evidence(bid_reference=self.bid, handle=handle, filename="datasheet.pdf", content=EICAR_PDF, expected_record_version=self.version(), idempotency_key=key(), user=DAVID)
		self.assertFalse(refused["ok"])
		view = requirements(self.bid)
		again = next(r for r in view["technical"] if r["key"] == row["key"])
		self.assertEqual((again["status"], again["tone"]), ("Needs evidence", "attention"))
		self.assertTrue(again["evidence_rejected"])  # a refused file is reported, never counted among the held ones
		self.assertNotIn("datasheet.pdf", again["evidence_names"])
		self.assertEqual((view["attention"]["tone"], view["attention"]["title"]), ("critical", "Fix 1 item"))
		self.assertEqual(view["attention"]["items"][0]["key"], row["key"])
		self.assertEqual(next(s for s in view["sections"] if s["key"] == "technical")["status"], "Needs attention")


class TestFilesStatus(BidCase):
	def test_one_status_reads_all_of_a_requirements_files(self):
		from kentender_procurement.bid_submission.services.requirements_view import _files_status

		file = lambda status: {"name": "f.pdf", "status": status}  # noqa: E731
		self.assertEqual(_files_status([]), "Missing")
		self.assertEqual(_files_status([file("Accepted"), file("Accepted")]), "Accepted")
		self.assertEqual(_files_status([file("Accepted"), file("Pending")]), "Pending")
		self.assertEqual(_files_status([file("Pending"), file("Rejected"), file("Accepted")]), "Rejected")


class TestNewRequirements(BidCase):
	def test_a_new_bid_has_every_row_not_started(self):
		bid = start_bid.start_bid(tender_reference=self.reference, organisation=AFYA, arrangement=self.single(), notice_contact_id=f"{AFYA}-C1", idempotency_key=key(), user=DAVID)["bid_reference"]
		view = requirements(bid)
		self.assertTrue(view["technical"] and all(r["status"] == "Not started" for r in view["technical"]))
		self.assertTrue(all(r["evidence"] == "—" for r in view["technical"]))
		self.assertTrue(all((r["evidence_count"], r["evidence_names"]) == (0, []) for r in view["technical"] + view["warranty"]))
		terms = view["acceptance"]
		self.assertTrue(terms and all((r["accepted"], r["accept_status"], r["accept_tone"]) == (False, "Not accepted yet", "draft") for r in terms))
		first = terms[0]["term"]
		self.assertEqual((first["check"], first["passes_when"], first["evidence"], first["applies_to"]), ("Quantity", "Delivered quantities equal the authorised schedule", "Inspection record", "All items"))
		self.assertEqual(next(s for s in view["sections"] if s["key"] == "acceptance")["status"], "Not accepted yet")
		events = frappe.db.count("Bid Submission Event")
		requirements(bid)
		self.assertEqual(frappe.db.count("Bid Submission Event"), events)
