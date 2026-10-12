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

from contextlib import contextmanager
from typing import Any
from uuid import uuid4

import frappe
from frappe.utils import cstr

from kentender_core.services.command_write_guard import command_write
from kentender_procurement.services import command_journal
from kentender_procurement.tenders.services.errors import fail

JOURNAL = "Tender Command Journal"
# The Tenders command-write family (AUD-XC-013): every Tender doctype's
# controller refuses a write that is not made inside `command_write(FAMILY)`.
FAMILY = "Tenders"


def token() -> str:
	return uuid4().hex


def fingerprint(payload: dict[str, Any]) -> str:
	return command_journal.fingerprint(payload)


def replay_or_none(idempotency_key: str, payload: dict[str, Any], *, command: str, actor: str) -> dict[str, Any] | None:
	"""Claim the key for this actor, command and payload, or return the recorded
	result of the same request (AUD-XC-131, AUD-XC-130; TPR09-AC-007).

	Call it after the caller has been authorised and before the command reads or
	changes anything else. A key reused by another user, for another command or
	with another payload is `TND_IDEMPOTENCY_CONFLICT` and the recorded result is
	not returned; a duplicate that arrives while the first request is still
	running waits for it and gets its result. `record_command` completes the claim."""
	return command_journal.claim_or_replay(
		journal=JOURNAL, family=FAMILY, idempotency_key=idempotency_key, command=command, actor=actor, payload=payload,
		conflict=lambda: fail("TND_IDEMPOTENCY_CONFLICT"),
		key_required=lambda: fail("TND_STALE_VERSION", "An idempotency key is required."),
	)


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
	command_journal.complete(
		journal=JOURNAL, family=FAMILY, idempotency_key=idempotency_key, command=command, actor=actor or frappe.session.user,
		payload=payload, result=result, document_type=document_type, document_name=document_name, fixture_namespace=fixture_namespace,
	)


def release_claim(idempotency_key: str) -> None:
	"""A command that returns a refusal as data records nothing; free its key."""
	command_journal.release(JOURNAL, idempotency_key)


def locked(doctype: str, name: str):
	"""Row-lock and load one document as last committed; masked not-found for
	missing rows. MariaDB runs at REPEATABLE READ, so a plain read after the
	lock returns this transaction's older snapshot and a waiter would pass
	`check_record_version` (or any recheck made on the document) on facts a
	competing command had already changed and committed, to be stopped only by
	Frappe's save-time timestamp check instead of `TND_STALE_VERSION`
	(AUD-XC-130, AUD-XC-107). The locking read (`for_update`) sees what that
	command committed."""
	rows = frappe.db.sql(f"select name from `tab{doctype}` where name=%s for update", cstr(name).strip(), as_dict=True)
	if not rows:
		raise frappe.DoesNotExistError(f"{doctype} not found")
	return frappe.get_doc(doctype, rows[0].name, for_update=True)


def check_record_version(doc, expected_record_version) -> None:
	if cstr(expected_record_version) == "" or cstr(doc.record_version) != cstr(expected_record_version):
		fail("TND_STALE_VERSION")


def bump(doc, **values) -> None:
	"""The one writer of immutable rows (plan D14): sets the given columns,
	bumps `record_version` when the doctype carries one, and saves under the
	command-write window the controllers' guards look for."""
	for field, value in values.items():
		doc.set(field, value)
	if doc.meta.has_field("record_version"):
		doc.record_version = int(doc.record_version or 0) + 1
	with command_write(FAMILY):
		doc.save(ignore_permissions=True)


def insert(doc):
	"""Insert a new lifecycle-owned row (the controllers refuse any insert made outside the window)."""
	with command_write(FAMILY):
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
