# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §7.4 (last paragraph) / §11.1 — the command envelope.

Every mutating command runs inside this envelope: a required idempotency key
(replayed verbatim from the Tender Command Journal on retry, rejected on
reuse with a different payload — `TND_IDEMPOTENCY_CONFLICT`), a required
expected record version checked under a row lock (`TND_STALE_VERSION`), and
a monotonic bump on success. Copied by diff from Procurement Requisitions'
proven `envelope.py` (same mechanics, this module's own journal doctype and
error contract) — AGENTS.md §4.2, "reuse existing services".
"""

from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from typing import Any
from uuid import uuid4

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.tenders.services.errors import fail

JOURNAL = "Tender Command Journal"


def token() -> str:
	return uuid4().hex


def fingerprint(payload: dict[str, Any]) -> str:
	material = {
		key: cstr(value)
		for key, value in sorted(payload.items())
		if key not in {"user", "idempotency_key"} and value is not None
	}
	return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()


def replay_or_none(idempotency_key: str, payload: dict[str, Any]) -> dict[str, Any] | None:
	"""Return the recorded result for a repeated key; reject key reuse."""
	key = cstr(idempotency_key).strip()
	if not key:
		fail("TND_STALE_VERSION", "An idempotency key is required.")
	row = frappe.db.get_value(JOURNAL, {"idempotency_key": key}, ["request_fingerprint", "result"], as_dict=True)
	if not row:
		return None
	if cstr(row.request_fingerprint) != fingerprint(payload):
		fail("TND_IDEMPOTENCY_CONFLICT")
	result = json.loads(row.result) if row.result else {}
	result["idempotent"] = True
	return result


def record_command(
	*,
	idempotency_key: str,
	command: str,
	payload: dict[str, Any],
	result: dict[str, Any],
	document_type: str = "",
	document_name: str = "",
	actor: str | None = None,
	fixture_namespace: str = "",
) -> None:
	frappe.get_doc(
		{
			"doctype": JOURNAL,
			"idempotency_key": cstr(idempotency_key).strip(),
			"command": command,
			"document_type": document_type,
			"document_name": document_name,
			"request_fingerprint": fingerprint(payload),
			"actor": actor or frappe.session.user,
			"result": json.dumps(result, default=str),
			"occurred_at": now_datetime(),
			"fixture_namespace": fixture_namespace,
		}
	).insert(ignore_permissions=True)


def locked(doctype: str, name: str):
	"""Row-lock and load one document; masked not-found for missing rows."""
	rows = frappe.db.sql(f"select name from `tab{doctype}` where name=%s for update", cstr(name).strip(), as_dict=True)
	if not rows:
		raise frappe.DoesNotExistError(f"{doctype} not found")
	return frappe.get_doc(doctype, rows[0].name)


def check_record_version(doc, expected_record_version) -> None:
	if cstr(expected_record_version) == "" or cstr(doc.record_version) != cstr(expected_record_version):
		fail("TND_STALE_VERSION")


def bump(doc, **values) -> None:
	"""The one writer of immutable rows (plan D14): sets the given columns,
	bumps `record_version` when the doctype carries one, and saves under the
	lifecycle flag the controllers' `validate()` guards look for."""
	for field, value in values.items():
		doc.set(field, value)
	if doc.meta.has_field("record_version"):
		doc.record_version = int(doc.record_version or 0) + 1
	doc.flags.kt_lifecycle = True
	doc.save(ignore_permissions=True)


def insert(doc):
	"""Insert a new lifecycle-owned row (the controllers only guard updates)."""
	doc.flags.kt_lifecycle = True
	doc.insert(ignore_permissions=True)
	return doc


def assert_task_token(task_doc, presented_token: str) -> None:
	if cstr(presented_token) == "" or cstr(task_doc.task_token) != cstr(presented_token):
		fail("TND_STALE_VERSION", "This task has already changed. Reload to see the current decision.")


@contextmanager
def atomic(_label: str = ""):
	"""A named savepoint around one command's own writes (§5.8 invariant 2:
	Draft creation and Requisition consumption commit together or neither
	commits). A failure inside rolls back to the savepoint without discarding
	the caller's outer transaction."""
	savepoint = f"tnd_{uuid4().hex[:12]}"
	frappe.db.savepoint(savepoint)
	try:
		yield
	except Exception:
		frappe.db.rollback(save_point=savepoint)
		raise
	else:
		frappe.db.release_savepoint(savepoint)
