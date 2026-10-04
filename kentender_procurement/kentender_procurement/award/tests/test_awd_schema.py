# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AWD-CHG-001 v0.4 §4 and plan D2 (AWD4-102): the Award records carry the
spec's facts under its names, change only through Award commands, and give
no business role a write path through Desk."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

MODULE = "Award"
RECORDS = (
	"Award Case", "Award Source Report", "Award Decision Cycle", "Award Professional Opinion", "Award Decision", "Award Decision Event",
	"Award Notice Batch", "Award Notice", "Award Supplier Response", "Award Issue", "Award Correspondence", "Award Clock",
	"Award Contracting Package", "Award Command Journal", "Award Test Contracting Inbox",
)
SINGLES = ("Award Settings", "Award Test Environment Controls")
FIELDS = {
	"Award Case": {"award_id", "tender", "tender_reference", "lot", "current_cycle", "stage", "decision_status", "notification_status", "record_version", "received_at"},
	"Award Decision Cycle": {"number", "predecessor", "authorising_decision", "source_report", "opinion", "decision", "stage", "outcome"},
	"Award Professional Opinion": {"version", "source_report", "author", "conclusion", "reason", "addressed_issues", "frozen_digest", "proof_reference", "signed_at"},
	"Award Decision": {"version", "decided_by", "decided_at", "opinion", "source_report", "outcome", "reason", "supplier_name", "bid", "submitted_amount",
		"evaluated_amount", "notice_batch"},
	"Award Decision Event": {"event_id", "decision", "payload_json", "recipient", "attempts_json", "receipt_reference", "received_at"},
	"Award Notice Batch": {"decision", "version", "status", "issued_at"},
	"Award Notice": {"batch", "version", "letter_html", "content_digest", "organisation", "bid", "contact_email", "channels_json", "attempts_json", "evidence_json"},
	"Award Supplier Response": {"notice", "notice_version", "response", "responder", "authority_evidence", "wording", "received_at", "late"},
	"Award Issue": {"source_event", "issue_type", "scope", "evidence", "effective_at", "received_at", "owner_role", "state", "disposition", "basis"},
	"Award Correspondence": {"request_text", "requested_at", "reply_text", "sent_at", "closed_at", "state"},
	"Award Clock": {"rule", "profile_version", "trigger_evidence", "timezone", "calendar", "deadline", "revision"},
	"Award Contracting Package": {"version", "digest", "content_json", "receipt_reference", "received_at"},
}
ISSUE_TYPES = {"Source correction", "Funding", "Validity", "Delivery", "Debrief", "Review/order", "Supplier response", "Service failure", "Rules and notice audience"}


class TestAwardSchema(IntegrationTestCase):
	def test_every_record_exists_in_the_award_module(self):
		for doctype in RECORDS + SINGLES:
			self.assertEqual(frappe.db.get_value("DocType", doctype, "module"), MODULE, doctype)

	def test_records_carry_the_spec_facts(self):
		for doctype, fields in FIELDS.items():
			have = {f.fieldname for f in frappe.get_meta(doctype).fields}
			self.assertEqual(fields - have, set(), doctype)

	def test_stages_and_statuses_are_the_spec_vocabulary(self):
		options = lambda dt, f: set(filter(None, (frappe.get_meta(dt).get_field(f).options or "").split("\n")))  # noqa: E731
		self.assertEqual(options("Award Case", "stage"), {"Opinion", "Decision", "Notices", "Waiting to proceed", "Sent to Contracting", "Closed"})
		self.assertEqual(options("Award Case", "notification_status"), {"Not issued", "Issue in progress", "Issued", "Unknown"})
		self.assertEqual(options("Award Case", "decision_status"), {"No decision recorded", "Award recorded", "No award recorded"})
		self.assertEqual(options("Award Issue", "issue_type"), ISSUE_TYPES)
		self.assertEqual(options("Award Issue", "basis"), {"Authoritative order", "Reported challenge"})
		self.assertEqual(options("Award Professional Opinion", "conclusion"), {"Recommend award", "No current recommendation"})

	def test_no_role_writes_through_desk(self):
		for doctype in RECORDS:
			for perm in frappe.get_meta(doctype).permissions:
				self.assertFalse(perm.write or perm.create or perm.delete, f"{doctype} gives {perm.role} a write path")

	def test_a_desk_save_is_refused(self):
		doc = frappe.get_doc({"doctype": "Award Command Journal", "idempotency_key": "awd-schema-probe", "command": "Probe", "payload_hash": "x"})
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)
		self.assertFalse(frappe.db.exists("Award Command Journal", "awd-schema-probe"))
