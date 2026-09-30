# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Who people are for Bid Evaluation (EVL-CHG-001 v0.4 §3; plan D17).

Authority comes only from an active `User Responsibility Assignment`
(AUTH-ADR-001), never a Frappe Role alone. Committee membership and the
secretary are appointments for one tender, never responsibilities: an
office (Accounting Officer, Head of Procurement) grants no bid access and no
finding authority. A technical user (Administrator, System Manager) is never
eligible and acts in no business capacity (KT-STD-001 §3A.6)."""

from __future__ import annotations

import frappe
from frappe.utils import cstr, get_datetime

ACCOUNTING_OFFICER = "Accounting Officer"
HEAD_OF_PROCUREMENT = "Head of Procurement Function"
PROCUREMENT_OFFICER = "Procurement Officer"
AUDITOR = "Auditor"
TECHNICAL_OPERATOR = "Technical Operator"


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


def holders(business_role: str) -> list[str]:
	users = frappe.get_all("User Responsibility Assignment", filters={"business_role": business_role, "status": "Enabled"}, pluck="user", distinct=True)
	return sorted(u for u in users if holds(u, business_role))


def active_responsibilities(user: str) -> list[str]:
	"""The business roles the user holds now, at any scope: enabled
	assignments inside their effective period. A department-scoped role is
	as much an active responsibility as a site-wide one (§3); `holds` asks a
	different question (may the user act site-wide in that role)."""
	from kentender_procurement.bid_evaluation.services import clock

	now = clock.now()
	out = []
	for row in frappe.get_all("User Responsibility Assignment", filters={"user": user, "status": "Enabled"},
			fields=["business_role", "effective_from", "effective_to"], order_by="creation asc"):
		if row.effective_from and get_datetime(row.effective_from) > now:
			continue
		if row.effective_to and get_datetime(row.effective_to) < now:
			continue
		if row.business_role not in out:
			out.append(row.business_role)
	return out


def internal(user: str) -> tuple[bool, str]:
	"""(eligible as an internal person, designation): an enabled System User,
	not technical, holding at least one active responsibility at any scope."""
	row = frappe.db.get_value("User", user, ["enabled", "user_type"], as_dict=True)
	if not row or not row.enabled or row.user_type != "System User" or technical(user):
		return False, ""
	held = active_responsibilities(user)
	return (True, held[0]) if held else (False, "")
