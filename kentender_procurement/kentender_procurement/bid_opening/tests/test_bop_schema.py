# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BOP-CHG-001 v0.10 §4 and plan D2/D12 (BOP10-103…105): the Bid Opening
records carry the spec's facts under its names, change only through Bid
Opening commands, give no role a write path, and the placeholder workspace is
gone (BOP-CHG-001 v0.10 §9: every view is reached from the Tender record)."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

MODULE = "Bid Opening"
RECORDS = (
	"Bid Opening Case", "Opening Committee Appointment", "Opening Arrangement", "Opening Presence", "Opening Custody Participation", "Opening Entry",
	"Opening Register", "Opening Exception", "Opening Access Incident", "Opening Decision Item", "Opening Register Request", "Evaluation Handoff",
)
NO_ROLE = ("Opening Command Journal", "Bid Opening Settings", "BOP Test Environment Controls")
FIELDS = {
	"Bid Opening Case": {
		"opening_id", "tender", "tender_reference", "tender_title", "effective_deadline", "state", "outcome", "proceeding", "manifest_handoff", "manifest_digest",
		"manifest_received_at", "current_appointment", "current_arrangement", "register", "last_committed_event", "started_at", "ended_at", "completed_at",
		"evaluation_handoff", "record_version",
	},
	"Opening Committee Appointment": {"appointment_id", "opening_case", "version_number", "appointed_by", "appointed_at", "status", "supersedes_appointment", "reason", "members"},
	"Opening Committee Member": {
		"member_user", "full_name", "designation", "committee_role", "is_chair", "is_recorder", "is_independent", "independence_basis", "excluded_from_evaluation",
	},
	"Opening Arrangement": {
		"arrangement_id", "opening_case", "version_number", "attendance_method", "access_instructions", "scheduled_at", "join_opens_at", "published_by", "published_at", "status",
	},
	"Opening Presence": {"presence_id", "opening_case", "member_user", "roster_segment", "joined_at", "last_seen_at", "left_at", "state"},
	"Opening Custody Participation": {
		"participation_id", "opening_case", "member_user", "manifest_digest", "roster_digest", "confirmed_at", "participation_reference", "correlation_id", "outcome", "stale",
	},
	"Opening Entry": {
		"entry_id", "opening_case", "entry_number", "envelope_id", "receipt_reference", "submission_version", "package_digest", "render_digest", "page_count",
		"price_page", "change_pages", "designated_pages", "bidder_name", "submitted_total", "currency", "permitted_changes", "security_given", "revealed_at",
		"revealed_by", "readout_speaker", "readout_confirmed_at", "readout_confirmed_by", "reported_speech_at", "status", "proceeding_event",
	},
	"Opening Register": {"register_id", "opening_case", "version_number", "entry_ids_json", "entry_count", "is_empty", "register_digest", "frozen_at", "minutes_reference"},
	"Opening Exception": {
		"exception_id", "opening_case", "exception_class", "entry", "envelope_id", "step", "observed_fact", "speaker_name", "response", "recorded_by", "recorded_at",
		"outcome", "holder", "incident", "proceeding_event",
	},
	"Opening Access Incident": {
		"incident_id", "opening_case", "incident_type", "envelope_id", "raised_at", "holder_user", "status", "resolution_note", "resolved_at", "resolved_by",
		"notification_state", "notification_attempts", "last_notified_at",
	},
	"Opening Decision Item": {
		"decision_item_id", "opening_case", "kind", "holder_user", "reason", "last_committed_event", "incident", "status", "created_at", "cleared_at", "clearing_event",
	},
	"Opening Register Request": {
		"request_id", "opening_case", "requester_user", "receipt_reference", "requested_at", "status", "delivery_mode", "register_digest", "delivered_at", "delivered_by",
		"decline_reason",
	},
	"Evaluation Handoff": {"handoff_id", "tender", "opening_case", "payload_json", "handoff_digest", "issued_at", "consumer", "delivery_status"},
	"Opening Command Journal": {"idempotency_key", "command", "payload_hash", "result_json", "actor", "opening_case", "recorded_at"},
	"Bid Opening Settings": {"presence_lapse_seconds", "public_join_lead_minutes", "register_self_service"},
}


