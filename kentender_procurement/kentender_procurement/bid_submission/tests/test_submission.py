# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §4.9–4.10, §5.7, §5.9, §5.10, §7.3, §12.3 and plan D5–D8
(plan Phase 8, BDS8-801): the Authorised Signatory signs the exact canonical
package through the (simulated) trust service and submits it; Submitted and
the receipt exist only from the tender box's acceptance; a definite
rejection leaves the Draft as it was; an uncertain deposit is reconciled
from its own correlation, never sent twice; the same request key returns the
same outcome; nothing is created when a check fails; and neither the
receipt nor any record holds the bid's content."""

from __future__ import annotations

import json
import re

import frappe

from kentender_procurement.bid_submission.services import (
	errors,
	package,
	bid_context,
	reads,
	receipts,
	save,
	signature,
	simulation,
	start_bid,
	submission,
)
from kentender_procurement.bid_submission.test_services import tender_box, trust
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, GRACE, MARY, PETER, BidCase, fill_everything, key, submission_on

SUBMIT_AT = "2027-05-30 14:30:00"
COUNTED = ("Bid Submission Attempt", "Bid Submission Version", "Tender Box Envelope", "Bid Receipt")


class SubmissionCase(BidCase):
	def setUp(self):
		super().setUp()
		submission_on(self)
		self.bid = start_bid.start_bid(tender_reference=self.reference, organisation=AFYA, arrangement=self.single(), notice_contact_id=f"{AFYA}-C1", idempotency_key=key(), user=DAVID)["bid_reference"]
		fill_everything(self.bid)
		self.certificate = trust.issue_certificate(user=MARY, organisation=AFYA, subject_name="Mary Wanjiku", valid_from="2027-01-01 00:00:00", valid_to="2027-12-31 23:59:59")
		self.at(SUBMIT_AT)

	def version(self):
		return frappe.db.get_value("Bid Workspace", self.bid, "record_version")

	def prepare(self, user=MARY, confirmed=True, **kw):
		return signature.prepare_bid_signature(bid_reference=self.bid, confirmed=confirmed, expected_record_version=self.version(), idempotency_key=key(), user=user, **kw)

	def signed(self, user=MARY, **kw):
		request = self.prepare(user=user, **kw)
		self.assertTrue(request["ok"], request)
		return signature.sign_with_test_trust_service(signing_request=request["signing_request"], user=user)["signature"]

	def submit(self, signature_ref, request_key=None, user=MARY, **kw):
		return submission.submit_bid(bid_reference=self.bid, signature_ref=signature_ref, confirmed=True, expected_record_version=kw.pop("expected", self.version()), idempotency_key=request_key or key(), user=user, **kw)

	def counts(self):
		return {d: frappe.db.count(d, {"bid_workspace": self.bid} if d != "Tender Box Envelope" else {"tender": self.name}) for d in COUNTED}

	def code(self, fn, *args, **kwargs):
		with self.assertRaises(errors.BidSubmissionError) as ctx:
			fn(*args, **kwargs)
		return ctx.exception.code

	def deadline(self):
		return frappe.db.get_value("Tender", self.name, "submission_deadline")

	def answer(self, pick, value):
		"""David changes one requirements answer (before the signing instant)."""
		field = next(f for g in reads.get_bid_task(bid_reference=self.bid, task="requirements", user=DAVID)["groups"] for f in g["fields"] if pick(f))
		self.at("2027-05-30 14:00:00")
		self.assertTrue(save.save_bid_task(bid_reference=self.bid, task="requirements", values={field["handle"]: value}, expected_record_version=self.version(), idempotency_key=key(), user=DAVID)["ok"])
		self.at(SUBMIT_AT)


