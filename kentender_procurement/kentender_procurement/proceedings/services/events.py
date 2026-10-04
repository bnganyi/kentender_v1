# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AppendProceedingEvent (PRC-CHG-001 v0.9 §4 Event, §7).

One ordered, attributed event per call, with a trusted server instant. An
earlier reported instant (for example when a readout was spoken) is kept as
an attributed human observation beside it and never replaces it (PRC-N11).
Owner facts are linked by their owner event ID, never rewritten (PRC-N01).
While Pending only custody participation and one opaque closed-manifest
reference are accepted: never a bid fact, and never a Start."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.proceedings.services import clock, records
from kentender_procurement.proceedings.services.errors import fail

SOURCES = {"Owner": "owner", "Recorder": "recorder", "Member": "member"}
PRE_SESSION_TYPES = ("CustodyParticipation", "ClosedManifestReference")
AFTER_SESSION_STATES = ("Session ended", "Awaiting attestations")


def active_members(doc) -> set[str]:
	return {m.member_user for m in doc.members if m.active}


def append_event(*, owner_type: str, owner_id: str, expected_version: int, event_type: str, source: str, idempotency_key: str, actor: str,
		owner_event_id: str = "", owner_reference: str = "", note: str = "", payload: dict | None = None, reported_at=None, reported_by: str = "",
		linked_event: str = "") -> dict[str, Any]:
	if source not in SOURCES:
		raise ValueError(f"Unknown event source {source!r}")
	body_digest = records.digest(records.event_body(event_type, source=source, payload=payload, note=note, owner_reference=owner_reference,
		reported_at=reported_at, reported_by=reported_by, linked_event=linked_event))

	def body() -> dict[str, Any]:
		doc = records.lock(owner_type, owner_id)
		replayed = records.owner_event_replay(doc, owner_event_id, body_digest)
		if replayed:
			return records.summary(doc, replayed, replayed=True)
		records.check_version(doc, expected_version)
		if doc.state == "Pending":
			if source != "Owner" or event_type not in PRE_SESSION_TYPES:
				fail("PRC_VERSION_CONFLICT", {"reason": "not_before_start", "state": doc.state})
			if event_type == "ClosedManifestReference" and frappe.db.exists(records.EVENT, {"proceeding": doc.name, "event_type": event_type}):
				fail("PRC_VERSION_CONFLICT", {"reason": "manifest_already_referenced"})
		elif doc.state in AFTER_SESSION_STATES:
			if source != "Owner":
				fail("PRC_VERSION_CONFLICT", {"reason": "session_ended", "state": doc.state})
		else:
			records.require_state(doc, ("In session",))
		if source == "Member" and actor not in active_members(doc):
			fail("PRC_MEMBER_REQUIRED")
		fields = {}
		if not cstr(event_type).strip():
			fields["event_type"] = "An event type is required."
		if reported_at:
			if not reported_by:
				fields["reported_by"] = "Say who reported this time."
			elif get_datetime(reported_at) > clock.now():
				fields["reported_at"] = "A reported time cannot be later than now."
		if linked_event and not frappe.db.exists(records.EVENT, {"event_id": linked_event, "proceeding": doc.name}):
			fields["linked_event"] = "The linked event is not part of this record."
		if fields:
			fail("PRC_EVIDENCE_INCOMPLETE", {"fields": fields})
		event_id = records.event(doc, event_type, source=source, actor=actor, owner_event_id=owner_event_id, payload=payload, note=note,
			owner_reference=owner_reference, reported_at=reported_at, reported_by=reported_by, linked_event=linked_event, pre_session=doc.state == "Pending")
		records.bump(doc)
		return records.summary(doc, event_id)

	return records.command("AppendProceedingEvent", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor,
		capacity=SOURCES[source], payload={"expected_version": expected_version, "owner_event_id": owner_event_id, "digest": body_digest}, body=body)
