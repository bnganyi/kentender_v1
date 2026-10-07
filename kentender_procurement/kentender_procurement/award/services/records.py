# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Writing Award records (AWD-CHG-001 v0.4 §7: "All writes require a current
record revision, active authority and a retry identity. A duplicate accepted
command returns its original result. Conflicting concurrent writes return the
current record without partially changing it.")

Every write goes through here under `flags.kt_awd_command`; each command runs
once per key under the case's row lock, and its writes commit together or not
at all (plan D3)."""

from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from typing import Any, Callable
from uuid import uuid4

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.award.services import clock
from kentender_procurement.award.services.errors import fail
from kentender_procurement.services import sequence

CASE = "Award Case"
JOURNAL = "Award Command Journal"
DOCTYPES = (
	"Award Case", "Award Source Report", "Award Decision Cycle", "Award Professional Opinion", "Award Decision", "Award Decision Event",
	"Award Notice Batch", "Award Notice", "Award Supplier Response", "Award Issue", "Award Correspondence", "Award Clock",
	"Award Contracting Package", "Award Command Journal", "Award Test Contracting Inbox",
)


def namespace() -> str:
	return cstr(frappe.flags.get("kt_awd_fixture_namespace") or "")


def insert(doc) -> Any:
	if doc.meta.has_field("fixture_namespace") and not doc.get("fixture_namespace"):
		doc.fixture_namespace = namespace()
	doc.flags.kt_awd_command = True
	doc.insert(ignore_permissions=True)
	return doc


def new(doctype: str, **values) -> Any:
	return insert(frappe.get_doc({"doctype": doctype, **values}))


def save(doc) -> Any:
	doc.flags.kt_awd_command = True
	doc.save(ignore_permissions=True)
	return doc


def bump(doc, **values) -> Any:
	"""Change a case and advance its record revision."""
	for field, value in values.items():
		doc.set(field, value)
	doc.record_version = cint(doc.record_version) + 1
	return save(doc)


def update(doc, **values) -> Any:
	for field, value in values.items():
		doc.set(field, value)
	return save(doc)


def digest(value: Any) -> str:
	return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8")).hexdigest()


def loads(value, default=None):
	if not value:
		return default if default is not None else {}
	return json.loads(value) if isinstance(value, str) else value


def dumps(value) -> str:
	return json.dumps(value, default=str, sort_keys=True, ensure_ascii=False)


def next_number(doctype: str, filters: dict, field: str = "version") -> int:
	return sequence.next_after(doctype, filters, field)


@contextmanager
def atomic():
	savepoint = f"awd_{uuid4().hex[:12]}"
	frappe.db.savepoint(savepoint)
	try:
		yield
	except Exception:
		frappe.db.rollback(save_point=savepoint)
		raise
	else:
		frappe.db.release_savepoint(savepoint)


def case_id(tender_reference: str, lot: str = "") -> str:
	base = "AWD-" + cstr(tender_reference).replace("TND-", "", 1)
	return base if not lot or lot in ("1", "Lot 1") else f"{base}-{lot}"


def lock(case: str):
	"""The case row, locked, as last committed. MariaDB runs at REPEATABLE READ,
	so a plain read after the lock would return the transaction's snapshot and
	a waiter would pass `check_version` on a revision another command had
	already replaced (AUD-XC-130); the locking read sees the committed row."""
	if not case or not frappe.db.exists(CASE, case):
		raise frappe.DoesNotExistError("Not found")
	return frappe.get_doc(CASE, case, for_update=True)


def check_version(doc, expected) -> None:
	try:
		ok = expected is not None and str(expected).strip() != "" and int(expected) == cint(doc.record_version)
	except (TypeError, ValueError):
		ok = False
	if not ok:
		fail("AWD_RECORD_CHANGED", {"record_version": cint(doc.record_version)})


def summary(doc, **extra) -> dict[str, Any]:
	return {"ok": True, "award": doc.name, "tender_reference": doc.tender_reference, "stage": doc.stage, "record_version": cint(doc.record_version), **extra}


def command(name: str, *, case: str, idempotency_key: str, actor: str, payload: dict[str, Any], body: Callable[[], dict[str, Any]],
		authorise: Callable[[], None] | None = None) -> dict[str, Any]:
	"""Run `body` once per key. A reused key with another command, actor or
	payload is a conflict. A result returned as data (`ok: False`) is not
	journalled, so a corrected retry runs.

	Order (AUD-XC-131, AUD-XC-130): `authorise` first, so a recorded result is
	never answered to someone who may not act; then the case lock, so two
	requests for one case run one after the other; then the key is claimed
	with a unique insert in the command's own transaction. A duplicate waits on
	that insert until the first request commits, then reads the winner's row
	with a locking read (a plain read would return its older snapshot) and
	returns the original result. A key is never read before it is claimed."""
	key = cstr(idempotency_key).strip()
	if not key:
		fail("AWD_RECORD_CHANGED", {"reason": "idempotency_key_required"})
	if authorise:
		authorise()
	payload_hash = digest({"command": name, "case": case, "actor": actor, **payload})
	if case and frappe.db.exists(CASE, case):
		lock(case)
	with atomic():
		if not _claim(key, name, payload_hash, actor, case):
			return _recorded(key, name, payload_hash)
		result = body()
		if result.get("ok") is False:
			frappe.db.delete(JOURNAL, {"idempotency_key": key})
		else:
			frappe.db.set_value(JOURNAL, {"idempotency_key": key}, {"result_json": dumps(result), "award_case": cstr(result.get("award") or case)},
				update_modified=False)
	return result


def _claim(key: str, name: str, payload_hash: str, actor: str, case: str) -> bool:
	"""Insert the key's journal row; False when a committed row holds it."""
	savepoint = f"awd_{uuid4().hex[:12]}"
	frappe.db.savepoint(savepoint)
	try:
		insert(frappe.get_doc({
			"doctype": JOURNAL, "idempotency_key": key, "command": name, "payload_hash": payload_hash, "result_json": "",
			"actor": actor if actor and frappe.db.exists("User", actor) else None, "award_case": cstr(case), "recorded_at": clock.now(),
		}))
	except (frappe.UniqueValidationError, frappe.DuplicateEntryError):
		frappe.db.rollback(save_point=savepoint)
		frappe.clear_last_message()
		return False
	frappe.db.release_savepoint(savepoint)
	return True