class TestSubmitBid(SubmissionCase):
	def test_mary_signs_and_submits_and_the_tender_box_acceptance_makes_the_receipt(self):
		screen = submission.get_submit_bid(bid_reference=self.bid, user=MARY)
		self.assertEqual((screen["can_submit"], screen["current_time"], screen["signatory"]["certificate"]), (True, "30 May 2027, 14:30 EAT", "Ready"))
		self.assertIn("The bid will not be opened or evaluated now.", screen["consequence"])
		self.assertEqual(screen["confirmation_label"], "I confirm that the information, declarations and evidence in this bid are correct and that I am authorised to submit it for Afya Digital Supplies Limited.")
		simulation.set_controls(accept_after_seconds=3)
		result = self.submit(self.signed())
		self.assertTrue(result["ok"], result)
		self.assertRegex(result["receipt_reference"], r"^RCPT-MOH-\d{4}-\d{3}-001$")
		ws = frappe.get_doc("Bid Workspace", self.bid)
		version = frappe.get_doc("Bid Submission Version", ws.current_submission_version)
		self.assertEqual((ws.status, version.status, version.version_number, str(version.received_at), str(version.accepted_at)), ("Submitted", "Submitted", 1, "2027-05-30 14:30:00", "2027-05-30 14:30:03"))
		self.assertEqual((version.definition_digest, version.organisation_snapshot, version.signed_by), (ws.definition_digest, ws.organisation_snapshot, MARY))
		self.assertEqual(frappe.db.get_value("Tender Box Envelope", version.tender_box_envelope, "box_state"), "Sealed")
		# the box holds exactly the signed package; the database only its digest
		stored = tender_box.stored_package(frappe.db.get_value("Bid Submission Attempt", version.attempt, "correlation_id"))
		self.assertEqual(package.sha256(stored), version.package_digest)
		# the receipt: every §4.10 fact, to the second, and nothing technical
		for reader in (MARY, DAVID):
			facts = receipts.get_bid_receipt(receipt_reference=result["receipt_reference"], user=reader)
			self.assertEqual(
				(facts["bidder"], facts["submitted_version"], facts["submitted_by"], facts["received_at"], facts["accepted_at"], facts["status"]),
				("Afya Digital Supplies Limited", "Submitted bid Version 1", "Mary Wanjiku", "30 May 2027, 14:30:00 EAT", "30 May 2027, 14:30:03 EAT", "Submitted"),
			)
		self.assertEqual(facts["notice"], "This receipt confirms submission only. It is not an opening, evaluation or award result.")
		text = json.dumps(facts)
		self.assertIsNone(re.search(r"[0-9a-f]{40,}", text))
		for internal in ("COR-", "SUBV-", "TBX-", "TCERT", "TSG-", "TSR-", "private/", "kt-bds-package"):
			self.assertNotIn(internal, text)
		name, pdf = receipts.receipt_pdf(receipt_reference=result["receipt_reference"], user=MARY)
		self.assertEqual((name, pdf[:4]), (f"{result['receipt_reference']}.pdf", b"%PDF"))
		# a Submitted bid is locked
		view = frappe.get_all("Bid Section Response", filters={"bid_workspace": self.bid, "section_key": "company"}, pluck="name")
		self.assertTrue(view)
		self.assertEqual(self.code(save.save_bid_task, bid_reference=self.bid, task="company", values={}, expected_record_version=self.version(), idempotency_key=key(), user=DAVID), "BDS_ALREADY_SUBMITTED")

	def test_the_same_request_key_returns_the_same_receipt_and_a_changed_one_is_refused(self):
		request_key = key()
		first = self.submit(self.signed(), request_key)
		expected = frappe.db.get_value("Bid Submission Attempt", {"bid_workspace": self.bid}, "payload_hash")
		again = self.submit(frappe.db.get_value("Bid Submission Attempt", {"bid_workspace": self.bid}, "signature_ref"), request_key)
		self.assertEqual(again, first)
		self.assertEqual(self.counts(), dict.fromkeys(COUNTED, 1))
		self.assertEqual(self.code(self.submit, "TSG-SOMETHING-ELSE", request_key), "BDS_IDEMPOTENCY_CONFLICT")
		self.assertEqual(self.code(self.submit, "TSG-SOMETHING-ELSE"), "BDS_ALREADY_SUBMITTED")
		self.assertEqual(frappe.db.get_value("Bid Submission Attempt", {"bid_workspace": self.bid}, "payload_hash"), expected)

	def test_the_package_is_the_same_bytes_for_the_same_draft_and_keeps_the_published_identities(self):
		ctx = bid_context.load(self.bid, actor=MARY, organisation=AFYA)
		signatory = signature.signatory_of(ctx, MARY)
		first, second = package.build(ctx, signatory=signatory, confirmed=True), package.build(bid_context.load(self.bid, actor=MARY), signatory=signatory, confirmed=True)
		self.assertEqual((first.content, first.package_digest), (second.content, second.package_digest))
		body = json.loads(first.content)
		self.assertTrue(all(r["response_id"].startswith("RSP-") and "evaluation_mapping_id" in r for r in body["responses"]))
		self.assertTrue(body["evidence"] and all(f["file_digest"] and f["content_base64"] for e in body["evidence"] for f in e["files"]))
		self.assertEqual((body["signatory"]["full_name"], body["confirmation"]["confirmed"]), ("Mary Wanjiku", True))
		self.assertTrue(body["price"]["complete"])


