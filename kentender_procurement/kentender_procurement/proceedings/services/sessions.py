# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Discussion sessions of a multi-session proceeding (EVL-CHG-001 v0.4 §5.2,
§6 owner-event table, plan D4).

One case holds zero or more actual sessions, and at most one is active.
Starting a session records the starter's own attendance in the same action;
everyone else joins and leaves personally, and nobody records attendance for
another person (there is no group attendance action). A conclusion commits
only while every member the owner requires is present in the active session;
the event names the actual participants. A member's own statement (for
example a disagreement) keeps that member's authorship. Owner facts outside a
session (appointments, findings, clarifications) are ordered events too.

These operations serve the Bid Evaluation profile; the Bid Opening profile
keeps its single session in `lifecycle`."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.proceedings.services import clock, owners, profiles, records
from kentender_procurement.proceedings.services.errors import fail

SESSION = "Proceeding Session"
ATTENDANCE = "Proceeding Attendance"
OPEN = "Open"
CAPACITY_FOR = {"Committee member": "member", "Secretary": "recorder"}


def _open(owner_type: str, owner_id: str, expected_version: int):
	doc = records.lock(owner_type, owner_id)
	records.check_version(doc, expected_version)
	if not profiles.profile(doc.proceeding_type)["multi_session"]:
		fail("PRC_VERSION_CONFLICT", {"reason": "single_session_profile"})
	records.require_state(doc, (OPEN,))
	return doc


def active_session(proceeding: str) -> str | None:
	return frappe.db.get_value(SESSION, {"proceeding": proceeding, "state": "Active"}, "name")


def _members(doc) -> set[str]:
	return {m.member_user for m in doc.members if cint(m.active)}


def _name(doc, user: str) -> str:
	row = next((m for m in doc.members if m.member_user == user), None)
	return cstr(row.full_name if row else frappe.db.get_value("User", user, "full_name") or user)


def present(proceeding: str, session: str | None = None) -> list[str]:
	"""The users whose latest movement in the active (or named) session is an arrival."""
	session = session or active_session(proceeding)
	if not session:
		return []
	latest: dict[str, str] = {}
	for row in frappe.get_all(ATTENDANCE, filters={"proceeding": proceeding, "session": session}, fields=["user", "movement"],
			order_by="occurred_at asc, creation asc"):
		latest[row.user] = row.movement
	return [user for user, movement in latest.items() if movement == "Arrival"]


def _movement(doc, session: str, *, user: str, capacity: str, movement: str, actor: str, source: str = "Member") -> str:
	event_id = records.event(doc, f"Attendance{movement}", source=source, actor=actor, session=session, payload={"user": user, "capacity": capacity},
		note=f"{_name(doc, user)} ({capacity})")
	number = frappe.db.count(ATTENDANCE, {"proceeding": doc.name}) + 1
	records.insert(frappe.get_doc({
		"doctype": ATTENDANCE, "attendance_id": f"{doc.name}-A{number:04d}", "proceeding": doc.name, "session": session, "person_name": _name(doc, user),
		"user": owners.user_or_none(user), "capacity": capacity, "movement": movement, "pre_session": 0, "occurred_at": clock.now(),
		"recorded_by": owners.user_or_none(actor), "event": event_id,
	}))
	return event_id


def record_roster(*, owner_type: str, owner_id: str, expected_version: int, roster: list[dict[str, Any]], reason: str, owner_event_id: str,
		idempotency_key: str, actor: str) -> dict[str, Any]:
	"""Appointment or replacement (§6 owner-event table): the new current roster
	starts a segment; earlier segments keep their history. PRC attendance
	creates no authority."""
	payload = {"expected_version": expected_version, "roster": roster, "reason": reason, "owner_event_id": owner_event_id}

	def body() -> dict[str, Any]:
		doc = _open(owner_type, owner_id, expected_version)
		from kentender_procurement.proceedings.services.lifecycle import _roster_rows

		segment = max((cint(m.roster_segment) for m in doc.members), default=0) + 1
		rows = _roster_rows(roster, segment)
		for member in doc.members:
			member.active = 0
		for row in rows:
			doc.append("members", row)
		event_id = records.event(doc, "RosterRecorded", source="Owner", actor=actor, owner_event_id=owner_event_id, note=cstr(reason).strip(),
			payload={"segment": segment, "roster": [r["member_user"] for r in rows]})
		records.bump(doc)
		return records.summary(doc, event_id, roster_segment=segment)

	return records.command("RecordRoster", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="owner",
		payload=payload, body=body)


