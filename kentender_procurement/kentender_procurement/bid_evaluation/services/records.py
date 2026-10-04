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
	name = case_for(tender)
	if not name:
		raise frappe.DoesNotExistError("Not found")
	frappe.db.sql("select name from `tabEvaluation Case` where name=%s for update", name)
	return frappe.get_doc(CASE, name)


def check_version(doc, expected) -> None:
	try:
		ok = expected is not None and int(expected) == cint(doc.record_version)
	except (TypeError, ValueError):
		ok = False
	if not ok:
		fail("EVL_VERSION_CONFLICT", {"record_version": cint(doc.record_version)})


def summary(doc, **extra) -> dict[str, Any]:
	return {"ok": True, "evaluation": doc.name, "tender": doc.tender, "state": doc.state, "record_version": cint(doc.record_version), **extra}


def command(name: str, *, tender: str, idempotency_key: str, actor: str, payload: dict[str, Any], body: Callable[[], dict[str, Any]]) -> dict[str, Any]:
	"""Run `body` once per key. A reused key with another payload is a
	conflict. A Proceedings error is re-raised in Evaluation's words. A result
	returned as data (`ok: False`) is not journalled, so a corrected retry runs."""
	from kentender_procurement.proceedings.services.errors import ProceedingsError

	from kentender_procurement.bid_evaluation.services import errors, prc_owner

	key = cstr(idempotency_key).strip()
	if not key:
		fail("EVL_VERSION_CONFLICT", {"reason": "idempotency_key_required"})
	payload_hash = digest({"command": name, "tender": tender, "actor": actor, **payload})
	row = frappe.db.get_value(JOURNAL, {"idempotency_key": key}, ["command", "payload_hash", "result_json"], as_dict=True)
	if row:
		if row.command != name or row.payload_hash != payload_hash:
			fail("EVL_VERSION_CONFLICT", {"reason": "idempotency_key_reused"})
		return json.loads(row.result_json or "{}")
	case = case_for(tender) if tender else None
	try:
		with atomic(), prc_owner.acting(case):
			result = body()
			if result.get("ok") is not False:
				insert(frappe.get_doc({
					"doctype": JOURNAL, "idempotency_key": key, "command": name, "payload_hash": payload_hash, "result_json": json.dumps(result, default=str),
					"actor": actor if actor and frappe.db.exists("User", actor) else None, "evaluation_case": cstr(result.get("evaluation") or case),
					"recorded_at": clock.now(),
				}))
	except ProceedingsError as exc:
		code = errors.from_prc(exc.code, exc.detail)
		raise EvaluationError(code, errors.MESSAGES[code], {"proceedings": exc.code, **exc.detail}) from exc
	return result
