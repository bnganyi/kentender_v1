# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RecordAttendance (PRC-CHG-001 v0.9 §4 Attendance, §5, §7).

The owner-designated recorder records actual arrivals and departures. While
Pending they are attributed pre-session facts with no Start; after Start
they are in-session facts. An arrival still active at Start appears in the
session's attendance view by reference: Start never writes a second arrival
(PRC-A11, PRC-N08). Attendance grants no role and no read."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr, get_datetime

from kentender_procurement.proceedings.services import clock, owners, records
from kentender_procurement.proceedings.services.errors import fail
from kentender_procurement.services import sequence

ATTENDANCE = "Proceeding Attendance"
CAPACITIES = ("Committee member", "Recorder", "Tenderer representative", "Public observer")
MOVEMENTS = ("Arrival", "Departure")


def identity(row) -> str:
	return cstr(row.get("user")) or cstr(row.get("person_name")).strip().lower()


def rows(proceeding: str) -> list[dict[str, Any]]:
	return frappe.get_all(ATTENDANCE, filters={"proceeding": proceeding}, fields=[
		"attendance_id", "person_name", "user", "capacity", "represented_tenderer", "movement", "pre_session", "occurred_at", "reported_at", "recorded_by", "event",
	], order_by="occurred_at asc, creation asc")


def present(proceeding: str) -> list[dict[str, Any]]:
	"""Everyone whose latest movement is an arrival, pre-session arrivals included."""
	latest: dict[str, dict[str, Any]] = {}
	for row in rows(proceeding):
		latest[identity(row)] = row
	return [row for row in latest.values() if row["movement"] == "Arrival"]


def record_attendance(*, owner_type: str, owner_id: str, expected_version: int, person_name: str, capacity: str, movement: str, idempotency_key: str, actor: str,
		user: str = "", represented_tenderer: str = "", reported_at=None, by_owner: bool = False) -> dict[str, Any]:
	"""`by_owner`: the owner records a fact it established itself (a member's
	authenticated join, or a presence lapse the system detected), so the
	owner capacity applies and the system actor may record it."""
	payload = {"expected_version": expected_version, "person_name": person_name, "capacity": capacity, "movement": movement, "user": user,
		"represented_tenderer": represented_tenderer, "reported_at": cstr(reported_at or ""), "by_owner": bool(by_owner)}

	def body() -> dict[str, Any]:
		doc = records.lock(owner_type, owner_id)
		records.check_version(doc, expected_version)
		records.require_state(doc, ("Pending", "In session"))
		fields = {}
		if not cstr(person_name).strip():
			fields["person_name"] = "Enter the person's name."
		if capacity not in CAPACITIES:
			fields["capacity"] = "Choose the capacity in which the person attends."
		if movement not in MOVEMENTS:
			fields["movement"] = "Choose arrival or departure."
		if reported_at and get_datetime(reported_at) > clock.now():
			fields["reported_at"] = "A reported time cannot be later than now."
		if fields:
			fail("PRC_EVIDENCE_INCOMPLETE", {"fields": fields})
		who = identity({"user": user, "person_name": person_name})
		active = {identity(r) for r in present(doc.name)}
		if movement == "Arrival" and who in active:
			fail("PRC_VERSION_CONFLICT", {"reason": "already_present"})
		if movement == "Departure" and who not in active:
			fail("PRC_VERSION_CONFLICT", {"reason": "not_present"})
		pre_session = doc.state == "Pending"
		event_id = records.event(doc, f"Attendance{movement}", source="Recorder", actor=actor, pre_session=pre_session, reported_at=reported_at,
			reported_by=actor if reported_at else "", payload={"person_name": person_name, "capacity": capacity, "represented_tenderer": represented_tenderer},
			note=f"{person_name} ({capacity})")
		number = sequence.next_count(ATTENDANCE, {"proceeding": doc.name})
		records.insert(frappe.get_doc({
			"doctype": ATTENDANCE, "attendance_id": f"{doc.name}-A{number:04d}", "proceeding": doc.name, "person_name": cstr(person_name).strip(),
			"user": owners.user_or_none(user), "capacity": capacity, "represented_tenderer": represented_tenderer, "movement": movement,
			"pre_session": 1 if pre_session else 0, "occurred_at": clock.now(), "reported_at": reported_at or None, "recorded_by": owners.user_or_none(actor),
			"event": event_id,
		}))
		records.bump(doc)
		return records.summary(doc, event_id, attendance_id=f"{doc.name}-A{number:04d}", pre_session=cint(pre_session))

	return records.command("RecordAttendance", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="owner" if by_owner else "recorder",
		payload=payload, body=body)
