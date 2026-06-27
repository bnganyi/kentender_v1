"""Shared guards for Budget module."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt


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


def assert_line_reduction_safe(budget_line_id: str, new_allocated: float) -> None:
	"""Block reducing a Budget Line's amount_allocated below its current obligations.

	Obligations = reserved + committed + consumed.  If the proposed new allocated
	amount would fall below this floor, raise a ValidationError.

	Use this guard in the Budget Builder before persisting an allocation change.
	"""
	if not budget_line_id:
		return
	row = frappe.db.get_value(
		"Budget Line",
		budget_line_id,
		["amount_reserved", "amount_committed", "amount_consumed"],
		as_dict=True,
	)
	if not row:
		return
	obligations = flt(row.amount_reserved) + flt(row.amount_committed) + flt(row.amount_consumed)
	new_alloc = flt(new_allocated)
	if new_alloc < obligations - 1e-9:
		frappe.throw(
			_(
				"Cannot reduce Budget Line allocation to {0}: "
				"current obligations (reserved + committed + consumed) total {1}. "
				"Release or convert reservations before reducing the allocation."
			).format(new_alloc, obligations),
			title=_("Revision Guard"),
		)


def assert_budget_total_reduction_safe(budget_name: str, new_total: float) -> None:
	"""Block reducing a Budget's total_budget_amount below the sum of line obligations.

	Aggregates reserved + committed + consumed across all active Budget Lines
	linked to this Budget.  Raises ValidationError if new_total falls below that sum.
	"""
	if not budget_name:
		return
	result = frappe.db.sql(
		"""
		SELECT
			COALESCE(SUM(amount_reserved),  0) AS total_reserved,
			COALESCE(SUM(amount_committed), 0) AS total_committed,
			COALESCE(SUM(amount_consumed),  0) AS total_consumed
		FROM `tabBudget Line`
		WHERE budget = %s AND is_active = 1
		""",
		(budget_name,),
		as_dict=True,
	)
	if not result:
		return
	row = result[0]
	obligations = flt(row.total_reserved) + flt(row.total_committed) + flt(row.total_consumed)
	new_t = flt(new_total)
	if new_t < obligations - 1e-9:
		frappe.throw(
			_(
				"Cannot reduce Budget total to {0}: "
				"line obligations (reserved + committed + consumed) total {1}. "
				"Resolve outstanding obligations before reducing the budget envelope."
			).format(new_t, obligations),
			title=_("Revision Guard"),
		)