def start_session(*, owner_type: str, owner_id: str, expected_version: int, subject: str, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""StartEvaluationDiscussion: the starter's own attendance is recorded in the same action."""

	def body() -> dict[str, Any]:
		doc = _open(owner_type, owner_id, expected_version)
		if active_session(doc.name):
			fail("PRC_VERSION_CONFLICT", {"reason": "active_session"})
		if actor not in _members(doc):
			fail("PRC_MEMBER_REQUIRED")
		number = frappe.db.count(SESSION, {"proceeding": doc.name}) + 1
		session_id = f"{doc.name}-S{number:02d}"
		records.insert(frappe.get_doc({
			"doctype": SESSION, "session_id": session_id, "proceeding": doc.name, "session_number": number, "state": "Active", "subject": cstr(subject).strip(),
			"started_by": owners.user_or_none(actor), "actual_start": clock.now(),
		}))
		event_id = records.event(doc, "SessionStarted", source="System", actor=actor, session=session_id, note=cstr(subject).strip())
		_movement(doc, session_id, user=actor, capacity="Committee member", movement="Arrival", actor=actor)
		records.bump(doc, current_session=session_id)
		return records.summary(doc, event_id, session_id=session_id, session_number=number)

	return records.command("StartSession", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="owner",
		payload={"expected_version": expected_version, "subject": subject}, body=body)


def _personal(name: str, movement: str, *, owner_type: str, owner_id: str, expected_version: int, capacity: str, idempotency_key: str, actor: str) -> dict[str, Any]:
	if capacity not in CAPACITY_FOR:
		fail("PRC_EVIDENCE_INCOMPLETE", {"fields": {"capacity": "Choose the capacity in which you attend."}})

	def body() -> dict[str, Any]:
		doc = _open(owner_type, owner_id, expected_version)
		session = active_session(doc.name)
		if not session:
			fail("PRC_VERSION_CONFLICT", {"reason": "no_active_session"})
		if capacity == "Committee member" and actor not in _members(doc):
			fail("PRC_MEMBER_REQUIRED")
		here = actor in present(doc.name, session)
		if (movement == "Arrival") == here:
			fail("PRC_VERSION_CONFLICT", {"reason": "already_present" if here else "not_present"})
		event_id = _movement(doc, session, user=actor, capacity=capacity, movement=movement, actor=actor)
		records.bump(doc)
		return records.summary(doc, event_id, session_id=session)

	return records.command(name, owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity=CAPACITY_FOR[capacity],
		payload={"expected_version": expected_version, "capacity": capacity}, body=body)


def join_session(**kwargs) -> dict[str, Any]:
	"""JoinEvaluationDiscussion: the actor's own arrival."""
	return _personal("JoinSession", "Arrival", **kwargs)


def leave_session(**kwargs) -> dict[str, Any]:
	"""LeaveEvaluationDiscussion: the actor's own departure."""
	return _personal("LeaveSession", "Departure", **kwargs)


def record_lapse(*, owner_type: str, owner_id: str, expected_version: int, member: str, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""The owner records that current participation could not be established
	(§5.2): the member is unavailable for decisions until they rejoin."""

	def body() -> dict[str, Any]:
		doc = _open(owner_type, owner_id, expected_version)
		session = active_session(doc.name)
		if not session or member not in present(doc.name, session):
			fail("PRC_VERSION_CONFLICT", {"reason": "not_present"})
		capacity = "Committee member" if member in _members(doc) else "Secretary"
		event_id = _movement(doc, session, user=member, capacity=capacity, movement="Departure", actor=actor, source="System")
		records.bump(doc)
		return records.summary(doc, event_id, session_id=session)

	return records.command("RecordLapse", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="owner",
		payload={"expected_version": expected_version, "member": member}, body=body)


def end_session(*, owner_type: str, owner_id: str, expected_version: int, note: str, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""EndEvaluationDiscussion: everyone still present leaves at the end instant."""

	def body() -> dict[str, Any]:
		doc = _open(owner_type, owner_id, expected_version)
		session = active_session(doc.name)
		if not session:
			fail("PRC_VERSION_CONFLICT", {"reason": "no_active_session"})
		_close(doc, session, actor=actor, note=note)
		event_id = records.event(doc, "SessionEnded", source="System", actor=actor, session=session, note=cstr(note).strip())
		records.bump(doc, current_session="")
		return records.summary(doc, event_id, session_id=session)

	return records.command("EndSession", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="owner",
		payload={"expected_version": expected_version, "note": note}, body=body)


def _close(doc, session: str, *, actor: str, note: str = "") -> None:
	members = _members(doc)
	for user in present(doc.name, session):
		_movement(doc, session, user=user, capacity="Committee member" if user in members else "Secretary", movement="Departure", actor=actor, source="System")
	row = frappe.get_doc(SESSION, session)
	row.state, row.actual_end, row.ended_by, row.end_note = "Ended", clock.now(), owners.user_or_none(actor), cstr(note).strip()
	records.save(row)


def record_conclusion(*, owner_type: str, owner_id: str, expected_version: int, event_type: str, owner_event_id: str, required_members: list[str],
		payload: dict[str, Any], note: str, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""RecordEvaluationConclusion: the owner's collective decision, committed
	only while every required member is present in the active session. The
	event records the actual participating roster (§6)."""
	body_digest = records.digest(records.event_body(event_type, source="Owner", payload=payload, note=note))

	def body() -> dict[str, Any]:
		doc = records.lock(owner_type, owner_id)
		prior = frappe.db.get_value(records.EVENT, {"event_key": f"{doc.name}:{owner_event_id}"}, ["event_id", "owner_reference"], as_dict=True)
		if prior:
			# The stored event also covers the participants it recorded.
			records.owner_event_replay(doc, owner_event_id, records.digest(records.event_body(event_type, source="Owner", payload=payload, note=note,
				owner_reference=prior.owner_reference)))
			return records.summary(doc, prior.event_id, replayed=True, participants=frappe.parse_json(prior.owner_reference or "[]"))
		doc = _open(owner_type, owner_id, expected_version)
		session = active_session(doc.name)
		if not session:
			fail("PRC_VERSION_CONFLICT", {"reason": "no_active_session"})
		required = sorted(set(required_members))
		if not required:
			fail("PRC_EVIDENCE_INCOMPLETE", {"missing": ["required_members"]})
		not_members = [u for u in required if u not in _members(doc)]
		if not_members:
			fail("PRC_MEMBER_REQUIRED", {"not_members": not_members})
		here = set(present(doc.name, session))
		absent = [u for u in required if u not in here]
		if absent:
			fail("PRC_EVIDENCE_INCOMPLETE", {"absent": absent, "session": session})
		participants = sorted(here)
		event_id = records.event(doc, event_type, source="Owner", actor=actor, owner_event_id=owner_event_id, payload=payload, note=note, session=session,
			owner_reference=frappe.as_json(participants))
		records.bump(doc)
		return records.summary(doc, event_id, session_id=session, participants=participants)

	return records.command("RecordConclusion", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="owner",
		payload={"expected_version": expected_version, "owner_event_id": owner_event_id, "digest": body_digest, "required": sorted(set(required_members))}, body=body)


def append_owner_event(*, owner_type: str, owner_id: str, expected_version: int, event_type: str, owner_event_id: str, payload: dict[str, Any], note: str,
		idempotency_key: str, actor: str) -> dict[str, Any]:
	"""An ordered owner fact outside any collective decision (appointment,
	declaration reference, finding, clarification, report event)."""
	body_digest = records.digest(records.event_body(event_type, source="Owner", payload=payload, note=note))

	def body() -> dict[str, Any]:
		doc = records.lock(owner_type, owner_id)
		replayed = records.owner_event_replay(doc, owner_event_id, body_digest)
		if replayed:
			return records.summary(doc, replayed, replayed=True)
		doc = _open(owner_type, owner_id, expected_version)
		event_id = records.event(doc, event_type, source="Owner", actor=actor, owner_event_id=owner_event_id, payload=payload, note=note,
			session=active_session(doc.name) or "")
		records.bump(doc)
		return records.summary(doc, event_id)

	return records.command("AppendOwnerEvent", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="owner",
		payload={"expected_version": expected_version, "owner_event_id": owner_event_id, "digest": body_digest}, body=body)


def record_member_statement(*, owner_type: str, owner_id: str, expected_version: int, event_type: str, owner_event_id: str, statement: str, linked_event: str,
		idempotency_key: str, actor: str) -> dict[str, Any]:
	"""A member's own words (a disagreement, a concern): the recorder cannot
	attribute unconfirmed words to anyone (§5.2)."""
	body_digest = records.digest(records.event_body(event_type, source="Member", note=cstr(statement).strip(), linked_event=linked_event))

	def body() -> dict[str, Any]:
		doc = records.lock(owner_type, owner_id)
		replayed = records.owner_event_replay(doc, owner_event_id, body_digest)
		if replayed:
			return records.summary(doc, replayed, replayed=True)
		doc = _open(owner_type, owner_id, expected_version)
		if actor not in _members(doc):
			fail("PRC_MEMBER_REQUIRED")
		if not cstr(statement).strip():
			fail("PRC_EVIDENCE_INCOMPLETE", {"fields": {"statement": "Write your statement."}})
		if linked_event and not frappe.db.exists(records.EVENT, {"event_id": linked_event, "proceeding": doc.name}):
			fail("PRC_EVIDENCE_INCOMPLETE", {"fields": {"linked_event": "The linked event is not part of this record."}})
		event_id = records.event(doc, event_type, source="Member", actor=actor, owner_event_id=owner_event_id, note=cstr(statement).strip(),
			linked_event=linked_event, session=active_session(doc.name) or "")
		records.bump(doc)
		return records.summary(doc, event_id)

	return records.command("RecordMemberStatement", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="member",
		payload={"expected_version": expected_version, "owner_event_id": owner_event_id, "digest": body_digest}, body=body)
