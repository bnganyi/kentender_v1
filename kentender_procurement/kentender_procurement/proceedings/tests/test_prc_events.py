# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PRC-CHG-001 v0.9 §4 Event and §7 AppendProceedingEvent (BOP10-202):
PRC-N01 (replay and conflict), PRC-N11 (trusted and reported time), the
Pending allow-list, and member/recorder authorship."""

from __future__ import annotations

import frappe

from kentender_procurement.proceedings.tests.support import CHAIR, INDEPENDENT, MEMBER, OUTSIDER, ProceedingsCase, events


class TestReplay(ProceedingsCase):
	def test_prc_n01_same_owner_event_id_replays_and_a_different_payload_fails(self):
		created = self.create()
		self.start(created)
		self.at("2027-06-12 11:01:00")
		first = self.owner_event(created, "PackageRevealed", "reveal-1", payload={"envelope": "ENV-TEST-1"})
		again = self.owner_event(created, "PackageRevealed", "reveal-1", payload={"envelope": "ENV-TEST-1"})
		self.assertEqual(first["event_id"], again["event_id"])
		before = frappe.db.get_value("Proceeding Event", first["event_id"], ["payload_digest", "sequence", "recorded_at"], as_dict=True)
		self.assertCode("PRC_VERSION_CONFLICT", self.owner_event, created, "PackageRevealed", "reveal-1", payload={"envelope": "ENV-TEST-OTHER"})
		after = frappe.db.get_value("Proceeding Event", first["event_id"], ["payload_digest", "sequence", "recorded_at"], as_dict=True)
		self.assertEqual(before, after)
		self.assertEqual(frappe.db.count("Proceeding Event", {"proceeding": created["proceeding"], "owner_event_id": "reveal-1"}), 1)

	def test_events_are_ordered_by_server_sequence_and_time(self):
		created = self.create()
		self.start(created)
		self.at("2027-06-12 11:01:00")
		a = self.owner_event(created, "PackageRevealed", "reveal-1")
		self.at("2027-06-12 11:01:45")
		b = self.owner_event(created, "ReadoutConfirmed", "readout-1", linked_event=a["event_id"])
		rows = frappe.get_all("Proceeding Event", filters={"proceeding": created["proceeding"]}, fields=["event_id", "sequence"], order_by="sequence asc")
		sequences = [r.sequence for r in rows]
		self.assertEqual(sequences, sorted(set(sequences)))
		self.assertLess(frappe.db.get_value("Proceeding Event", a["event_id"], "sequence"), frappe.db.get_value("Proceeding Event", b["event_id"], "sequence"))


class TestReportedTime(ProceedingsCase):
	def test_prc_n11_confirmation_keeps_trusted_time_and_attributes_the_speech_time(self):
		created = self.create()
		self.start(created)
		self.at("2027-06-12 11:01:00")
		reveal = self.owner_event(created, "PackageRevealed", "reveal-1")
		self.at("2027-06-12 11:01:45")
		readout = self.owner_event(created, "ReadoutConfirmed", "readout-1", linked_event=reveal["event_id"], reported_at="2027-06-12 11:01:30", reported_by=CHAIR)
		row = frappe.db.get_value("Proceeding Event", readout["event_id"], ["recorded_at", "reported_at", "reported_by"], as_dict=True)
		self.assertEqual((str(row.recorded_at), str(row.reported_at), row.reported_by), ("2027-06-12 11:01:45", "2027-06-12 11:01:30", CHAIR))

	def test_a_confirmation_before_its_reveal_fails(self):
		created = self.create()
		self.start(created)
		self.assertCode("PRC_EVIDENCE_INCOMPLETE", self.owner_event, created, "ReadoutConfirmed", "readout-early", linked_event="PRC-EVT-NOT-THERE")

	def test_a_reported_time_needs_an_author_and_cannot_be_in_the_future(self):
		created = self.create()
		self.start(created)
		self.at("2027-06-12 11:01:45")
		self.assertCode("PRC_EVIDENCE_INCOMPLETE", self.owner_event, created, "ReadoutConfirmed", "r-1", reported_at="2027-06-12 11:01:30")
		self.assertCode("PRC_EVIDENCE_INCOMPLETE", self.owner_event, created, "ReadoutConfirmed", "r-2", reported_at="2027-06-12 11:05:00", reported_by=CHAIR)


class TestPendingAllowList(ProceedingsCase):
	def test_pending_accepts_custody_and_one_closed_manifest_reference_only(self):
		created = self.create()
		self.owner_event(created, "CustodyParticipation", "custody-1")
		self.owner_event(created, "ClosedManifestReference", "manifest-1", payload={"manifest": "opaque"})
		self.assertCode("PRC_VERSION_CONFLICT", self.owner_event, created, "ClosedManifestReference", "manifest-2", payload={"manifest": "other"})
		self.assertCode("PRC_VERSION_CONFLICT", self.owner_event, created, "PackageRevealed", "reveal-early")
		rows = frappe.get_all("Proceeding Event", filters={"proceeding": created["proceeding"], "source": "Owner"}, fields=["pre_session"])
		self.assertEqual({r.pre_session for r in rows}, {1})
		self.assertIsNone(frappe.db.get_value("Proceeding", created["proceeding"], "actual_start"))


class TestAuthorship(ProceedingsCase):
	def test_a_member_records_their_own_account_and_the_recorder_links_a_response(self):
		created = self.create()
		self.start(created)
		self.at("2027-06-12 11:02:25")
		account = events.append_event(**self.ref(created), event_type="MemberAccount", source="Member", note="I could not hear the security reference clearly.",
			idempotency_key=self.key(), actor=INDEPENDENT)
		self.at("2027-06-12 11:02:40")
		response = events.append_event(**self.ref(created), event_type="RecorderResponse", source="Recorder", note="The reference was repeated.",
			linked_event=account["event_id"], idempotency_key=self.key(), actor=CHAIR)
		self.assertEqual(frappe.db.get_value("Proceeding Event", account["event_id"], "actor"), INDEPENDENT)
		self.assertEqual(frappe.db.get_value("Proceeding Event", response["event_id"], ["actor", "linked_event"]), (CHAIR, account["event_id"]))

	def test_nobody_writes_another_persons_account_or_the_recorders_note(self):
		created = self.create()
		self.start(created)
		self.assertCode("PRC_MEMBER_REQUIRED", events.append_event, **self.ref(created), event_type="MemberAccount", source="Member", note="x", idempotency_key=self.key(), actor=OUTSIDER)
		self.assertCode("PRC_OWNER_UNAVAILABLE", events.append_event, **self.ref(created), event_type="RecorderNote", source="Recorder", note="x", idempotency_key=self.key(), actor=MEMBER)
