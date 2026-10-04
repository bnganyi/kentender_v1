# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Bid Evaluation profile of Proceedings (EVL-CHG-001 v0.4 §6 "PRC change
is explicit", plan D4; tracker EVL4-201…206), against a simulated owner:
several actual sessions with one active at a time; the chair's attendance
recorded by Start; personal join and leave; a conclusion only with the whole
required roster present; member-authored statements; report and verification
report versions with exact targets and personal proofs; completion without
finalizing the case; corrections appended. A pass here is shared-service
evidence only (PRC-CHG-001 v0.9 §15)."""

from __future__ import annotations

from itertools import count
from typing import Any

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.proceedings.services import lifecycle, record_versions, sessions
from kentender_procurement.proceedings.services.errors import ProceedingsError
from kentender_procurement.proceedings.test_services.evaluation_owner import SimulatedEvaluationOwner
from kentender_procurement.proceedings.tests.support import CHAIR, INDEPENDENT, MEMBER, OUTSIDER, VISITOR, ensure_people, remove_people, wipe

OWNER_TYPE = SimulatedEvaluationOwner.OWNER_TYPE
SECRETARY = VISITOR  # a test user who records but is not a member
MEMBERS = (CHAIR, MEMBER, INDEPENDENT)
ROSTER = [
	{"member_user": CHAIR, "full_name": "Test Chair", "designation": "Test designation", "committee_capacity": "Chair", "appointment_reference": "TEST-EVAL-1"},
	{"member_user": MEMBER, "full_name": "Test Member", "designation": "Test designation", "committee_capacity": "Member", "appointment_reference": "TEST-EVAL-1"},
	{"member_user": INDEPENDENT, "full_name": "Test Independent", "designation": "Test designation", "committee_capacity": "Member", "appointment_reference": "TEST-EVAL-1"},
]


class TestEvaluationProfile(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_people()
		cls.addClassCleanup(remove_people)
		cls.addClassCleanup(wipe)

	def setUp(self):
		self.owner = SimulatedEvaluationOwner(chair=CHAIR, secretary=SECRETARY, members=list(MEMBERS), readers=[*MEMBERS, SECRETARY])
		self._flag("kt_prc_owner_adapters", {OWNER_TYPE: self.owner})
		self._flag("kt_prc_fixture_namespace", "prc-contract-test")
		self._flag("kt_prc_signing_outcome", None)
		self._keys = count(1)
		self.addCleanup(wipe)
		self.owner_id = f"SIM-EVL-{frappe.generate_hash(length=6)}"
		self.owner.add(self.owner_id)
		self.at("2027-06-11 09:00:00")
		self.created = lifecycle.create_proceeding(owner_type=OWNER_TYPE, owner_id=self.owner_id, title="Test evaluation", idempotency_key=self.key(), actor=CHAIR)

	def _flag(self, name: str, value) -> None:
		previous = frappe.flags.get(name)
		frappe.flags[name] = value
		self.addCleanup(lambda: frappe.flags.__setitem__(name, previous))

	def at(self, instant: str) -> None:
		self._flag("kt_prc_clock", instant)

	def key(self) -> str:
		return f"prce-{frappe.generate_hash(length=8)}-{next(self._keys)}"

	def ref(self) -> dict[str, Any]:
		version = frappe.db.get_value("Proceeding", self.created["proceeding"], "record_version")
		return {"owner_type": OWNER_TYPE, "owner_id": self.owner_id, "expected_version": int(version)}

	def assertCode(self, code: str, fn, *args, **kwargs) -> ProceedingsError:
		with self.assertRaises(ProceedingsError) as ctx:
			fn(*args, **kwargs)
		self.assertEqual(ctx.exception.code, code)
		return ctx.exception

	# -- helpers --------------------------------------------------------------
	def roster(self, roster=ROSTER, reason: str = "Appointed") -> dict[str, Any]:
		return sessions.record_roster(**self.ref(), roster=roster, reason=reason, owner_event_id=f"roster-{frappe.generate_hash(length=6)}", idempotency_key=self.key(),
			actor=CHAIR)

	def start(self, at: str = "2027-06-14 09:00:00") -> dict[str, Any]:
		self.at(at)
		return sessions.start_session(**self.ref(), subject="Service-location evidence", idempotency_key=self.key(), actor=CHAIR)

	def join(self, user: str, capacity: str = "Committee member") -> dict[str, Any]:
		return sessions.join_session(**self.ref(), capacity=capacity, idempotency_key=self.key(), actor=user)

	def leave(self, user: str, capacity: str = "Committee member") -> dict[str, Any]:
		return sessions.leave_session(**self.ref(), capacity=capacity, idempotency_key=self.key(), actor=user)

	def conclude(self, owner_event_id: str = "", required=MEMBERS) -> dict[str, Any]:
		return sessions.record_conclusion(**self.ref(), event_type="CommitteeConclusion", owner_event_id=owner_event_id or f"c-{frappe.generate_hash(length=6)}",
			required_members=list(required), payload={"result": "Meets"}, note="Conclusion", idempotency_key=self.key(), actor=CHAIR)

	def targets(self, kind: str = "Report signature", members=MEMBERS) -> list[dict[str, Any]]:
		return [{"target_id": f"RPT-{m.split('@')[0]}", "target_type": kind, "target_reference": "REPORT-1", "target_digest": frappe.generate_hash(length=16),
			"required_member": m} for m in members]

	def freeze(self, kind: str = "Evaluation report", targets=None, content: str = "Report version 1") -> dict[str, Any]:
		return record_versions.freeze_record(**self.ref(), record_kind=kind, owner_reference="EVL-REPORT-1", content=content,
			targets=targets if targets is not None else self.targets(), idempotency_key=self.key(), actor=SECRETARY)

	def prove(self, version: dict[str, Any], target: dict[str, Any], actor: str | None = None) -> dict[str, Any]:
		return record_versions.record_proof(**self.ref(), record_version=version["record_version"], target_id=target["target_id"],
			target_digest=target["target_digest"], action="Sign", idempotency_key=self.key(), actor=actor or target["required_member"])

	# -- create -----------------------------------------------------------------
	def test_create_uses_the_owner_profile(self):
		row = frappe.db.get_value("Proceeding", self.created["proceeding"], ["proceeding_type", "state"], as_dict=True)
		self.assertEqual((row.proceeding_type, row.state), ("Bid Evaluation", "Open"))

	# -- sessions -------------------------------------------------------------
	def test_start_records_the_chairs_attendance_and_one_session_at_a_time(self):
		self.roster()
		started = self.start()
		self.assertTrue(started["ok"])
		self.assertEqual(started["session_number"], 1)
		self.assertEqual(sessions.present(self.created["proceeding"]), [CHAIR])
		self.assertCode("PRC_VERSION_CONFLICT", self.start)
		# the chair is already present: no redundant join (board D05-START)
		self.assertCode("PRC_VERSION_CONFLICT", self.join, CHAIR)

	def test_members_and_the_secretary_join_personally(self):
		self.roster()
		self.start()
		self.at("2027-06-14 09:02:00")
		self.join(MEMBER)
		self.join(SECRETARY, "Secretary")
		self.assertEqual(sorted(sessions.present(self.created["proceeding"])), sorted([CHAIR, MEMBER, SECRETARY]))
		self.assertCode("PRC_MEMBER_REQUIRED", self.join, OUTSIDER)
		self.assertCode("PRC_MEMBER_REQUIRED", self.join, SECRETARY)  # a secretary is not a committee member
		rows = frappe.get_all("Proceeding Attendance", filters={"proceeding": self.created["proceeding"]}, fields=["user", "capacity", "session", "movement"])
		self.assertEqual({r.session for r in rows}, {f"{self.created['proceeding']}-S01"})
		self.assertEqual({(r.user, r.capacity) for r in rows}, {(CHAIR, "Committee member"), (MEMBER, "Committee member"), (SECRETARY, "Secretary")})

	def test_a_conclusion_needs_every_required_member_present(self):
		self.roster()
		self.start()
		self.join(MEMBER)
		error = self.assertCode("PRC_EVIDENCE_INCOMPLETE", self.conclude)
		self.assertEqual(error.detail["absent"], [INDEPENDENT])
		self.join(INDEPENDENT)
		out = self.conclude(owner_event_id="concl-1")
		event = frappe.get_doc("Proceeding Event", out["event_id"])
		self.assertEqual((event.source, event.session, event.event_type), ("Owner", f"{self.created['proceeding']}-S01", "CommitteeConclusion"))
		self.assertEqual(sorted(out["participants"]), sorted(MEMBERS))
		# the same owner event returns its original event, once
		self.assertEqual(self.conclude(owner_event_id="concl-1")["event_id"], out["event_id"])

	def test_leaving_pauses_collective_decisions_until_the_member_rejoins(self):
		self.roster()
		self.start()
		self.join(MEMBER)
		self.join(INDEPENDENT)
		self.at("2027-06-14 09:03:30")
		self.leave(INDEPENDENT)
		self.assertEqual(self.assertCode("PRC_EVIDENCE_INCOMPLETE", self.conclude).detail["absent"], [INDEPENDENT])
		self.join(INDEPENDENT)
		self.assertTrue(self.conclude()["ok"])

	def test_a_lapse_is_recorded_by_the_owner_as_the_system(self):
		self.roster()
		self.start()
		self.join(MEMBER)
		out = sessions.record_lapse(**self.ref(), member=MEMBER, idempotency_key=self.key(), actor="system")
		self.assertTrue(out["ok"])
		self.assertNotIn(MEMBER, sessions.present(self.created["proceeding"]))

	def test_ending_closes_the_session_and_a_later_session_is_numbered(self):
		self.roster()
		self.start()
		self.at("2027-06-14 09:06:00")
		ended = sessions.end_session(**self.ref(), note="", idempotency_key=self.key(), actor=CHAIR)
		self.assertTrue(ended["ok"])
		self.assertEqual(sessions.present(self.created["proceeding"]), [])
		self.assertCode("PRC_VERSION_CONFLICT", self.conclude)
		second = self.start(at="2027-06-16 09:00:00")
		self.assertEqual(second["session_number"], 2)
		times = frappe.get_all("Proceeding Session", filters={"proceeding": self.created["proceeding"]}, fields=["session_number", "state", "actual_start", "actual_end"],
			order_by="session_number asc")
		self.assertEqual([(t.session_number, t.state) for t in times], [(1, "Ended"), (2, "Active")])
		self.assertEqual(str(times[0].actual_end), "2027-06-14 09:06:00")

	def test_owner_facts_outside_a_session_and_member_statements(self):
		self.roster()
		fact = sessions.append_owner_event(**self.ref(), event_type="EvidenceFinding", owner_event_id="finding-1", payload={"result": "Needs review"}, note="",
			idempotency_key=self.key(), actor=CHAIR)
		self.assertEqual(frappe.db.get_value("Proceeding Event", fact["event_id"], "session"), None)
		said = sessions.record_member_statement(**self.ref(), event_type="Disagreement", owner_event_id="dis-1", statement="I disagree because …",
			linked_event=fact["event_id"], idempotency_key=self.key(), actor=MEMBER)
		event = frappe.get_doc("Proceeding Event", said["event_id"])
		self.assertEqual((event.source, event.actor, event.note), ("Member", MEMBER, "I disagree because …"))
		self.assertCode("PRC_MEMBER_REQUIRED", sessions.record_member_statement, **self.ref(), event_type="Disagreement", owner_event_id="dis-2",
			statement="Not mine to say", linked_event="", idempotency_key=self.key(), actor=SECRETARY)

	def test_a_roster_change_keeps_history(self):
		self.roster()
		replaced = [ROSTER[0], ROSTER[1], {**ROSTER[2], "member_user": OUTSIDER, "full_name": "Test Outsider"}]
		self.roster(replaced, reason="Replacement after a declared conflict")
		doc = frappe.get_doc("Proceeding", self.created["proceeding"])
		self.assertEqual({(m.member_user, m.roster_segment, m.active) for m in doc.members if m.member_user in (INDEPENDENT, OUTSIDER)},
			{(INDEPENDENT, 1, 0), (OUTSIDER, 2, 1)})

	# -- record versions and proofs ---------------------------------------------
	def test_report_targets_and_personal_proofs(self):
		self.roster()
		version = self.freeze()
		self.assertEqual(frappe.db.get_value("Proceeding Minutes Version", version["record_version"], ["record_kind", "state"]), ("Evaluation report", "Frozen"))
		mine, other = version["targets"][1], version["targets"][2]
		self.assertTrue(self.prove(version, mine)["ok"])
		self.assertCode("PRC_MEMBER_REQUIRED", self.prove, version, other, MEMBER)  # no proxy
		self.assertCode("PRC_TARGET_CHANGED", self.prove, version, {**other, "target_digest": "stale"})
		self._flag("kt_prc_signing_outcome", "Indeterminate")
		out = self.prove(version, other)
		self.assertFalse(out["ok"])
		self.assertEqual(out["verification_result"], "Indeterminate")
		self.assertIn({"target_id": other["target_id"], "required_member": INDEPENDENT}, record_versions.missing_proofs(version["record_version"]))

	def test_targets_are_checked(self):
		self.roster()
		self.assertCode("PRC_EVIDENCE_INCOMPLETE", self.freeze, targets=self.targets(kind="Minutes page"))
		self.assertCode("PRC_MEMBER_REQUIRED", self.freeze, targets=self.targets(members=(OUTSIDER,)))
		self.assertCode("PRC_EVIDENCE_INCOMPLETE", self.freeze, targets=[])
		self.freeze()
		self.assertCode("PRC_VERSION_CONFLICT", self.freeze)  # one frozen version of a kind at a time

	def test_superseding_makes_old_proofs_historical(self):
		self.roster()
		first = self.freeze()
		self.prove(first, first["targets"][0])
		record_versions.supersede_record(**self.ref(), record_version=first["record_version"], reason="Correct the page reference", idempotency_key=self.key(),
			actor=SECRETARY)
		self.assertEqual(frappe.db.get_value("Proceeding Minutes Version", first["record_version"], "state"), "Superseded")
		self.assertCode("PRC_TARGET_CHANGED", self.prove, first, first["targets"][1])
		second = self.freeze(content="Report version 2")
		self.assertEqual(len(record_versions.missing_proofs(second["record_version"])), 3)

	def test_completion_needs_every_proof_and_keeps_the_case_open(self):
		self.roster()
		version = self.freeze()
		self.assertCode("PRC_EVIDENCE_INCOMPLETE", record_versions.complete_record, **self.ref(), record_version=version["record_version"],
			idempotency_key=self.key(), actor="system")
		for target in version["targets"]:
			self.prove(version, target)
		done = record_versions.complete_record(**self.ref(), record_version=version["record_version"], idempotency_key=self.key(), actor="system")
		self.assertTrue(done["ok"])
		self.assertEqual(frappe.db.get_value("Proceeding Minutes Version", version["record_version"], "state"), "Finalized")
		self.assertEqual(frappe.db.get_value("Proceeding", self.created["proceeding"], "state"), "Open")
		note = record_versions.append_correction(**self.ref(), record_version=version["record_version"], kind="Correction notice",
			correct_information="Read page 2, section 3.", reason="Wrong page reference", idempotency_key=self.key(), actor=CHAIR)
		self.assertEqual(frappe.db.get_value("Proceeding Supplement", note["supplement_id"], "original_version"), version["record_version"])
		self.assertEqual(frappe.db.get_value("Proceeding Minutes Version", version["record_version"], "content"), "Report version 1")

	def test_a_verification_report_is_independent_of_the_report(self):
		self.roster()
		report = self.freeze()
		verification = self.freeze(kind="Verification report", targets=self.targets(kind="Verification report signature", members=(CHAIR, MEMBER)),
			content="Verification report 1")
		self.assertNotEqual(report["record_version"], verification["record_version"])
		self.prove(verification, verification["targets"][0])
		self.assertEqual(len(record_versions.missing_proofs(verification["record_version"])), 1)
		self.assertEqual(len(record_versions.missing_proofs(report["record_version"])), 3)
		self.assertCode("PRC_EVIDENCE_INCOMPLETE", self.freeze, kind="Verification report", targets=self.targets(kind="Report signature"))

	def test_cancellation_aborts_and_keeps_the_partial_record(self):
		self.roster()
		self.start()
		out = record_versions.abort(**self.ref(), cancellation_reference="MOH/CANCEL/TEST", idempotency_key=self.key(), actor="system")
		self.assertTrue(out["ok"])
		doc = frappe.get_doc("Proceeding", self.created["proceeding"])
		self.assertEqual((doc.state, doc.cancellation_reference), ("Aborted after start", "MOH/CANCEL/TEST"))
		self.assertEqual(frappe.db.get_value("Proceeding Session", f"{doc.name}-S01", "state"), "Ended")
		self.assertCode("PRC_VERSION_CONFLICT", self.start)

	def test_reads_are_owner_scoped(self):
		self.roster()
		self.start()
		view = record_versions.read(owner_type=OWNER_TYPE, owner_id=self.owner_id, user=MEMBER)
		self.assertEqual([s["session_number"] for s in view["sessions"]], [1])
		self.assertEqual(view["sessions"][0]["attendance"][0]["user"], CHAIR)
		self.assertCode("PRC_OWNER_UNAVAILABLE", record_versions.read, owner_type=OWNER_TYPE, owner_id=self.owner_id, user=OUTSIDER)
		self.assertCode("PRC_OWNER_UNAVAILABLE", record_versions.read, owner_type=OWNER_TYPE, owner_id=self.owner_id, user="Administrator")
