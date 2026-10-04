# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Proceeding lifecycle (PRC-CHG-001 v0.9 §5, §7).

Pending → In session → Session ended → Awaiting attestations → Finalized,
plus two terminal failures: Not held (never started) and Aborted after start
(authoritative cancellation after an actual Start). Start and end are trusted
recorded instants, never entered retrospectively. Only the owner invokes
these, after its own statutory guards."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.proceedings.services import attendance, clock, owners, profiles, records
from kentender_procurement.proceedings.services.errors import fail

MEMBER_FIELDS = ("member_user", "full_name", "committee_capacity", "appointment_reference")


def _roster_rows(roster: list[dict[str, Any]], segment: int) -> list[dict[str, Any]]:
	if not roster:
		fail("PRC_EVIDENCE_INCOMPLETE", {"missing": ["roster"]})
	out = []
	for row in roster:
		missing = [f for f in MEMBER_FIELDS if not cstr(row.get(f)).strip()]
		if missing or not frappe.db.exists("User", row.get("member_user")):
			fail("PRC_EVIDENCE_INCOMPLETE", {"missing": missing or ["member_user"], "member": cstr(row.get("member_user"))})
		out.append({f: row.get(f) for f in (*MEMBER_FIELDS, "designation")} | {"roster_segment": segment, "active": 1})
	return out