class TestWhoAndWhen(SubmissionCase):
	def test_only_the_authorised_signatory_can_sign_or_submit(self):
		self.assertEqual(self.code(self.prepare, user=DAVID), "BDS_SIGNATORY_REQUIRED")
		self.assertEqual(self.code(signature.check_certificate, bid_reference=self.bid, user=DAVID), "BDS_SIGNATORY_REQUIRED")
		screen = submission.get_submit_bid(bid_reference=self.bid, user=DAVID)
		self.assertEqual((screen["can_submit"], screen["blocked"]["code"]), (False, "BDS_SIGNATORY_REQUIRED"))
		self.assertEqual(self.code(self.submit, self.signed(), user=DAVID), "BDS_SIGNATORY_REQUIRED")
		self.assertEqual(self.prepare(confirmed=False)["errors"], {"confirmed": signature.CONFIRMATION_MISSING})

	def test_the_deadline_is_the_trusted_server_instant_strictly_before(self):
		signed = self.signed()
		self.at(str(self.deadline()))
		before = self.counts()
		self.assertEqual(self.code(self.submit, signed), "BDS_DEADLINE_PASSED")
		self.assertEqual(self.counts(), before)

	def test_a_signature_must_be_the_signatorys_own_for_this_exact_package(self):
		self.accounts.assign(GRACE, AFYA, "Authorised Signatory", job_title="Director")
		trust.issue_certificate(user=GRACE, organisation=AFYA, subject_name="Grace Njeri", valid_from="2027-01-01 00:00:00", valid_to="2027-12-31 23:59:59")
		grace = self.signed(user=GRACE, organisation=AFYA)
		self.assertEqual(self.code(self.submit, grace), "BDS_SIGNATURE_INVALID")  # another person's
		for typed in ("Mary Wanjiku", "on", "true", ""):
			self.assertEqual(self.code(self.submit, typed), "BDS_SIGNATURE_INVALID")
		mine = self.signed()
		self.answer(lambda f: f["label"] == "Offered make and model", "ApexBook Pro 15")
		self.assertEqual(self.code(self.submit, mine), "BDS_SIGNATURE_INVALID")  # signed a different package
		trust.revoke_certificate(self.certificate)
		self.assertEqual(self.code(self.submit, mine), "BDS_SIGNATORY_CERTIFICATE_REQUIRED")
		self.assertEqual(self.counts(), dict.fromkeys(COUNTED, 0))


class TestNothingIsCreatedWhenUnavailable(SubmissionCase):
	def test_each_refusal_creates_no_signature_request_attempt_or_receipt(self):
		requests = frappe.db.count("Test Trust Signature")
		frappe.conf["production_bid_submission_enabled"] = 0
		self.assertEqual(self.code(self.prepare), "BDS_PRODUCTION_SUBMISSION_NOT_ENABLED")
		frappe.conf["production_bid_submission_enabled"] = 1
		for controls, expected in (({"trust_service_down": 1}, "BDS_SIGNATURE_UNAVAILABLE"), ({"custody_service_down": 1}, "BDS_SUBMISSION_SERVICE_UNAVAILABLE"), ({"gate_closed": 1}, "BDS_PRODUCTION_SUBMISSION_NOT_ENABLED")):
			with self.subTest(controls=controls):
				simulation.set_controls(**controls)
				self.assertEqual(self.code(self.prepare), expected)
				self.assertEqual(submission.get_submit_bid(bid_reference=self.bid, user=MARY)["blocked"]["code"], expected)
				simulation.reset_controls()
		trust.revoke_certificate(self.certificate)
		self.assertEqual(self.code(self.prepare), "BDS_SIGNATORY_CERTIFICATE_REQUIRED")
		self.assertEqual(signature.check_certificate(bid_reference=self.bid, user=MARY)["status"], "Required")
		self.assertEqual((frappe.db.count("Test Trust Signature"), self.counts()), (requests, dict.fromkeys(COUNTED, 0)))
		self.assertEqual(frappe.db.get_value("Bid Workspace", self.bid, "status"), "Ready to submit")


