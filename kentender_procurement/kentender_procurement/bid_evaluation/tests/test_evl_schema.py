# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""EVL-CHG-001 v0.4 §6.1 and plan D2 (EVL4-102…107): the Evaluation records
carry the spec's facts under its names, change only through Evaluation
commands and give no role a write path. Bid content, findings and the
committee's correspondence are not readable even by administrators."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

MODULE = "Bid Evaluation"
RECORDS = (
	"Evaluation Case", "Evaluation Appointment", "Evaluation Secretary Appointment", "Evaluation Declaration", "Evaluation Member Unavailability",
	"Evaluation Source Intake", "Evaluation Bid", "Evaluation Check Run", "Evaluation Check Result", "Evaluation Finding", "Evaluation Discussion Item",
	"Evaluation Conclusion", "Evaluation Disagreement", "Evaluation Clarification", "Evaluation Clarification Reply", "Evaluation Verification Plan",
	"Evaluation Verification Observation", "Evaluation Report Version", "Evaluation Report Delivery", "Evaluation Source Event", "Evaluation Correction Notice",
)
NO_ROLE = ("Evaluation Command Journal", "Bid Evaluation Settings", "EVL Test Environment Controls")
BID_CONTENT = (
	"Evaluation Bid", "Evaluation Check Result", "Evaluation Finding", "Evaluation Discussion Item", "Evaluation Conclusion", "Evaluation Disagreement",
	"Evaluation Clarification", "Evaluation Clarification Reply", "Evaluation Verification Observation", "Evaluation Report Version",
)
FIELDS = {
	"Evaluation Case": {
		"evaluation_id", "tender", "tender_reference", "state", "publication", "definition_id", "definition_version", "definition_digest", "opening_handoff",
		"source_intake", "current_run", "current_appointment", "secretary_appointment", "proceeding", "current_report", "suspended", "suspension_event",
		"cancellation_event", "validity_end", "evaluation_deadline", "scope_issue", "record_version",
	},
	"Evaluation Appointment": {"appointment_id", "evaluation_case", "version_number", "appointment_reference", "change_kind", "reason", "appointed_by", "appointed_at", "status", "members"},
	"Evaluation Committee Member": {"member_user", "full_name", "department", "designation", "capacity", "status", "replaced_by_user", "change_reason"},
	"Evaluation Secretary Appointment": {"secretary_appointment_id", "evaluation_case", "secretary_user", "appointment_reference", "self_appointment", "assigned_by", "assigned_at", "status"},
	"Evaluation Declaration": {"declaration_id", "evaluation_case", "member_user", "appointment", "choice", "conflict_description", "confidentiality_accepted", "declared_at", "status"},
	"Evaluation Member Unavailability": {"unavailability_id", "evaluation_case", "member_user", "reason", "recorded_at", "status"},
	"Evaluation Source Intake": {"intake_id", "evaluation_case", "operation_key", "source_kind", "opening_handoff", "handoff_digest", "definition_id", "status", "attempts", "support_issue", "received_at"},
	"Evaluation Bid": {"evaluation_bid_id", "evaluation_case", "intake", "entry_reference", "envelope_id", "submission_version", "package_digest", "tenderer_name", "submitted_total", "currency"},
	"Evaluation Check Run": {"run_id", "evaluation_case", "run_number", "reason", "rules_version", "rules_digest", "definition_id", "definition_version", "definition_digest", "status", "superseded_by"},
	"Evaluation Check Result": {
		"result_id", "check_run", "evaluation_bid", "mapping_id", "requirement_key", "response_id", "check_kind", "applicable", "result", "reason", "basis",
		"evidence_assessment_required", "inputs_json", "calculation_json",
	},
	"Evaluation Finding": {"finding_id", "evaluation_bid", "requirement_key", "kind", "result", "reason", "evidence_reference", "author", "recorded_at", "prior_finding", "status", "discussion_item"},
	"Evaluation Discussion Item": {"item_id", "evaluation_bid", "requirement_key", "status", "resolution_kind", "resolution_reference", "cleared_at"},
	"Evaluation Conclusion": {"conclusion_id", "session", "kind", "result", "reason", "evidence_json", "next_action", "recorded_by", "recorded_at", "participants_json", "proceeding_event"},
	"Evaluation Disagreement": {"disagreement_id", "conclusion", "report_version", "member_user", "statement", "recorded_at"},
	"Evaluation Clarification": {
		"clarification_id", "evaluation_bid", "requirement_key", "question", "reply_scope", "reply_deadline", "authorised_by", "authorised_at", "session", "status",
		"sent_at", "notice_state", "notice_attempts", "replaces", "replaced_by", "withdrawal_reason", "disposition", "disposition_reason", "closed_at", "closure_reason",
	},
	"Evaluation Clarification Reply": {"reply_id", "clarification", "organisation", "author_user", "state", "body", "attachments_json", "received_at", "timeliness"},
	"Evaluation Verification Plan": {"plan_id", "version_number", "scope", "basis", "participants_json", "lead_user", "change_reason", "session", "status", "report_state", "report_digest"},
	"Evaluation Verification Observation": {"observation_id", "verification_plan", "participant_user", "findings", "evidence_json", "recorded_at", "status"},
	"Evaluation Report Version": {
		"report_id", "version_number", "state", "narrative", "content_json", "content_digest", "outcome", "recommended_bid", "recommended_total", "frozen_at",
		"change_summary", "supersession_kind", "supersession_reason",
	},
	"Evaluation Report Delivery": {"delivery_id", "report_version", "delivery_key", "recipient_user", "status", "attempts", "delivered_at", "review_state", "downstream_status"},
	"Evaluation Source Event": {"source_event_id", "event_key", "source", "kind", "authority", "instruction_reference", "permitted_actions_json", "impact", "impact_reason", "head_review_state"},
	"Evaluation Correction Notice": {"notice_id", "report_version", "reason", "correction", "recorded_by", "recorded_at", "head_review_state"},
	"Evaluation Command Journal": {"idempotency_key", "command", "payload_hash", "result_json", "actor", "evaluation_case", "recorded_at"},
	"Bid Evaluation Settings": {"presence_lapse_seconds"},
}


