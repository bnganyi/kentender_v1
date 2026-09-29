# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Writing Proceedings records (PRC-CHG-001 v0.9 §7, §12).

Every mutating command takes the owner reference, an expected record
version and an idempotency key, authenticates the actor through the owner
seam, and returns the committed record version, event ID and current state.
A retry returns the original committed result; a reused key with a
different payload, or a stale version, fails with no partial write. Each
command's writes commit together (`atomic`) under the Proceeding's row lock,
which also serialises the event sequence."""

from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from typing import Any, Callable
from uuid import uuid4

import frappe
from frappe.utils import cint, cstr, get_datetime

from kentender_procurement.proceedings.services import clock, owners
from kentender_procurement.proceedings.services.errors import fail

PROCEEDING = "Proceeding"
EVENT = "Proceeding Event"
JOURNAL = "Proceeding Command Journal"
TERMINAL = ("Not held", "Aborted after start")


def namespace() -> str:
	return cstr(frappe.flags.get("kt_prc_fixture_namespace") or "")


def insert(doc) -> Any:
	if doc.meta.has_field("fixture_namespace") and not doc.get("fixture_namespace"):
		doc.fixture_namespace = namespace()
	doc.flags.kt_prc_command = True
	doc.insert(ignore_permissions=True)
	return doc


def save(doc) -> Any:
	doc.flags.kt_prc_command = True
	doc.save(ignore_permissions=True)
	return doc


def bump(doc, **values) -> Any:
	for field, value in values.items():
		doc.set(field, value)
	doc.record_version = cint(doc.record_version) + 1
	return save(doc)


def digest(value: Any) -> str:
	return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8")).hexdigest()


def text_digest(text: str) -> str:
	return hashlib.sha256(cstr(text).encode("utf-8")).hexdigest()


@contextmanager
def atomic():
	savepoint = f"prc_{uuid4().hex[:12]}"
	frappe.db.savepoint(savepoint)
	try:
		yield
	except Exception:
		frappe.db.rollback(save_point=savepoint)
		raise
	else:
		frappe.db.release_savepoint(savepoint)


def owner_key(owner_type: str, owner_id: str) -> str:
	return f"{cstr(owner_type)}:{cstr(owner_id)}"


def find(owner_type: str, owner_id: str) -> str | None:
	return frappe.db.get_value(PROCEEDING, {"owner_key": owner_key(owner_type, owner_id)}, "name")


def lock(owner_type: str, owner_id: str):
	name = find(owner_type, owner_id)
	if not name:
		fail("PRC_OWNER_UNAVAILABLE")
	frappe.db.sql("select name from `tabProceeding` where name=%s for update", name)
	return frappe.get_doc(PROCEEDING, name)


def check_version(doc, expected) -> None:
	try:
		ok = expected is not None and int(expected) == cint(doc.record_version)
	except (TypeError, ValueError):
		ok = False
	if not ok:
		fail("PRC_VERSION_CONFLICT", {"reason": "stale_version", "record_version": cint(doc.record_version)})


def require_state(doc, allowed: tuple[str, ...], *, start: bool = False) -> None:
	"""Finalized is immutable; the terminal failures accept nothing; any other
	wrong state is a stale action the screen should not have offered."""
	if doc.state == "Finalized" and "Finalized" not in allowed:
		fail("PRC_ALREADY_FINALIZED")
	if doc.state not in allowed:
		fail("PRC_START_BLOCKED" if start else "PRC_VERSION_CONFLICT", {"reason": "state", "state": doc.state})


def summary(doc, event_id: str = "", **extra) -> dict[str, Any]:
	return {"ok": True, "proceeding": doc.name, "record_version": cint(doc.record_version), "state": doc.state, "event_id": event_id, **extra}


def command(name: str, *, owner_type: str, owner_id: str, idempotency_key: str, actor: str, capacity: str, payload: dict[str, Any],
		body: Callable[[], dict[str, Any]]) -> dict[str, Any]:
	"""Authorise, then replay or run `body` once for this key."""
	owners.require(owner_type, owner_id, actor, capacity)
	key = cstr(idempotency_key).strip()
	if not key:
		fail("PRC_EVIDENCE_INCOMPLETE", {"fields": {"idempotency_key": "A request key is required."}})
	payload_hash = digest({"command": name, "owner_type": owner_type, "owner_id": owner_id, "actor": actor, **payload})
	row = frappe.db.get_value(JOURNAL, {"idempotency_key": key}, ["command", "payload_hash", "result_json"], as_dict=True)
	if row:
		if row.command != name or row.payload_hash != payload_hash:
			fail("PRC_VERSION_CONFLICT", {"reason": "idempotency_key_reused"})
		return json.loads(row.result_json or "{}")
	with atomic():
		result = body()
		if result.get("ok") is not False:
			insert(frappe.get_doc({
				"doctype": JOURNAL, "idempotency_key": key, "command": name, "payload_hash": payload_hash, "result_json": json.dumps(result, default=str),
				"actor": owners.user_or_none(actor), "proceeding": cstr(result.get("proceeding")), "recorded_at": clock.now(),
			}))
	return result


def next_sequence(proceeding: str) -> int:
	value = frappe.db.sql("select max(sequence) from `tabProceeding Event` where proceeding=%s", proceeding)[0][0]
	return cint(value) + 1


def event_body(event_type: str, *, source: str, payload: dict | None = None, note: str = "", owner_reference: str = "", reported_at=None,
		reported_by: str = "", linked_event: str = "") -> dict[str, Any]:
	"""What an event's digest covers: its facts, never its sequence or time."""
	return {"event_type": event_type, "source": source, "payload": payload or {}, "note": cstr(note), "owner_reference": cstr(owner_reference),
		"reported_at": cstr(get_datetime(reported_at)) if reported_at else "", "reported_by": cstr(reported_by), "linked_event": cstr(linked_event)}


