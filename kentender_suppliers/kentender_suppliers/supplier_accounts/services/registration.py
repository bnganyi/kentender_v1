# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`RegisterSupplierOrganisation` (BDS-CHG-001 v0.8 §4.1–4.2, §5.1–5.2, §7.2,
§10.4 BDS-DES-03; BDS01-IMP-004/005, BDS01-AC-004).

A signed-in person creates — or, repeating their own registration, gets
back — one Pending verification Account: the organisation, its official
contacts (unverified), the person's Authorised Signatory assignment with the
authority evidence they upload, and a verification link to the official
email. Nothing here approves, prequalifies or qualifies the organisation,
creates a Tender-bound arrangement or opens a bid. Internal KenTender users
cannot register an Account."""

from __future__ import annotations

import hashlib
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_suppliers.supplier_accounts.services import audit, clock, evidence, facts, files, records, verification
from kentender_suppliers.supplier_accounts.services import authorization as authz
from kentender_suppliers.supplier_accounts.services.errors import fail, field_errors

ORGANISATION = "Supplier Organisation"
AUTHORITY_TEXT = "Upload the evidence of your authority to sign for the organisation."
JOB_TITLE_TEXT = "Enter your job title (up to 140 characters)."
NOT_APPROVAL = "Account setup gives your organisation access to bid preparation. It does not prequalify or approve the organisation for a Tender."


def _result(org, *, sent_to: str, idempotent: bool) -> dict[str, Any]:
	return {"ok": True, "idempotent": idempotent, "organisation": org.name, "account_status": org.account_status, "record_version": int(org.record_version or 0), "verification_sent_to": sent_to}


def register_supplier_organisation(
	*,
	legal_name: str,
	country: str,
	registration_number: str,
	registered_address: str,
	official_email: str,
	official_phone: str = "",
	tax_identifier: str = "",
	job_title: str = "",
	authority_filename: str = "",
	authority_content: bytes = b"",
	idempotency_key: str,
	user: str | None = None,
) -> dict[str, Any]:
	principal = authz.require_signed_in(user)
	if authz.is_internal_user(principal):
		fail("BDS_RESPONSIBILITY_REQUIRED", "Internal KenTender users cannot register a supplier account.")
	values = facts.normalise(locals())
	title = cstr(job_title).strip()
	payload = {**values, "job_title": title, "authority_filename": cstr(authority_filename), "authority_digest": hashlib.sha256(authority_content or b"").hexdigest()}

	def _do() -> dict[str, Any]:
		existing = facts.same_identity(values["country"], values["registration_number"]) if values["country"] and values["registration_number"] else ""
		if existing and frappe.db.get_value(ORGANISATION, existing, "registered_by") == principal:
			org = frappe.get_doc(ORGANISATION, existing)
			return _result(org, sent_to=verification.unverified_official_email(org), idempotent=True)
		errors = facts.errors_for(values)
		if existing:
			errors["registration_number"] = facts.TEXT["duplicate"]
		if not title or len(title) > 140:
			errors["job_title"] = JOB_TITLE_TEXT
		if not authority_content:
			errors["authority_evidence"] = AUTHORITY_TEXT
		if errors:
			return field_errors(errors)
		checked = files.check(authority_content, authority_filename)
		if not checked["ok"]:
			return {**field_errors({"authority_evidence": checked["reason"]}), "code": "BDS_EVIDENCE_REJECTED", "message": "This file could not be accepted."}
		now = clock.now()
		contacts = [{"channel": "Email", "value": values["official_email"], "is_official": 1, "verification_status": "Unverified", "contact_version": 1}]
		if values["official_phone"]:
			contacts.append({"channel": "Phone", "value": values["official_phone"], "is_official": 1, "verification_status": "Unverified", "contact_version": 1})
		org = records.insert(frappe.get_doc({
			"doctype": ORGANISATION, **values, "account_status": "Pending verification", "status_since": now, "contacts": contacts,
			"registered_by": principal, "registered_at": now, "record_version": 0, "fixture_namespace": records.namespace(),
		}))
		doc, _reason = evidence.create_record(organisation=org.name, evidence_type="Signatory authority", filename=authority_filename, content=authority_content, actor=principal, title="Signatory authority", namespace=org.fixture_namespace)
		assignment = records.insert(frappe.get_doc({
			"doctype": authz.ASSIGNMENT, "organisation": org.name, "user": principal, "responsibility": authz.SIGNATORY, "job_title": title,
			"authority_evidence": doc.name, "effective_from": now, "assigned_by": principal, "assigned_at": now, "fixture_namespace": org.fixture_namespace,
		}))
		sent = verification.issue(org, email=values["official_email"], actor=principal)
		audit.record(doctype=ORGANISATION, name=org.name, action="register_supplier_organisation", actor=principal, metadata={"assignment": assignment.name, "authority_evidence": doc.name, "evidence_status": doc.status, "verification_sent": sent["sent"]})
		return _result(org, sent_to=values["official_email"], idempotent=False)

	return records.idempotent(idempotency_key, "RegisterSupplierOrganisation", payload, _do, actor=principal)
