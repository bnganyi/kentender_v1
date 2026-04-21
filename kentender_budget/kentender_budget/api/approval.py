# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""B5.4 / B5.5 / B5.11 — Whitelisted submit, approve, reject (8.Budget-Approval-Flow.md, 8.a)."""

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def submit_budget(budget_name: str | None = None):
	"""Draft → Submitted or Rejected → Submitted. Permissions and validate() enforce roles and locks."""
	if not budget_name:
		frappe.throw(_("Budget name is required."))
	doc = frappe.get_doc("Budget", budget_name)
	doc.check_permission("write")
	if doc.status not in ("Draft", "Rejected"):
		frappe.throw(_("Only Draft or Rejected budgets can be submitted."))
	doc.status = "Submitted"
	doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def approve_budget(budget_name: str | None = None):
	"""Submitted → Approved."""
	if not budget_name:
		frappe.throw(_("Budget name is required."))
	doc = frappe.get_doc("Budget", budget_name)
	doc.check_permission("write")
	if doc.status != "Submitted":
		frappe.throw(_("Only Submitted budgets can be approved."))
	doc.status = "Approved"
	doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def reject_budget(budget_name: str | None = None, rejection_reason: str | None = None):
	"""Submitted → Rejected. Planning Authority (or superuser bypass). Reason required."""
	if not budget_name:
		frappe.throw(_("Budget name is required."))
	reason = (rejection_reason or "").strip()
	if not reason:
		frappe.throw(_("Reason for rejection is required."))
	doc = frappe.get_doc("Budget", budget_name)
	doc.check_permission("write")
	if doc.status != "Submitted":
		frappe.throw(_("Only Submitted budgets can be rejected."))
	doc.status = "Rejected"
	doc.rejection_reason = reason
	doc.rejected_by = frappe.session.user
	doc.rejected_at = now_datetime()
	doc.save()
	return {"name": doc.name, "status": doc.status}
