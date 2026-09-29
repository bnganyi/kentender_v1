# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PRC-CHG-001 v0.9 §5 lifecycle against the simulated owner (BOP10-201,
BOP10-206): PRC-S01, PRC-N07 (never-started part), PRC-N08, PRC-N09, PRC-N10,
PRC-N12. Shared-service evidence only (PRC v0.9 §15)."""

from __future__ import annotations

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
		self.assertEqual((row.state, str(row.actual_start)), ("In session", "2027-06-12 11:00:12"))
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
		self.at("2027-06-12 10:55:00")
		attendance.record_attendance(**ref(), person_name="Test Member", user=MEMBER, capacity="Committee member", movement="Arrival", idempotency_key=self.key(), actor=CHAIR)
		self.at("2027-06-12 10:58:00")
		attendance.record_attendance(**ref(), person_name="Test Visitor", user=VISITOR, capacity="Public observer", movement="Arrival", idempotency_key=self.key(), actor=CHAIR)
		self.at("2027-06-12 10:59:00")
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
		self.at("2027-06-26 11:10:00")
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
		self.at("2027-06-12 11:01:45")
		self.owner_event(created, "ReadoutConfirmed", "readout-1")
		self.at("2027-06-12 11:03:00")
		key = self.key()
		closed = lifecycle.close_aborted(**self.ref(created), cancellation_reference="TEST-CANCEL-1", custody_reference="TEST-CUSTODY", idempotency_key=key, actor=CHAIR)
		replay = lifecycle.close_aborted(**(self.ref(created) | {"expected_version": closed["record_version"] - 1}), cancellation_reference="TEST-CANCEL-1",
			custody_reference="TEST-CUSTODY", idempotency_key=key, actor=CHAIR)
		self.assertEqual(closed, replay)
		row = frappe.db.get_value("Proceeding", created["proceeding"], ["state", "actual_start", "ceased_at", "actual_end"], as_dict=True)
		self.assertEqual((row.state, str(row.actual_start), str(row.ceased_at), row.actual_end), ("Aborted after start", "2027-06-12 11:00:12", "2027-06-12 11:03:00", None))
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
		self.at("2027-06-19 11:01:00")
		outcome = {"event_type": "NoBidsOutcome", "owner_event_id": "zero-1", "payload": {"count": 0}, "note": "No bids to open"}
		ended = lifecycle.end_proceeding(**self.ref(created), owner_event_id="end-zero", outcome_event=outcome, idempotency_key=key, actor=CHAIR)
		replay = lifecycle.end_proceeding(**(self.ref(created) | {"expected_version": ended["record_version"] - 1}), owner_event_id="end-zero", outcome_event=outcome,
			idempotency_key=key, actor=CHAIR)
		self.assertEqual(ended, replay)
		self.assertEqual(count_events(created["proceeding"], "NoBidsOutcome"), 1)
		self.assertEqual(count_events(created["proceeding"], "ProceedingEnded"), 1)
		row = frappe.db.get_value("Proceeding", created["proceeding"], ["state", "actual_end"], as_dict=True)
		self.assertEqual((row.state, str(row.actual_end)), ("Session ended", "2027-06-19 11:01:00"))
		self.assertCode("PRC_VERSION_CONFLICT", lifecycle.mark_not_held, **self.ref(created), reason="x", idempotency_key=self.key(), actor=CHAIR)


class TestRoster(ProceedingsCase):
	def test_a_successor_segment_keeps_the_prior_roster(self):
		created = self.create()
		self.start(created)
		successor = [dict(r) for r in ROSTER]
		successor[2] = successor[2] | {"member_user": VISITOR, "full_name": "Test Visitor", "appointment_reference": "TEST-APPT-2"}
		self.at("2027-06-12 11:05:00")
		lifecycle.add_roster_segment(**self.ref(created), roster=successor, reason="Successor appointed", idempotency_key=self.key(), actor=CHAIR)
		members = frappe.get_doc("Proceeding", created["proceeding"]).members
		self.assertEqual({(m.member_user, m.roster_segment, m.active) for m in members if m.roster_segment == 1 and m.member_user == ROSTER[2]["member_user"]},
			{(ROSTER[2]["member_user"], 1, 0)})
		self.assertIn((VISITOR, 2, 1), {(m.member_user, m.roster_segment, m.active) for m in members})
		self.assertEqual(count_events(created["proceeding"], "RosterSegmentStarted"), 1)
