# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §8.2 command envelope.

Every mutating command runs inside this envelope: a required idempotency key
(replayed verbatim from the Planning Command Journal on retry, rejected on
reuse with a different payload), a required expected record version checked
under a row lock, and a monotonic bump on success. Ported from the proven
NDS lifecycle mechanics; the journal replaces NDS's decision-row fingerprint
because most Planning commands (§8.2) have no business decision record.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import uuid4

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.errors import fail


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
		fail("PLN_STALE_WRITE", "An idempotency key is required.")
	row = frappe.db.get_value(
		"Planning Command Journal",
		{"idempotency_key": key},
		["request_fingerprint", "result"],
		as_dict=True,
	)
	if not row:
		return None
	if cstr(row.request_fingerprint) != fingerprint(payload):
		fail(
			"PLN_STALE_WRITE",
			"This idempotency key was already used with a different request.",
		)
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
			"doctype": "Planning Command Journal",
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
	rows = frappe.db.sql(
		f"select name from `tab{doctype}` where name=%s for update",
		cstr(name).strip(),
		as_dict=True,
	)
	if not rows:
		raise frappe.DoesNotExistError(f"{doctype} not found")
	return frappe.get_doc(doctype, rows[0].name)


def check_record_version(doc, expected_record_version) -> None:
	if cstr(expected_record_version) == "" or cstr(doc.record_version) != cstr(
		expected_record_version
	):
		fail("PLN_STALE_WRITE", "Another user changed this record. Reload before continuing.")


def bump(doc, **values) -> None:
	for field, value in values.items():
		doc.set(field, value)
	doc.record_version = int(doc.record_version or 0) + 1
	doc.save(ignore_permissions=True)


def assert_task_token(task_doc, presented_token: str) -> None:
	if cstr(presented_token) == "" or cstr(task_doc.task_token) != cstr(presented_token):
		fail("PLN_REVIEW_STALE", "This task has already changed. Reload to see the current decision.")
