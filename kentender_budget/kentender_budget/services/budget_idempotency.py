# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.9 §9.3 / KT-STD-001 §11 — idempotent execution for the
governance commands (tracker D7) and the downstream-module money commands
(BUD-BR-015). RG-16, AUD-XC-002, AUD-XC-131.

A command that carries an `idempotency_key` runs in this order:

1. the caller is authorised (`authorise`), so a caller with no standing learns
   nothing about a key and leaves no claim behind;
2. the key is claimed by inserting a `Budget Command Journal` row inside a
   savepoint; the unique index on the key is the authority. The row binds the key
   to the actor, the command and a digest of the payload;
3. a claim that already exists is read with a locking read (it waits for an
   uncommitted first request and sees what it committed). The same actor,
   command and payload gets the recorded result flagged `replayed`; anything
   else is `BUDGET_IDEMPOTENCY_CONFLICT` and the recorded result is not returned;
4. only the winner of the claim runs the effect, so two concurrent requests
   with one key apply it once; its result is recorded on the claim.

A refusal returned as data (`ok: false`) records nothing and frees the key.
Commands without a key run as before: the journal is additive.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable
from uuid import uuid4

import frappe
from frappe import _
from frappe.utils import cstr, now_datetime

from kentender_budget.services.budget_write_family import budget_write

JOURNAL = "Budget Command Journal"
_EXCLUDED = ("idempotency_key",)


def payload_digest(payload: dict[str, Any]) -> str:
	clean = {k: v for k, v in (payload or {}).items() if k not in _EXCLUDED}
	text = json.dumps(clean, sort_keys=True, default=str, separators=(",", ":"))
	return hashlib.sha256(text.encode("utf-8")).hexdigest()


def conflict(key: str) -> dict[str, Any]:
	return {
		"ok": False,
		"code": "BUDGET_IDEMPOTENCY_CONFLICT",
		"errors": {"idempotency_key": _("This request differs from the original attempt. Check the original result before retrying; no new effect was created.")},
		"idempotency_key": key,
	}


def _insert_claim(key: str, command: str, actor: str, digest: str) -> bool:
	savepoint = f"bj_{uuid4().hex[:12]}"
	frappe.db.savepoint(savepoint)
	try:
		with budget_write():
			frappe.get_doc(
				{"doctype": JOURNAL, "idempotency_key": key, "command": command, "actor": actor, "request_fingerprint": digest, "occurred_at": now_datetime()}
			).insert(ignore_permissions=True)
	except (frappe.UniqueValidationError, frappe.DuplicateEntryError):
		frappe.db.rollback(save_point=savepoint)
		frappe.clear_last_message()
		return False
	frappe.db.release_savepoint(savepoint)
	return True


def _claim_or_replay(key: str, command: str, actor: str, digest: str) -> dict[str, Any] | None:
	"""None: this request owns the key and runs the command. A dict: the recorded result or the conflict."""
	for _attempt in range(3):
		if _insert_claim(key, command, actor, digest):
			return None
		row = frappe.db.get_value(JOURNAL, {"idempotency_key": key}, ["name", "command", "actor", "request_fingerprint", "result"], as_dict=True, for_update=True)
		if not row:
			continue  # the first request rolled back between the two statements: claim again
		if cstr(row.actor) != actor:
			return conflict(key)
		if not row.result:
			# nothing was recorded for this key: the same actor may reuse it
			frappe.db.set_value(JOURNAL, row.name, {"command": command, "request_fingerprint": digest}, update_modified=False)
			return None
		if cstr(row.command) != command or cstr(row.request_fingerprint) != digest:
			return conflict(key)
		try:
			replayed = json.loads(row.result or "{}")
		except ValueError:
			replayed = {}
		replayed["replayed"] = True
		return replayed
	return conflict(key)


def _release(key: str) -> None:
	"""Free a claim that produced no result."""
	frappe.db.sql(f"delete from `tab{JOURNAL}` where idempotency_key=%s and (result is null or result='')", key)


def _complete(key: str, result: dict[str, Any], budget: str | None) -> None:
	values = {"result": json.dumps(result, default=str), "occurred_at": now_datetime()}
	if budget:
		values["budget"] = budget
	frappe.db.set_value(JOURNAL, {"idempotency_key": key}, values, update_modified=False)


def run_idempotent(
	*,
	payload: dict[str, Any],
	fn: Callable[[], dict[str, Any]],
	budget_for: Callable[[dict[str, Any]], str | None],
	command: str,
	authorise: Callable[[], None] | None = None,
	actor: str | None = None,
) -> dict[str, Any]:
	"""Run `fn` once per (key, actor, command, payload digest). `authorise`
	raises when the caller has no standing for the command; it runs first, with
	or without a key. `actor` is the signed-in user unless a downstream module's
	service principal is acting. `budget_for(result)` names the Procurement
	Budget the recorded result belongs to, when it can be resolved."""
	if authorise:
		authorise()
	key = (payload.get("idempotency_key") or "").strip()
	if not key:
		return fn()
	actor = cstr(actor or frappe.session.user)
	digest = payload_digest({"command": command, **payload})
	prior = _claim_or_replay(key, command, actor, digest)
	if prior is not None:
		return prior
	try:
		result = fn()
	except BaseException:
		_release(key)
		raise
	if isinstance(result, dict) and result.get("ok") is False:
		_release(key)
		return result
	_complete(key, result, budget_for(result))
	return result