def event(doc, event_type: str, *, source: str, actor: str, owner_event_id: str = "", payload: dict | None = None, note: str = "", owner_reference: str = "",
		reported_at=None, reported_by: str = "", linked_event: str = "", pre_session: bool = False) -> str:
	"""Append one ordered event with a trusted server instant (PRC-CHG-001 v0.9 §4 Event)."""
	sequence = next_sequence(doc.name)
	event_id = f"{doc.name}-E{sequence:04d}"
	body = event_body(event_type, source=source, payload=payload, note=note, owner_reference=owner_reference, reported_at=reported_at,
		reported_by=reported_by, linked_event=linked_event)
	insert(frappe.get_doc({
		"doctype": EVENT, "event_id": event_id, "proceeding": doc.name, "sequence": sequence, "event_type": event_type, "recorded_at": clock.now(),
		"actor": owners.user_or_none(actor), "source": source, "owner_event_id": owner_event_id,
		"event_key": f"{doc.name}:{owner_event_id}" if owner_event_id else f"{doc.name}:{event_id}", "payload_digest": digest(body),
		"owner_reference": owner_reference, "note": note, "reported_at": reported_at or None, "reported_by": reported_by or None,
		"pre_session": 1 if pre_session else 0, "linked_event": linked_event,
	}))
	return event_id


def owner_event_replay(doc, owner_event_id: str, body_digest: str) -> str | None:
	"""PRC-N01: the same owner event ID returns its original event; a different
	payload under that ID fails and changes nothing."""
	if not owner_event_id:
		return None
	row = frappe.db.get_value(EVENT, {"event_key": f"{doc.name}:{owner_event_id}"}, ["event_id", "payload_digest"], as_dict=True)
	if not row:
		return None
	if row.payload_digest != body_digest:
		fail("PRC_VERSION_CONFLICT", {"reason": "owner_event_conflict", "owner_event_id": owner_event_id})
	return row.event_id
