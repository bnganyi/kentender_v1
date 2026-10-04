# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`AssignSupplierRepresentative` / `AssignAuthorisedSignatory` (BDS-CHG-001
v0.8 §4.2, §6, §7.2, §11.3 "Add person"; BDS01-IMP-007/008, BDS01-AC-007/008).

Only an active Authorised Signatory assigns people ("under organisation
authority"). An assignment is immutable: person, responsibility, job title,
effective window, assigner and time. A signatory assignment needs its own
authority evidence. A person without a KenTender sign-in gets a portal
(Website) user; internal KenTender users — Desk staff, technical operators,
Administrator — can never hold a supplier responsibility."""

from __future__ import annotations

import hashlib
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime, validate_email_address

from kentender_suppliers.supplier_accounts.services import audit, authz_state, clock, evidence, files, records
from kentender_suppliers.supplier_accounts.services import authorization as authz
from kentender_suppliers.supplier_accounts.services.errors import field_errors

TEXT = {
	"email": "Enter the person's email address.",
	"full_name": "Enter the person's full name.",
	"job_title": "Enter at most 140 characters.",
	"effective_from": "Enter a valid start date and time.",
	"effective_to": "The end must be after the start.",
	"internal": "Internal KenTender users cannot hold supplier responsibilities.",
	"disabled": "This person's sign-in is disabled. Contact Supplier support.",
	"duplicate": "This person already holds this responsibility for the organisation.",
	"authority": "Upload the evidence of this person's authority to sign.",
}


def _instant(value):
	try:
		return get_datetime(value) if value else None
	except Exception:
		return False


def _person(email: str, full_name: str) -> tuple[str, str]:
	"""(user, error text) — the existing portal user, or a new one."""
	existing = frappe.db.get_value("User", email, ["name", "user_type", "enabled"], as_dict=True)
	if existing:
		if existing.name == "Administrator" or existing.user_type == "System User":
			return "", TEXT["internal"]
		if not existing.enabled:
			return "", TEXT["disabled"]
		return existing.name, ""
	first, _, last = full_name.partition(" ")
	doc = frappe.get_doc({"doctype": "User", "email": email, "first_name": first, "last_name": last, "user_type": "Website User", "send_welcome_email": 0 if frappe.flags.in_test else 1})
	doc.insert(ignore_permissions=True)
	return doc.name, ""


def assign_supplier_person(
	*,
	organisation: str,
	responsibility: str,
	email: str,
	full_name: str,
	job_title: str = "",
	effective_from=None,
	effective_to=None,
	authority_filename: str = "",
	authority_content: bytes = b"",
	idempotency_key: str,
	user: str | None = None,
) -> dict[str, Any]:
	principal = authz.require_signed_in(user)
	authz.require_signatory(organisation, principal)
	authz_state.require_not_suspended(organisation)
	if responsibility not in authz.RESPONSIBILITIES:
		raise ValueError(responsibility)
	address, name, title = cstr(email).strip().lower(), cstr(full_name).strip(), cstr(job_title).strip()
	payload = {"organisation": organisation, "responsibility": responsibility, "email": address, "full_name": name, "job_title": title, "effective_from": cstr(effective_from), "effective_to": cstr(effective_to), "authority_digest": hashlib.sha256(authority_content or b"").hexdigest()}

	def _do() -> dict[str, Any]:
		errors: dict[str, str] = {}
		if not address or not validate_email_address(address, throw=False):
			errors["email"] = TEXT["email"]
		if not 2 <= len(name) <= 140:
			errors["full_name"] = TEXT["full_name"]
		if len(title) > 140:
			errors["job_title"] = TEXT["job_title"]
		starts = _instant(effective_from) if effective_from else clock.now()
		ends = _instant(effective_to)
		if starts is False:
			errors["effective_from"] = TEXT["effective_from"]
		elif ends is False or (ends and starts and ends <= starts):
			errors["effective_to"] = TEXT["effective_to"]
		if responsibility == authz.SIGNATORY and not authority_content:
			errors["authority_evidence"] = TEXT["authority"]
		if errors:
			return field_errors(errors)
		if responsibility == authz.SIGNATORY:
			checked = files.check(authority_content, authority_filename)
			if not checked["ok"]:
				return {**field_errors({"authority_evidence": checked["reason"]}), "code": "BDS_EVIDENCE_REJECTED", "message": "This file could not be accepted."}
		person, problem = _person(address, name)
		if problem:
			return field_errors({"email": problem})
		if any(r["responsibility"] == responsibility for r in authz.assignments_of(person, organisation=organisation, at=starts)):
			return field_errors({"email": TEXT["duplicate"]})
		proof = ""
		if responsibility == authz.SIGNATORY:
			doc, _reason = evidence.create_record(organisation=organisation, evidence_type="Signatory authority", filename=authority_filename, content=authority_content, actor=principal, title=f"Signatory authority — {name}")
			proof = doc.name
		now = clock.now()
		row = records.insert(frappe.get_doc({
			"doctype": authz.ASSIGNMENT, "organisation": organisation, "user": person, "responsibility": responsibility, "job_title": title,
			"authority_evidence": proof or None, "effective_from": starts, "effective_to": ends or None, "assigned_by": principal, "assigned_at": now,
		}))
		audit.record(doctype=authz.ASSIGNMENT, name=row.name, action="assign_supplier_person", actor=principal, metadata={"organisation": organisation, "user": person, "responsibility": responsibility, "authority_evidence": proof})
		return {"ok": True, "organisation": organisation, "assignment": row.name, "user": person, "responsibility": responsibility}

	command = "AssignAuthorisedSignatory" if responsibility == authz.SIGNATORY else "AssignSupplierRepresentative"
	return records.idempotent(idempotency_key, command, payload, _do, actor=principal, organisation=organisation)


def assign_supplier_representative(**kwargs) -> dict[str, Any]:
	return assign_supplier_person(responsibility=authz.REPRESENTATIVE, **kwargs)


def assign_authorised_signatory(**kwargs) -> dict[str, Any]:
	return assign_supplier_person(responsibility=authz.SIGNATORY, **kwargs)
