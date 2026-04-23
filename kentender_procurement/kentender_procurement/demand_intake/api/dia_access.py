# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""F3 — DIA workspace and API entry guards (PRD §17.2, Cursor F3)."""

from __future__ import annotations

import frappe
from frappe import _

# Roles that may use the Demand Intake workspace shell and DIA Desk APIs (PRD §17.2).
DIA_WORKSPACE_ROLES = frozenset(
	(
		"Requisitioner",
		"Department Approver",
		"Finance Reviewer",
		"Procurement Planner",
		"Auditor",
	)
)


def user_has_dia_workspace_access(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	roles = set(frappe.get_roles(user))
	if "System Manager" in roles:
		return True
	return bool(roles & DIA_WORKSPACE_ROLES)


def require_dia_workspace_user() -> None:
	if not user_has_dia_workspace_access():
		frappe.throw(
			_("You are not allowed to access Demand Intake."),
			frappe.PermissionError,
		)


def require_demand_read(name: str | None) -> None:
	"""Ensure current user may read this Demand (DocPerm + F1 row rules)."""
	require_dia_workspace_user()
	if not name or not str(name).strip():
		return
	name = str(name).strip()
	if not frappe.db.exists("Demand", name):
		return
	if not frappe.has_permission("Demand", "read", doc=name):
		frappe.throw(_("You do not have permission to read this demand."), frappe.PermissionError)


def require_demand_write(name: str | None) -> None:
	require_dia_workspace_user()
	if not name or not str(name).strip():
		return
	name = str(name).strip()
	if not frappe.db.exists("Demand", name):
		return
	if not frappe.has_permission("Demand", "write", doc=name):
		frappe.throw(_("You do not have permission to update this demand."), frappe.PermissionError)
