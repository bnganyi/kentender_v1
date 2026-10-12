# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Writing Bid Submission records: every insert or change goes through here
under `flags.kt_bid_command` (the DocType controllers refuse any other
write); every command is idempotent by key (BDS-CHG-001 v0.8 §7: "Every
mutation accepts an expected record version and idempotency key"); and each
command's own writes commit together or not at all (`atomic`)."""

from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from typing import Any, Callable
from uuid import uuid4

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_submission.services import clock
from kentender_procurement.bid_submission.services.errors import fail

JOURNAL = "Bid Command Journal"
EVENT = "Bid Submission Event"
EVENT_SCHEMA_VERSION = 1  # §12.1: event identity and schema version


def namespace() -> str:
	"""Test and seed worlds stamp their records so they can be removed exactly."""
	return cstr(frappe.flags.get("kt_bds_fixture_namespace") or "")


def insert(doc) -> Any:
	if doc.meta.has_field("fixture_namespace") and not doc.get("fixture_namespace"):
		doc.fixture_namespace = namespace()
	doc.flags.kt_bid_command = True
	doc.insert(ignore_permissions=True)
	return doc


def save(doc) -> Any:
	doc.flags.kt_bid_command = True
	doc.save(ignore_permissions=True)
	return doc


def bump(doc, **values) -> Any:
	"""Apply `values` and advance `record_version`. A bid's status change is
	remembered for the command's events (§12.1 previous and resulting states)."""
	context = getattr(frappe.local, "kt_bds_command", None)
	if context and doc.doctype == "Bid Workspace" and "status" in values:
		context["transitions"].setdefault(doc.name, cstr(doc.status))
	for field, value in values.items():
		doc.set(field, value)
	if doc.meta.has_field("record_version"):
		doc.record_version = int(doc.record_version or 0) + 1
	return save(doc)


def check_version(doc, expected) -> None:
	try:
		ok = expected is not None and int(expected) == int(doc.record_version or 0)
	except (TypeError, ValueError):
		ok = False
	if not ok:
		fail("BDS_STALE_VERSION", detail={"record_version": int(doc.record_version or 0)})


@contextmanager
def atomic(label: str = ""):
	"""A savepoint around one command's own writes: a failure inside rolls
	back to it without discarding the caller's outer transaction (§7.2
	`StartBid`: "No standalone arrangement survives a failed workspace
	creation")."""
	savepoint = f"bds_{uuid4().hex[:12]}"
	frappe.db.savepoint(savepoint)
	try:
		yield
	except Exception:
		frappe.db.rollback(save_point=savepoint)
		raise
	else:
		frappe.db.release_savepoint(savepoint)


def _hash(payload: dict[str, Any]) -> str:
	return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _claim(key: str, command: str, digest: str, actor: str, organisation: str) -> bool:
	"""Claim the key with a unique insert inside a savepoint; the unique index on the key is the authority."""
	savepoint = f"bdj_{uuid4().hex[:12]}"
	frappe.db.savepoint(savepoint)
	try:
		insert(frappe.get_doc({"doctype": JOURNAL, "idempotency_key": key, "command": command, "payload_hash": digest, "actor": actor, "organisation": organisation, "recorded_at": clock.now()}))
	except (frappe.UniqueValidationError, frappe.DuplicateEntryError):
		frappe.db.rollback(save_point=savepoint)
		frappe.clear_last_message()
		return False
	frappe.db.release_savepoint(savepoint)
	return True


def idempotent(key: str, command: str, payload: dict[str, Any], fn: Callable[[], dict[str, Any]], *, actor: str, organisation: str = "") -> dict[str, Any]:
	"""Run `fn` once per key (RG-17, AUD-XC-131). The key is claimed by a unique insert before the command
	runs, bound to the actor, the command and the payload: the same actor repeating the same request gets the
	recorded result (a duplicate that arrives while the first is still running waits for it and replays it);
	another user, another command or another payload is refused. A result that is returned as data
	(`ok: False`) is not recorded, so a corrected retry runs."""
	key = cstr(key).strip()
	if not key:
		fail("BDS_FIELD_INVALID", "A request key is required.", {"fields": {"idempotency_key": "A request key is required."}})
	digest = _hash({"command": command, **payload})
	actor = cstr(actor)
	for _attempt in range(3):
		if _claim(key, command, digest, actor, organisation):
			break
		# a locking read: it waits for an uncommitted claim and sees the committed row (a plain read would use the older snapshot)
		row = frappe.db.get_value(JOURNAL, {"idempotency_key": key}, ["name", "command", "payload_hash", "result_json", "actor"], as_dict=True, for_update=True)
		if not row:
			continue  # the first request rolled back between the two statements: claim again
		if cstr(row.actor) != actor or row.command != command or row.payload_hash != digest:
			fail("BDS_IDEMPOTENCY_CONFLICT")
		if row.result_json:
			return json.loads(row.result_json)
		break  # a claim that recorded nothing (interrupted): the same actor may run the command
	else:
		fail("BDS_IDEMPOTENCY_CONFLICT")
	with running(command, key):
		result = fn()
	if result.get("ok") is not False:
		frappe.db.set_value(JOURNAL, {"idempotency_key": key}, {"result_json": json.dumps(result, default=str), "recorded_at": clock.now()}, update_modified=False)
	else:
		frappe.db.sql(f"delete from `tab{JOURNAL}` where idempotency_key=%s and (result_json is null or result_json='')", key)
	return result


@contextmanager
def running(command: str, key: str):
	"""The command a mutation runs under, for its events (§12.1: command name
	and idempotency-key hash). Nested commands keep their own."""
	previous = getattr(frappe.local, "kt_bds_command", None)
	frappe.local.kt_bds_command = {"command": command, "key_hash": hashlib.sha256(cstr(key).encode()).hexdigest(), "transitions": {}}
	try:
		yield
	finally:
		frappe.local.kt_bds_command = previous


def remember_assignment(actor: str, assignment_id: str) -> None:
	"""The acting assignment resolved for `actor` in this request (§12.1)."""
	if getattr(frappe.local, "kt_bds_assignments", None) is None:
		frappe.local.kt_bds_assignments = {}
	frappe.local.kt_bds_assignments[cstr(actor)] = cstr(assignment_id)


def emit(event_type: str, *, tender: str, actor: str, arrangement: str = "", workspace: str = "", organisation: str = "", payload: dict[str, Any] | None = None, at=None) -> Any:
	"""One audit event with the §12.1 minimum: schema version; the Tender,
	arrangement, workspace, organisation and resulting record version; the
	command and its request-key hash; the actor and acting assignment; the
	instant in UTC and as displayed in EAT; the bid's previous and resulting
	states. Its payload carries identities and facts, never response values."""
	from kentender_core.utils.instants import to_utc_iso

	from kentender_procurement.bid_submission.services import labels

	at = at or clock.now()
	context = getattr(frappe.local, "kt_bds_command", None) or {}
	previous = resulting = ""
	record_version = 0
	if workspace:
		row = frappe.db.get_value("Bid Workspace", workspace, ["status", "record_version"], as_dict=True)
		if row:
			resulting, record_version = cstr(row.status), int(row.record_version or 0)
			previous = (context.get("transitions") or {}).get(workspace, resulting)
	return insert(frappe.get_doc({
		"doctype": EVENT, "event_type": event_type, "tender": tender, "bidder_arrangement": arrangement, "bid_workspace": workspace, "organisation": organisation,
		"actor": actor, "occurred_at": at, "payload_json": json.dumps(payload or {}, sort_keys=True, default=str),
		"schema_version": EVENT_SCHEMA_VERSION, "command": cstr(context.get("command")), "idempotency_key_hash": cstr(context.get("key_hash")),
		"assignment": cstr((getattr(frappe.local, "kt_bds_assignments", None) or {}).get(cstr(actor))),
		"occurred_at_utc": to_utc_iso(at), "occurred_at_eat": labels.datetime_seconds_label(at),
		"previous_status": previous, "resulting_status": resulting, "record_version": record_version,
	}))
