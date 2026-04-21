"""Shared guards for Budget module (draft-only mutations)."""

import frappe
from frappe import _


def assert_budget_draft_for_mutation(budget_name: str | None) -> None:
	"""B5.3 / B5.14: allow allocations in Draft or Rejected (revision) only."""
	if not budget_name:
		return
	status = frappe.db.get_value("Budget", budget_name, "status")
	if status and status not in ("Draft", "Rejected"):
		frappe.throw(
			_("Budget allocations can only be changed while the budget is in Draft or Rejected status."),
			title=_("Not editable"),
		)
