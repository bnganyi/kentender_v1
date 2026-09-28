# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Writing Supplier Account records: every insert or change goes through
here under `flags.kt_account_command` (the DocType controllers refuse any
other write), and every command is idempotent by key (BDS-CHG-001 v0.8 §7:
"Every mutation accepts an expected record version and idempotency key")."""

from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from typing import Any, Callable

import frappe
from frappe.utils import cstr

from kentender_suppliers.supplier_accounts.services import clock
from kentender_suppliers.supplier_accounts.services.errors import fail

JOURNAL = "Supplier Account Command Journal"


def namespace() -> str:
	"""Test and seed worlds stamp their records so they can be removed exactly."""
	return cstr(frappe.flags.get("kt_accounts_fixture_namespace") or "")


def insert(doc) -> Any:
	if doc.meta.has_field("fixture_namespace") and not doc.get("fixture_namespace"):
		doc.fixture_namespace = namespace()
	doc.flags.kt_account_command = True
	doc.insert(ignore_permissions=True)
	return doc


def save(doc) -> Any:
	doc.flags.kt_account_command = True
	doc.save(ignore_permissions=True)
	return doc


def bump(doc, **values) -> Any:
	"""Apply `values` and advance `record_version` (when the record has one).
	An Account's status change is remembered for the command's audit event
	(§12.1 previous and resulting states)."""
	context = getattr(frappe.local, "kt_acc_command", None)
	if context and doc.doctype == "Supplier Organisation" and "account_status" in values:
		context["transitions"].setdefault(doc.name, cstr(doc.account_status))
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


def _hash(payload: dict[str, Any]) -> str:
	return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


@contextmanager
def running(command: str, key: str):
	"""The command a mutation runs under, for its audit event (§12.1: command
	name and idempotency-key hash)."""
	previous = getattr(frappe.local, "kt_acc_command", None)
	frappe.local.kt_acc_command = {"command": command, "key_hash": hashlib.sha256(cstr(key).encode()).hexdigest(), "transitions": {}}
	try:
		yield
	finally:
		frappe.local.kt_acc_command = previous


def idempotent(key: str, command: str, payload: dict[str, Any], fn: Callable[[], dict[str, Any]], *, actor: str, organisation: str = "") -> dict[str, Any]:
	"""Run `fn` once per key. The same key with the same payload returns the
	recorded result; with a different payload it is refused. Field-error
	results (`ok: False`) are not recorded, so a corrected retry runs."""
	key = cstr(key).strip()
	if not key:
		fail("BDS_FIELD_INVALID", "A request key is required.", {"fields": {"idempotency_key": "A request key is required."}})
	digest = _hash({"command": command, **payload})
	row = frappe.db.get_value(JOURNAL, {"idempotency_key": key}, ["command", "payload_hash", "result_json"], as_dict=True)
	if row:
		if row.command != command or row.payload_hash != digest:
			fail("BDS_IDEMPOTENCY_CONFLICT")
		return json.loads(row.result_json or "{}")
	with running(command, key):
		result = fn()
	if result.get("ok") is not False:
		insert(frappe.get_doc({
			"doctype": JOURNAL, "idempotency_key": key, "command": command, "payload_hash": digest,
			"result_json": json.dumps(result, default=str), "actor": actor, "organisation": organisation or cstr(result.get("organisation")), "recorded_at": clock.now(),
		}))
	return result