def create_proceeding(*, owner_type: str, owner_id: str, title: str, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""CreateProceeding: exactly one proceeding per owner (PRC-A01), in the
	owner's profile (EVL-CHG-001 v0.4 plan D4): a Bid Opening starts Pending,
	a Bid Evaluation case starts Open for its later sessions."""

	def body() -> dict[str, Any]:
		existing = records.find(owner_type, owner_id)
		if existing:
			doc = frappe.get_doc(records.PROCEEDING, existing)
			first = frappe.db.get_value(records.EVENT, {"proceeding": doc.name, "event_type": "ProceedingCreated"}, "event_id")
			return records.summary(doc, cstr(first))
		if not cstr(title).strip():
			fail("PRC_EVIDENCE_INCOMPLETE", {"fields": {"title": "A title is required."}})
		proceeding_type = profiles.type_for(owners.adapters().get(owner_type))
		doc = records.insert(frappe.get_doc({
			"doctype": records.PROCEEDING, "proceeding_id": f"PRC-{owner_id}", "owner_type": owner_type, "owner_id": owner_id,
			"owner_key": records.owner_key(owner_type, owner_id), "proceeding_type": proceeding_type, "title": cstr(title).strip(),
			"state": profiles.profile(proceeding_type)["initial_state"],
			"created_at": clock.now(), "created_by": owners.user_or_none(actor), "record_version": 1,
		}))
		event_id = records.event(doc, "ProceedingCreated", source="System", actor=actor, pre_session=True)
		return records.summary(doc, event_id)

	return records.command("CreateProceeding", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="owner",
		payload={"title": title}, body=body)


def start_proceeding(*, owner_type: str, owner_id: str, expected_version: int, roster: list[dict[str, Any]], custody_reference: str, owner_event_id: str,
		idempotency_key: str, actor: str) -> dict[str, Any]:
	"""StartProceeding: only from Pending; snapshots the actual roster and
	references still-active arrivals without writing a second arrival."""

	def body() -> dict[str, Any]:
		doc = records.lock(owner_type, owner_id)
		records.check_version(doc, expected_version)
		records.require_state(doc, ("Pending",), start=True)
		rows = _roster_rows(roster, 1)
		carried = [{"attendance_id": r["attendance_id"], "person_name": r["person_name"]} for r in attendance.present(doc.name)]
		for row in rows:
			doc.append("members", row)
		event_id = records.event(doc, "ProceedingStarted", source="System", actor=actor, owner_event_id=owner_event_id, owner_reference=cstr(custody_reference),
			payload={"roster": [r["member_user"] for r in rows], "carried": carried}, note=json.dumps(carried, ensure_ascii=False))
		records.bump(doc, state="In session", actual_start=clock.now(), custody_reference=custody_reference)
		return records.summary(doc, event_id, carried=carried)

	return records.command("StartProceeding", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="owner",
		payload={"expected_version": expected_version, "roster": roster, "custody_reference": custody_reference, "owner_event_id": owner_event_id}, body=body)


def add_roster_segment(*, owner_type: str, owner_id: str, expected_version: int, roster: list[dict[str, Any]], reason: str, idempotency_key: str,
		actor: str) -> dict[str, Any]:
	"""A lawful successor appointment starts a new roster segment; earlier
	segments keep their actual roster (BOP-CHG-001 v0.10 §7.1 "Roster and target scope")."""

	def body() -> dict[str, Any]:
		doc = records.lock(owner_type, owner_id)
		records.check_version(doc, expected_version)
		records.require_state(doc, ("In session",))
		if not cstr(reason).strip():
			fail("PRC_EVIDENCE_INCOMPLETE", {"fields": {"reason": "Give the reason for the new roster."}})
		segment = max((cint(m.roster_segment) for m in doc.members), default=0) + 1
		for member in doc.members:
			member.active = 0
		for row in _roster_rows(roster, segment):
			doc.append("members", row)
		event_id = records.event(doc, "RosterSegmentStarted", source="System", actor=actor, note=cstr(reason).strip(),
			payload={"segment": segment, "roster": [r.get("member_user") for r in roster]})
		records.bump(doc)
		return records.summary(doc, event_id, roster_segment=segment)

	return records.command("AddRosterSegment", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="owner",
		payload={"expected_version": expected_version, "roster": roster, "reason": reason}, body=body)


def end_proceeding(*, owner_type: str, owner_id: str, expected_version: int, owner_event_id: str, idempotency_key: str, actor: str,
		outcome_event: dict[str, Any] | None = None) -> dict[str, Any]:
	"""EndProceeding. With `outcome_event` (the empty outcome), the fact and
	the End commit together, once (PRC-N12)."""

	def body() -> dict[str, Any]:
		doc = records.lock(owner_type, owner_id)
		records.check_version(doc, expected_version)
		records.require_state(doc, ("In session",))
		outcome_id = ""
		if outcome_event:
			if not cstr(outcome_event.get("event_type")).strip() or not cstr(outcome_event.get("owner_event_id")).strip():
				fail("PRC_EVIDENCE_INCOMPLETE", {"missing": ["outcome_event"]})
			outcome_id = records.event(doc, outcome_event["event_type"], source="Owner", actor=actor, owner_event_id=outcome_event["owner_event_id"],
				payload=outcome_event.get("payload") or {}, note=cstr(outcome_event.get("note")))
		event_id = records.event(doc, "ProceedingEnded", source="System", actor=actor, owner_event_id=owner_event_id)
		records.bump(doc, state="Session ended", actual_end=clock.now())
		return records.summary(doc, event_id, outcome_event_id=outcome_id)

	return records.command("EndProceeding", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="owner",
		payload={"expected_version": expected_version, "owner_event_id": owner_event_id, "outcome_event": outcome_event or {}}, body=body)


def mark_not_held(*, owner_type: str, owner_id: str, expected_version: int, reason: str, idempotency_key: str, actor: str, cancellation_reference: str = "",
		custody_reference: str = "") -> dict[str, Any]:
	"""MarkNotHeld: terminal, only from Pending with no Start (PRC-N10)."""

	def body() -> dict[str, Any]:
		doc = records.lock(owner_type, owner_id)
		records.check_version(doc, expected_version)
		records.require_state(doc, ("Pending",))
		if not cstr(reason).strip():
			fail("PRC_EVIDENCE_INCOMPLETE", {"fields": {"reason": "Record what happened."}})
		event_id = records.event(doc, "ProceedingNotHeld", source="System", actor=actor, note=cstr(reason).strip(),
			owner_reference=cstr(cancellation_reference or custody_reference))
		records.bump(doc, state="Not held", not_held_reason=cstr(reason).strip(), cancellation_reference=cancellation_reference,
			custody_reference=custody_reference or doc.custody_reference)
		return records.summary(doc, event_id)

	return records.command("MarkNotHeld", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="owner",
		payload={"expected_version": expected_version, "reason": reason, "cancellation_reference": cancellation_reference, "custody_reference": custody_reference},
		body=body)


def close_aborted(*, owner_type: str, owner_id: str, expected_version: int, cancellation_reference: str, custody_reference: str, idempotency_key: str,
		actor: str) -> dict[str, Any]:
	"""CloseAbortedProceeding: terminal after an actual Start; the partial
	chronology and actual cessation time are kept (PRC-N09)."""

	def body() -> dict[str, Any]:
		doc = records.lock(owner_type, owner_id)
		records.check_version(doc, expected_version)
		records.require_state(doc, ("In session", "Session ended", "Awaiting attestations"))
		if not cstr(cancellation_reference).strip():
			fail("PRC_EVIDENCE_INCOMPLETE", {"fields": {"cancellation_reference": "The authoritative cancellation is required."}})
		last = frappe.db.get_value(records.EVENT, {"proceeding": doc.name}, "event_id", order_by="sequence desc")
		event_id = records.event(doc, "ProceedingAborted", source="System", actor=actor, owner_reference=cstr(cancellation_reference),
			payload={"last_event": last, "custody_reference": custody_reference})
		records.bump(doc, state="Aborted after start", ceased_at=clock.now(), cancellation_reference=cancellation_reference,
			custody_reference=custody_reference or doc.custody_reference)
		return records.summary(doc, event_id, last_event=last)

	return records.command("CloseAbortedProceeding", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="owner",
		payload={"expected_version": expected_version, "cancellation_reference": cancellation_reference, "custody_reference": custody_reference}, body=body)
