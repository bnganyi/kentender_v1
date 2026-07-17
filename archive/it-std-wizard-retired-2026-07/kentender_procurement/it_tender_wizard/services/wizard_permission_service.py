# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Role and permission checks for IT Wizard."""

from __future__ import annotations

import frappe
from frappe import _

PERM_CREATE = "std_it_wizard.create"
PERM_VIEW = "std_it_wizard.view"
PERM_DELETE_DRAFT = "std_it_wizard.delete_draft"

_DRAFTER_ROLES = frozenset(
	{
		"IT Tender Drafter",
		"Procurement Officer",
		"Procurement Planner",
		"System Manager",
		"Administrator",
	}
)


def _user_roles(user: str | None = None) -> set[str]:
	user = user or frappe.session.user
	return set(frappe.get_roles(user))


def assert_permission(permission: str, *, user: str | None = None) -> None:
	user = user or frappe.session.user
	if user == "Administrator":
		return
	roles = _user_roles(user)
	if permission == PERM_CREATE and roles & _DRAFTER_ROLES:
		return
	if permission == PERM_VIEW and roles & (_DRAFTER_ROLES | {"Auditor"}):
		return
	if permission == PERM_DELETE_DRAFT and roles & _DRAFTER_ROLES:
		return
	frappe.throw(_("Not permitted."), frappe.PermissionError)


def can_create(*, user: str | None = None) -> bool:
	try:
		assert_permission(PERM_CREATE, user=user)
		return True
	except frappe.PermissionError:
		return False