def _recorded(key: str, name: str, payload_hash: str) -> dict[str, Any]:
	"""The original result of a key that is already claimed; the same key for
	another command or payload is a conflict."""
	row = frappe.db.get_value(JOURNAL, {"idempotency_key": key}, ["command", "payload_hash", "result_json"], as_dict=True, for_update=True)
	if not row or row.command != name or row.payload_hash != payload_hash or not row.result_json:
		fail("AWD_RECORD_CHANGED", {"reason": "idempotency_key_reused"})
	return json.loads(row.result_json)


def append_json(doc, field: str, entry: dict[str, Any]) -> list:
	rows = loads(doc.get(field), [])
	rows.append(entry)
	doc.set(field, dumps(rows))
	return rows


def audit(case: str, action: str, actor: str, **metadata) -> None:
	"""§12: actor/service, command identity, trusted time and outcome, kept in
	the shared audit log as well as the Award records themselves."""
	from kentender_core.services.audit_event_service import log_audit_event

	try:
		log_audit_event(event_type=f"Award {action}", entity="Award", document_type=CASE, document_name=cstr(case), action=action,
			performed_by=actor or frappe.session.user, metadata={"at": str(clock.now()), **metadata})
	except Exception:
		frappe.log_error(title="Award audit write failed")


def wipe(namespace_value: str) -> int:
	"""Delete every Award row of one fixture namespace (tests and browser worlds).

	A direct delete: `delete_doc` would enqueue a dynamic-link job per row, and
	this bench runs no worker by default (AGENTS.md §8.1)."""
	if not namespace_value:
		raise ValueError("a fixture wipe needs a namespace")
	count = 0
	for doctype in DOCTYPES:
		count += frappe.db.count(doctype, {"fixture_namespace": namespace_value})
		frappe.db.delete(doctype, {"fixture_namespace": namespace_value})
	return count
