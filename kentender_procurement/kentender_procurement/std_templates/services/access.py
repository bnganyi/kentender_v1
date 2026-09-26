# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Templates access (STD-TPL-IMP-001 v1.0 §10; AUTH-ADR-001 v1.10 §8.1;
owner ruling R4).

Read and bounded-concern access for Administrator and System Manager (the
KT-STD-001 §3A.6 technical read) and for a Procurement Officer or Head of
Procurement Function holding an Active Site-wide responsibility resolved by
the shared AUTH resolver. Nobody receives template-edit, activation,
supersession or withdrawal access here; those are deployment-only commands
naming the release owner (ruling R5). A Frappe Role alone grants nothing.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services.authorization import PURPOSE_READ, authorise_record, is_technical

ROLE_PROCUREMENT_OFFICER = "Procurement Officer"
ROLE_HEAD_OF_PROCUREMENT_FUNCTION = "Head of Procurement Function"
BUSINESS_ROLES: tuple[str, ...] = (ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION)
#: The four menu audiences (§11): client-side visibility only, never authority.
MENU_ROLES: tuple[str, ...] = ("Administrator", "System Manager", ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION)
FORBIDDEN_MESSAGE = "STD Templates is available to Administrators, System Managers, Procurement Officers and Heads of Procurement Function."


def _principal(user: str | None) -> str:
	return cstr(user or frappe.session.user).strip()


def resolve(user: str | None = None) -> dict[str, Any]:
	"""The caller's STD Templates access, resolved once per request."""
	principal = _principal(user)
	if not principal or principal == "Guest":
		return {"allowed": False, "technical": False, "responsibilities": []}
	technical = is_technical(principal)
	held = [
		role
		for role in BUSINESS_ROLES
		if authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_READ).allowed
	]
	return {"allowed": technical or bool(held), "technical": technical, "responsibilities": held}


def can_read(user: str | None = None) -> bool:
	return resolve(user)["allowed"]


def require_reader(user: str | None = None) -> dict[str, Any]:
	"""Masked: an unauthorised caller cannot learn a release exists (§12)."""
	access = resolve(user)
	if not access["allowed"]:
		from kentender_procurement.std_templates.compiler.errors import fail

		fail("STD_RELEASE_NOT_FOUND")
	return access
