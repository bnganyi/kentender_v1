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
	rows = frappe.get_all(doctype, filters=filters, pluck=field)
	return (max(cint(r) for r in rows) if rows else 0) + 1


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
	if not case or not frappe.db.exists(CASE, case):
		raise frappe.DoesNotExistError("Not found")
	frappe.db.sql("select name from `tabAward Case` where name=%s for update", case)
	return frappe.get_doc(CASE, case)


def check_version(doc, expected) -> None:
	try:
		ok = expected is not None and str(expected).strip() != "" and int(expected) == cint(doc.record_version)
	except (TypeError, ValueError):
		ok = False
	if not ok:
		fail("AWD_RECORD_CHANGED", {"record_version": cint(doc.record_version)})


def summary(doc, **extra) -> dict[str, Any]:
	return {"ok": True, "award": doc.name, "tender_reference": doc.tender_reference, "stage": doc.stage, "record_version": cint(doc.record_version), **extra}


def command(name: str, *, case: str, idempotency_key: str, actor: str, payload: dict[str, Any], body: Callable[[], dict[str, Any]]) -> dict[str, Any]:
	"""Run `body` once per key. A reused key with another payload is a
	conflict. A result returned as data (`ok: False`) is not journalled, so a
	corrected retry runs."""
	key = cstr(idempotency_key).strip()
	if not key:
		fail("AWD_RECORD_CHANGED", {"reason": "idempotency_key_required"})
	payload_hash = digest({"command": name, "case": case, "actor": actor, **payload})
	row = frappe.db.get_value(JOURNAL, {"idempotency_key": key}, ["command", "payload_hash", "result_json"], as_dict=True)
	if row:
		if row.command != name or row.payload_hash != payload_hash:
			fail("AWD_RECORD_CHANGED", {"reason": "idempotency_key_reused"})
		return json.loads(row.result_json or "{}")
	with atomic():
		result = body()
		if result.get("ok") is not False:
			insert(frappe.get_doc({
				"doctype": JOURNAL, "idempotency_key": key, "command": name, "payload_hash": payload_hash, "result_json": dumps(result),
				"actor": actor if actor and frappe.db.exists("User", actor) else None, "award_case": cstr(result.get("award") or case),
				"recorded_at": clock.now(),
			}))
	return result


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
