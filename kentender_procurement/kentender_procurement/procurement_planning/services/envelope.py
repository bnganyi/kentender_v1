# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §8.2 command envelope.

Every mutating command runs inside this envelope: a required idempotency key
(replayed verbatim from the Planning Command Journal on retry), a required
expected record version checked under a row lock, and a monotonic bump on
success. Ported from the proven NDS lifecycle mechanics; the journal replaces
NDS's decision-row fingerprint because most Planning commands (§8.2) have no
business decision record.

A key is bound to the command, the actor and the payload that first used it
(AUD-XC-131): the same key from another user, for another command or with
another payload is `PLN_IDEMPOTENCY_CONFLICT`, never a silent replay. The key
is claimed with a unique insert at the start of the command, inside its
transaction, so a duplicate that arrives meanwhile waits for the first request
to finish and then returns its original result (AUD-XC-130); the claim is
completed by `record_command` and removed again if the command fails (the
command's savepoint) or finishes without recording it.

The commands authorise in many different ways inside their bodies, so instead
of re-running each one's check the journal records the actor's standing (their
active responsibilities) when it claims the key, and answers a replay only
while the actor still holds all of it.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import uuid4

import frappe
from frappe.utils import cstr, now_datetime

from kentender_core.services.authorization import active_assignment_rows
from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.write_family import current_scope, planning_write

JOURNAL = "Planning Command Journal"


def token() -> str:
	return uuid4().hex


def _material(payload: dict[str, Any]) -> dict[str, str]:
	return {
		key: cstr(value)
		for key, value in sorted(payload.items())
		if key not in {"user", "idempotency_key"} and value is not None
	}


def legacy_fingerprint(payload: dict[str, Any]) -> str:
	"""The payload-only digest journal rows carried before AUD-XC-131. Kept to
	recognise those rows (replayed to the actor who wrote them only)."""
	return hashlib.sha256(json.dumps(_material(payload), sort_keys=True).encode()).hexdigest()


def fingerprint(payload: dict[str, Any], *, command: str = "", actor: str = "") -> str:
	"""A digest of the command, its actor and the caller's payload."""
	scope = current_scope()
	command = command or (scope.command if scope else "")
	actor = actor or (scope.actor if scope else cstr(frappe.session.user))
	return hashlib.sha256(
		json.dumps({"command": command, "actor": actor, "payload": _material(payload)}, sort_keys=True).encode()
	).hexdigest()


def standing(actor: str) -> list[str]:
	"""What the actor holds now: each active responsibility with its role and
	scope. A replay is answered only to an actor who still holds everything they
	held when the command first ran, so a responsibility that has ended since
	does not get a recorded result."""
	if not actor:
		return []
	return sorted(
		f"{row['name']}|{row['business_role']}|{row.get('organisation_unit') or ''}" for row in active_assignment_rows(actor)
	)


def replay_or_none(idempotency_key: str, payload: dict[str, Any]) -> dict[str, Any] | None:
	"""Claim the key for this command, or return the recorded result of a
	repeated one. Returns `None` when the caller should run the command."""
	key = cstr(idempotency_key).strip()
	if not key:
		fail("PLN_STALE_WRITE", "An idempotency key is required.")
	scope = current_scope()
	if scope is None:
		raise RuntimeError("replay_or_none must run inside a @planning_command")
	fp = fingerprint(payload)
	if _claim(key, scope.command, scope.actor, fp):
		scope.claimed.append(key)
		return None
	return _recorded(key, scope, payload, fp)


def _claim(key: str, command: str, actor: str, fp: str) -> bool:
	"""Insert the key's journal row; False when a committed row holds it. The
	insert waits for a request that has claimed the key but not yet finished."""
	savepoint = f"pln_{uuid4().hex[:12]}"
	frappe.db.savepoint(savepoint)
	try:
		with planning_write():
			frappe.get_doc(
				{
					"doctype": JOURNAL,
					"idempotency_key": key,
					"command": command,
					"request_fingerprint": fp,
					"actor": actor,
					"standing": json.dumps(standing(actor)),
					"occurred_at": now_datetime(),
				}
			).insert(ignore_permissions=True)
	except (frappe.UniqueValidationError, frappe.DuplicateEntryError):
		frappe.db.rollback(save_point=savepoint)
		frappe.clear_last_message()
		return False
	frappe.db.release_savepoint(savepoint)
	return True


def _recorded(key: str, scope, payload: dict[str, Any], fp: str) -> dict[str, Any] | None:
	"""The original result of a key that is already claimed: a conflict for
	another actor, command or payload; refused (as not found) to an actor who no
	longer holds the standing it was recorded with."""
	# A locking read: a plain one returns this transaction's older snapshot,
	# which cannot see a row another request committed while this one waited.
	row = frappe.db.get_value(
		JOURNAL, {"idempotency_key": key}, ["actor", "request_fingerprint", "standing", "result"], as_dict=True, for_update=True
	)
	if row is None:
		# The first request rolled back after this one began waiting: run it here.
		return replay_or_none(key, payload)
	legacy = row.standing is None  # written before the key was bound to command and actor
	same = cstr(row.actor) == scope.actor and cstr(row.request_fingerprint) == (legacy_fingerprint(payload) if legacy else fp)
	if not same:
		fail("PLN_IDEMPOTENCY_CONFLICT")
	if not legacy and not set(json.loads(row.standing or "[]")) <= set(standing(scope.actor)):
		raise frappe.DoesNotExistError("Not found")
	if not row.result:
		# Claimed and committed without a recorded result: run it here.
		scope.claimed.append(key)
		return None
	result = json.loads(row.result)
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
	"""Complete the claim this command made (or, for a command that never
	claimed its key, insert the row)."""
	key = cstr(idempotency_key).strip()
	scope = current_scope()
	values = {
		"command": command,
		"document_type": document_type,
		"document_name": document_name,
		"result": json.dumps(result, default=str),
		"occurred_at": now_datetime(),
		"fixture_namespace": fixture_namespace,
	}
	if scope is not None and key in scope.claimed:
		frappe.db.set_value(JOURNAL, {"idempotency_key": key}, values, update_modified=False)
		scope.recorded.add(key)
		return
	who = actor or (scope.actor if scope else frappe.session.user)
	with planning_write():
		frappe.get_doc(
			{
				"doctype": JOURNAL,
				"idempotency_key": key,
				"request_fingerprint": fingerprint(payload, command=scope.command if scope else command, actor=who),
				"actor": who,
				"standing": json.dumps(standing(who)),
				**values,
			}
		).insert(ignore_permissions=True)
	if scope is not None:
		scope.recorded.add(key)


def release_unrecorded(scope) -> None:
	"""A command that claimed a key and finished without recording it (an early
	return that changed nothing) gives the key back."""
	for key in scope.claimed:
		if key not in scope.recorded:
			frappe.db.delete(JOURNAL, {"idempotency_key": key})


def locked(doctype: str, name: str):
	"""Row-lock and load one document as last committed; masked not-found for
	missing rows. MariaDB runs at REPEATABLE READ, so a plain read after the
	lock would return this transaction's older snapshot and a recheck made on it
	(a hold, an item state, a record version) would pass on facts a competing
	command had already changed and committed (AUD-XC-107); the locking read
	(`for_update`) sees what that command committed."""
	rows = frappe.db.sql(
		f"select name from `tab{doctype}` where name=%s for update",
		cstr(name).strip(),
		as_dict=True,
	)
	if not rows:
		raise frappe.DoesNotExistError(f"{doctype} not found")
	return frappe.get_doc(doctype, rows[0].name, for_update=True)


def check_record_version(doc, expected_record_version) -> None:
	if cstr(expected_record_version) == "" or cstr(doc.record_version) != cstr(
		expected_record_version
	):
		fail("PLN_STALE_WRITE", "Another user changed this record. Reload before continuing.")


def bump(doc, **values) -> None:
	for field, value in values.items():
		doc.set(field, value)
	doc.record_version = int(doc.record_version or 0) + 1
	with planning_write():  # the one save every lifecycle step goes through
		doc.save(ignore_permissions=True)


def assert_task_token(task_doc, presented_token: str) -> None:
	if cstr(presented_token) == "" or cstr(task_doc.task_token) != cstr(presented_token):
		fail("PLN_REVIEW_STALE", "This task has already changed. Reload to see the current decision.")
