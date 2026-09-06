# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable Procurement Planning service errors (PLN-CHG-001 v1.12 §9).

§9 defines a closed set of codes. They are stable service results; `fail()`
refuses any code outside the contract — an invented code is a defect in the
caller, not a new error type. Unauthorised detail and task reads do not use
these codes at all: they raise the same not-found as a nonexistent record
(`planning_authorization.not_found()`). AUTH-ADR-001 v1.6 §10 codes are
remapped onto this set at the service boundary (tracker D4) and never reach
a client.
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
		"PLN_TENDERING_PERIOD_BELOW_MINIMUM",
		"PLN_EVALUATION_PERIOD_ABOVE_MAXIMUM",
		"PLN_STANDSTILL_BELOW_MINIMUM",
		"PLN_DELIVERY_BOUNDARY_INSUFFICIENT",
		"PLN_FORECAST_REASON_REQUIRED",
		"PLN_CASCADE_INCLUDES_ACTUAL_MILESTONE",
		"PLN_BASELINE_LOCKED",
		"PLN_ACTUAL_NOT_WRITABLE",
		"PLN_PLAN_NOT_AFFORDABLE",
		"PLN_FINANCE_STALE",
		"PLN_RESERVATION_RELEASE_FAILED",
		"PLN_REVIEW_STALE",
		"PLN_SEGREGATION_CONFLICT",
		"PLN_PUBLICATION_FAILED",
		"PLN_REMOVAL_BLOCKED",
		"PLN_STATUTORY_ROUTE_UNCONFIGURED",
		"PLN_PLAN_CONTENTS_INCOMPLETE",
		"PLN_METHOD_NOT_ADMISSIBLE",
		"PLN_RESERVATION_REQUIRED",
		"PLN_REFERENCE_UNAVAILABLE",
		"PLN_STALE_WRITE",
	}
)

MESSAGES: dict[str, str] = {
	"PLN_NO_CONTEXT": "You do not have an assigned Procurement Planning scope, or no configured Financial Year is available.",
	"PLN_WINDOW_CLOSED": "The initial departmental-plan submission window is closed.",
	"PLN_NEED_COVERAGE_INCOMPLETE": "Add every current accepted Need to this departmental plan before submitting.",
	"PLN_ENTRY_INCOMPLETE": "Complete the highlighted requirement fields before submitting.",
	"PLN_BUDGET_LINE_INELIGIBLE": "Select an Active Procurement Budget Line available to this department and Financial Year.",
	"PLN_DPP_STALE": "This departmental plan changed. Reload and review the current Version.",
	"PLN_CLASSIFICATION_INCOMPLETE": "Classify every submitted requirement before accepting the plan.",
	"PLN_SOURCE_UNAVAILABLE": "One or more selected departmental entries are no longer available for Plan Item formation.",
	"PLN_SOURCE_INCOMPATIBLE": "The selected entries cannot form one Plan Item. Create separate items.",
	"PLN_SOURCE_CORRECTION_REQUIRED": "A departmental source changed. Dissolve and re-form the affected Draft item before continuing.",
	"PLN_DISSOLUTION_BLOCKED": "This Plan Item is no longer in a mutable Draft and cannot be dissolved.",
	"PLN_OBJECTIVE_INELIGIBLE": "Select an Active Strategic Objective valid for this Plan.",
	"PLN_SCHEDULE_INVALID": "Correct the highlighted dates so the schedule is chronological and meets the required-by date.",
	"PLN_TENDERING_PERIOD_BELOW_MINIMUM": "The tendering period must be at least 7 days.",
	"PLN_EVALUATION_PERIOD_ABOVE_MAXIMUM": "The evaluation period cannot exceed 30 days.",
	"PLN_STANDSTILL_BELOW_MINIMUM": "The standstill period before contract signing must be at least 14 days.",
	"PLN_DELIVERY_BOUNDARY_INSUFFICIENT": "The computed contract signing date leaves no reasonable delivery period before the required-by date. Adjust the target invitation date or the governed periods.",
	"PLN_FORECAST_REASON_REQUIRED": "State why the forecast date is changing before saving.",
	"PLN_CASCADE_INCLUDES_ACTUAL_MILESTONE": "A milestone with a recorded actual date cannot be included in a forecast cascade.",
	"PLN_BASELINE_LOCKED": "The baseline schedule is locked once the Plan Version is submitted. Prepare a Plan successor to change it.",
	"PLN_ACTUAL_NOT_WRITABLE": "Actual dates cannot be entered directly. This value is populated only by the module that recorded the real event.",
	"PLN_PLAN_NOT_AFFORDABLE": "The planned total exceeds the approved amount on one or more Procurement Budget Lines.",
	"PLN_FINANCE_STALE": "Funding confirmation is no longer current. Request confirmation again.",
	"PLN_RESERVATION_RELEASE_FAILED": "Funding could not be released. The Planning change was not completed. Try again or quote the support reference.",
	"PLN_REVIEW_STALE": "This task has already changed. Reload to see the current decision.",
	"PLN_SEGREGATION_CONFLICT": "You cannot make this decision because you performed an incompatible earlier action.",
	"PLN_PUBLICATION_FAILED": "Publication was not acknowledged. The approved Plan remains unchanged and may be retried.",
	"PLN_REMOVAL_BLOCKED": "This Active Plan Item has downstream use and cannot be removed through Planning.",
	"PLN_STATUTORY_ROUTE_UNCONFIGURED": "The statutory approval route for this entity is not configured. Adoption cannot proceed; a plan cannot lawfully complete without statutory approval.",
	"PLN_PLAN_CONTENTS_INCOMPLETE": "One or more Plan Items are missing a plan horizon, aggregation indicator, lotting indicator, multi-year justification or lot count required by the plan contents rules.",
	"PLN_METHOD_NOT_ADMISSIBLE": "The selected procurement method is not admissible for this planned value.",
	"PLN_RESERVATION_REQUIRED": "Record a preference and reservation category before requesting Finance confirmation. None is a valid choice.",
	"PLN_REFERENCE_UNAVAILABLE": "The threshold matrix for this financial year has not been configured. Method admissibility cannot be checked and readiness fails closed.",
	"PLN_STALE_WRITE": "Another user changed this record. Reload before continuing.",
}


class ProcurementPlanningError(frappe.ValidationError):
	def __init__(self, code: str, message: str, detail: dict | None = None):
		self.code = code
		self.detail = detail or {}
		super().__init__(message)


def fail(code: str, message: str = "", detail: dict | None = None) -> None:
	if code not in ERROR_CODES:
		raise ValueError(
			f"{code!r} is not part of the PLN-CHG-001 v1.12 §9 error contract. "
			f"Map the condition onto one of: {', '.join(sorted(ERROR_CODES))}."
		)
	raise ProcurementPlanningError(code, message or MESSAGES[code], detail)
