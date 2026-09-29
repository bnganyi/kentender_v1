# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Who people are for Bid Opening: names, designations, the Accounting
Officer's authority, committee eligibility (BOP-CHG-001 v0.10 §4 Appointment,
§6, §7 AppointOpeningCommittee; plan D13).

Authority comes only from an active `User Responsibility Assignment`
(AUTH-ADR-001), never a Frappe Role alone. A technical user (Administrator,
System Manager) is never eligible and acts in no business capacity. A
committee member must be an enabled internal user holding at least one
active KenTender responsibility, whose name becomes their designation;
holding the Accounting Officer responsibility does not itself make anyone a
member (PRC-CHG-001 v0.9 §13)."""

from __future__ import annotations

import frappe
from frappe.utils import cstr

ACCOUNTING_OFFICER = "Accounting Officer"
HEAD_OF_PROCUREMENT = "Head of Procurement Function"
PROCUREMENT_OFFICER = "Procurement Officer"
AUDITOR = "Auditor"


def full_name(user: str) -> str:
	return cstr(frappe.db.get_value("User", user, "full_name")) or cstr(user)


def technical(user: str) -> bool:
	from kentender_core.services.authorization import is_technical

	return is_technical(user)


def holds(user: str, business_role: str) -> bool:
	from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record

	if not user or technical(user):
		return False
	return authorise_record(user=user, business_role=business_role, purpose=PURPOSE_COMMAND).allowed


def responsibilities(user: str) -> list[str]:
	return frappe.get_all("User Responsibility Assignment", filters={"user": user, "status": "Enabled"}, pluck="business_role", order_by="creation asc",
		distinct=True)


def accounting_officers() -> list[str]:
	users = frappe.get_all("User Responsibility Assignment", filters={"business_role": ACCOUNTING_OFFICER, "status": "Enabled"}, pluck="user", distinct=True)
	return [u for u in users if holds(u, ACCOUNTING_OFFICER)]


def eligibility(user: str) -> tuple[bool, str]:
	"""(eligible, designation). Designation is the member's first active responsibility."""
	row = frappe.db.get_value("User", user, ["enabled", "user_type"], as_dict=True)
	if not row or not row.enabled or row.user_type != "System User" or technical(user):
		return False, ""
	held = [r for r in responsibilities(user) if holds(user, r)]
	return (True, held[0]) if held else (False, "")
