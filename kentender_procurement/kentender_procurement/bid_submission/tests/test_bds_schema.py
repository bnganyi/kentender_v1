# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §4.3, §4.5, §8 and plan D2/D12 (BDS8-501): the Bid
Submission records carry the spec's facts under its names, change only
through Bid Submission commands, give no role a write path, and the error
contract is §8's closed set."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.bid_submission.services import errors

RECORDS = ("Bidder Arrangement", "Bid Workspace", "Bid Organisation Snapshot", "Bid Command Journal", "Bid Submission Event", "Bid Submission Attempt", "Bid Submission Version", "Tender Box Envelope", "Bid Receipt")
#: OD-C simulation state: no role reads or writes it at all.
SIMULATION = ("Test Trust Certificate", "Test Trust Signature", "BDS Test Environment Controls")
FIELDS = {
	# §4.3 BidderArrangement
	"Bidder Arrangement": {
		"bidder_arrangement_id", "tender", "arrangement_type", "lead_organisation", "members", "joint_venture_name", "agreement_evidence",
		"authorised_signatory_assignment", "tender_contact_user", "tender_contact_email", "tender_contact_phone", "candidate_registered_at",
		"mandatory_notice_email", "notice_contact_version", "notice_contacts", "status", "record_version",
	},
	# §4.5 BidWorkspace
	"Bid Workspace": {
		"bid_reference", "tender", "bidder_arrangement", "bid_definition_id", "definition_version", "definition_digest", "organisation_snapshot",
		"organisation_snapshot_version", "status", "current_draft_version", "current_submission_version", "created_by", "created_at", "last_saved_by",
		"last_saved_at", "record_version",
	},
	# §4.9 BidSubmissionVersion
	"Bid Submission Version": {
		"bid_submission_version_id", "version_number", "bid_workspace", "bid_definition_id", "definition_digest", "organisation_snapshot", "organisation_snapshot_version",
		"response_snapshot_digest", "evidence_set_digest", "package_digest", "signed_by", "signed_at", "signature_certificate_ref", "signature_verification_evidence",
		"received_at", "accepted_at", "status", "predecessor_submission_version", "tender_box_envelope", "receipt",
	},
	# §4.10 TenderBoxEnvelope and BidReceipt
	"Tender Box Envelope": {"envelope_id", "tender", "submission_version", "package_digest", "accepted_at", "custody_receipt", "box_state"},
	"Bid Receipt": {
		"receipt_reference", "tender_reference", "tender_title", "bidder_name", "submission_version", "version_number", "received_at", "accepted_at", "submitted_by",
		"predecessor_receipt",
	},
}


class TestBidSubmissionRecords(IntegrationTestCase):
	def test_the_records_carry_the_spec_facts(self):
		for doctype, fields in FIELDS.items():
			with self.subTest(doctype=doctype):
				self.assertEqual(frappe.get_meta(doctype).module, "Bid Submission")
				self.assertEqual(fields - {f.fieldname for f in frappe.get_meta(doctype).fields}, set())
		self.assertEqual(frappe.get_meta("Bid Workspace").get_field("status").options.split("\n"), ["Draft", "Needs attention", "Ready to submit", "Submitted", "Withdrawn", "Closed without submission"])
		self.assertEqual(frappe.get_meta("Bidder Arrangement").get_field("arrangement_type").options.split("\n"), ["Single organisation", "Joint venture"])

	def test_no_role_can_write_a_bid_record(self):
		for doctype in RECORDS:
			with self.subTest(doctype=doctype):
				perms = frappe.get_meta(doctype).permissions
				self.assertTrue({p.role for p in perms} <= {"System Manager"}, doctype)
				self.assertFalse([p for p in perms if p.write or p.create or p.delete or p.submit], doctype)

	def test_no_role_can_touch_the_simulation_state(self):
		for doctype in SIMULATION:
			with self.subTest(doctype=doctype):
				self.assertEqual(frappe.get_meta(doctype).permissions, [])
		self.assertEqual(frappe.get_meta("Bid Submission Version").get_field("status").options.split("\n"), ["Submitted", "Superseded", "Withdrawn"])

	def test_a_bid_record_changes_only_through_a_command(self):
		doc = frappe.get_doc({"doctype": "Bid Submission Event", "event_type": "Probe"})
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)
		self.assertFalse(frappe.db.exists("Bid Submission Event", {"event_type": "Probe"}))


class TestErrorContract(IntegrationTestCase):
	def test_the_contract_is_the_closed_section_8_set(self):
		self.assertEqual(len(errors.ERROR_CODES), 34)
		with self.assertRaises(errors.BidSubmissionError) as ctx:
			errors.fail("BDS_NOTICE_CONTACT_REQUIRED")
		self.assertEqual((ctx.exception.code, str(ctx.exception)), ("BDS_NOTICE_CONTACT_REQUIRED", "Choose a verified email for Tender notices."))
		with self.assertRaises(ValueError):
			errors.fail("BDS_SOMETHING_NEW")

	def test_a_correctable_input_is_data_not_an_exception(self):
		self.assertEqual(errors.field_errors({"joint_venture_name": "Enter the joint-venture name."})["code"], "BDS_FIELD_INVALID")
