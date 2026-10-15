# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Writing Contract Management records (CM-CHG-001 v0.8 §7: "Common envelope: subject identity, expected revision, stable
operation key, actor/service authority and only the business inputs below. ... Retrying the same key with different content
fails; an identical retry returns the original result. Stale versions return a conflict without losing unsaved user text.")

Every write goes through here under core's command-write window for the family `Contract Management` (plan D3); each command
runs once per key under the case's row lock, and its writes commit together or not at all (plan D4)."""

from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from typing import Any, Callable
from uuid import uuid4

import frappe
from frappe.utils import cint, cstr

from kentender_contracts.services import clock
from kentender_contracts.services.errors import fail
from kentender_core.services.command_write_guard import command_write
from kentender_core.utils.series import allocation_lock

FAMILY = "Contract Management"
CASE = "Contract Case"
JOURNAL = "Contract Command Journal"
#: Every record of the module a fixture wipe must reach; a phase that adds a record adds it here.
DOCTYPES = (
	"Contract Case", "Contract Operation Intent", "Contract Transaction Link", "Contract Simulated Signature", "Contract Command Journal",
	"Contract Agreement Version", "Contract Source Package", "Contract Signature", "Contract Appointment", "Contract Arrival", "Contract Inspection",
	"Contract Certificate", "Contract Acceptance", "Contract Invoice", "Contract Certification", "Contract Settlement", "Contract Closeout",
	"Contract Task", "Contract Event", "Contract Simulated Funding", "Contract Security", "Contract Award Inbox",
)


def namespace() -> str:
	return cstr(frappe.flags.get("kt_cm_fixture_namespace") or "")


def insert(doc) -> Any:
	if doc.meta.has_field("fixture_namespace") and not doc.get("fixture_namespace"):
		doc.fixture_namespace = namespace()
	with command_write(FAMILY):
		doc.insert(ignore_permissions=True)
	return doc


def new(doctype: str, **values) -> Any:
	return insert(frappe.get_doc({"doctype": doctype, **values}))


def save(doc) -> Any:
	with command_write(FAMILY):
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


def short(value: str) -> str:
	"""A short stable token for a long identity part (a person's address inside an operation key); the full value is kept on the record it belongs to."""
	return hashlib.sha1(str(value).lower().encode("utf-8")).hexdigest()[:8]


def loads(value, default=None):
	if not value:
		return default if default is not None else {}
	return json.loads(value) if isinstance(value, str) else value


def dumps(value) -> str:
	return json.dumps(value, default=str, sort_keys=True, ensure_ascii=False)


def next_number(doctype: str, filters: dict, field: str = "version") -> int:
	"""The highest `field` among the matching rows, plus one, as of the latest committed state.

	MariaDB runs at REPEATABLE READ: a plain read taken after waiting for the case lock would answer from the transaction's older
	snapshot, so two commands would take the same number. A locking read sees what the waited-for command committed (RG-19)."""
	allocation_lock(doctype)
	values = frappe.db.get_values(doctype, filters, field, pluck=field, for_update=True) or []
	return (max((cint(v) for v in values), default=0)) + 1


@contextmanager
def atomic():
	savepoint = f"cm_{uuid4().hex[:12]}"
	frappe.db.savepoint(savepoint)
	try:
		yield
	except Exception:
		frappe.db.rollback(save_point=savepoint)
		raise
	else:
		frappe.db.release_savepoint(savepoint)


def lock(case: str):
	"""The case row, locked, as last committed (a plain read after the lock would return the transaction's snapshot, so a waiter
	would pass `check_version` on a revision another command had already replaced)."""
	if not case or not frappe.db.exists(CASE, case):
		raise frappe.DoesNotExistError("Not found")
	return frappe.get_doc(CASE, case, for_update=True)


def check_version(doc, expected) -> None:
	try:
		ok = expected is not None and str(expected).strip() != "" and int(expected) == cint(doc.record_version)
	except (TypeError, ValueError):
		ok = False
	if not ok:
		fail("CM_CHANGED", {"record_version": cint(doc.record_version)})


def summary(doc, **extra) -> dict[str, Any]:
	return {"ok": True, "contract": doc.name, "lifecycle": doc.lifecycle, "record_version": cint(doc.record_version), **extra}


def command(name: str, *, case: str, idempotency_key: str, actor: str, payload: dict[str, Any], body: Callable[[], dict[str, Any]],
		authorise: Callable[[], None] | None = None) -> dict[str, Any]:
	"""Run `body` once per key. A reused key with another command, actor or payload is a conflict. A result returned as data
	(`ok: False`) is not journalled, so a corrected retry runs.

	Order: `authorise` first, so a recorded result is never answered to someone who may not act; then the case lock, so two
	requests for one case run one after the other; then the key is claimed with a unique insert in the command's own
	transaction. A duplicate waits on that insert until the first request commits, then reads the winner's row with a locking
	read and returns the original result. A key is never read before it is claimed."""
	key = cstr(idempotency_key).strip()
	if not key:
		fail("CM_CHANGED", {"reason": "idempotency_key_required"})
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
			frappe.db.set_value(JOURNAL, {"idempotency_key": key}, {"result_json": dumps(result), "contract_case": cstr(result.get("contract") or case)}, update_modified=False)
	return result


def _claim(key: str, name: str, payload_hash: str, actor: str, case: str) -> bool:
	"""Insert the key's journal row; False when a committed row holds it."""
	savepoint = f"cm_{uuid4().hex[:12]}"
	frappe.db.savepoint(savepoint)
	try:
		insert(frappe.get_doc({
			"doctype": JOURNAL, "idempotency_key": key, "command": name, "payload_hash": payload_hash, "result_json": "",
			"actor": actor if actor and frappe.db.exists("User", actor) else None, "contract_case": cstr(case), "recorded_at": clock.now(),
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
		fail("CM_CHANGED", {"reason": "idempotency_key_reused"})
	return json.loads(row.result_json)


def append_json(doc, field: str, entry: dict[str, Any]) -> list:
	rows = loads(doc.get(field), [])
	rows.append(entry)
	doc.set(field, dumps(rows))
	return rows


def audit(case: str, action: str, actor: str, **metadata) -> None:
	"""§12: actor or service, command identity, trusted time and outcome, kept in the shared audit log as well as the Contract
	Management records themselves."""
	from kentender_core.services.audit_event_service import log_audit_event

	try:
		log_audit_event(event_type=f"Contract {action}", entity="Contract Management", document_type=CASE, document_name=cstr(case), action=action,
			performed_by=actor or frappe.session.user, metadata={"at": str(clock.now()), **metadata})
	except Exception:
		frappe.log_error(title="Contract Management audit write failed")


def wipe(namespace_value: str) -> int:
	"""Delete every Contract Management row of one fixture namespace (tests and browser worlds).

	A direct delete: `delete_doc` would enqueue a dynamic-link job per row, and this bench runs no worker by default."""
	if not namespace_value:
		raise ValueError("a fixture wipe needs a namespace")
	count = 0
	for doctype in DOCTYPES:
		count += frappe.db.count(doctype, {"fixture_namespace": namespace_value})
		frappe.db.delete(doctype, {"fixture_namespace": namespace_value})
	return count
