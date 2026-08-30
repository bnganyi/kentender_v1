# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable Procurement Planning service errors (PLN-CHG-001 v1.2 §9).

§9 defines a closed set of twenty-one codes. They are stable service results;
`fail()` refuses any code outside the contract — an invented code is a defect
in the caller, not a new error type. Unauthorised detail and task reads do not
use these codes at all: they raise the same not-found as a nonexistent record
(`authority.not_found()`).
"""

from __future__ import annotations

import frappe

ERROR_CODES: frozenset[str] = frozenset(
	{
		"PLN_NO_CONTEXT",
		"PLN_WINDOW_CLOSED",
		"PLN_NEED_COVERAGE_INCOMPLETE",
		"PLN_ENTRY_INCOMPLETE",
		"PLN_BUDGET_LINE_INELIGIBLE",
		"PLN_DPP_STALE",
		"PLN_CLASSIFICATION_INCOMPLETE",
		"PLN_SOURCE_UNAVAILABLE",
		"PLN_SOURCE_INCOMPATIBLE",
		"PLN_SOURCE_CORRECTION_REQUIRED",
		"PLN_DISSOLUTION_BLOCKED",
		"PLN_OBJECTIVE_INELIGIBLE",
		"PLN_SCHEDULE_INVALID",
		"PLN_FINANCE_SHORTFALL",
		"PLN_FINANCE_STALE",
		"PLN_RESERVATION_RELEASE_FAILED",
		"PLN_REVIEW_STALE",
		"PLN_SEGREGATION_CONFLICT",
		"PLN_PUBLICATION_FAILED",
		"PLN_REMOVAL_BLOCKED",
		"PLN_STALE_WRITE",
	}
)


class ProcurementPlanningError(frappe.ValidationError):
	def __init__(self, code: str, message: str):
		self.code = code
		super().__init__(message)


def fail(code: str, message: str) -> None:
	if code not in ERROR_CODES:
		raise ValueError(
			f"{code!r} is not part of the PLN-CHG-001 v1.2 §9 error contract. "
			f"Map the condition onto one of: {', '.join(sorted(ERROR_CODES))}."
		)
	# Pass a constructed instance so frappe.throw records the message for the
	# client while `.code` survives for programmatic handling (NDS precedent).
	frappe.throw(message, exc=ProcurementPlanningError(code, message))
