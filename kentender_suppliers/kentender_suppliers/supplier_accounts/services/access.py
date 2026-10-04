# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Suspend and restore supplier access (plan owner decision OD-D; BDS-CHG-001
v0.8 §5.2(5), §5.12 "Account Suspended", §5.14 "Account access suspended";
BDS01-AC-010, BDS03-AC-010).

Only a holder of the "Supplier Account Support Officer" responsibility
decides, with a reason, from the Supplier Organisation form. Suspension
blocks every preparation and change command; receipts stay readable through
the recovery route. Restoring returns the Account to Active when its
official email is verified, otherwise to Pending verification — a supplier
never reactivates itself. Every decision is kept as its own record."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_suppliers.supplier_accounts.services import audit, clock, records
from kentender_suppliers.supplier_accounts.services import authorization as authz
from kentender_suppliers.supplier_accounts.services.errors import field_errors, not_found

ORGANISATION = "Supplier Organisation"
DECISION = "Supplier Account Access Decision"
REASON_TEXT = "Enter a reason of 10 to 500 characters."
STATE_TEXT = {"Suspend": "This account is already suspended.", "Restore": "This account is not suspended."}


def _official_email_verified(org) -> bool:
	return any(r.channel == "Email" and r.is_official and r.verification_status == "Verified" for r in org.contacts)


def _decide(decision: str, *, organisation: str, reason: str, expected_version, idempotency_key: str, user: str | None) -> dict[str, Any]:
	principal = authz.require_support_officer(user)
	if not organisation or not frappe.db.exists(ORGANISATION, organisation):
		not_found()
	text = cstr(reason).strip()

	def _do() -> dict[str, Any]:
		org = frappe.get_doc(ORGANISATION, organisation)
		records.check_version(org, expected_version)
		if not 10 <= len(text) <= 500:
			return field_errors({"reason": REASON_TEXT})
		if (decision == "Suspend") == (org.account_status == "Suspended"):
			return field_errors({"decision": STATE_TEXT[decision]})
		previous = org.account_status
		resulting = "Suspended" if decision == "Suspend" else ("Active" if _official_email_verified(org) else "Pending verification")
		now = clock.now()
		row = records.insert(frappe.get_doc({
			"doctype": DECISION, "organisation": org.name, "decision": decision, "reason": text, "previous_status": previous,
			"resulting_status": resulting, "decided_by": principal, "decided_at": now, "fixture_namespace": org.fixture_namespace,
		}))
		records.bump(org, account_status=resulting, status_since=now)
		audit.record(doctype=ORGANISATION, name=org.name, action=f"{decision.lower()}_supplier_account", actor=principal, metadata={"decision": row.name, "previous_status": previous, "resulting_status": resulting})
		return {"ok": True, "organisation": org.name, "decision": row.name, "account_status": resulting, "record_version": int(org.record_version)}

	payload = {"organisation": organisation, "reason": text, "expected_version": cstr(expected_version)}
	return records.idempotent(idempotency_key, f"{decision}SupplierAccount", payload, _do, actor=principal, organisation=organisation)


def suspend_supplier_account(*, organisation: str, reason: str, expected_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	return _decide("Suspend", organisation=organisation, reason=reason, expected_version=expected_version, idempotency_key=idempotency_key, user=user)


def restore_supplier_account(*, organisation: str, reason: str, expected_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	return _decide("Restore", organisation=organisation, reason=reason, expected_version=expected_version, idempotency_key=idempotency_key, user=user)
