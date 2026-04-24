# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Phase E1 — Authoritative role checks for whitelisted workflow and PP APIs.

Desk saves still rely on DocType permissions + ``has_permission`` hooks; trusted
workflow entry points call ``assert_*`` then ``doc.save(ignore_permissions=True)``.
"""

from __future__ import annotations

import frappe
from frappe import _

_ROLE_PLANNER = frozenset(("Procurement Planner",))
_ROLE_AUTHORITY = frozenset(("Planning Authority",))
_ROLE_ADMIN = frozenset(("Administrator", "System Manager"))
_ROLE_PLANNER_ADMIN = _ROLE_PLANNER | _ROLE_ADMIN
_ROLE_AUTHORITY_ADMIN = _ROLE_AUTHORITY | _ROLE_ADMIN
_ROLE_OFFICER_OR_AUTHORITY_ADMIN = frozenset(
	("Procurement Officer", "Planning Authority", "Administrator", "System Manager")
)


def _session_roles() -> frozenset[str]:
	return frozenset(frappe.get_roles(frappe.session.user))


def assert_may_run_plan_workflow(action: str, doc) -> None:
	"""Raise if the current user may not run this plan workflow action (server-side)."""
	roles = _session_roles()
	st = (doc.status or "").strip()
	if action == "submit_plan":
		if st not in ("Draft", "Returned"):
			frappe.throw(_("Invalid plan state for this action."), title=_("Not permitted"))
		if not (roles & _ROLE_PLANNER_ADMIN):
			frappe.throw(_("Not permitted."), frappe.PermissionError)
	elif action in ("approve_plan", "return_plan", "reject_plan"):
		if st != "Submitted":
			frappe.throw(_("Invalid plan state for this action."), title=_("Not permitted"))
		if not (roles & _ROLE_AUTHORITY_ADMIN):
			frappe.throw(_("Not permitted."), frappe.PermissionError)
	elif action == "lock_plan":
		if st != "Approved":
			frappe.throw(_("Invalid plan state for this action."), title=_("Not permitted"))
		if not (roles & _ROLE_AUTHORITY_ADMIN):
			frappe.throw(_("Not permitted."), frappe.PermissionError)
	else:
		frappe.throw(_("Unknown workflow action."), title=_("Not permitted"))


def assert_may_run_package_workflow(action: str, doc) -> None:
	"""Raise if the current user may not run this package workflow action (server-side)."""
	roles = _session_roles()
	st = (doc.status or "").strip()
	if action in ("complete_package", "submit_package"):
		if action == "complete_package" and st not in ("Draft", "Returned"):
			frappe.throw(_("Invalid package state for this action."), title=_("Not permitted"))
		if action == "submit_package" and st != "Completed":
			frappe.throw(_("Invalid package state for this action."), title=_("Not permitted"))
		if not (roles & _ROLE_PLANNER_ADMIN):
			frappe.throw(_("Not permitted."), frappe.PermissionError)
	elif action in ("approve_package", "return_package", "reject_package"):
		if st != "Submitted":
			frappe.throw(_("Invalid package state for this action."), title=_("Not permitted"))
		if not (roles & _ROLE_AUTHORITY_ADMIN):
			frappe.throw(_("Not permitted."), frappe.PermissionError)
	elif action == "mark_ready_for_tender":
		if st != "Approved":
			frappe.throw(_("Invalid package state for this action."), title=_("Not permitted"))
		if not (roles & _ROLE_OFFICER_OR_AUTHORITY_ADMIN):
			frappe.throw(_("Not permitted."), frappe.PermissionError)
	elif action == "release_package_to_tender":
		if st != "Ready for Tender":
			frappe.throw(_("Invalid package state for this action."), title=_("Not permitted"))
		if not (roles & _ROLE_OFFICER_OR_AUTHORITY_ADMIN):
			frappe.throw(_("Not permitted."), frappe.PermissionError)
	else:
		frappe.throw(_("Unknown workflow action."), title=_("Not permitted"))


def assert_may_apply_template_to_demands() -> None:
	"""C2 / D5 — only planners (and admins) may apply templates to demands."""
	roles = _session_roles()
	if not (roles & _ROLE_PLANNER_ADMIN):
		frappe.throw(_("Not permitted."), frappe.PermissionError)


def assert_may_edit_package_lines(doc) -> None:
	"""D4 package line APIs — planner/admin only, Draft / Completed / Returned package."""
	roles = _session_roles()
	if not (roles & _ROLE_PLANNER_ADMIN):
		frappe.throw(_("Not permitted."), frappe.PermissionError)
	st = (doc.status or "").strip()
	if st not in ("Draft", "Completed", "Returned"):
		frappe.throw(_("Package lines cannot be edited in this state."), title=_("Not permitted"))