def options(doctype: str, field: str) -> list[str]:
	return frappe.get_meta(doctype).get_field(field).options.split("\n")


class TestEvaluationRecords(IntegrationTestCase):
	def test_the_records_carry_the_spec_facts(self):
		for doctype, fields in FIELDS.items():
			with self.subTest(doctype=doctype):
				self.assertEqual(frappe.get_meta(doctype).module, MODULE)
				self.assertEqual(fields - {f.fieldname for f in frappe.get_meta(doctype).fields}, set())

	def test_the_states_are_the_spec_states(self):
		# EVL-CHG-001 v0.4 §7.1: six states; checking, waiting, overdue and
		# suspended are conditions, never states.
		self.assertEqual(options("Evaluation Case", "state"), ["Preparing", "Reviewing", "Signing", "Report sent", "No evaluation required", "Cancelled"])
		# §4.2 results.
		self.assertEqual(options("Evaluation Check Result", "result"), ["Meets", "Does not meet", "Needs review", "Not applicable"])
		self.assertEqual(options("Evaluation Declaration", "choice"), ["No conflict to declare", "Declare a conflict"])
		self.assertEqual(options("Evaluation Committee Member", "capacity"), ["Chair", "Member"])

	def test_once_only_identities(self):
		for doctype, field in (
			("Evaluation Case", "tender"), ("Evaluation Source Intake", "operation_key"), ("Evaluation Report Delivery", "delivery_key"),
			("Evaluation Source Event", "event_key"), ("Evaluation Clarification Reply", "clarification"), ("Evaluation Command Journal", "idempotency_key"),
		):
			with self.subTest(doctype=doctype):
				self.assertTrue(frappe.get_meta(doctype).get_field(field).unique)

	def test_no_role_can_write_an_evaluation_record(self):
		for doctype in RECORDS:
			with self.subTest(doctype=doctype):
				perms = frappe.get_meta(doctype).permissions
				self.assertTrue({p.role for p in perms} <= {"System Manager"}, doctype)
				self.assertFalse([p for p in perms if p.write or p.create or p.delete or p.submit or p.share or p.export], doctype)
		for doctype in NO_ROLE:
			self.assertEqual(frappe.get_meta(doctype).permissions, [])
		self.assertTrue(frappe.get_meta("Evaluation Committee Member").istable)
		self.assertTrue(frappe.get_meta("Bid Evaluation Settings").issingle)

	def test_administrators_cannot_read_bid_content_or_findings(self):
		"""EVL-CHG-001 v0.4 §3 (KT-STD-001 §3A.6): technical readers get no bid
		content, finding, correspondence or report text, not even read-only."""
		for doctype in BID_CONTENT:
			with self.subTest(doctype=doctype):
				self.assertEqual(frappe.get_meta(doctype).permissions, [])

	def test_a_record_changes_only_through_a_command(self):
		doc = frappe.get_doc({"doctype": "Evaluation Finding", "finding_id": "EVL-PROBE", "kind": "Concern", "reason": "probe", "status": "Current"})
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True, ignore_links=True, ignore_mandatory=True)
		self.assertFalse(frappe.db.exists("Evaluation Finding", "EVL-PROBE"))


class TestSupportIssueRecord(IntegrationTestCase):
	"""EVL-CHG-001 v0.4 plan D12 (OD-B): the platform support issue."""

	def test_the_record(self):
		meta = frappe.get_meta("Support Issue")
		self.assertEqual(meta.module, "Kentender Core")
		self.assertTrue(meta.get_field("issue_key").unique)
		self.assertEqual(meta.get_field("status").options.split("\n"), ["Open", "Resolved"])
		self.assertFalse([p for p in meta.permissions if p.write or p.create or p.delete])
		doc = frappe.get_doc({"doctype": "Support Issue", "issue_id": "SI-PROBE", "issue_key": "probe", "module": "x", "operation": "x", "subject": "x",
			"holder_role": "Technical Operator", "status": "Open"})
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True, ignore_links=True, ignore_mandatory=True)
