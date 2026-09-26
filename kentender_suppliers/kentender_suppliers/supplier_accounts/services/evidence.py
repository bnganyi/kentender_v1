# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Reusable Account evidence (BDS-CHG-001 v0.8 §4.7, §11.3 "Add evidence" /
"View evidence"). Uploading creates Account evidence only — never bid
evidence until a bid explicitly links an exact copy (§10.5 item 4). Facts on
it are supplier-provided; nothing here claims external verification
(BDS01-IMP-011)."""

from __future__ import annotations

import hashlib
from typing import Any

import frappe
from frappe.utils import cstr, getdate

from kentender_suppliers.supplier_accounts.services import audit, authz_state, clock, files, records
from kentender_suppliers.supplier_accounts.services import authorization as authz
from kentender_suppliers.supplier_accounts.services.errors import field_errors, not_found

DOCTYPE = "Supplier Account Evidence"
TYPES = ("Certificate of incorporation", "Tax compliance certificate", "Reservation evidence", "Signatory authority", "Joint-venture agreement", "Other")


def create_record(*, organisation: str, evidence_type: str, filename: str, content: bytes, actor: str, reference: str = "", valid_until=None, title: str = "", namespace: str = "") -> tuple[Any, str]:
	"""Check and store one file as Account evidence: `(doc, "")` or `(None, reason)`."""
	checked = files.check(content, filename)
	if not checked["ok"]:
		return None, checked["reason"]
	doc = records.insert(frappe.get_doc({
		"doctype": DOCTYPE, "organisation": organisation, "evidence_type": evidence_type, "title": cstr(title).strip() or evidence_type,
		"reference": cstr(reference).strip(), "valid_until": getdate(valid_until) if valid_until else None, "file_name": cstr(filename).strip(),
		"file_size": checked["size"], "file_digest": checked["digest"], "check_result": checked["check_result"], "status": checked["status"],
		"uploaded_by": actor, "uploaded_at": clock.now(), "fixture_namespace": namespace,
	}))
	doc.file = files.store(attached_to=doc.name, filename=filename, content=content)
	records.save(doc)
	return doc, ""


def _valid_date(value) -> bool:
	if not value:
		return True
	try:
		getdate(value)
		return True
	except Exception:
		return False


def upload_account_evidence(*, organisation: str, evidence_type: str, filename: str, content: bytes, reference: str = "", valid_until: str = "", title: str = "", idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""`UploadAccountEvidence` (§11.3 Add evidence)."""
	principal = authz.require_signed_in(user)
	authz.require_member(organisation, principal)
	authz_state.require_not_suspended(organisation)
	payload = {"organisation": organisation, "evidence_type": evidence_type, "reference": cstr(reference), "valid_until": cstr(valid_until), "title": cstr(title), "filename": cstr(filename), "digest": hashlib.sha256(content or b"").hexdigest()}

	def _do() -> dict[str, Any]:
		errors: dict[str, str] = {}
		if evidence_type not in TYPES:
			errors["evidence_type"] = "Choose the kind of evidence."
		if len(cstr(reference).strip()) > 140:
			errors["reference"] = "Enter at most 140 characters."
		if not _valid_date(valid_until):
			errors["valid_until"] = "Enter a valid date."
		if errors:
			return field_errors(errors)
		doc, reason = create_record(organisation=organisation, evidence_type=evidence_type, filename=filename, content=content, actor=principal, reference=reference, valid_until=valid_until or None, title=title)
		if not doc:
			return {**field_errors({"file": reason}), "code": "BDS_EVIDENCE_REJECTED", "message": "This file could not be accepted."}
		audit.record(doctype=DOCTYPE, name=doc.name, action="upload_account_evidence", actor=principal, metadata={"organisation": organisation, "evidence_type": evidence_type, "status": doc.status, "file_digest": doc.file_digest})
		return {"ok": True, "organisation": organisation, "evidence": doc.name, "status": doc.status}

	return records.idempotent(idempotency_key, "UploadAccountEvidence", payload, _do, actor=principal, organisation=organisation)


def get_account_evidence_file(*, organisation: str, evidence: str, user: str | None = None) -> dict[str, Any]:
	"""`View evidence` — the exact stored file, to an assigned user only."""
	authz.require_member(organisation, user)
	row = frappe.db.get_value(DOCTYPE, evidence, ["organisation", "file", "file_name"], as_dict=True)
	if not row or row.organisation != organisation or not row.file:
		not_found()
	from frappe.utils.file_manager import get_file

	_, content = get_file(row.file)
	name = cstr(row.file_name)
	kind = name.rsplit(".", 1)[-1].lower() if "." in name else ""
	return {"file_name": name, "content_type": "application/pdf" if kind == "pdf" else ("image/png" if kind == "png" else "image/jpeg"), "content": content if isinstance(content, bytes) else cstr(content).encode("utf-8")}
