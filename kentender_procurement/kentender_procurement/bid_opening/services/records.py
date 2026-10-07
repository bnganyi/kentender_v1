# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Writing Bid Opening records (BOP-CHG-001 v0.10 §7: "Every mutation takes
expected version and idempotency key, authenticates actor, and uses trusted
server time. Replay of the same committed request returns its result;
conflicting replay or stale write has no partial effect.")

Every write goes through here under `flags.kt_bop_command`; each command runs
once per key under the case's row lock, and its own writes, including the
Proceedings writes it makes, commit together or not at all."""

from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from typing import Any, Callable
from uuid import uuid4

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.bid_opening.services import clock
from kentender_procurement.bid_opening.services.errors import BidOpeningError, fail

CASE = "Bid Opening Case"
JOURNAL = "Opening Command Journal"
TERMINAL = ("Not held", "Cancelled after start", "Opening complete")
STARTED = ("Opening", "Interrupted", "Readout complete", "Awaiting attestations", "Opening complete", "Cancelled after start")


def namespace() -> str:
	return cstr(frappe.flags.get("kt_bop_fixture_namespace") or "")


def insert(doc) -> Any:
	if doc.meta.has_field("fixture_namespace") and not doc.get("fixture_namespace"):
		doc.fixture_namespace = namespace()
	doc.flags.kt_bop_command = True
	doc.insert(ignore_permissions=True)
	return doc


def save(doc) -> Any:
	doc.flags.kt_bop_command = True
	doc.save(ignore_permissions=True)
	return doc


def bump(doc, **values) -> Any:
	for field, value in values.items():
		doc.set(field, value)
	doc.record_version = cint(doc.record_version) + 1
	return save(doc)


def digest(value: Any) -> str:
	return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8")).hexdigest()


@contextmanager
def atomic():
	savepoint = f"bop_{uuid4().hex[:12]}"
	frappe.db.savepoint(savepoint)
	try:
		yield
	except Exception:
		frappe.db.rollback(save_point=savepoint)
		raise
	else:
		frappe.db.release_savepoint(savepoint)


def case_for(tender: str) -> str | None:
	return frappe.db.get_value(CASE, {"tender": tender}, "name")


def lock(tender: str):
	name = case_for(tender)
	if not name:
		raise frappe.DoesNotExistError("Not found")
	# The case row, locked, as last committed: a plain read after the lock would return this transaction's
	# older snapshot, and a waiter would pass `check_version` on a revision another command had already
	# replaced, then fail in `save` with a raw timestamp error (RG-18, AUD-XC-130).
	return frappe.get_doc(CASE, name, for_update=True)


def check_version(doc, expected) -> None:
	try:
		ok = expected is not None and int(expected) == cint(doc.record_version)
	except (TypeError, ValueError):
		ok = False
	if not ok:
		fail("BOP_VERSION_CONFLICT", {"record_version": cint(doc.record_version)})


def summary(doc, **extra) -> dict[str, Any]:
	return {"ok": True, "opening": doc.name, "tender": doc.tender, "state": doc.state, "record_version": cint(doc.record_version), **extra}


def command(name: str, *, tender: str, idempotency_key: str, actor: str, payload: dict[str, Any], body: Callable[[], dict[str, Any]]) -> dict[str, Any]:
	"""Run `body` once per key. A reused key with another command, actor or
	payload is a conflict. A Proceedings error is re-raised in Bid Opening's words
	(BOP-CHG-001 v0.10 §7.1 "Product vocabulary"). A result returned as data
	(`ok: False`) is not journalled, so a corrected retry runs.

	The key is claimed with a unique insert in the command's own transaction
	before `body` runs (RG-18, AUD-XC-131): a duplicate waits on that insert until
	the first request commits, then reads the winner's row with a locking read (a
	plain read would return its older snapshot) and returns the original result.
	A key is never read before it is claimed. Callers authorise before they get here."""
	from kentender_procurement.proceedings.services.errors import ProceedingsError

	from kentender_procurement.bid_opening.services import errors, prc_owner

	key = cstr(idempotency_key).strip()
	if not key:
		fail("BOP_VERSION_CONFLICT", {"reason": "idempotency_key_required"})
	payload_hash = digest({"command": name, "tender": tender, "actor": actor, **payload})
	case = case_for(tender)
	try:
		with atomic():
			if not _claim(key, name, payload_hash, actor, case):
				return _recorded(key, name, payload_hash)
			with prc_owner.acting(case):
				result = body()
			if result.get("ok") is False:
				frappe.db.delete(JOURNAL, {"idempotency_key": key})
			else:
				frappe.db.set_value(JOURNAL, {"idempotency_key": key}, {"result_json": json.dumps(result, default=str), "opening_case": cstr(result.get("opening") or case)}, update_modified=False)
	except ProceedingsError as exc:
		code, message = errors.from_prc(exc.code)
		raise BidOpeningError(code, message, {"proceedings": exc.code, **exc.detail}) from exc
	return result


def _claim(key: str, name: str, payload_hash: str, actor: str, case: str | None) -> bool:
	"""Insert the key's journal row; False when a committed row holds it."""
	savepoint = f"bopj_{uuid4().hex[:12]}"
	frappe.db.savepoint(savepoint)
	try:
		insert(frappe.get_doc({
			"doctype": JOURNAL, "idempotency_key": key, "command": name, "payload_hash": payload_hash, "result_json": "",
			"actor": actor if actor and frappe.db.exists("User", actor) else None, "opening_case": cstr(case), "recorded_at": clock.now(),
		}))
	except (frappe.UniqueValidationError, frappe.DuplicateEntryError):
		frappe.db.rollback(save_point=savepoint)
		frappe.clear_last_message()
		return False
	frappe.db.release_savepoint(savepoint)
	return True


def _recorded(key: str, name: str, payload_hash: str) -> dict[str, Any]:
	"""The original result of a key that is already claimed; the same key for another command or payload is a conflict."""
	row = frappe.db.get_value(JOURNAL, {"idempotency_key": key}, ["command", "payload_hash", "result_json"], as_dict=True, for_update=True)
	if not row or row.command != name or row.payload_hash != payload_hash or not row.result_json:
		fail("BOP_VERSION_CONFLICT", {"reason": "idempotency_key_reused"})
	return json.loads(row.result_json)
