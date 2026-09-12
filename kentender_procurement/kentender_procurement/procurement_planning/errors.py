# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable Procurement Planning service errors (PLN-CHG-001 v1.18 §8).

§8 defines a closed set of 51 codes with their user-facing messages;
`fail()` refuses any code outside the contract — an invented code is a defect
in the caller, not a new error type. The set and messages are generated from
the specification table and pinned by `test_planning_v118_schema`.

Removed by v1.18: the reservation-release code (Planning holds no
reservation) and the three fixed-number timing codes, replaced by
`PLN_PROFILE_PERIOD_INVALID` whose `detail` carries the resolved rule as
labelled parameters (period, rule, limit, offered) — never a universal
guessed constant.

Unauthorised detail and task reads do not use these codes at all: they raise
the same not-found as a nonexistent record (`planning_authorization.not_found()`).
AUTH-ADR-001 v1.6 §10 codes are remapped onto this set at the service boundary
and never reach a client.
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
		"PLN_CORRECTION_COHORT_VIOLATION",
		"PLN_DISSOLUTION_BLOCKED",
		"PLN_OBJECTIVE_INELIGIBLE",
		"PLN_STRATEGY_REVIEW_CHANGED",
		"PLN_SCHEDULE_INVALID",
		"PLN_PROFILE_PERIOD_INVALID",
		"PLN_DELIVERY_BOUNDARY_INSUFFICIENT",
		"PLN_DELIVERY_PERIOD_REQUIRED",
		"PLN_MULTI_YEAR_UNSUPPORTED",
		"PLN_FORECAST_REASON_REQUIRED",
		"PLN_CASCADE_INCLUDES_ACTUAL_MILESTONE",
		"PLN_BASELINE_LOCKED",
		"PLN_ACTUAL_NOT_WRITABLE",
		"PLN_PLAN_NOT_AFFORDABLE",
		"PLN_FINANCE_STALE",
		"PLN_REVIEW_STALE",
		"PLN_SEGREGATION_CONFLICT",
		"PLN_STATUTORY_ROUTE_UNCONFIGURED",
		"PLN_COLLECTIVE_RESOLUTION_REQUIRED",
		"PLN_PLAN_CONTENTS_INCOMPLETE",
		"PLN_METHOD_NOT_ADMISSIBLE",
		"PLN_METHOD_EVIDENCE_REQUIRED",
		"PLN_RESERVATION_REQUIRED",
		"PLN_RESERVATION_SHORTFALL",
		"PLN_REFERENCE_UNAVAILABLE",
		"PLN_MONEY_PRECISION_INVALID",
		"PLN_ITEM_SCOPE_LOCKED",
		"PLN_ITEM_AUTHORISATION_HELD",
		"PLN_CORRECTION_NOT_ACTIVE",
		"PLN_REMOVAL_BLOCKED",
		"PLN_ALLOWANCE_EXCEEDED",
		"PLN_TREASURY_EVIDENCE_REQUIRED",
		"PLN_PUBLICATION_FAILED",
		"PLN_PUBLICATION_UNKNOWN",
		"PLN_PUBLICATION_HELD",
		"PLN_PUBLICATION_ACK_MISMATCH",
		"PLN_WITHDRAWAL_NOT_PERMITTED",
		"PLN_ACTIVATION_HELD",
		"PLN_LATE_EXPLANATION_REQUIRED",
		"PLN_STALE_WRITE",
		"PLN_IDEMPOTENCY_CONFLICT",
	}
)

