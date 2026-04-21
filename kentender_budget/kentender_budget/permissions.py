# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""B5.2 — Budget DocType has_permission hook (see 8.Budget-Approval-Flow.md)."""

import frappe

from kentender_budget.services.budget_permissions import SUPER_ROLES


def budget_has_permission(doc, ptype=None, user=None, debug=False) -> bool:
	"""Deny role-inappropriate access. Controllers may only deny (return False)."""
	if not user:
		user = frappe.session.user
	if user == "Administrator":
		return True

	if ptype not in ("create", "write", "delete"):
		return True

	roles = set(frappe.get_roles(user))
	if SUPER_ROLES & roles:
		return True

	if ptype == "create":
		if "Planning Authority" in roles and "Strategy Manager" not in roles:
			return False
		return True

	if ptype == "delete":
		return True

	status = _budget_status_from_doc(doc)
	if status == "Draft":
		if "Planning Authority" in roles and "Strategy Manager" not in roles:
			return False
		return True

	if status == "Submitted":
		if "Planning Authority" in roles:
			return True
		return False

	if status == "Approved":
		return False

	return True


def _budget_status_from_doc(doc) -> str:
	"""Use the row in the database when it exists so Draft→Submitted is still gated as Draft."""
	if doc is None:
		return "Draft"
	if getattr(doc, "__islocal", None) or getattr(doc, "is_new", lambda: False)():
		return getattr(doc, "status", None) or "Draft"
	name = getattr(doc, "name", None)
	if name:
		stored = frappe.db.get_value("Budget", name, "status")
		return stored or "Draft"
	return getattr(doc, "status", None) or "Draft"