def options(doctype: str, field: str) -> list[str]:
	return frappe.get_meta(doctype).get_field(field).options.split("\n")


class TestBidOpeningRecords(IntegrationTestCase):
	def test_the_records_carry_the_spec_facts(self):
		for doctype, fields in FIELDS.items():
			with self.subTest(doctype=doctype):
				self.assertEqual(frappe.get_meta(doctype).module, MODULE)
				self.assertEqual(fields - {f.fieldname for f in frappe.get_meta(doctype).fields}, set())

	def test_the_states_are_the_spec_states(self):
		# BOP-CHG-001 v0.10 §5 lifecycle; the no-bids branch is an outcome, not a state.
		self.assertEqual(options("Bid Opening Case", "state"), [
			"Awaiting deadline", "Ready to open", "Opening", "Interrupted", "Readout complete", "Awaiting attestations", "Opening complete", "Not held", "Cancelled after start",
		])
		self.assertEqual(options("Bid Opening Case", "outcome"), ["", "Bids opened", "No bids"])
		# BOP-CHG-001 v0.10 §5.1 outcomes, including the two §10 labels.
		self.assertIn("Answered during opening", options("Opening Exception", "outcome"))
		self.assertIn("Recorded for Evaluation", options("Opening Exception", "outcome"))

	def test_once_only_identities(self):
		for doctype, field in (("Bid Opening Case", "tender"), ("Evaluation Handoff", "tender"), ("Opening Command Journal", "idempotency_key")):
			with self.subTest(doctype=doctype):
				self.assertTrue(frappe.get_meta(doctype).get_field(field).unique)
		self.assertEqual(frappe.get_meta("Evaluation Handoff").get_field("consumer").default, "evaluation")

	def test_no_role_can_write_a_bid_opening_record(self):
		for doctype in RECORDS:
			with self.subTest(doctype=doctype):
				perms = frappe.get_meta(doctype).permissions
				self.assertTrue({p.role for p in perms} <= {"System Manager"}, doctype)
				self.assertFalse([p for p in perms if p.write or p.create or p.delete or p.submit or p.share or p.export], doctype)
		for doctype in NO_ROLE:
			self.assertEqual(frappe.get_meta(doctype).permissions, [])
		self.assertTrue(frappe.get_meta("Opening Committee Member").istable)
		self.assertTrue(frappe.get_meta("Bid Opening Settings").issingle)

	def test_administrators_cannot_read_bid_content(self):
		"""Board h3 / BOP-CHG-001 v0.10 §6: bids, the register and the opening
		record are never shown to administrators, not even as a read-only form."""
		for doctype in ("Opening Entry", "Opening Register", "Opening Exception", "Opening Register Request", "Evaluation Handoff"):
			with self.subTest(doctype=doctype):
				self.assertEqual(frappe.get_meta(doctype).permissions, [])

	def test_a_record_changes_only_through_a_command(self):
		doc = frappe.get_doc({"doctype": "Opening Exception", "exception_id": "BOP-PROBE", "exception_class": "Procedural comment", "outcome": "Open"})
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True, ignore_links=True, ignore_mandatory=True)
		self.assertFalse(frappe.db.exists("Opening Exception", "BOP-PROBE"))


class TestPlaceholderRetired(IntegrationTestCase):
	def test_the_placeholder_workspace_is_gone(self):
		self.assertFalse(frappe.db.exists("Workspace", "Bid Opening"))
		path = Path(frappe.get_app_path("kentender_procurement", "kentender_procurement", "workspace", "bid_opening"))
		self.assertFalse(path.exists())
