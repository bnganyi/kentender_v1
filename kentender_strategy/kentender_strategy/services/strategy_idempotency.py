# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 BR-017 / STR §8.2 / KT-STD-001 §11 — the Strategy command journal.

One idempotency key belongs to one (actor, command, payload). The journal
answers in this order, and only in this order:

1. the caller is authorised for the command (`authorise`), so a recorded
   result is never shown to someone who may not act;
2. the key is claimed with a unique-key insert inside the command's own
   transaction. A concurrent duplicate blocks on that insert until the first
   execution commits (and runs for itself if it rolled back), so two requests
   with one key can never both execute;
3. a key that already exists is replayed only when its actor, command and
   payload hash all match; anything else is `STRATEGY_IDEMPOTENCY_CONFLICT`
   and nothing runs.

The claim, the command's effects and the recorded result commit or roll back
together: a command that raises leaves no journal row, so a corrected retry
with the same key runs.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable
from uuid import uuid4

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender_core.services.command_write_guard import command_write

JOURNAL = "Strategy Command Journal"
CONFLICT = "STRATEGY_IDEMPOTENCY_CONFLICT"
KEY_REQUIRED = "STRATEGY_IDEMPOTENCY_REQUIRED"
VERSION_REQUIRED = "STRATEGY_VERSION_REQUIRED"


def payload_hash(payload: Any) -> str:
	text = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"), ensure_ascii=False)
	return hashlib.sha256(text.encode("utf-8")).hexdigest()


def require_command_inputs(idempotency_key: str | None, expected_version: str | None = None, *, version_required: bool = False) -> tuple[str, str | None]:
	"""STR §8 / KT-STD-001 §11 — every state command carries an idempotency
	key, and a command on an existing version carries the expected version.
	Returns the trimmed key and token."""
	key = (idempotency_key or "").strip()
	if not key:
		frappe.throw(_("This request needs an idempotency key so a retry cannot repeat it."), frappe.ValidationError, title=KEY_REQUIRED)
	token = (str(expected_version).strip() if expected_version is not None else "") or None
	if version_required and not token:
		frappe.throw(_("This request needs the version you loaded, so a stale save cannot overwrite a newer one."), frappe.ValidationError, title=VERSION_REQUIRED)
	return key, token


def _conflict() -> None:
	frappe.throw(
		_("This idempotency key was used for a different request. Check the original result before retrying; nothing was changed."),
		frappe.ValidationError,
		title=CONFLICT,
	)


def _claim(key: str, document_type: str, document_name: str, action: str, actor: str, digest: str) -> bool:
	"""Insert the key's journal row. False when a committed (or, after
	waiting, a just-committed) row already holds the key."""
	savepoint = f"strj_{uuid4().hex[:12]}"
	frappe.db.savepoint(savepoint)
	try:
		with command_write("Strategy"):
			frappe.get_doc(
				{
					"doctype": JOURNAL,
					"idempotency_key": key,
					"document_type": document_type,
					"document_name": document_name,
					"action": action,
					"actor": actor,
					"payload_hash": digest,
					"created_at": now_datetime(),
					"result": "",
				}
			).insert(ignore_permissions=True)
	except (frappe.UniqueValidationError, frappe.DuplicateEntryError):
		frappe.db.rollback(save_point=savepoint)
		frappe.clear_last_message()
		return False
	frappe.db.release_savepoint(savepoint)
	return True


def run_idempotent(
	idempotency_key: str | None,
	document_type: str,
	document_name: str,
	action: str,
	fn: Callable[[], dict],
	*,
	payload: Any = None,
	authorise: Callable[[], Any] | None = None,
) -> dict:
	"""Run `fn` once per (key, actor, `action`, `payload`); a replay returns
	the original result. `authorise` raises unless the caller may issue the
	command, and runs before the journal is read."""
	if authorise is not None:
		authorise()
	if not idempotency_key:
		return fn()

	actor = frappe.session.user
	digest = payload_hash(payload)
	savepoint = f"strc_{uuid4().hex[:12]}"
	frappe.db.savepoint(savepoint)
	if not _claim(idempotency_key, document_type, document_name, action, actor, digest):
		frappe.db.release_savepoint(savepoint)
		# A locking read: it sees the row the winner has just committed.
		row = frappe.db.get_value(
			JOURNAL, {"idempotency_key": idempotency_key}, ["actor", "action", "payload_hash", "result"], as_dict=True, for_update=True
		)
		if not row or row.actor != actor or row.action != action or row.payload_hash != digest or not row.result:
			_conflict()
		return frappe.parse_json(row.result)

	try:
		result = fn()
	except Exception:
		# The claim goes with the failed command: a corrected retry runs.
		frappe.db.rollback(save_point=savepoint)
		raise
	frappe.db.release_savepoint(savepoint)
	frappe.db.set_value(JOURNAL, {"idempotency_key": idempotency_key}, "result", frappe.as_json(result), update_modified=False)
	return result
