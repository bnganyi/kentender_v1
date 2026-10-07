# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Writing Bid Evaluation records (EVL-CHG-001 v0.4 §7.2: "Every write records
actor, exact object/version, trusted time, reason where stated and an
idempotency key. Replays return the original result; stale or conflicting
requests have no partial effect.")

Every write goes through here under `flags.kt_evl_command`; each command runs
once per key under the case's row lock, and its own writes, including the
Proceedings writes it makes, commit together or not at all (plan D3)."""

from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from typing import Any, Callable
from uuid import uuid4

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.bid_evaluation.services import clock
from kentender_procurement.bid_evaluation.services.errors import EvaluationError, fail

CASE = "Evaluation Case"
JOURNAL = "Evaluation Command Journal"
TERMINAL = ("No evaluation required", "Cancelled")


def namespace() -> str:
	return cstr(frappe.flags.get("kt_evl_fixture_namespace") or "")


def insert(doc) -> Any:
	if doc.meta.has_field("fixture_namespace") and not doc.get("fixture_namespace"):
		doc.fixture_namespace = namespace()
	doc.flags.kt_evl_command = True
	doc.insert(ignore_permissions=True)
	return doc


def save(doc) -> Any:
	doc.flags.kt_evl_command = True
	doc.save(ignore_permissions=True)
	return doc


def bump(doc, **values) -> Any:
	for field, value in values.items():
		doc.set(field, value)
	doc.record_version = cint(doc.record_version) + 1
	return save(doc)


def digest(value: Any) -> str:
	return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8")).hexdigest()


def next_id(doctype: str, field: str, prefix: str, width: int = 2) -> str:
	"""`prefix-NN`, the next free number for this prefix."""
	taken = frappe.get_all(doctype, filters={field: ("like", f"{prefix}-%")}, pluck=field)
	numbers = [cint(n.rsplit("-", 1)[-1]) for n in taken if n.rsplit("-", 1)[-1].isdigit()]
	return f"{prefix}-{(max(numbers) if numbers else 0) + 1:0{width}d}"


@contextmanager
def atomic():
	savepoint = f"evl_{uuid4().hex[:12]}"
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
	"""The case row, locked, as last committed. MariaDB runs at REPEATABLE READ,
	so a plain read after the lock would return the transaction's snapshot and
	a waiter would pass `check_version` on a revision another command had
	already replaced (AUD-XC-130); the locking read sees the committed row."""
	name = case_for(tender)
	if not name:
		raise frappe.DoesNotExistError("Not found")
	return frappe.get_doc(CASE, name, for_update=True)


def check_version(doc, expected) -> None:
	try:
		ok = expected is not None and int(expected) == cint(doc.record_version)
	except (TypeError, ValueError):
		ok = False
	if not ok:
		fail("EVL_VERSION_CONFLICT", {"record_version": cint(doc.record_version)})


def summary(doc, **extra) -> dict[str, Any]:
	return {"ok": True, "evaluation": doc.name, "tender": doc.tender, "state": doc.state, "record_version": cint(doc.record_version), **extra}


def standing(case: str | None, actor: str) -> list[str]:
	"""What the actor holds now: their active responsibilities and, in this
	case, their committee capacities. A replay is answered only to an actor who
	still holds everything they held when the command first ran (AUD-XC-131),
	so a member removed since, or one whose responsibility has ended, is not
	handed a recorded result. The system acts with no standing."""
	from kentender_procurement.bid_evaluation.services import people, roster

	if not actor or actor == "system":
		return []
	held = [f"responsibility:{r}" for r in people.active_responsibilities(actor)]
	if case:
		if actor in roster.member_users(case):
			held.append("member")
		if roster.chair(case) == actor:
			held.append("chair")
		if roster.secretary(case) == actor:
			held.append("secretary")
	return sorted(held)


def command(name: str, *, tender: str, idempotency_key: str, actor: str, payload: dict[str, Any], body: Callable[[], dict[str, Any]]) -> dict[str, Any]:
	"""Run `body` once per key. A reused key with another command, actor or
	payload is a conflict. A Proceedings error is re-raised in Evaluation's
	words. A result returned as data (`ok: False`) is not journalled, so a
	corrected retry runs.

	Order (AUD-XC-131, AUD-XC-130): the case is locked first, so two requests
	for one case run one after the other; the key is then claimed with a unique
	insert in the command's own transaction, so a duplicate waits on it until
	the first request commits and reads the winner's row with a locking read (a
	plain read would return its older snapshot). A replay is returned only to
	an actor who still holds the standing recorded with it. A key is never read
	before it is claimed."""
	from kentender_procurement.proceedings.services.errors import ProceedingsError

	from kentender_procurement.bid_evaluation.services import errors, prc_owner

	key = cstr(idempotency_key).strip()
	if not key:
		fail("EVL_VERSION_CONFLICT", {"reason": "idempotency_key_required"})
	payload_hash = digest({"command": name, "tender": tender, "actor": actor, **payload})
	case = case_for(tender) if tender else None
	if case:
		lock(tender)
	try:
		with atomic(), prc_owner.acting(case):
			if not _claim(key, name, payload_hash, actor, case):
				return _recorded(key, name, payload_hash, case, actor)
			result = body()
			if result.get("ok") is False:
				frappe.db.delete(JOURNAL, {"idempotency_key": key})
			else:
				frappe.db.set_value(JOURNAL, {"idempotency_key": key}, {"result_json": json.dumps(result, default=str),
					"evaluation_case": cstr(result.get("evaluation") or case)}, update_modified=False)
	except ProceedingsError as exc:
		code = errors.from_prc(exc.code, exc.detail)
		raise EvaluationError(code, errors.MESSAGES[code], {"proceedings": exc.code, **exc.detail}) from exc
	return result


def _claim(key: str, name: str, payload_hash: str, actor: str, case: str | None) -> bool:
	"""Insert the key's journal row; False when a committed row holds it."""
	savepoint = f"evl_{uuid4().hex[:12]}"
	frappe.db.savepoint(savepoint)
	try:
		insert(frappe.get_doc({
			"doctype": JOURNAL, "idempotency_key": key, "command": name, "payload_hash": payload_hash, "result_json": "",
			"actor": actor if actor and frappe.db.exists("User", actor) else None, "evaluation_case": cstr(case),
			"standing": json.dumps(standing(case, actor)), "recorded_at": clock.now(),
		}))
	except (frappe.UniqueValidationError, frappe.DuplicateEntryError):
		frappe.db.rollback(save_point=savepoint)
		frappe.clear_last_message()
		return False
	frappe.db.release_savepoint(savepoint)
	return True


def _recorded(key: str, name: str, payload_hash: str, case: str | None, actor: str) -> dict[str, Any]:
	"""The original result of a key that is already claimed: refused to an actor
	who no longer holds the standing it was recorded with, a conflict for
	another command or payload."""
	row = frappe.db.get_value(JOURNAL, {"idempotency_key": key}, ["command", "payload_hash", "result_json", "standing"], as_dict=True, for_update=True)
	if not row or row.command != name or row.payload_hash != payload_hash or not row.result_json:
		fail("EVL_VERSION_CONFLICT", {"reason": "idempotency_key_reused"})
	if not set(json.loads(row.standing or "[]")) <= set(standing(case, actor)):
		raise frappe.DoesNotExistError("Not found")
	return json.loads(row.result_json)
