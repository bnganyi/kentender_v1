# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`UpdateSupplierOrganisation` (BDS-CHG-001 v0.8 §7.2, §11.3 "Edit
organisation"). Any assigned supplier user may maintain the permitted
self-declared facts (§6), with a version check; a Suspended Account cannot
be edited (§5.2(5)).

The registered identity — legal name, country and registration number — can
be corrected only while the Account is Pending verification; afterwards it
changes through Supplier support. A new official email is added as an
unverified contact and gets its own verification link; the previously
verified address stays a verified notice contact and earlier notices are
never rewritten (§5.2(10))."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_suppliers.supplier_accounts.services import audit, authz_state, facts, records, verification
from kentender_suppliers.supplier_accounts.services import authorization as authz
from kentender_suppliers.supplier_accounts.services.errors import field_errors

ORGANISATION = "Supplier Organisation"
IDENTITY = ("legal_name", "country", "registration_number")
IDENTITY_LOCKED_TEXT = "Contact Supplier support to change the registered identity."
UNKNOWN_TEXT = "This value cannot be changed here."


def _snapshot(org) -> dict[str, str]:
	return {field: cstr(org.get(field)) for field in facts.FIELDS}


def _apply_contacts(org, before: dict[str, str], after: dict[str, str]) -> str:
	"""Keep the contact rows in step; returns an email needing verification."""
	pending = ""
	if after["official_email"] != before["official_email"].lower():
		match = None
		for row in org.contacts:
			if row.channel == "Email":
				row.is_official = 0
				if cstr(row.value).lower() == after["official_email"]:
					match = row
		if match is None:
			match = org.append("contacts", {"channel": "Email", "value": after["official_email"], "verification_status": "Unverified", "contact_version": 1})
		match.is_official = 1
		if match.verification_status != "Verified":
			pending = after["official_email"]
	if after["official_phone"] != before["official_phone"]:
		phones = [row for row in org.contacts if row.channel == "Phone" and row.is_official]
		if phones:
			phones[0].value, phones[0].verification_status = after["official_phone"], "Unverified"
			phones[0].contact_version = int(phones[0].contact_version or 1) + 1
		else:
			org.append("contacts", {"channel": "Phone", "value": after["official_phone"], "is_official": 1, "verification_status": "Unverified", "contact_version": 1})
	return pending


def update_supplier_organisation(*, organisation: str, values: dict[str, Any], expected_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	principal = authz.require_signed_in(user)
	authz.require_member(organisation, principal)
	authz_state.require_not_suspended(organisation)
	changes = {k: v for k, v in (values or {}).items()}

	def _do() -> dict[str, Any]:
		org = frappe.get_doc(ORGANISATION, organisation)
		records.check_version(org, expected_version)
		before = _snapshot(org)
		errors = {k: UNKNOWN_TEXT for k in changes if k not in facts.FIELDS}
		after = facts.normalise({**before, **{k: v for k, v in changes.items() if k in facts.FIELDS}})
		if org.account_status != "Pending verification":
			for field in IDENTITY:
				if after[field] != before[field]:
					errors[field] = IDENTITY_LOCKED_TEXT
		errors = {**facts.errors_for(after), **errors}
		if not errors.get("registration_number") and (after["country"], after["registration_number"]) != (before["country"], before["registration_number"]):
			if facts.same_identity(after["country"], after["registration_number"], exclude=org.name):
				errors["registration_number"] = facts.TEXT["duplicate"]
		if errors:
			return field_errors(errors)
		pending = _apply_contacts(org, before, after)
		records.bump(org, **after)
		sent = verification.issue(org, email=pending, actor=principal) if pending else {"sent": False}
		changed = {k: {"before": before[k], "after": after[k]} for k in facts.FIELDS if before[k] != after[k]}
		audit.record(doctype=ORGANISATION, name=org.name, action="update_supplier_organisation", actor=principal, metadata={"changed": changed, "record_version": int(org.record_version)})
		return {"ok": True, "organisation": org.name, "record_version": int(org.record_version), "verification_sent_to": pending if sent.get("sent") else ""}

	payload = {"organisation": organisation, "values": {k: cstr(v) for k, v in changes.items()}, "expected_version": cstr(expected_version)}
	return records.idempotent(idempotency_key, "UpdateSupplierOrganisation", payload, _do, actor=principal, organisation=organisation)