class TestCustodyOutcomes(SubmissionCase):
	def test_a_definite_rejection_keeps_the_draft_and_allows_a_new_attempt(self):
		simulation.set_controls(deposit_outcome="Reject", rejection_reference="TBX-REJECT-033-01")
		result = self.submit(self.signed())
		self.assertEqual((result["ok"], result["code"], result["rejection_reference"], result["retry_allowed"]), (False, "BDS_CUSTODY_REJECTED", "TBX-REJECT-033-01", True))
		self.assertEqual(self.counts(), {**dict.fromkeys(COUNTED, 0), "Bid Submission Attempt": 1})
		self.assertEqual(frappe.db.get_value("Bid Workspace", self.bid, ["status", "current_submission_version"]), ("Ready to submit", None))
		self.assertEqual(submission.get_submission_status(bid_reference=self.bid, user=MARY)["status"], "Rejected")
		simulation.set_controls(deposit_outcome="Accept")
		self.assertTrue(self.submit(self.signed())["ok"])

	def test_an_uncertain_deposit_is_reconciled_from_its_own_correlation_and_never_sent_twice(self):
		simulation.set_controls(deposit_outcome="Uncertain")
		request_key = key()
		signed = self.signed()
		pending = self.submit(signed, request_key)
		self.assertEqual(pending["code"], "BDS_SUBMISSION_UNCERTAIN")
		self.assertRegex(pending["correlation_id"], r"^COR-BDS-\d{4}-\d{3}-01$")
		self.assertRegex(pending["support_reference"], r"^SUP-BDS-\d{4}-\d{3}-01$")
		self.assertEqual(self.code(self.submit, signed), "BDS_SUBMISSION_UNCERTAIN")  # no second dispatch
		self.assertEqual(self.submit(signed, request_key)["correlation_id"], pending["correlation_id"])
		status = submission.get_submission_status(bid_reference=self.bid, user=MARY)
		self.assertEqual((status["status"], status["support_reference"]), ("Confirmation pending", pending["support_reference"]))
		self.assertEqual(frappe.db.get_value("Bid Workspace", self.bid, "status"), "Ready to submit")
		submission.reconcile_uncertain_attempts()
		self.assertEqual(frappe.db.get_value("Bid Submission Attempt", {"correlation_id": pending["correlation_id"]}, "status"), "Uncertain")
		simulation.set_controls(uncertain_resolution="Accept")
		submission.reconcile_uncertain_attempts()
		self.assertEqual(self.counts(), dict.fromkeys(COUNTED, 1))
		self.assertTrue(self.submit(signed, request_key)["ok"])
		self.assertEqual(frappe.db.get_value("Bid Workspace", self.bid, "status"), "Submitted")


class TestConfidentiality(SubmissionCase):
	def test_no_record_or_event_holds_the_bids_content(self):
		# a response the receipt never prints (it shows only bid total, offered item, quantity and delivery date)
		self.answer(lambda f: f["kind"] == "short_text" and f["editable"] and f["visible"] and f["label"] != "Offered make and model", "Zorblax Confidential 9000")
		self.assertTrue(self.submit(self.signed())["ok"])
		for doctype in ("Bid Submission Attempt", "Bid Submission Version", "Tender Box Envelope", "Bid Receipt", "Bid Submission Event", "Bid Command Journal", "Test Trust Signature"):
			with self.subTest(doctype=doctype):
				rows = frappe.get_all(doctype, fields=["*"], limit_page_length=0)
				text = json.dumps(rows, default=str)
				self.assertNotIn("Zorblax Confidential 9000", text)
				self.assertNotIn("content_base64", text)


class TestEndpoints(SubmissionCase):
	def as_user(self, user, fn, **kwargs):
		frappe.set_user(user)
		try:
			return fn(**kwargs)
		finally:
			frappe.set_user("Administrator")

	def test_commands_are_post_reads_are_get_and_another_supplier_sees_not_found(self):
		from kentender_procurement.bid_submission import api

		methods = frappe.allowed_http_methods_for_whitelisted_func
		for fn in (api.prepare_bid_signature, api.sign_with_test_trust_service, api.submit_bid):
			self.assertEqual(methods[fn], ["POST"], fn.__name__)
		for fn in (api.get_submit_bid, api.check_certificate, api.get_submission_status, api.get_bid_receipt, api.download_bid_receipt):
			self.assertEqual(methods[fn], ["GET"], fn.__name__)
		receipt = self.submit(self.signed())["receipt_reference"]
		self.assertEqual(self.as_user(PETER, api.get_submit_bid, bid_reference=self.bid)["outcome"], "NOT_FOUND")
		self.assertEqual(self.as_user(PETER, api.get_bid_receipt, receipt_reference=receipt)["outcome"], "NOT_FOUND")
		self.assertEqual(self.as_user(MARY, api.get_bid_receipt, receipt_reference=receipt)["receipt_reference"], receipt)
