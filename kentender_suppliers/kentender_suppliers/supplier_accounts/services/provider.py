# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Supplier Accounts' `kt_supplier_account_provider` (kentender_core
supplier_account_contract; BDS-CHG-001 v0.8 plan D1). Bid Submission reads
Account identity and access facts only through these functions. An
assignment's `signatory_ready` says whether it can sign now (active window
and Available authority evidence). `find_active_account` answers a
joint-venture member lookup with the legal name only (§4.3)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_suppliers.supplier_accounts.services import authorization as authz

ORGANISATION = "Supplier Organisation"
EVIDENCE = "Supplier Account Evidence"


def _assignment(row, at=None) -> dict[str, Any]:
	return {
		"assignment_id": row["name"], "organisation_id": row["organisation"], "user": row["user"], "responsibility": row["responsibility"],
		"job_title": cstr(row.get("job_title")), "effective_from": cstr(row["effective_from"]), "effective_to": cstr(row.get("effective_to") or ""),
		"authority_evidence_id": cstr(row.get("authority_evidence") or ""), "active": authz.is_active(row, at), "signatory_ready": authz.is_active_signatory(row, at),
	}


def active_assignments(*, user: str, at=None) -> list[dict[str, Any]]:
	if not user or authz.is_internal_user(user):
		return []
	return [_assignment(r, at) for r in authz.assignments_of(user, at=at)]


def assignment(*, assignment_id: str, at=None) -> dict[str, Any] | None:
	row = frappe.db.get_value(authz.ASSIGNMENT, assignment_id, ["name", "organisation", "user", "responsibility", "job_title", "effective_from", "effective_to", "authority_evidence"], as_dict=True)
	return _assignment(row, at) if row else None


def organisation_signatories(*, organisation_id: str, at=None) -> list[dict[str, Any]]:
	"""The organisation's Authorised Signatories who can sign now (for the
	bid's "waiting for …" line; BDS-CHG-001 v0.8 §5.12)."""
	rows = frappe.get_all(
		authz.ASSIGNMENT, filters={"organisation": organisation_id, "responsibility": "Authorised Signatory"},
		fields=["name", "organisation", "user", "responsibility", "job_title", "effective_from", "effective_to", "authority_evidence"], order_by="effective_from asc, creation asc",
	)
	return [a for a in (_assignment(r, at) for r in rows) if a["signatory_ready"]]


def organisation(*, organisation_id: str) -> dict[str, Any] | None:
	if not organisation_id or not frappe.db.exists(ORGANISATION, organisation_id):
		return None
	org = frappe.get_doc(ORGANISATION, organisation_id)
	return {
		"organisation_id": org.name, "legal_name": org.legal_name, "country": org.country, "registration_number": org.registration_number,
		"tax_identifier": cstr(org.tax_identifier), "registered_address": org.registered_address, "official_email": org.official_email,
		"official_phone": cstr(org.official_phone), "account_status": org.account_status, "record_version": int(org.record_version or 0),
	}


def verified_contacts(*, organisation_id: str) -> list[dict[str, Any]]:
	if not organisation_id or not frappe.db.exists(ORGANISATION, organisation_id):
		return []
	org = frappe.get_doc(ORGANISATION, organisation_id)
	return [
		{"contact_id": r.name, "channel": r.channel, "value": cstr(r.value), "contact_version": int(r.contact_version or 1), "is_official": bool(r.is_official)}
		for r in org.contacts if r.channel == "Email" and r.verification_status == "Verified"
	]


def account_evidence(*, organisation_id: str) -> list[dict[str, Any]]:
	rows = frappe.get_all(EVIDENCE, filters={"organisation": organisation_id}, fields=["name", "evidence_type", "title", "reference", "valid_until", "status", "file_name", "file_digest"], order_by="uploaded_at asc, creation asc", limit_page_length=0)
	return [
		{"evidence_id": r.name, "evidence_type": r.evidence_type, "title": cstr(r.title), "reference": cstr(r.reference), "valid_until": cstr(r.valid_until or ""), "status": r.status, "file_name": cstr(r.file_name), "file_digest": cstr(r.file_digest)}
		for r in rows
	]


def evidence_file(*, organisation_id: str, evidence_id: str) -> dict[str, Any] | None:
	row = frappe.db.get_value(EVIDENCE, evidence_id, ["organisation", "file", "file_name", "file_digest", "status"], as_dict=True)
	if not row or row.organisation != organisation_id or not row.file or row.status != "Available":
		return None
	from kentender_core.services.file_integrity import read_bytes

	return {"file_name": cstr(row.file_name), "content": read_bytes(row.file), "digest": cstr(row.file_digest)}


def find_active_account(*, country: str, registration_number: str) -> dict[str, Any] | None:
	name = frappe.db.get_value(ORGANISATION, {"country": cstr(country).strip(), "registration_number": cstr(registration_number).strip(), "account_status": "Active"}, "name")
	return {"organisation_id": name, "legal_name": cstr(frappe.db.get_value(ORGANISATION, name, "legal_name"))} if name else None
