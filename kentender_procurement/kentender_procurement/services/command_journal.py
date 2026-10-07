# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The idempotency journal mechanics shared by the Requisitions and Tenders
command envelopes (AUD-XC-131, AUD-XC-130).

A command claims its idempotency key with a unique insert in its own
transaction, after the caller has been authorised and before the command reads
or changes anything else:

* the key is bound to the actor, the command and the payload: a key reused by
  another user, for another command or with another payload is a typed
  conflict and the recorded result is never handed back;
* two requests with one key run once: the second request's insert waits on the
  first request's uncommitted claim, and when the first commits the second reads
  that row with a locking read (a plain read would return its older
  REPEATABLE READ snapshot) and replays the original result;
* a claim that never produced a result (a command that returned a refusal as
  data, or one that was interrupted after a commit) carries nothing to replay,
  so the same actor may reuse the key; nobody else may.

Journal rows written before this change carry the same `actor`, `command` and
payload fingerprint columns, so they replay for the same actor and command
exactly as before and are a conflict for anyone else.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable
from uuid import uuid4

import frappe
from frappe.utils import cstr, now_datetime

from kentender_core.services.command_write_guard import command_write

IGNORED_PAYLOAD_KEYS = {"user", "idempotency_key"}


def fingerprint(payload: dict[str, Any]) -> str:
	material = {
		key: cstr(value)
		for key, value in sorted(payload.items())
		if key not in IGNORED_PAYLOAD_KEYS and value is not None
	}
	return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()


def claim_or_replay(
	*,
	journal: str,
	family: str,
	idempotency_key: str,
	command: str,
	actor: str,
	payload: dict[str, Any],
	conflict: Callable[[], None],
	key_required: Callable[[], None],
) -> dict[str, Any] | None:
	"""Claim the key (None: run the command) or return the recorded result.
	`conflict` and `key_required` raise the module's typed refusals."""
	key = cstr(idempotency_key).strip()
	if not key:
		key_required()
	actor = cstr(actor or frappe.session.user)
	fp = fingerprint(payload)
	for _ in range(3):
		if _insert_claim(journal, family, key, command, actor, fp):
			return None
		# a locking read: waits for an uncommitted claim, sees the committed row
		row = frappe.db.get_value(
			journal, {"idempotency_key": key}, ["name", "command", "actor", "request_fingerprint", "result"], as_dict=True, for_update=True
		)
		if not row:
			continue  # the first request rolled back between the two statements: claim again
		if cstr(row.actor) != actor:
			conflict()
		if not row.result:
			# nothing was recorded for this key: the same actor may reuse it
			frappe.db.set_value(journal, row.name, {"command": command, "request_fingerprint": fp}, update_modified=False)
			return None
		if cstr(row.command) != command or cstr(row.request_fingerprint) != fp:
			conflict()
		result = json.loads(row.result) if isinstance(row.result, str) else dict(row.result)
		result["idempotent"] = True
		return result
	conflict()
	return None


def _insert_claim(journal: str, family: str, key: str, command: str, actor: str, fp: str) -> bool:
	savepoint = f"jr_{uuid4().hex[:12]}"
	frappe.db.savepoint(savepoint)
	try:
		with command_write(family):
			frappe.get_doc(
				{
					"doctype": journal, "idempotency_key": key, "command": command, "request_fingerprint": fp,
					"actor": actor, "occurred_at": now_datetime(),
				}
			).insert(ignore_permissions=True)
	except (frappe.UniqueValidationError, frappe.DuplicateEntryError):
		frappe.db.rollback(save_point=savepoint)
		frappe.clear_last_message()
		return False
	frappe.db.release_savepoint(savepoint)
	return True


def complete(
	*,
	journal: str,
	family: str,
	idempotency_key: str,
	command: str,
	actor: str,
	payload: dict[str, Any],
	result: dict[str, Any],
	document_type: str = "",
	document_name: str = "",
	fixture_namespace: str = "",
) -> None:
	"""Record the command's result on its claim (or insert the row when the
	command never claimed one, e.g. a caller outside the envelope)."""
	key = cstr(idempotency_key).strip()
	values = {
		"command": command, "document_type": document_type, "document_name": document_name,
		"request_fingerprint": fingerprint(payload), "actor": cstr(actor or frappe.session.user),
		"result": json.dumps(result, default=str), "occurred_at": now_datetime(), "fixture_namespace": fixture_namespace,
	}
	name = frappe.db.get_value(journal, {"idempotency_key": key}, "name", for_update=True)
	if name:
		frappe.db.set_value(journal, name, values, update_modified=False)
		return
	with command_write(family):
		frappe.get_doc({"doctype": journal, "idempotency_key": key, **values}).insert(ignore_permissions=True)


def release(journal: str, idempotency_key: str) -> None:
	"""Give up a claim that produced no result (a refusal returned as data), so
	the key stays free for a corrected attempt."""
	frappe.db.sql(
		f"delete from `tab{journal}` where idempotency_key=%s and (result is null or result='')", cstr(idempotency_key).strip()
	)
