# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Who people are for Award (AWD-CHG-001 v0.4 §6).

Authority comes only from an active `User Responsibility Assignment`
(AUTH-ADR-001), rechecked at every action. A technical user acts in no
business capacity and never becomes the business substitute (§5.9 last
paragraph). No per-tender grant or new committee role is added (§6)."""

from __future__ import annotations

import frappe
from frappe.utils import cstr

ACCOUNTING_OFFICER = "Accounting Officer"
HEAD_OF_PROCUREMENT = "Head of Procurement Function"
AUDITOR = "Auditor"
TECHNICAL_OPERATOR = "Technical Operator"


def full_name(user: str) -> str:
	return cstr(frappe.db.get_value("User", user, "full_name")) or cstr(user)


def technical(user: str) -> bool:
	from kentender_core.services.authorization import is_technical

	return bool(user) and is_technical(user)


def holds(user: str, business_role: str) -> bool:
	from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record

	if not user or user == "Guest" or technical(user):
		return False
	return authorise_record(user=user, business_role=business_role, purpose=PURPOSE_COMMAND).allowed


def holders(business_role: str) -> list[str]:
	users = frappe.get_all("User Responsibility Assignment", filters={"business_role": business_role, "status": "Enabled"}, pluck="user", distinct=True)
	return sorted(u for u in users if holds(u, business_role))


def first_holder(business_role: str) -> str:
	found = holders(business_role)
	return found[0] if found else ""


def is_technical_operator(user: str) -> bool:
	"""An active, in-force Technical Operator assignment, rechecked now (§6).
	Unlike `holds`, a technical-role user may hold it: the Technical Operator
	acts in no business capacity, but the assignment must still be effective."""
	from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record

	if not user or user == "Guest":
		return False
	return authorise_record(user=user, business_role=TECHNICAL_OPERATOR, purpose=PURPOSE_COMMAND).allowed


def technical_operators() -> list[str]:
	users = frappe.get_all("User Responsibility Assignment", filters={"business_role": TECHNICAL_OPERATOR, "status": "Enabled"}, pluck="user", distinct=True)
	return sorted(u for u in set(users) if is_technical_operator(u))
