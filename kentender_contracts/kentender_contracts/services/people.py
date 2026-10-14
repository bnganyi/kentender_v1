# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Who people are for Contract Management (CM-CHG-001 v0.8 §6).

Authority comes only from an active `User Responsibility Assignment` (AUTH-ADR-001), rechecked at every action, plus -- for the
capacities that need it (§6.2) -- a CM-owned subject binding (`services/authority.py`). A technical user acts in no business
capacity (§6 technical read: site-wide read-only, no business commands). Nothing here reads a tendering table."""

from __future__ import annotations

import frappe
from frappe.utils import cstr


def full_name(user: str) -> str:
	return cstr(frappe.db.get_value("User", user, "full_name")) or cstr(user)


def technical(user: str) -> bool:
	from kentender_core.services.authorization import is_technical

	return bool(user) and is_technical(user)


def decision(user: str, business_role: str, organisation_unit: str = "", *, read: bool = False, at=None):
	"""The AUTH decision for one role at one scope; a read purpose admits the site-wide technical reader."""
	from kentender_core.services.authorization import PURPOSE_COMMAND, PURPOSE_READ, authorise_record

	return authorise_record(user=user, business_role=business_role, organisation_unit=organisation_unit, at=at, purpose=PURPOSE_READ if read else PURPOSE_COMMAND)


def holds(user: str, business_role: str, organisation_unit: str = "", *, at=None) -> bool:
	"""May `user` exercise `business_role` now (at `organisation_unit` for an Organisation Unit role)? A technical user never does."""
	if not user or user == "Guest" or technical(user):
		return False
	return decision(user, business_role, organisation_unit, at=at).allowed


def holders(business_role: str, organisation_unit: str = "") -> list[str]:
	users = frappe.get_all("User Responsibility Assignment", filters={"business_role": business_role, "status": "Enabled"}, pluck="user", distinct=True)
	return sorted(u for u in users if holds(u, business_role, organisation_unit))
