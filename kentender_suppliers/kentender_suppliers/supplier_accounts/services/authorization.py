# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Who may act for a supplier organisation (BDS-CHG-001 v0.8 §4.2, §5.2, §6;
plan D12). Explicit services, not role permissions:

- a supplier user acts only through an immutable Supplier User Assignment
  that is active at command time (`effective_from <= at < effective_to`);
- the organisation is always named by the caller and revalidated on every
  call — never a session default — so a person assigned to several
  organisations acts for exactly one per request (§5.2(4), BDS01-AC-009);
- an organisation the actor is not assigned to is masked as Not found
  (§8 record-existence masking, BDS01-AC-006);
- an Authorised Signatory needs Available authority evidence as well as an
  active window (§5.2(7), BDS01-AC-008);
- internal KenTender users (Desk "System User" accounts, including
  Administrator) never hold supplier authority (BDS01-IMP-008);
- account access decisions belong to the "Supplier Account Support
  Officer" business responsibility (plan OD-D), checked through the core
  assignment service like every other KenTender responsibility.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_suppliers.supplier_accounts.services import clock
from kentender_suppliers.supplier_accounts.services.errors import fail, not_found

ASSIGNMENT = "Supplier User Assignment"
ORGANISATION = "Supplier Organisation"
REPRESENTATIVE = "Supplier Representative"
SIGNATORY = "Authorised Signatory"
RESPONSIBILITIES = (REPRESENTATIVE, SIGNATORY)
SUPPORT_ROLE = "Supplier Account Support Officer"
_FIELDS = ["name", "organisation", "user", "responsibility", "job_title", "authority_evidence", "effective_from", "effective_to", "assigned_by", "assigned_at"]


def actor(user: str | None = None) -> str:
	return cstr(user or frappe.session.user)


def require_signed_in(user: str | None = None) -> str:
	principal = actor(user)
	if not principal or principal == "Guest":
		fail("BDS_SIGN_IN_REQUIRED")
	return principal


def is_internal_user(user: str) -> bool:
	"""Desk staff and technical accounts can never act for a supplier."""
	if user in ("Administrator", "Guest"):
		return user == "Administrator"
	return cstr(frappe.db.get_value("User", user, "user_type")) == "System User"


def is_active(row: dict[str, Any], at=None) -> bool:
	instant = get_datetime(at or clock.now())
	starts = get_datetime(row["effective_from"]) if row.get("effective_from") else None
	ends = get_datetime(row["effective_to"]) if row.get("effective_to") else None
	return bool(starts and starts <= instant and (ends is None or instant < ends))


def assignments_of(user: str, *, organisation: str = "", at=None, active_only: bool = True) -> list[dict[str, Any]]:
	filters: dict[str, Any] = {"user": user}
	if organisation:
		filters["organisation"] = organisation
	rows = frappe.get_all(ASSIGNMENT, filters=filters, fields=_FIELDS, order_by="assigned_at asc, creation asc", limit_page_length=0)
	return [r for r in rows if is_active(r, at)] if active_only else rows


def evidence_available(evidence: str) -> bool:
	return bool(evidence) and frappe.db.get_value("Supplier Account Evidence", evidence, "status") == "Available"


def is_active_signatory(row: dict[str, Any], at=None) -> bool:
	return row["responsibility"] == SIGNATORY and is_active(row, at) and evidence_available(cstr(row.get("authority_evidence")))


def organisations_of(user: str, at=None) -> list[str]:
	"""The organisations a person currently acts for, in assignment order."""
	seen: list[str] = []
	for row in assignments_of(user, at=at):
		if row["organisation"] not in seen:
			seen.append(row["organisation"])
	return seen


def require_member(organisation: str, user: str | None = None, at=None) -> list[dict[str, Any]]:
	"""The actor's active assignments on `organisation`; Not found otherwise."""
	principal = require_signed_in(user)
	if not organisation or not frappe.db.exists(ORGANISATION, organisation) or is_internal_user(principal):
		not_found()
	rows = assignments_of(principal, organisation=organisation, at=at)
	if not rows:
		not_found()
	return rows


def require_signatory(organisation: str, user: str | None = None, at=None) -> dict[str, Any]:
	"""An active Authorised Signatory with Available authority evidence."""
	rows = require_member(organisation, user, at)
	for row in rows:
		if is_active_signatory(row, at):
			return row
	fail("BDS_RESPONSIBILITY_REQUIRED")
	return {}  # unreachable


def responsibility_of(organisation: str, user: str, at=None) -> str:
	"""The strongest active responsibility the person holds, or ''."""
	rows = assignments_of(user, organisation=organisation, at=at)
	if any(is_active_signatory(r, at) for r in rows):
		return SIGNATORY
	return REPRESENTATIVE if rows else ""


def is_support_officer(user: str | None = None) -> bool:
	from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record

	principal = actor(user)
	if not principal or principal == "Guest":
		return False
	return authorise_record(user=principal, business_role=SUPPORT_ROLE, organisation_unit="", purpose=PURPOSE_COMMAND).allowed


def require_support_officer(user: str | None = None) -> str:
	principal = require_signed_in(user)
	if not is_support_officer(principal):
		fail("BDS_RESPONSIBILITY_REQUIRED", "Only a Supplier Account support officer can change account access.")
	return principal
