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
	"""Apply `values` and advance `record_version`."""
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


def idempotent(key: str, command: str, payload: dict[str, Any], fn: Callable[[], dict[str, Any]], *, actor: str, organisation: str = "") -> dict[str, Any]:
	"""Run `fn` once per key. The same key with the same payload returns the
	recorded result; with a different payload it is refused. A result that is
	returned as data (`ok: False`) is not recorded, so a corrected retry runs."""
	key = cstr(key).strip()
	if not key:
		fail("BDS_FIELD_INVALID", "A request key is required.", {"fields": {"idempotency_key": "A request key is required."}})
	digest = _hash({"command": command, **payload})
	row = frappe.db.get_value(JOURNAL, {"idempotency_key": key}, ["command", "payload_hash", "result_json"], as_dict=True)
	if row:
		if row.command != command or row.payload_hash != digest:
			fail("BDS_IDEMPOTENCY_CONFLICT")
		return json.loads(row.result_json or "{}")
	result = fn()
	if result.get("ok") is not False:
		insert(frappe.get_doc({
			"doctype": JOURNAL, "idempotency_key": key, "command": command, "payload_hash": digest, "result_json": json.dumps(result, default=str),
			"actor": actor, "organisation": organisation, "recorded_at": clock.now(),
		}))
	return result


def emit(event_type: str, *, tender: str, actor: str, arrangement: str = "", workspace: str = "", organisation: str = "", payload: dict[str, Any] | None = None, at=None) -> Any:
	"""One audit event (§12.1). Its payload carries identities and facts,
	never response values."""
	return insert(frappe.get_doc({
		"doctype": EVENT, "event_type": event_type, "tender": tender, "bidder_arrangement": arrangement, "bid_workspace": workspace, "organisation": organisation,
		"actor": actor, "occurred_at": at or clock.now(), "payload_json": json.dumps(payload or {}, sort_keys=True, default=str),
	}))
