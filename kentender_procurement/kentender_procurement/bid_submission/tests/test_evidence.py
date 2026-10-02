# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §4.7, §5.5, §7.2 `UploadBidEvidence` and
`LinkAccountEvidenceToBid` (plan Phase 6, BDS8-601; plan D16): a file proves
one published requirement, is usable only with a clean scanner verdict, is
kept out entirely when rejected, is copied exactly from the Account, stays in
history when removed, and a bid with every answer and file is Ready to
submit."""

from __future__ import annotations

import hashlib
import json

import frappe

from kentender_procurement.bid_submission.services import errors, evidence, reads, start_bid
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, PETER, BidCase, fill_everything, key, pdf, simulation_on

EICAR_PDF = pdf() + b"\n% X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*\n"


class EvidenceCase(BidCase):
	def setUp(self):
		super().setUp()
		simulation_on(self)
		self.bid = start_bid.start_bid(tender_reference=self.reference, organisation=AFYA, arrangement=self.single(), notice_contact_id=f"{AFYA}-C1", idempotency_key=key(), user=DAVID)["bid_reference"]

	def version(self):
		return frappe.db.get_value("Bid Workspace", self.bid, "record_version")

	def requirement(self, task="requirements", *, maximum=None):
		for g in reads.get_bid_task(bid_reference=self.bid, task=task, user=DAVID)["groups"]:
			for f in g["fields"]:
				if f["kind"] == "evidence" and f["visible"] and f["evidence"]["mandatory"] and (maximum is None or f["evidence"]["maximum"] == maximum):
					return f
		raise AssertionError("no evidence requirement")

	def field(self, handle, task="requirements"):
		return next(f for g in reads.get_bid_task(bid_reference=self.bid, task=task, user=DAVID)["groups"] for f in g["fields"] if f["handle"] == handle)

	def upload(self, handle, content=None, name="proof.pdf", user=DAVID):
		return evidence.upload_bid_evidence(bid_reference=self.bid, handle=handle, filename=name, content=pdf() if content is None else content, expected_record_version=self.version(), idempotency_key=key(), user=user)


class TestReplaceBidEvidence(EvidenceCase):
	"""A file's own Replace: the new file takes the old one's place in one
	change, also where the requirement takes one file and Upload is refused."""

	def replace(self, evidence_id, content=None, name="new-proof.pdf", user=DAVID):
		return evidence.replace_bid_evidence(bid_reference=self.bid, evidence_id=evidence_id, filename=name, content=pdf("new") if content is None else content, expected_record_version=self.version(), idempotency_key=key(), user=user)

	def test_the_new_file_takes_the_old_ones_place_in_one_change(self):
		target = self.requirement("company", maximum=1)
		old = self.upload(target["handle"])
		self.assertEqual((self.upload(target["handle"])["ok"]), False)  # a second file is refused: that is why Replace exists
		replaced = self.replace(old["evidence"])
		self.assertEqual((replaced["ok"], replaced["scan_status"], replaced["replaced"], replaced["draft_version"]), (True, "Accepted", old["evidence"], 3))
		shown = self.field(target["handle"], "company")
		self.assertEqual((shown["value"], shown["issue"], [(f["name"], f["status"]) for f in shown["evidence"]["files"]]), ([replaced["evidence"]], None, [("new-proof.pdf", "Accepted")]))
		self.assertEqual(frappe.db.get_value("Bid Evidence", old["evidence"], ["status", "removed_by"]), ("Replaced", DAVID))
		change = frappe.get_all("Bid Draft Change", filters={"bid_workspace": self.bid, "draft_version": 3}, fields=["prior_value", "new_value"])
		self.assertEqual([(json.loads(c.prior_value), json.loads(c.new_value)) for c in change], [([old["evidence"]], [replaced["evidence"]])])
		self.assertIn("BidEvidenceReplaced", frappe.get_all("Bid Submission Event", filters={"bid_workspace": self.bid}, pluck="event_type"))

	def test_a_refused_new_file_leaves_the_old_one_in_place(self):
		target = self.requirement("company", maximum=1)
		old = self.upload(target["handle"])
		refused = self.replace(old["evidence"], content=b"", name="empty.pdf")
		self.assertEqual((refused["ok"], refused["code"]), (False, "BDS_EVIDENCE_REJECTED"))
		self.assertEqual(frappe.db.get_value("Bid Evidence", old["evidence"], "status"), "Current")
		self.assertEqual(frappe.db.get_value("Bid Workspace", self.bid, "current_draft_version"), 2)
		shown = self.field(target["handle"], "company")
		self.assertEqual(shown["value"], [old["evidence"]])
		self.assertEqual(sorted((f["name"], f["status"]) for f in shown["evidence"]["files"]), [("empty.pdf", "Rejected"), ("proof.pdf", "Accepted")])

	def test_only_a_current_file_of_this_bid_can_be_replaced_and_only_by_its_own_organisation(self):
		target = self.requirement("company", maximum=1)
		old = self.upload(target["handle"])
		with self.assertRaises(frappe.DoesNotExistError):
			self.replace(old["evidence"], user=PETER)
		with self.assertRaises(errors.BidSubmissionError) as unknown:
			self.replace("no-such-file")
		self.assertEqual(unknown.exception.code, "BDS_UNKNOWN_RESPONSE")
		evidence.remove_bid_evidence(bid_reference=self.bid, evidence_id=old["evidence"], expected_record_version=self.version(), idempotency_key=key(), user=DAVID)
		with self.assertRaises(errors.BidSubmissionError) as removed:
			self.replace(old["evidence"])
		self.assertEqual(removed.exception.code, "BDS_UNKNOWN_RESPONSE")


class TestUploadBidEvidence(EvidenceCase):
	def test_a_clean_file_is_accepted_and_proves_its_requirement(self):
		target = self.requirement()
		self.assertEqual(target["issue"]["text"], "Add the required supporting evidence.")
		added = self.upload(target["handle"])
		self.assertEqual((added["ok"], added["scan_status"], added["draft_version"]), (True, "Accepted", 2))
		shown = self.field(target["handle"])
		self.assertEqual((shown["value"], shown["issue"], [f["status"] for f in shown["evidence"]["files"]]), ([added["evidence"]], None, ["Accepted"]))
		row = frappe.get_doc("Bid Evidence", added["evidence"])
		stored = frappe.get_doc("File", row.file)
		self.assertEqual((stored.is_private, stored.attached_to_doctype, stored.attached_to_name, row.scan_result), (1, "Bid Evidence", row.name, "Clean — test scanner (simulation)"))
		change = frappe.get_all("Bid Draft Change", filters={"bid_workspace": self.bid}, fields=["prior_value", "new_value"])
		self.assertEqual([(c.prior_value, json.loads(c.new_value)) for c in change], [("[]", [added["evidence"]])])

	def test_a_rejected_file_is_kept_as_a_record_without_its_bytes_until_replaced(self):
		# Owner decision 27 Sep 2026: keep a Rejected record (no bytes) so the bid can name it (FU-V08-42).
		target = self.requirement()
		files_before = frappe.db.count("File", {"attached_to_doctype": "Bid Evidence"})
		for content, name, reason in ((b"", "empty.pdf", "File is empty or unreadable."), (b"PK\x03\x04 word document", "notes.docx", "File type .docx is not permitted. Use PDF, PNG, JPG, JPEG."), (b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF\n", "truncated.pdf", "File is empty or unreadable."), (EICAR_PDF, "infected.pdf", "File failed malware scanning.")):
			with self.subTest(name=name):
				refused = self.upload(target["handle"], content=content, name=name)
				self.assertEqual((refused["ok"], refused["code"], refused["errors"]), (False, "BDS_EVIDENCE_REJECTED", {target["handle"]: reason}))
		rows = frappe.get_all("Bid Evidence", filters={"bid_workspace": self.bid}, fields=["original_filename", "scan_status", "status", "file", "scan_result"], order_by="creation asc")
		self.assertEqual([(r.original_filename, r.scan_status, r.status, r.file) for r in rows], [("empty.pdf", "Rejected", "Replaced", None), ("notes.docx", "Rejected", "Replaced", None), ("truncated.pdf", "Rejected", "Replaced", None), ("infected.pdf", "Rejected", "Current", None)])
		self.assertEqual(rows[-1].scan_result, "File failed malware scanning.")
		self.assertEqual(frappe.db.count("File", {"attached_to_doctype": "Bid Evidence"}), files_before)  # no bytes kept
		self.assertEqual(frappe.db.get_value("Bid Workspace", self.bid, "current_draft_version"), 1)
		shown = self.field(target["handle"])
		self.assertEqual((shown["value"], shown["issue"]["text"]), (None, "Replace the rejected file."))
		self.assertEqual([(f["name"], f["status"], f.get("reason")) for f in shown["evidence"]["files"]], [("infected.pdf", "Rejected", "File failed malware scanning.")])
		label = target["label"][:1].lower() + target["label"][1:]
		step = reads.get_bid_workspace(bid_reference=self.bid, user=DAVID)["next_step"]
		self.assertEqual((step["kind"], step["headline"]), ("your_turn_blocked", f"Replace the rejected {label} before submitting."))
		self.assertTrue(self.upload(target["handle"])["ok"])
		self.assertEqual(frappe.db.get_value("Bid Evidence", {"bid_workspace": self.bid, "original_filename": "infected.pdf"}, "status"), "Replaced")
		self.assertNotIn("rejected", reads.get_bid_workspace(bid_reference=self.bid, user=DAVID)["next_step"]["headline"])

	def test_without_a_scanner_a_file_stays_pending_and_does_not_count(self):
		frappe.conf["kt_bds_simulation_environment"] = 0
		target = self.requirement()
		added = self.upload(target["handle"])
		self.assertEqual(added["scan_status"], "Pending")
		shown = self.field(target["handle"])
		self.assertEqual((shown["value"], shown["issue"]["severity"]), (None, "Must fix"))

	def test_account_evidence_is_copied_exactly_into_the_bid(self):
		content = pdf("AGPO-Y-2026-04172")
		self.accounts.add_evidence(AFYA, "EVD-BDST-AGPO", "Reservation evidence", "agpo-youth.pdf", content=content)
		target = self.requirement()
		linked = evidence.link_account_evidence_to_bid(bid_reference=self.bid, handle=target["handle"], account_evidence_id="EVD-BDST-AGPO", expected_record_version=self.version(), idempotency_key=key(), user=DAVID)
		self.assertTrue(linked.get("ok"), linked)
		row = frappe.get_doc("Bid Evidence", linked["evidence"])
		self.assertEqual((row.source_evidence, row.file_digest, row.original_filename, row.scan_status), ("EVD-BDST-AGPO", hashlib.sha256(content).hexdigest(), "agpo-youth.pdf", "Accepted"))
		missing = evidence.link_account_evidence_to_bid(bid_reference=self.bid, handle=target["handle"], account_evidence_id="EVD-NOT-OURS", expected_record_version=self.version(), idempotency_key=key(), user=DAVID)
		self.assertEqual((missing["ok"], missing["code"]), (False, "BDS_FIELD_INVALID"))

	def test_a_removed_file_leaves_the_requirement_open_and_stays_in_history(self):
		target = self.requirement()
		added = self.upload(target["handle"])
		removed = evidence.remove_bid_evidence(bid_reference=self.bid, evidence_id=added["evidence"], expected_record_version=self.version(), idempotency_key=key(), user=DAVID)
		self.assertEqual(removed["draft_version"], 3)
		self.assertEqual(frappe.db.get_value("Bid Evidence", added["evidence"], ["status", "removed_by"]), ("Removed", DAVID))
		self.assertEqual(self.field(target["handle"])["issue"]["severity"], "Must fix")

	def test_the_published_maximum_is_kept(self):
		target = self.requirement("company", maximum=1)
		self.upload(target["handle"])
		over = self.upload(target["handle"])
		self.assertEqual((over["ok"], list(over["errors"])), (False, [target["handle"]]))

	def test_another_organisation_can_neither_add_nor_download(self):
		target = self.requirement()
		added = self.upload(target["handle"])
		with self.assertRaises(frappe.DoesNotExistError):
			self.upload(target["handle"], user=PETER)
		with self.assertRaises(frappe.DoesNotExistError):
			evidence.get_bid_evidence_file(bid_reference=self.bid, evidence_id=added["evidence"], user=PETER)
		self.assertEqual(evidence.get_bid_evidence_file(bid_reference=self.bid, evidence_id=added["evidence"], user=DAVID)["file_name"], "proof.pdf")

	def test_an_answer_field_cannot_take_a_file(self):
		answer = next(f for g in reads.get_bid_task(bid_reference=self.bid, task="company", user=DAVID)["groups"] for f in g["fields"] if f["editable"] and f["kind"] != "evidence")
		with self.assertRaises(errors.BidSubmissionError) as ctx:
			self.upload(answer["handle"])
		self.assertEqual(ctx.exception.code, "BDS_UNKNOWN_RESPONSE")


class TestReadyToSubmit(EvidenceCase):
	def test_every_answer_and_file_makes_the_bid_ready_to_submit(self):
		fill_everything(self.bid)
		view = reads.get_bid_workspace(bid_reference=self.bid, user=DAVID)
		self.assertEqual({t["key"]: t["status"] for t in view["tasks"]}, {"documents": "Complete", "company": "Complete", "requirements": "Complete", "price": "Complete", "review": "Complete"})
		self.assertEqual((view["must_fix"], view["bid"]["status"], frappe.db.get_value("Bid Workspace", self.bid, "status")), (0, "Ready to submit", "Ready to submit"))
