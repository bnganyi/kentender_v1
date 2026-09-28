# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Who may act on a bid (BDS-CHG-001 v0.8 §5.2, §6 and plan D12). Explicit
checks over the Supplier Account provider's assignment facts, never Frappe
role permissions. The acting organisation is named on every request and
revalidated each time, never taken from a session default (KT-STD-001 §10).
An organisation the person holds no assignment in is answered exactly as if
they had no supplier account, so nothing about it is disclosed."""

from __future__ import annotations

from typing import Any

from frappe.utils import cstr

from kentender_procurement.bid_submission.services import supplier_gateway
from kentender_procurement.bid_submission.services.errors import fail

REPRESENTATIVE = "Supplier Representative"
SIGNATORY = "Authorised Signatory"
PREPARERS = (REPRESENTATIVE, SIGNATORY)


def require_person(user: str) -> str:
	if not user or user == "Guest":
		fail("BDS_SIGN_IN_REQUIRED")
	return user


def acting_assignment(user: str, organisation: str, *, at=None) -> dict[str, Any]:
	"""The person's active preparing assignment in `organisation`."""
	rows = [a for a in supplier_gateway.active_assignments(user=user, at=at) if a.get("active") and a.get("responsibility") in PREPARERS]
	organisation = cstr(organisation).strip()
	if not organisation and len({a["organisation_id"] for a in rows}) == 1:
		organisation = rows[0]["organisation_id"]
	mine = [a for a in rows if a["organisation_id"] == organisation]
	if not mine:
		fail("BDS_ACCOUNT_REQUIRED")
	return sorted(mine, key=lambda a: a["responsibility"] != SIGNATORY)[0]


def active_account(organisation: str) -> dict[str, Any]:
	org = supplier_gateway.organisation(organisation_id=organisation)
	if not org:
		fail("BDS_ACCOUNT_REQUIRED")
	if org.get("account_status") == "Suspended":
		fail("BDS_ACCOUNT_SUSPENDED")
	if org.get("account_status") != "Active":
		fail("BDS_ACCOUNT_REQUIRED")
	return org


def active_signatory(assignment_id: str, organisation: str, *, at=None) -> dict[str, Any] | None:
	row = supplier_gateway.assignment(assignment_id=cstr(assignment_id).strip(), at=at)
	if not row or row.get("organisation_id") != organisation or row.get("responsibility") != SIGNATORY or not row.get("active"):
		return None
	return row


# --------------------------------------------------------------------------
# Desk: a bid's content is never a Desk read (BDS-CHG-001 v0.8 §12;
# BDS01-AC-080). These records hold its answers, files, prior/new values,
# command results, receipt summary and withdrawal reasons; no role is
# granted them, and these hooks refuse any user a record or a list. The
# supplier reads them only through this module's own services; technical
# users see metadata through the technical read. (Administrator bypasses
# Frappe's permission checks — a recorded production-gate residual, plan D7.)
# --------------------------------------------------------------------------

CONTENT_DOCTYPES = ("Bid Section Response", "Bid Evidence", "Bid Draft Change", "Bid Command Journal", "Bid Receipt", "Bid Submission Change")


def deny_desk_access(doc=None, ptype=None, user=None, debug=False) -> bool:
	return False


def deny_desk_query(user=None, doctype=None) -> str:
	return "1=0"
