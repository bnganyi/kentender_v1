# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Durable operation intents (CM-CHG-001 v0.8 §5.17, §7 last paragraph, §12; plan D5).

Every cross-owner or uncertain effect (a native order, receipt, invoice or payment; a funding operation; a signing attempt; a
dispatch) is one `Contract Operation Intent` with one **operation identity**: case | subject | version | kind | key. A command
records the decision and a `Recorded` intent atomically; the effect itself is executed afterwards, in its own transactions, so
the `Attempting` state is committed *before* the owner is called (spike S7: a hard crash after the owner committed and before
the link was written was recovered this way).

The order is fixed and proved by the spike: read the owner first by identity; if the document exists, link it and stop;
only then create it. An unexpected failure leaves the outcome **Uncertain**; only the owner's explicit refusal
(`OwnerRefused`) is **Failed**. One native document belongs to one operation (`Contract Transaction Link`), so a retry cannot
post twice. Native records stay authoritative: the link is provenance, never a second ledger."""

from __future__ import annotations

from typing import Any, Callable

import frappe
from frappe.utils import add_to_date, cstr, get_datetime, now_datetime

from kentender_contracts.services import clock, records
from kentender_contracts.services.errors import fail, invalid

INTENT = "Contract Operation Intent"
LINK = "Contract Transaction Link"
SETTLED = ("Succeeded", "Reconciled")
PENDING = ("Recorded", "Attempting", "Failed", "Uncertain")
#: How long an `Attempting` intent belongs to the worker that committed it; after it a retry reads the owner first and carries on.
LEASE_SECONDS = 120
#: The owner's record type for a kind, used when an executor returns only a name.
OWNER_RECORD = {
	"Purchase order": "Purchase Order", "Accepted receipt": "Purchase Receipt", "Native invoice": "Purchase Invoice", "Native payment": "Payment Entry",
	"Funding conversion": "Procurement Commitment", "Funding adjustment": "Procurement Commitment", "Funding closure": "Procurement Commitment",
	"Signing attempt": "Signature proof", "Report dispatch": "Report delivery", "Notice dispatch": "Notice delivery",
}


class OwnerRefused(Exception):
	"""The owning module definitively refused the operation: nothing was created, and a corrected retry may run."""


def identity(case: str, subject: str, version: int, kind: str, key: str) -> str:
	return f"{case}|{subject}|{version}|{kind}|{key}"


def kinds() -> set[str]:
	return set(filter(None, (frappe.get_meta(INTENT).get_field("operation_kind").options or "").split("\n")))


def record(case: str, subject: str, version: int, kind: str, key: str, *, recovery_owner: str) -> Any:
	"""Record (or find) the intent for one operation. Idempotent on the operation identity."""
	if kind not in kinds():
		invalid({"operation_kind": f"{kind or 'This operation'} is not a recognised kind of operation."})
	ident = identity(case, subject, version, kind, key)
	existing = frappe.db.get_value(INTENT, {"operation_identity": ident}, "name")
	if existing:
		return frappe.get_doc(INTENT, existing)
	savepoint = f"cm_intent_{abs(hash(ident))}"
	frappe.db.savepoint(savepoint)
	try:
		return records.new(INTENT, contract_case=case, subject=subject, subject_version=version, operation_kind=kind, operation_key=key, operation_identity=ident,
			state="Recorded", recovery_owner=recovery_owner)
	except (frappe.UniqueValidationError, frappe.DuplicateEntryError):
		frappe.db.rollback(save_point=savepoint)
		frappe.clear_last_message()
		return frappe.get_doc(INTENT, frappe.db.get_value(INTENT, {"operation_identity": ident}, "name"))


def _result(doc, detail: str = "") -> dict[str, Any]:
	return {"intent": doc.name, "state": doc.state, "reference": cstr(doc.result_reference), "detail": detail}


def _lease_held(doc) -> bool:
	return doc.state == "Attempting" and get_datetime(doc.modified) > add_to_date(now_datetime(), seconds=-LEASE_SECONDS)


def _settle(name: str, state: str, reference: str = "", native_doctype: str = "", detail: str = "") -> dict[str, Any]:
	"""Write the outcome (and the link) in one transaction, then commit it."""
	doc = frappe.get_doc(INTENT, name, for_update=True)
	duplicate = False
	if reference and state in SETTLED:
		conflict = _link(doc, native_doctype or OWNER_RECORD.get(doc.operation_kind, "Owner record"), reference)
		if conflict:
			state, detail, reference, duplicate = "Failed", conflict, "", True
	entry = {"at": str(clock.now()), "outcome": state}
	if detail:
		entry["detail"] = detail[:400]
	records.append_json(doc, "attempts_json", entry)
	doc.state = state
	if reference:
		doc.result_reference = reference
	records.save(doc)
	frappe.db.commit()
	if duplicate:
		fail("CM_DUPLICATE", intent=name, conflict=detail)
	return _result(doc, detail)


def _link(doc, native_doctype: str, native_name: str, native_row: str = "") -> str:
	"""Link the operation to its native document. Returns a refusal text if that document already belongs to another operation."""
	key = f"{native_doctype}|{native_name}|{native_row}"
	holder = frappe.db.get_value(LINK, {"native_key": key}, "operation_identity")
	if holder and holder != doc.operation_identity:
		return f"{native_doctype} {native_name} is already linked to another operation."
	if frappe.db.exists(LINK, {"operation_identity": doc.operation_identity}):
		return ""
	records.new(LINK, contract_case=doc.contract_case, operation_identity=doc.operation_identity, native_doctype=native_doctype, native_name=native_name, native_row=native_row,
		native_key=key, native_modified=frappe.db.get_value(native_doctype, native_name, "modified") if frappe.db.exists("DocType", native_doctype) and frappe.db.exists(native_doctype, native_name) else None,
		native_status=cstr(frappe.db.get_value(native_doctype, native_name, "docstatus")) if frappe.db.exists("DocType", native_doctype) and frappe.db.exists(native_doctype, native_name) else "", linked_at=clock.now())
	return ""


def execute(name: str, executor: Callable[[str], Any], lookup: Callable[[str], str | None], *, native_doctype: str = "") -> dict[str, Any]:
	"""Carry one intent through the owner. `lookup(identity)` returns the owner's document name if one exists for the identity;
	`executor(identity)` creates it and returns `(name, owner_record_type)` or just the name. Runs its own transactions."""
	doc = frappe.get_doc(INTENT, name, for_update=True)
	if doc.state in SETTLED:
		return _result(doc)
	if _lease_held(doc):
		frappe.db.commit()
		return _result(doc, "Another worker is carrying out this operation.")
	doc.state = "Attempting"
	records.save(doc)
	frappe.db.commit()  # committed BEFORE the owner is called
	ident = doc.operation_identity
	existing = lookup(ident)
	if existing:
		return _settle(name, "Reconciled", cstr(existing), native_doctype)
	try:
		created = executor(ident)
	except OwnerRefused as exc:
		frappe.db.rollback()
		return _settle(name, "Failed", detail=str(exc) or "The owning module refused the operation.")
	except Exception as exc:  # noqa: BLE001 - an unexpected failure means the outcome is unknown, not that nothing happened
		frappe.db.rollback()
		frappe.log_error(title=f"Contract operation {ident} outcome uncertain")
		return _settle(name, "Uncertain", detail=f"{type(exc).__name__}: {str(exc)[:300]}")
	reference, doctype = (created if isinstance(created, tuple) else (created, native_doctype))
	return _settle(name, "Succeeded", cstr(reference), cstr(doctype))


def reconcile(name: str, lookup: Callable[[str], str | None], *, native_doctype: str = "") -> dict[str, Any]:
	"""Technical recovery: read the owner by identity and link what exists. Never creates anything and never retries an effect."""
	doc = frappe.get_doc(INTENT, name, for_update=True)
	if doc.state in SETTLED:
		return _result(doc)
	existing = lookup(doc.operation_identity)
	if not existing:
		frappe.db.commit()
		return _result(doc, "The owner holds nothing for this operation.")
	return _settle(name, "Reconciled", cstr(existing), native_doctype)


def pending(case: str) -> list[dict[str, Any]]:
	"""The case's operations that have not completed: what the truthful state and the holds are read from (§5.17)."""
	rows = frappe.get_all(INTENT, filters={"contract_case": case, "state": ["in", list(PENDING)]}, fields=["name", "operation_kind", "state", "subject", "subject_version", "recovery_owner", "operation_identity"],
		order_by="creation asc")
	return [{"intent": r.name, "kind": r.operation_kind, "state": r.state, "subject": r.subject, "version": r.subject_version, "recovery_owner": r.recovery_owner, "identity": r.operation_identity} for r in rows]
