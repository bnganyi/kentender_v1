# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""Review workbench payload — allocation-focused view of a budget."""

import frappe
from frappe import _

from kentender_budget.api.builder import _get_builder_payload


@frappe.whitelist()
def get_budget_review_data(budget_name: str | None = None):
	"""Return anchor + allocation rows for Budget Management Review mode."""
	if not budget_name:
		frappe.throw(_("Budget is required."))
	if not frappe.has_permission("Budget", "read", budget_name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return _get_builder_payload(budget_name, lines_filter="active")