MESSAGES: dict[str, str] = {
	"PLN_NO_CONTEXT": "Procurement Planning is not available for your current responsibilities or configuration.",
	"PLN_WINDOW_CLOSED": "The initial departmental-plan submission window is closed.",
	"PLN_NEED_COVERAGE_INCOMPLETE": "Account for every accepted Need within this submission’s coverage before submitting.",
	"PLN_ENTRY_INCOMPLETE": "Complete the highlighted requirement fields before submitting.",
	"PLN_BUDGET_LINE_INELIGIBLE": "Select an Active Procurement Budget Line available to this department and financial year.",
	"PLN_DPP_STALE": "This departmental plan changed; reload and review the current Submission.",
	"PLN_CLASSIFICATION_INCOMPLETE": "Classify every proceeding requirement before accepting the plan.",
	"PLN_SOURCE_UNAVAILABLE": "One or more selected requirements are no longer available for item formation.",
	"PLN_SOURCE_INCOMPATIBLE": "The selected requirements cannot form one Plan Item; create separate items.",
	"PLN_SOURCE_CORRECTION_REQUIRED": "A departmental source changed; dissolve and re-form the affected Draft item before continuing.",
	"PLN_CORRECTION_COHORT_VIOLATION": "This correction cannot include an unrelated requirement; use a subsequent plan update.",
	"PLN_DISSOLUTION_BLOCKED": "This Plan Item is no longer in a mutable Draft and cannot be dissolved.",
	"PLN_OBJECTIVE_INELIGIBLE": "Select an Active Strategic Objective valid for this Plan.",
	"PLN_STRATEGY_REVIEW_CHANGED": "The Strategy selection no longer matches the reviewed evidence; return the Plan for correction.",
	"PLN_SCHEDULE_INVALID": "Correct the highlighted schedule to meet its applicable sequencing and period rules.",
	"PLN_PROFILE_PERIOD_INVALID": "The highlighted period does not meet the selected procedure’s rules.",
	"PLN_DELIVERY_BOUNDARY_INSUFFICIENT": "Estimated completion exceeds the required-by date; review the schedule or correct the source through its departmental process.",
	"PLN_DELIVERY_PERIOD_REQUIRED": "Enter the estimated delivery or implementation period in calendar days.",
	"PLN_MULTI_YEAR_UNSUPPORTED": "Multi-year procurement is not supported in this release.",
	"PLN_FORECAST_REASON_REQUIRED": "State why the forecast date is changing before saving.",
	"PLN_CASCADE_INCLUDES_ACTUAL_MILESTONE": "A milestone with a recorded actual cannot be reforecast.",
	"PLN_BASELINE_LOCKED": "The submitted baseline cannot be edited; prepare a governed correction or successor.",
	"PLN_ACTUAL_NOT_WRITABLE": "Actual dates must come from the process that recorded the event.",
	"PLN_PLAN_NOT_AFFORDABLE": "The planned total exceeds the approved amount on one or more Budget Lines.",
	"PLN_FINANCE_STALE": "Funding confirmation is no longer current; use the available reassessment or correction action.",
	"PLN_REVIEW_STALE": "This task has changed; reload before deciding.",
	"PLN_SEGREGATION_CONFLICT": "You cannot make this decision because you performed an incompatible earlier action.",
	"PLN_STATUTORY_ROUTE_UNCONFIGURED": "Configure the applicable statutory approval route before submitting this Plan.",
	"PLN_COLLECTIVE_RESOLUTION_REQUIRED": "Enter the collective resolution reference for this decision.",
	"PLN_PLAN_CONTENTS_INCOMPLETE": "Complete the highlighted package, structure and evidence fields before continuing.",
	"PLN_METHOD_NOT_ADMISSIBLE": "The selected method does not meet the applicable procurement conditions.",
	"PLN_METHOD_EVIDENCE_REQUIRED": "Provide the evidence required for the selected procurement method.",
	"PLN_RESERVATION_REQUIRED": "Select the planned reservation designation; choose None where no designation applies.",
	"PLN_RESERVATION_SHORTFALL": "The required reservation allocation is not met; review the displayed shortfall.",
	"PLN_REFERENCE_UNAVAILABLE": "Required procurement rules or their calculation basis are missing or unverified.",
	"PLN_MONEY_PRECISION_INVALID": "Enter an amount using the supported currency precision.",
	"PLN_ITEM_SCOPE_LOCKED": "This Plan Item already has an authorised Requisition. Create a separate Plan Item for the additional requirement.",
	"PLN_ITEM_AUTHORISATION_HELD": "New Requisition authorisations for this item are on hold while correction requests remain unresolved.",
	"PLN_CORRECTION_NOT_ACTIVE": "Resolve this request only after the correcting Plan Version is Active.",
	"PLN_REMOVAL_BLOCKED": "This item has downstream use and cannot be removed through Planning.",
	"PLN_ALLOWANCE_EXCEEDED": "The requested quantity or value exceeds the remaining original allowance.",
	"PLN_TREASURY_EVIDENCE_REQUIRED": "Record submission evidence for this exact approved Plan before website publication.",
	"PLN_PUBLICATION_FAILED": "Publication failed; the approved content is preserved for a safe retry.",
	"PLN_PUBLICATION_UNKNOWN": "The publication result is unknown and must be reconciled before withdrawal or replacement.",
	"PLN_PUBLICATION_HELD": "Publication is on hold; review the recorded issue before continuing.",
	"PLN_PUBLICATION_ACK_MISMATCH": "The publication evidence does not match this approved Plan.",
	"PLN_WITHDRAWAL_NOT_PERMITTED": "Withdrawal requires confirmed non-publication and no outstanding transmission.",
	"PLN_ACTIVATION_HELD": "Publication is confirmed, but this Version cannot be activated until the recorded issues are corrected.",
	"PLN_LATE_EXPLANATION_REQUIRED": "Explain why this initial Plan is being adopted after the financial year began.",
	"PLN_STALE_WRITE": "Another user changed this record; reload before continuing.",
	"PLN_IDEMPOTENCY_CONFLICT": "This request reference was already used for different content.",
}


class ProcurementPlanningError(frappe.ValidationError):
	def __init__(self, code: str, message: str, detail: dict | None = None):
		self.code = code
		self.detail = detail or {}
		super().__init__(message)


def fail(code: str, message: str = "", detail: dict | None = None) -> None:
	if code not in ERROR_CODES:
		raise ValueError(
			f"{code!r} is not part of the PLN-CHG-001 v1.18 §8 error contract. "
			f"Map the condition onto one of: {', '.join(sorted(ERROR_CODES))}."
		)
	raise ProcurementPlanningError(code, message or MESSAGES[code], detail)
