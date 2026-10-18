# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PRC-CHG-001 v0.9 §5 lifecycle against the simulated owner (BOP10-201,
BOP10-206): PRC-S01, PRC-N07 (never-started part), PRC-N08, PRC-N09, PRC-N10,
PRC-N12. Shared-service evidence only (PRC v0.9 §15)."""

from __future__ import annotations

from kentender_core.seeds.calendar import fiscal as F, world as W  # noqa: F401
import json

import frappe

from kentender_procurement.proceedings.tests.support import CHAIR, MEMBER, OWNER_TYPE, ROSTER, VISITOR, ProceedingsCase, attendance, events, finalize, lifecycle, reads


def count_events(proceeding: str, event_type: str | None = None) -> int:
	filters = {"proceeding": proceeding}
	if event_type:
		filters["event_type"] = event_type
	return frappe.db.count("Proceeding Event", filters)


class TestCreate(ProceedingsCase):
	def test_prc_s01_one_owner_one_proceeding_and_replay_is_safe(self):
		key = self.key()
		self.owner.add("SIM-S01")
		first = lifecycle.create_proceeding(owner_type=OWNER_TYPE, owner_id="SIM-S01", title="Test opening — synthetic bids only", idempotency_key=key, actor=CHAIR)
		again = lifecycle.create_proceeding(owner_type=OWNER_TYPE, owner_id="SIM-S01", title="Test opening — synthetic bids only", idempotency_key=key, actor=CHAIR)
		other_key = lifecycle.create_proceeding(owner_type=OWNER_TYPE, owner_id="SIM-S01", title="Test opening — synthetic bids only", idempotency_key=self.key(), actor=CHAIR)
		self.assertEqual(first, again)
		self.assertEqual(other_key["proceeding"], first["proceeding"])
		self.assertEqual(frappe.db.count("Proceeding", {"owner_id": "SIM-S01"}), 1)
		self.assertEqual(count_events(first["proceeding"], "ProceedingCreated"), 1)
		row = frappe.db.get_value("Proceeding", first["proceeding"], ["state", "actual_start", "actual_end"], as_dict=True)
		self.assertEqual((row.state, row.actual_start, row.actual_end), ("Pending", None, None))

	def test_a_missing_owner_cannot_create(self):
		self.assertCode("PRC_OWNER_UNAVAILABLE", lifecycle.create_proceeding, owner_type=OWNER_TYPE, owner_id="SIM-NOBODY", title="x", idempotency_key=self.key(), actor=CHAIR)
		self.assertCode("PRC_OWNER_UNAVAILABLE", lifecycle.create_proceeding, owner_type="Unknown owner", owner_id="X", title="x", idempotency_key=self.key(), actor=CHAIR)


class TestStart(ProceedingsCase):
	def test_start_records_trusted_time_and_the_roster(self):
		created = self.create()
		started = self.start(created)
		row = frappe.get_doc("Proceeding", created["proceeding"])
		self.assertEqual((row.state, str(row.actual_start)), ("In session", W("2027-06-12 11:00:12")))
		self.assertEqual([m.member_user for m in row.members], [r["member_user"] for r in ROSTER])
		self.assertEqual({m.roster_segment for m in row.members}, {1})
		self.assertEqual(started["state"], "In session")

	def test_a_stale_start_has_no_partial_effect(self):
		created = self.create()
		ref = self.ref(created) | {"expected_version": 99}
		self.assertCode("PRC_VERSION_CONFLICT", lifecycle.start_proceeding, **ref, roster=ROSTER, custody_reference="C", owner_event_id="s", idempotency_key=self.key(), actor=CHAIR)
		self.assertEqual(frappe.db.get_value("Proceeding", created["proceeding"], "state"), "Pending")
		self.assertEqual(count_events(created["proceeding"]), 1)

	def test_start_twice_is_blocked(self):
		created = self.create()
		self.start(created)
		self.assertCode("PRC_START_BLOCKED", self.start, created)

	def test_prc_n08_pre_session_arrivals_carry_into_the_session_without_a_second_arrival(self):
		created = self.create()
		ref = lambda: self.ref(created)  # noqa: E731
		self.at(W("2027-06-12 10:55:00"))
		attendance.record_attendance(**ref(), person_name="Test Member", user=MEMBER, capacity="Committee member", movement="Arrival", idempotency_key=self.key(), actor=CHAIR)
		self.at(W("2027-06-12 10:58:00"))
		attendance.record_attendance(**ref(), person_name="Test Visitor", user=VISITOR, capacity="Public observer", movement="Arrival", idempotency_key=self.key(), actor=CHAIR)
		self.at(W("2027-06-12 10:59:00"))
		attendance.record_attendance(**ref(), person_name="Test Member", user=MEMBER, capacity="Committee member", movement="Departure", idempotency_key=self.key(), actor=CHAIR)
		rows = frappe.get_all("Proceeding Attendance", filters={"proceeding": created["proceeding"]}, fields=["pre_session", "movement"])
		self.assertEqual({r.pre_session for r in rows}, {1})
		self.assertIsNone(frappe.db.get_value("Proceeding", created["proceeding"], "actual_start"))
		self.assertEqual(count_events(created["proceeding"], "ProceedingStarted"), 0)

		self.start(created)
		self.assertEqual(frappe.db.count("Proceeding Attendance", {"proceeding": created["proceeding"]}), 3)
		view = reads.read_proceeding(owner_type=OWNER_TYPE, owner_id=self.owner_id(created), user=CHAIR)
		present = {(p["person_name"], p["pre_session"]) for p in view["present"]}
		self.assertEqual(present, {("Test Visitor", 1)})
		started = frappe.get_all("Proceeding Event", filters={"proceeding": created["proceeding"], "event_type": "ProceedingStarted"}, fields=["note"])
		self.assertEqual(len(started), 1)
		self.assertEqual([p["person_name"] for p in json.loads(started[0].note)], ["Test Visitor"])

	def test_an_active_arrival_cannot_be_recorded_twice(self):
		created = self.create()
		attendance.record_attendance(**self.ref(created), person_name="Test Visitor", user=VISITOR, capacity="Public observer", movement="Arrival", idempotency_key=self.key(), actor=CHAIR)
		self.assertCode("PRC_VERSION_CONFLICT", attendance.record_attendance, **self.ref(created), person_name="Test Visitor", user=VISITOR, capacity="Public observer",
			movement="Arrival", idempotency_key=self.key(), actor=CHAIR)
		self.assertCode("PRC_VERSION_CONFLICT", attendance.record_attendance, **self.ref(created), person_name="Nobody", capacity="Public observer",
			movement="Departure", idempotency_key=self.key(), actor=CHAIR)

	def owner_id(self, created) -> str:
		return frappe.db.get_value("Proceeding", created["proceeding"], "owner_id")


class TestTerminalOutcomes(ProceedingsCase):
	def test_prc_n10_not_held_is_terminal(self):
		created = self.create()
		self.at(W("2027-06-26 11:10:00"))
		out = lifecycle.mark_not_held(**self.ref(created), reason="The public attendance service was unavailable; opening did not start", custody_reference="TEST-CUSTODY",
			idempotency_key=self.key(), actor=CHAIR)
		self.assertEqual(out["state"], "Not held")
		row = frappe.db.get_value("Proceeding", created["proceeding"], ["actual_start", "actual_end", "not_held_reason"], as_dict=True)
		self.assertEqual((row.actual_start, row.actual_end), (None, None))
		self.assertCode("PRC_START_BLOCKED", self.start, created)
		self.assertCode("PRC_VERSION_CONFLICT", finalize.finalize_proceeding, **self.ref(created), idempotency_key=self.key(), actor=CHAIR)
		self.assertCode("PRC_VERSION_CONFLICT", self.owner_event, created, "CustodyParticipation", "late")
		self.assertEqual(frappe.db.count("Proceeding Minutes Version", {"proceeding": created["proceeding"]}), 0)

	def test_a_started_session_cannot_be_relabelled_not_held(self):
		created = self.create()
		self.start(created)
		self.assertCode("PRC_VERSION_CONFLICT", lifecycle.mark_not_held, **self.ref(created), reason="x", idempotency_key=self.key(), actor=CHAIR)

	def test_prc_n09_cancellation_after_start_closes_the_partial_session(self):
		created = self.create()
		self.start(created)
		self.at(W("2027-06-12 11:01:45"))
		self.owner_event(created, "ReadoutConfirmed", "readout-1")
		self.at(W("2027-06-12 11:03:00"))
		key = self.key()
		closed = lifecycle.close_aborted(**self.ref(created), cancellation_reference="TEST-CANCEL-1", custody_reference="TEST-CUSTODY", idempotency_key=key, actor=CHAIR)
		replay = lifecycle.close_aborted(**(self.ref(created) | {"expected_version": closed["record_version"] - 1}), cancellation_reference="TEST-CANCEL-1",
			custody_reference="TEST-CUSTODY", idempotency_key=key, actor=CHAIR)
		self.assertEqual(closed, replay)
		row = frappe.db.get_value("Proceeding", created["proceeding"], ["state", "actual_start", "ceased_at", "actual_end"], as_dict=True)
		self.assertEqual((row.state, str(row.actual_start), str(row.ceased_at), row.actual_end), ("Aborted after start", W("2027-06-12 11:00:12"), W("2027-06-12 11:03:00"), None))
		self.assertEqual(count_events(created["proceeding"], "ReadoutConfirmed"), 1)
		self.assertCode("PRC_START_BLOCKED", self.start, created)
		self.assertCode("PRC_VERSION_CONFLICT", self.end, created)
		self.assertCode("PRC_VERSION_CONFLICT", self.freeze, created)
		self.assertCode("PRC_VERSION_CONFLICT", finalize.finalize_proceeding, **self.ref(created), idempotency_key=self.key(), actor=CHAIR)

	def test_abort_needs_an_actual_start(self):
		created = self.create()
		self.assertCode("PRC_VERSION_CONFLICT", lifecycle.close_aborted, **self.ref(created), cancellation_reference="C", custody_reference="C", idempotency_key=self.key(), actor=CHAIR)


class TestEmptyOutcome(ProceedingsCase):
	def test_prc_n12_empty_outcome_and_end_commit_once(self):
		created = self.create()
		self.assertCode("PRC_VERSION_CONFLICT", self.end, created, outcome_event={"event_type": "NoBidsOutcome", "owner_event_id": "zero-early", "payload": {"count": 0}})
		self.start(created)
		key = self.key()
		self.at(W("2027-06-19 11:01:00"))
		outcome = {"event_type": "NoBidsOutcome", "owner_event_id": "zero-1", "payload": {"count": 0}, "note": "No bids to open"}
		ended = lifecycle.end_proceeding(**self.ref(created), owner_event_id="end-zero", outcome_event=outcome, idempotency_key=key, actor=CHAIR)
		replay = lifecycle.end_proceeding(**(self.ref(created) | {"expected_version": ended["record_version"] - 1}), owner_event_id="end-zero", outcome_event=outcome,
			idempotency_key=key, actor=CHAIR)
		self.assertEqual(ended, replay)
		self.assertEqual(count_events(created["proceeding"], "NoBidsOutcome"), 1)
		self.assertEqual(count_events(created["proceeding"], "ProceedingEnded"), 1)
		row = frappe.db.get_value("Proceeding", created["proceeding"], ["state", "actual_end"], as_dict=True)
		self.assertEqual((row.state, str(row.actual_end)), ("Session ended", W("2027-06-19 11:01:00")))
		self.assertCode("PRC_VERSION_CONFLICT", lifecycle.mark_not_held, **self.ref(created), reason="x", idempotency_key=self.key(), actor=CHAIR)


class TestRoster(ProceedingsCase):
	def test_a_successor_segment_keeps_the_prior_roster(self):
		created = self.create()
		self.start(created)
		successor = [dict(r) for r in ROSTER]
		successor[2] = successor[2] | {"member_user": VISITOR, "full_name": "Test Visitor", "appointment_reference": "TEST-APPT-2"}
		self.at(W("2027-06-12 11:05:00"))
		lifecycle.add_roster_segment(**self.ref(created), roster=successor, reason="Successor appointed", idempotency_key=self.key(), actor=CHAIR)
		members = frappe.get_doc("Proceeding", created["proceeding"]).members
		self.assertEqual({(m.member_user, m.roster_segment, m.active) for m in members if m.roster_segment == 1 and m.member_user == ROSTER[2]["member_user"]},
			{(ROSTER[2]["member_user"], 1, 0)})
		self.assertIn((VISITOR, 2, 1), {(m.member_user, m.roster_segment, m.active) for m in members})
		self.assertEqual(count_events(created["proceeding"], "RosterSegmentStarted"), 1)


class TestCancellationLineage(ProceedingsCase):
	"""PRC-CHG-001 v0.14 §5, §7.2 (PRC-OF-AC-006, AC-007): the TPR cancellation ID deduplicates closure. An identical replay (even with a new key) returns the
	first closure; a conflicting cancellation or a wrong state fails with no change; the closure keeps the authoritative source time and the receipt time
	apart; a cancellation arriving after Not held is attached to that record without relabelling or re-opening it."""

	def test_closing_after_start_keeps_the_source_time_and_the_receipt_time_apart_and_the_replay_returns_the_first_closure(self):
		created = self.create()
		self.start(created)
		self.at(W("2027-06-12 11:01:45"))
		self.owner_event(created, "ReadoutConfirmed", "readout-1")
		self.at(W("2027-06-12 11:09:00"))  # delivery runs later than the decision
		first = lifecycle.close_aborted(**self.ref(created), cancellation_reference="TCN-LINEAGE-1", custody_reference="TEST-CUSTODY", idempotency_key=self.key(), actor=CHAIR,
			source_at=W("2027-06-12 11:03:00"))
		row = frappe.db.get_value("Proceeding", created["proceeding"], ["state", "ceased_at", "cancellation_source_at", "cancellation_received_at"], as_dict=True)
		self.assertEqual((row.state, str(row.ceased_at), str(row.cancellation_source_at), str(row.cancellation_received_at)),
			("Aborted after start", W("2027-06-12 11:03:00"), W("2027-06-12 11:03:00"), W("2027-06-12 11:09:00")))
		before = count_events(created["proceeding"])
		# the same cancellation delivered again, under a new key and at the current version: the first closure, no second event
		again = lifecycle.close_aborted(**self.ref(created), cancellation_reference="TCN-LINEAGE-1", custody_reference="TEST-CUSTODY", idempotency_key=self.key(), actor=CHAIR,
			source_at=W("2027-06-12 11:03:00"))
		self.assertEqual((again["event_id"], again["state"]), (first["event_id"], "Aborted after start"))
		self.assertEqual(count_events(created["proceeding"]), before)
		self.assertEqual(count_events(created["proceeding"], "ProceedingAborted"), 1)
		# a different cancellation is a conflict and changes nothing
		self.assertCode("PRC_VERSION_CONFLICT", lifecycle.close_aborted, **self.ref(created), cancellation_reference="TCN-OTHER", custody_reference="TEST-CUSTODY",
			idempotency_key=self.key(), actor=CHAIR)
		self.assertEqual(count_events(created["proceeding"]), before)
		self.assertEqual(frappe.db.get_value("Proceeding", created["proceeding"], "cancellation_reference"), "TCN-LINEAGE-1")

	def test_not_held_before_start_by_cancellation_is_once_and_a_replay_returns_the_first(self):
		created = self.create()
		self.at(W("2027-06-26 11:10:00"))
		first = lifecycle.mark_not_held(**self.ref(created), reason="The Tender was cancelled before the opening.", cancellation_reference="TCN-LINEAGE-2", custody_reference="TEST-CUSTODY",
			idempotency_key=self.key(), actor=CHAIR, source_at=W("2027-06-26 11:05:00"))
		row = frappe.db.get_value("Proceeding", created["proceeding"], ["state", "cancellation_source_at", "cancellation_received_at"], as_dict=True)
		self.assertEqual((row.state, str(row.cancellation_source_at), str(row.cancellation_received_at)), ("Not held", W("2027-06-26 11:05:00"), W("2027-06-26 11:10:00")))
		again = lifecycle.mark_not_held(**self.ref(created), reason="The Tender was cancelled before the opening.", cancellation_reference="TCN-LINEAGE-2",
			custody_reference="TEST-CUSTODY", idempotency_key=self.key(), actor=CHAIR)
		self.assertEqual(again["event_id"], first["event_id"])
		self.assertEqual(count_events(created["proceeding"], "ProceedingNotHeld"), 1)
		self.assertCode("PRC_VERSION_CONFLICT", lifecycle.mark_not_held, **self.ref(created), reason="x", cancellation_reference="TCN-OTHER", idempotency_key=self.key(), actor=CHAIR)

	def test_a_cancellation_after_a_factual_not_held_is_attached_without_relabelling_the_record(self):
		created = self.create()
		self.at(W("2027-06-26 11:10:00"))
		lifecycle.mark_not_held(**self.ref(created), reason="The public attendance service was unavailable; opening did not start", custody_reference="TEST-CUSTODY",
			idempotency_key=self.key(), actor=CHAIR)
		self.assertEqual(frappe.db.get_value("Proceeding", created["proceeding"], "cancellation_reference") or "", "")
		self.at(W("2027-06-26 14:00:00"))
		attached = lifecycle.attach_cancellation(**self.ref(created), cancellation_reference="TCN-LINEAGE-3", idempotency_key=self.key(), actor=CHAIR, source_at=W("2027-06-26 13:00:00"))
		row = frappe.db.get_value("Proceeding", created["proceeding"], ["state", "not_held_reason", "cancellation_reference", "cancellation_source_at", "cancellation_received_at", "actual_start"], as_dict=True)
		self.assertEqual((row.state, row.cancellation_reference, str(row.cancellation_source_at), str(row.cancellation_received_at), row.actual_start),
			("Not held", "TCN-LINEAGE-3", W("2027-06-26 13:00:00"), W("2027-06-26 14:00:00"), None))
		self.assertIn("attendance service was unavailable", row.not_held_reason)  # the factual reason is untouched
		self.assertEqual(count_events(created["proceeding"], "ProceedingCancellationReceived"), 1)
		again = lifecycle.attach_cancellation(**self.ref(created), cancellation_reference="TCN-LINEAGE-3", idempotency_key=self.key(), actor=CHAIR)
		self.assertEqual((again["event_id"], count_events(created["proceeding"], "ProceedingCancellationReceived")), (attached["event_id"], 1))
		self.assertCode("PRC_VERSION_CONFLICT", lifecycle.attach_cancellation, **self.ref(created), cancellation_reference="TCN-OTHER", idempotency_key=self.key(), actor=CHAIR)
		# still terminal: no start, no finalisation
		self.assertCode("PRC_START_BLOCKED", self.start, created)

	def test_attach_needs_a_not_held_record_and_a_reference(self):
		created = self.create()
		self.assertCode("PRC_VERSION_CONFLICT", lifecycle.attach_cancellation, **self.ref(created), cancellation_reference="TCN-X", idempotency_key=self.key(), actor=CHAIR)
		self.at(W("2027-06-26 11:10:00"))
		lifecycle.mark_not_held(**self.ref(created), reason="Did not start", custody_reference="C", idempotency_key=self.key(), actor=CHAIR)
		self.assertCode("PRC_EVIDENCE_INCOMPLETE", lifecycle.attach_cancellation, **self.ref(created), cancellation_reference=" ", idempotency_key=self.key(), actor=CHAIR)
