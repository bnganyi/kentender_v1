# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Attendance, requests, members' own accounts and comments for Evaluation
(BOP-CHG-001 v0.10 §5.1, §7 RecordAttendance, RecordIntervention,
RecordMemberAccount, DisposeOpeningException; §10.3 ATTENDANCE, OBSERVATION /
DIFFERING ACCOUNT, FACTUAL EXCEPTION; binding rows → PRC; BOP-A14, BOP-N15).

- The recorder records each attendee's actual arrival and departure and who
  they say they represent; saying so proves no submission and grants nothing.
- The recorder records a request or procedural comment, who made it, the
  affected bid, the chair's response and the outcome "Answered during
  opening". It never changes a bid.
- A member records their own differing account under their own identity;
  nobody records it for them. The recorder's response is a separate linked
  entry that leaves their words as written.
- The chair records a factual comment the Evaluation Committee should check
  as "Recorded for Evaluation". It is not a finding, never rejects, scores or
  amends a bid, and cannot dispose of an identity, integrity or unreadable
  package problem."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.bid_opening.services import appointment, ceremony, clock, errors, prc, records

ATTENDEE_CAPACITIES = ("Tenderer representative", "Public observer")
REQUEST_CLASSES = ("Repeat request", "Procedural comment")


def _reported(reported_at) -> dict[str, str] | None:
	if reported_at and get_datetime(reported_at) > clock.now():
		return {"reported_at": "A reported time cannot be later than now."}
	return None


def _entry(doc, entry: str, *, read_out: bool = False) -> Any | None:
	if not entry:
		return None
	name = frappe.db.get_value(ceremony.ENTRY, {"opening_case": doc.name, "entry_id": entry}, "name")
	if not name:
		errors.fail("BOP_VERSION_CONFLICT", {"reason": "unknown_bid"})
	row = frappe.get_doc(ceremony.ENTRY, name)
	if read_out and row.status != "Read out":
		errors.fail("BOP_READOUT_INCOMPLETE")
	return row


def record_attendance(*, tender: str, person_name: str, capacity: str, movement: str, idempotency_key: str, user: str, attendee: str = "",
		represented_tenderer: str = "", reported_at=None) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import attendance

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		ceremony.require_recorder(doc, user)
		if doc.state not in ("Awaiting deadline", "Ready to open", "Opening", "Interrupted"):
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state", "state": doc.state})
		if capacity not in ATTENDEE_CAPACITIES or not cstr(person_name).strip() or _reported(reported_at):
			return {"ok": False, "errors": _reported(reported_at) or {"person_name": "Enter the attendee's name and how they attend."}}
		out = attendance.record_attendance(**prc.ref(doc.name), person_name=person_name, user=attendee, capacity=capacity, movement=movement,
			represented_tenderer=represented_tenderer if capacity == "Tenderer representative" else "", reported_at=reported_at,
			idempotency_key=prc.key(idempotency_key, "attendance"), actor=user)
		records.bump(doc)
		return records.summary(doc, attendance=out["attendance_id"])

	return records.command("RecordAttendance", tender=tender, idempotency_key=idempotency_key, actor=user,
		payload={"person": person_name, "capacity": capacity, "movement": movement, "attendee": attendee, "represents": represented_tenderer,
			"reported": cstr(reported_at or "")}, body=body)


