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
		"PLN_CLASSIFICATION_UNCHANGED",
		"PLN_CLASSIFICATION_CORRECTION_STALE",
		"PLN_CLASSIFICATION_CORRECTION_BLOCKED",
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
		# PLN-CHG-001 v1.23 §8 dropped these two from the user-facing table with
		# the forecast facility (PLN23-CHG-001). They stay registered only so the
		# dormant cascade code in `schedule.py` remains importable and its tests
		# keep passing; nothing routed, whitelisted or scheduled can reach them.
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
	"PLN_NO_CONTEXT": "Procurement Planning is not available for your responsibilities or the current setup.",
	"PLN_WINDOW_CLOSED": "Initial departmental-plan submissions are closed.",
	"PLN_NEED_COVERAGE_INCOMPLETE": "Include each required departmental need or record why it is not included this year.",
	"PLN_ENTRY_INCOMPLETE": "Complete the highlighted requirement fields before submitting.",
	"PLN_BUDGET_LINE_INELIGIBLE": "Choose a budget line available to this department for this financial year.",
	"PLN_DPP_STALE": "This departmental plan has changed. Refresh before continuing.",
	"PLN_CLASSIFICATION_INCOMPLETE": "Choose a requirement type for each included requirement.",
	"PLN_CLASSIFICATION_UNCHANGED": "Choose a different requirement type to correct this classification.",
	"PLN_CLASSIFICATION_CORRECTION_STALE": "This classification was already corrected. Refresh before continuing.",
	"PLN_CLASSIFICATION_CORRECTION_BLOCKED": "This classification cannot be corrected through this action. Follow the source, plan or procurement correction shown.",
	"PLN_SOURCE_UNAVAILABLE": "One or more selected requirements are no longer available to add.",
	"PLN_SOURCE_INCOMPATIBLE": "These requirements cannot be combined. Add them as separate purchases.",
	"PLN_SOURCE_CORRECTION_REQUIRED": "A departmental requirement has changed. Review the change before rebuilding the affected draft purchase.",
	"PLN_CORRECTION_COHORT_VIOLATION": "This requirement belongs in a later update. It cannot be added to the current correction.",
	"PLN_DISSOLUTION_BLOCKED": "This item can no longer be removed from the draft.",
	"PLN_OBJECTIVE_INELIGIBLE": "Choose a strategic objective currently available for this plan.",
	"PLN_STRATEGY_REVIEW_CHANGED": "The selected strategy has changed since submission. Return the plan for correction.",
	"PLN_SCHEDULE_INVALID": "Review the highlighted dates and the rule shown for them.",
	"PLN_PROFILE_PERIOD_INVALID": "The highlighted period does not meet the procurement rule shown.",
	"PLN_DELIVERY_BOUNDARY_INSUFFICIENT": "Estimated completion is after the department’s required date. Review the schedule or request a departmental correction.",
	"PLN_DELIVERY_PERIOD_REQUIRED": "Enter the estimated delivery or implementation period in calendar days.",
	"PLN_MULTI_YEAR_UNSUPPORTED": "Multi-year procurement is not supported in this release.",
	"PLN_BASELINE_LOCKED": "This submitted plan cannot be edited. Use the available correction or update action.",
	"PLN_ACTUAL_NOT_WRITABLE": "Actual dates must come from the process that recorded the event.",
	"PLN_PLAN_NOT_AFFORDABLE": "The planned amount exceeds the approved budget on the lines shown.",
	"PLN_FINANCE_STALE": "Funding needs to be checked again. Follow the action shown for this plan.",
	"PLN_REVIEW_STALE": "This review has changed. Refresh before deciding.",
	"PLN_SEGREGATION_CONFLICT": "You cannot make this decision because of your earlier role in this plan. An authorised, independent decision-maker is required.",
	"PLN_STATUTORY_ROUTE_UNCONFIGURED": "The plan’s approving authority is not configured. A KenTender administrator must complete this setting.",
	"PLN_COLLECTIVE_RESOLUTION_REQUIRED": "Enter the Board or Council resolution reference for this decision.",
	"PLN_PLAN_CONTENTS_INCOMPLETE": "Complete the highlighted purchase details and required evidence.",
	"PLN_METHOD_NOT_ADMISSIBLE": "The selected method does not meet the applicable procurement conditions.",
	"PLN_METHOD_EVIDENCE_REQUIRED": "Provide the evidence required for the selected procurement method.",
	"PLN_RESERVATION_REQUIRED": "Choose who this procurement is reserved for, or None if no designation applies.",
	"PLN_RESERVATION_SHORTFALL": "Reserved procurement is below the required amount. Review the shortfall shown.",
	"PLN_REFERENCE_UNAVAILABLE": "A required procurement rule or calculation basis is missing or unverified. The setting shown needs attention.",
	"PLN_MONEY_PRECISION_INVALID": "Enter the amount using the decimal places allowed for this currency.",
	"PLN_ITEM_SCOPE_LOCKED": "This item already has an authorised requisition. Add extra requirements as a separate item in a plan update.",
	"PLN_ITEM_AUTHORISATION_HELD": "New requisition authorisations are on hold for this item until its correction requests are resolved.",
	"PLN_CORRECTION_NOT_ACTIVE": "Record completion only after the corrected plan becomes the current plan.",
	"PLN_REMOVAL_BLOCKED": "This item is already used in procurement and cannot be removed through Planning.",
	"PLN_ALLOWANCE_EXCEEDED": "The requested quantity or amount exceeds what remains under the original plan item.",
	"PLN_TREASURY_EVIDENCE_REQUIRED": "Record evidence that this approved plan was sent to Treasury before website publication.",
	"PLN_PUBLICATION_FAILED": "The plan was not published. The approved document is unchanged.",
	"PLN_PUBLICATION_UNKNOWN": "We could not confirm whether publication succeeded. Check the existing attempt before trying again.",
	"PLN_PUBLICATION_HELD": "Publication is on hold. Review the issue shown.",
	"PLN_PUBLICATION_ACK_MISMATCH": "The publication confirmation does not match this approved plan.",
	"PLN_WITHDRAWAL_NOT_PERMITTED": "Withdrawal requires confirmation that the plan was not published and that no publication attempt is still pending.",
	"PLN_ACTIVATION_HELD": "The plan was published, but it is not available for new procurement. The issues shown must be corrected.",
	"PLN_LATE_EXPLANATION_REQUIRED": "Explain why this initial plan is being adopted after the financial year started.",
	"PLN_STALE_WRITE": "This record changed after you opened it. Refresh before continuing.",
	"PLN_IDEMPOTENCY_CONFLICT": "This action could not be processed. Refresh before trying again; contact support if the problem continues.",
	# PLN-CHG-001 v1.23 §8 removed both of these from the user-facing table with
	# the forecast facility (PLN23-CHG-001). Retained only so the dormant code
	# that raises them still imports; nothing routed can reach them.
	"PLN_FORECAST_REASON_REQUIRED": "State why the forecast date is changing before saving.",
	"PLN_CASCADE_INCLUDES_ACTUAL_MILESTONE": "This activity has an actual date recorded. Its expected date cannot be changed.",
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
