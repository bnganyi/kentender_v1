# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""B5.2 / B5.3 — Budget role rules and submission locks (8.Budget-Approval-Flow.md)."""

import frappe
from frappe import _
from frappe.utils import flt

# Desk "Administrator" role (not the Administrator user, which bypasses checks elsewhere).
SUPER_ROLES = frozenset(("System Manager", "Administrator"))


def budget_superuser_bypass() -> bool:
	if frappe.session.user == "Administrator":
		return True
	roles = set(frappe.get_roles())
	return bool(SUPER_ROLES & roles)


def assert_allowed_transition_roles(previous: str, new: str) -> None:
	"""Raise if the current user may not perform this status change."""
	if previous == new:
		return
	if budget_superuser_bypass():
		return
	roles = set(frappe.get_roles())
	if (previous, new) == ("Draft", "Submitted"):
		if "Strategy Manager" not in roles:
			frappe.throw(
				_("Only a Strategy Manager can submit this budget."),
				frappe.PermissionError,
			)
		return
	if (previous, new) == ("Submitted", "Approved"):
		if "Planning Authority" not in roles:
			frappe.throw(
				_("Only Planning Authority can approve this budget."),
				frappe.PermissionError,
			)
		return
	if (previous, new) == ("Submitted", "Rejected"):
		if "Planning Authority" not in roles:
			frappe.throw(
				_("Only Planning Authority can reject this budget."),
				frappe.PermissionError,
			)
		return
	if (previous, new) == ("Rejected", "Submitted"):
		if "Strategy Manager" not in roles:
			frappe.throw(
				_("Only a Strategy Manager can submit this budget."),
				frappe.PermissionError,
			)
		return


def _budget_field_values_equal(fieldname: str, old_v, new_v) -> bool:
	if fieldname == "total_budget_amount":
		return flt(old_v or 0) == flt(new_v or 0)
	return old_v == new_v


def enforce_budget_submitted_approved_immutability(doc) -> None:
	"""B5.3: No edits to budget content once Submitted or Approved (except Submitted→Approved approval)."""
	if budget_superuser_bypass():
		return
	if doc.is_new():
		return
	stored = frappe.db.get_value("Budget", doc.name, "status") or "Draft"
	if stored not in ("Submitted", "Approved"):
		return
	prev = doc.get_doc_before_save()
	if not prev:
		return
	ignore = frozenset(("modified", "modified_by"))
	rejecting = (
		stored == "Submitted"
		and prev.get("status") == "Submitted"
		and doc.get("status") == "Rejected"
	)
	allowed_on_submitted_to_rejected = frozenset(
		("status", "rejection_reason", "rejected_by", "rejected_at")
	)
	for field in doc.meta.get_valid_columns():
		if field in ignore:
			continue
		old_v, new_v = prev.get(field), doc.get(field)
		if _budget_field_values_equal(field, old_v, new_v):
			continue
		if rejecting and field in allowed_on_submitted_to_rejected:
			continue
		if field == "status":
			if stored == "Submitted" and old_v == "Submitted" and new_v == "Approved":
				continue
			frappe.throw(
				_("This budget is locked; its status cannot be changed in this way."),
				title=_("Not editable"),
			)
		frappe.throw(
			_("Submitted or approved budgets cannot be edited. Change is allowed only when approving (Submitted → Approved) or rejecting (Submitted → Rejected)."),
			title=_("Not editable"),
		)