def record_intervention(*, tender: str, exception_class: str, speaker_name: str, what: str, response: str, idempotency_key: str, user: str, entry: str = "",
		reported_at=None, linked_account: str = "") -> dict[str, Any]:
	from kentender_procurement.proceedings.services import events

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		ceremony.require_recorder(doc, user)
		if doc.state != "Opening":
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state", "state": doc.state})
		refused = ceremony._material_check(doc)
		if refused:
			return refused
		if exception_class not in REQUEST_CLASSES or not cstr(what).strip() or not cstr(speaker_name).strip() or _reported(reported_at):
			return {"ok": False, "errors": _reported(reported_at) or {"what": "Record who spoke and what was asked or said."}}
		row = _entry(doc, entry)
		event = events.append_event(**prc.ref(doc.name), event_type="Intervention", source="Recorder", owner_event_id="",
			payload={"class": exception_class, "speaker": speaker_name, "entry": entry, "what": what, "response": response}, note=f"{speaker_name}: {what}",
			linked_event=linked_account or (row.proceeding_event if row else ""), reported_at=reported_at, reported_by=user if reported_at else "",
			idempotency_key=prc.key(idempotency_key, "intervention"), actor=user)
		exception = ceremony._exception(doc, exception_class, fact=cstr(what).strip(), user=user, entry=entry, outcome="Answered during opening",
			speaker=cstr(speaker_name).strip(), response=cstr(response).strip(), event_id=event["event_id"])
		records.bump(doc, last_committed_event=event["event_id"])
		return records.summary(doc, exception=exception.exception_id, event=event["event_id"])

	return records.command("RecordIntervention", tender=tender, idempotency_key=idempotency_key, actor=user,
		payload={"class": exception_class, "speaker": speaker_name, "what": what, "response": response, "entry": entry, "reported": cstr(reported_at or ""),
			"linked": linked_account}, body=body)


def record_member_account(*, tender: str, account: str, idempotency_key: str, user: str, entry: str = "") -> dict[str, Any]:
	from kentender_procurement.proceedings.services import events

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		member = appointment.member(doc.name, user)
		if not member:
			raise frappe.DoesNotExistError("Not found")
		if doc.state != "Opening":
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state", "state": doc.state})
		refused = ceremony._material_check(doc)
		if refused:
			return refused
		if not cstr(account).strip():
			return {"ok": False, "errors": {"account": "Write your account in your own words."}}
		row = _entry(doc, entry)
		event = events.append_event(**prc.ref(doc.name), event_type="MemberAccount", source="Member", payload={"entry": entry, "account": cstr(account).strip()},
			note=cstr(account).strip(), linked_event=row.proceeding_event if row else "", idempotency_key=prc.key(idempotency_key, "account"), actor=user)
		records.bump(doc, last_committed_event=event["event_id"])
		return records.summary(doc, event=event["event_id"])

	return records.command("RecordMemberAccount", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"account": account, "entry": entry}, body=body)


def record_comment_for_evaluation(*, tender: str, entry: str, made_by: str, comment: str, response: str, idempotency_key: str, user: str,
		reported_at=None) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import events

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		ceremony.require_chair(doc, user)
		if doc.state != "Opening":
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state", "state": doc.state})
		refused = ceremony._material_check(doc)
		if refused:
			return refused
		row = _entry(doc, entry, read_out=True)
		if not cstr(comment).strip() or not cstr(made_by).strip() or _reported(reported_at):
			return {"ok": False, "errors": _reported(reported_at) or {"comment": "Record who made the comment and what it was."}}
		event = events.append_event(**prc.ref(doc.name), event_type="CommentForEvaluation", source="Owner", owner_event_id="",
			payload={"entry": entry, "made_by": made_by, "comment": comment, "response": response}, note=f"{made_by}: {comment}", linked_event=row.proceeding_event,
			reported_at=reported_at, reported_by=user if reported_at else "", idempotency_key=prc.key(idempotency_key, "comment"), actor=user)
		exception = ceremony._exception(doc, "Comment for Evaluation", fact=cstr(comment).strip(), user=user, entry=entry, outcome="Recorded for Evaluation",
			speaker=cstr(made_by).strip(), response=cstr(response).strip(), event_id=event["event_id"])
		records.bump(doc, last_committed_event=event["event_id"])
		return records.summary(doc, exception=exception.exception_id)

	return records.command("RecordCommentForEvaluation", tender=tender, idempotency_key=idempotency_key, actor=user,
		payload={"entry": entry, "made_by": made_by, "comment": comment, "response": response, "reported": cstr(reported_at or "")}, body=body)
