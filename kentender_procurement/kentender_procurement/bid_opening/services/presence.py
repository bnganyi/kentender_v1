# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""JoinOpening, LeaveOpening and presence (BOP-CHG-001 v0.10 §5 committee-
presence invariant, §7; binding row `JoinOpening`, `LeaveOpening` → PRC
`RecordAttendance`; plan D7).

Presence is an authenticated, server-maintained join with a recorded
departure, never a checkbox or a name in the appointment. Each appointed
member joins under their own identity; nobody joins for another. While the
Proceeding is Pending the join is a pre-session arrival, with no Start. A
member whose heartbeat stops for longer than the operating profile's lapse
is recorded as having left, and their custody participation lapses with
them. Every material command rechecks presence on the server."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import frappe
from frappe.utils import cint, get_datetime

from kentender_procurement.bid_opening.services import appointment, arrangements, clock, custody_participation, labels, prc, records, settings
from kentender_procurement.services import sequence

PRESENCE = "Opening Presence"
OPEN_STATES = ("Awaiting deadline", "Ready to open", "Opening", "Interrupted", "Readout complete")


def active(case: str, user: str) -> Any | None:
	name = frappe.db.get_value(PRESENCE, {"opening_case": case, "member_user": user, "state": "Present"}, "name")
	return frappe.get_doc(PRESENCE, name) if name else None


def present_members(case: str) -> dict[str, Any]:
	"""user → joined_at for every member currently present."""
	return {r.member_user: r.joined_at for r in frappe.get_all(PRESENCE, filters={"opening_case": case, "state": "Present"}, fields=["member_user", "joined_at"])}


def _record(doc, user: str, movement: str, key: str, *, by_system: bool = False) -> None:
	from kentender_procurement.proceedings.services import attendance

	row = appointment.member(doc.name, user)
	attendance.record_attendance(**prc.ref(doc.name), person_name=row["full_name"] if row else user, user=user, capacity="Committee member", movement=movement,
		idempotency_key=prc.key(key, f"attendance:{movement}:{user}"), actor=prc.SYSTEM_ACTOR if by_system else user, by_owner=True)


def join_opening(*, tender: str, idempotency_key: str, user: str) -> dict[str, Any]:
	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if not appointment.member(doc.name, user):
			raise frappe.DoesNotExistError("Not found")
		if doc.state not in OPEN_STATES:
			from kentender_procurement.bid_opening.services import errors

			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state", "state": doc.state})
		now = clock.now()
		opens = arrangements.join_opens_at(doc.effective_deadline)
		if opens is not None and now < opens and doc.state == "Awaiting deadline":
			return {"ok": False, "reason": "join_not_open", "message": f"You can join from {labels.when(opens)}.", "join_opens_label": labels.when(opens)}
		existing = active(doc.name, user)
		if existing:
			return records.summary(doc, presence=existing.name, joined=False)
		number = sequence.next_count(PRESENCE, {"opening_case": doc.name})
		row = records.insert(frappe.get_doc({
			"doctype": PRESENCE, "presence_id": f"{doc.opening_id}-PRS-{number:03d}", "opening_case": doc.name, "member_user": user, "roster_segment": 1,
			"joined_at": now, "last_seen_at": now, "state": "Present",
		}))
		_record(doc, user, "Arrival", idempotency_key)
		resumed = False
		if doc.manifest_digest and doc.state in ("Ready to open", "Opening", "Interrupted"):
			custody_participation.confirm(doc, user, idempotency_key)
			from kentender_procurement.bid_opening.services import ceremony

			resumed = ceremony.try_resume_after_rejoin(doc, idempotency_key)
		records.bump(doc)
		return records.summary(doc, presence=row.name, joined=True, resumed=resumed)

	return records.command("JoinOpening", tender=tender, idempotency_key=idempotency_key, actor=user, payload={}, body=body)


def leave_opening(*, tender: str, idempotency_key: str, user: str) -> dict[str, Any]:
	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		row = active(doc.name, user)
		if not row:
			return records.summary(doc, left=False)
		_close(doc, row, "Left", idempotency_key)
		records.bump(doc)
		return records.summary(doc, left=True)

	return records.command("LeaveOpening", tender=tender, idempotency_key=idempotency_key, actor=user, payload={}, body=body)


def _close(doc, row, state: str, key: str) -> None:
	row.state = state
	row.left_at = clock.now()
	records.save(row)
	_record(doc, row.member_user, "Departure", key, by_system=state == "Lapsed")
	custody_participation.mark_stale(doc.name, row.member_user)
	if doc.state == "Opening":
		# BOP-CHG-001 v0.10 §5: a member's absence pauses the opening before the next material act.
		from kentender_procurement.bid_opening.services import ceremony, errors

		name = (appointment.member(doc.name, row.member_user) or {}).get("full_name") or row.member_user
		ceremony.pause(doc, "Member absent", fact=errors.message("BOP_MEMBER_ABSENT", started=True, name=name), key=f"{key}:{row.name}", member=row.member_user)


def heartbeat(*, tender: str, user: str) -> dict[str, Any]:
	"""A present member's page reports they are still here. Not a business
	event; a lapsed member must join again."""
	case = records.case_for(tender)
	row = active(case, user) if case else None
	if not row:
		return {"present": False}
	lapse = settings.get()["presence_lapse_seconds"]
	now = clock.now()
	if lapse and now - get_datetime(row.last_seen_at) > timedelta(seconds=cint(lapse)):
		sweep_lapses(tender)
		return {"present": False}
	row.last_seen_at = now
	records.save(row)
	return {"present": True, "last_seen_at": str(now)}


def sweep_lapses(tender: str) -> int:
	"""Record every present member whose heartbeat stopped longer than the lapse."""
	lapse = settings.get()["presence_lapse_seconds"]
	case = records.case_for(tender)
	if not lapse or not case:
		return 0
	now = clock.now()
	stale = [r for r in frappe.get_all(PRESENCE, filters={"opening_case": case, "state": "Present"}, fields=["name", "last_seen_at"])
		if now - get_datetime(r.last_seen_at) > timedelta(seconds=cint(lapse))]
	if not stale:
		return 0

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		for r in stale:
			_close(doc, frappe.get_doc(PRESENCE, r.name), "Lapsed", f"lapse:{r.name}")
		records.bump(doc)
		return records.summary(doc, lapsed=len(stale))

	records.command("RecordPresenceLapse", tender=tender, idempotency_key=f"lapse:{case}:{','.join(sorted(r.name for r in stale))}", actor=prc.SYSTEM_ACTOR,
		payload={}, body=body)
	return len(stale)
