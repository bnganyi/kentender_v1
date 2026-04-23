# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared DIA Desk context (role bucket for KPIs, queues, lists)."""

import frappe


def dia_roles() -> set[str]:
	return set(frappe.get_roles(frappe.session.user) or [])


def dia_is_privileged() -> bool:
	u = frappe.session.user
	if u == "Administrator":
		return True
	return "System Manager" in dia_roles()


def resolve_dia_role_key() -> str:
	roles = dia_roles()
	if dia_is_privileged():
		return "admin"
	if "Finance Reviewer" in roles:
		return "finance"
	if "Department Approver" in roles:
		return "hod"
	if "Procurement Planner" in roles:
		return "procurement"
	if "Auditor" in roles:
		return "auditor"
	return "requisitioner"
