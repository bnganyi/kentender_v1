# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PRC-CHG-001 v0.9 §4 and BOP-CHG-001 v0.10 plan D1/D2 (BOP10-102, BOP10-104):
the Proceedings records carry the spec's facts under its names, change only
through Proceedings commands, give no role a write path, and never import
their first owner."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

MODULE = "Proceedings"
RECORDS = ("Proceeding", "Proceeding Attendance", "Proceeding Event", "Proceeding Minutes Version", "Proceeding Attestation", "Proceeding Supplement")
CHILDREN = ("Proceeding Member", "Proceeding Minutes Target")
NO_ROLE = ("Proceeding Command Journal",)
FIELDS = {
	"Proceeding": {
		"proceeding_id", "owner_type", "owner_id", "owner_key", "proceeding_type", "title", "state", "created_at", "created_by", "actual_start", "actual_end",
		"ceased_at", "not_held_reason", "cancellation_reference", "custody_reference", "current_minutes_version", "finalized_at", "members", "record_version",
	},
	"Proceeding Member": {"member_user", "full_name", "designation", "committee_capacity", "appointment_reference", "roster_segment", "active"},
	"Proceeding Attendance": {
		"attendance_id", "proceeding", "person_name", "user", "capacity", "represented_tenderer", "movement", "pre_session", "occurred_at", "reported_at", "recorded_by", "event",
	},
	"Proceeding Event": {
		"event_id", "proceeding", "sequence", "event_type", "recorded_at", "actor", "source", "owner_event_id", "event_key", "payload_digest", "owner_reference", "note",
		"reported_at", "reported_by", "pre_session", "linked_event",
	},
	"Proceeding Minutes Version": {
		"minutes_version_id", "proceeding", "version_number", "content", "content_digest", "page_count", "register_reference", "register_digest", "event_ids_json",
		"authored_by", "frozen_at", "frozen_by", "state", "supersedes_version", "supersede_reason", "targets",
	},
	"Proceeding Minutes Target": {"target_id", "target_type", "target_reference", "page_number", "target_digest", "required_member", "roster_segment"},
	"Proceeding Attestation": {
		"attestation_id", "proceeding", "minutes_version", "target_id", "target_digest", "member_user", "action", "method", "recorded_at", "proof_reference",
		"correlation_id", "verification_result", "satisfies_current",
	},
	"Proceeding Supplement": {"supplement_id", "proceeding", "original_version", "kind", "correct_information", "reason", "evidence_reference", "author", "recorded_at"},
	"Proceeding Command Journal": {"idempotency_key", "command", "payload_hash", "result_json", "actor", "proceeding", "recorded_at"},
}


def options(doctype: str, field: str) -> list[str]:
	return frappe.get_meta(doctype).get_field(field).options.split("\n")


class TestProceedingsRecords(IntegrationTestCase):
	def test_the_records_carry_the_spec_facts(self):
		for doctype, fields in FIELDS.items():
			with self.subTest(doctype=doctype):
				self.assertEqual(frappe.get_meta(doctype).module, MODULE)
				self.assertEqual(fields - {f.fieldname for f in frappe.get_meta(doctype).fields}, set())

	def test_the_lifecycle_states_are_the_spec_states(self):
		# PRC-CHG-001 v0.9 §5, including the two terminal failure states.
		self.assertEqual(options("Proceeding", "state"), ["Pending", "In session", "Session ended", "Awaiting attestations", "Finalized", "Not held", "Aborted after start"])
		# TRUST-ADR-001 v0.1 §4: four distinct trust outcomes.
		self.assertEqual(options("Proceeding Attestation", "verification_result"), ["Accepted/Verified", "Rejected", "Unavailable", "Indeterminate"])

	def test_one_session_per_owner_and_one_event_per_owner_event_id(self):
		self.assertTrue(frappe.get_meta("Proceeding").get_field("owner_key").unique)
		self.assertTrue(frappe.get_meta("Proceeding Event").get_field("event_key").unique)
		self.assertTrue(frappe.get_meta("Proceeding Command Journal").get_field("idempotency_key").unique)

	def test_children_are_tables(self):
		for doctype in CHILDREN:
			with self.subTest(doctype=doctype):
				self.assertTrue(frappe.get_meta(doctype).istable)

	def test_no_role_can_write_a_proceedings_record(self):
		for doctype in RECORDS:
			with self.subTest(doctype=doctype):
				perms = frappe.get_meta(doctype).permissions
				self.assertTrue({p.role for p in perms} <= {"System Manager"}, doctype)
				self.assertFalse([p for p in perms if p.write or p.create or p.delete or p.submit or p.share or p.export], doctype)
		for doctype in NO_ROLE:
			self.assertEqual(frappe.get_meta(doctype).permissions, [])

	def test_a_record_changes_only_through_a_command(self):
		doc = frappe.get_doc({"doctype": "Proceeding Event", "event_id": "PRC-PROBE", "proceeding": "PRC-PROBE", "sequence": 1, "event_type": "Probe"})
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True, ignore_links=True, ignore_mandatory=True)
		self.assertFalse(frappe.db.exists("Proceeding Event", "PRC-PROBE"))

	def test_proceedings_never_imports_its_owner(self):
		# Plan D1: the shared service knows its owner only through a hook.
		root = Path(frappe.get_app_path("kentender_procurement", "proceedings"))
		offenders = [str(p) for p in root.rglob("*.py") if p.name != "test_prc_schema.py" and "bid_opening" in p.read_text(encoding="utf-8")]
		self.assertEqual(offenders, [])
