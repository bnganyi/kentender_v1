# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Who reads which Budget rows (OVS-CHG-001 v0.6 §4.1; plan Phase 10; tracker OVS6-1002).

The core scope hooks decide whether a user holds a responsibility that may read a Budget DocType. On top
of that, a reader of approved versions only (the Accounting Officer and the Head of Procurement Function,
who hold no Budget responsibility) sees a Budget, its lines and their versions only through a version that
is Active, Superseded or Closed: never a Draft, a version awaiting approval, or a line that only exists in
one. Everyone else is exactly as the core hooks decide."""

from __future__ import annotations

import frappe
from frappe.utils import cstr

from kentender_budget.services.budget_authorization import APPROVED_VERSION_STATUSES, approved_only_reader
from kentender_core.services import authorization as core

VERSION, BUDGET, LINE, LINE_VERSION = "Procurement Budget Version", "Procurement Budget", "Procurement Budget Line", "Procurement Budget Line Version"


def _approved() -> str:
	return ", ".join(frappe.db.escape(s) for s in APPROVED_VERSION_STATUSES)


def _approved_versions() -> str:
	return f"select name from `tab{VERSION}` where status in ({_approved()})"


def _restriction(doctype: str) -> str:
	if doctype == VERSION:
		return f"`tab{VERSION}`.status in ({_approved()})"
	if doctype == BUDGET:
		return f"`tab{BUDGET}`.name in (select budget from `tab{VERSION}` where status in ({_approved()}))"
	if doctype == LINE_VERSION:
		return f"`tab{LINE_VERSION}`.budget_version in ({_approved_versions()})"
	if doctype == LINE:
		return f"`tab{LINE}`.name in (select budget_line from `tab{LINE_VERSION}` where budget_version in ({_approved_versions()}))"
	return ""


def permission_query_conditions(user: str | None = None, doctype: str | None = None) -> str:
	base = core.permission_query_conditions(user, doctype)
	if base == "1=0" or not approved_only_reader(user):
		return base
	restriction = _restriction(doctype or "")
	return f"({base}) and {restriction}" if base and restriction else (restriction or base)


def has_permission(doc=None, ptype: str = "read", user: str | None = None):
	allowed = core.has_permission(doc, ptype, user)
	if not allowed or doc is None or not approved_only_reader(user):
		return allowed
	doctype = getattr(doc, "doctype", "") or (doc.get("doctype") if isinstance(doc, dict) else "")
	name = getattr(doc, "name", "") or (doc.get("name") if isinstance(doc, dict) else "")
	if not name:
		return allowed
	if doctype == VERSION:
		return cstr(frappe.db.get_value(VERSION, name, "status")) in APPROVED_VERSION_STATUSES
	if doctype == BUDGET:
		return bool(frappe.db.exists(VERSION, {"budget": name, "status": ("in", APPROVED_VERSION_STATUSES)}))
	if doctype == LINE_VERSION:
		return cstr(frappe.db.get_value(VERSION, frappe.db.get_value(LINE_VERSION, name, "budget_version"), "status")) in APPROVED_VERSION_STATUSES
	if doctype == LINE:
		versions = frappe.get_all(LINE_VERSION, filters={"budget_line": name}, pluck="budget_version")
		return bool(versions) and bool(frappe.db.exists(VERSION, {"name": ("in", versions), "status": ("in", APPROVED_VERSION_STATUSES)}))
	return allowed
