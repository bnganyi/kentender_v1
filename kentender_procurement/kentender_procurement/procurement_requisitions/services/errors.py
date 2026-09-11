# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable Procurement Requisitions service errors (REQ-CHG-001 v1.6 §11).

§11 defines a closed set of codes. They are stable service results; `fail()`
refuses any code outside the contract — an invented code is a defect in the
caller, not a new error type. `REQ_ROLE_REQUIRED` and `REQ_SCOPE_DENIED` are
deliberately absent (§11): a record outside the actor's authorised
responsibility returns `REQ_NOT_FOUND`, the same non-disclosure
`requisition_authorization.not_found()` already uses.
"""

from __future__ import annotations

import frappe

ERROR_CODES: frozenset[str] = frozenset(
	{
		"REQ_NOT_FOUND",
		"REQ_RESPONSIBILITY_REQUIRED",
		"REQ_PLAN_INELIGIBLE",
		"REQ_BALANCE_CHANGED",
		"REQ_OPEN_EXISTS",
		"REQ_CONTROL_INVALID",
		"REQ_QUANTITY_MISMATCH",
		"REQ_PRODUCT_UNSUPPORTED",
		"REQ_REQUIREMENT_RESTRICTIVE",
		"REQ_FILE_INVALID",
		"REQ_BLOCKING_FINDINGS",
		"REQ_STALE_VERSION",
		"REQ_SOD_BLOCKED",
		"REQ_HANDOFF_CONSUMED",
		"REQ_FUNDING_UNAVAILABLE",
		"REQ_DEPARTMENT_NOT_CONTRIBUTING",
		"REQ_IDEMPOTENCY_CONFLICT",
	}
)

MESSAGES: dict[str, str] = {
	"REQ_NOT_FOUND": "Requisition not found.",
	"REQ_RESPONSIBILITY_REQUIRED": "You do not have the required responsibility for this action.",
	"REQ_PLAN_INELIGIBLE": "This Plan Item is not currently eligible. Refresh Planning status.",
	"REQ_BALANCE_CHANGED": "Remaining quantity or value changed. Refresh the drawdown step.",
	"REQ_OPEN_EXISTS": "Another open Requisition exists for this Plan Item. Open it.",
	"REQ_CONTROL_INVALID": "A value does not match its released type, range or options.",
	"REQ_QUANTITY_MISMATCH": "Item and drawdown quantities do not reconcile.",
	"REQ_PRODUCT_UNSUPPORTED": "This Plan Item is not supported by the IT-equipment Requisition pattern.",
	"REQ_REQUIREMENT_RESTRICTIVE": "A brand or restrictive term lacks permitted equivalent treatment.",
	"REQ_FILE_INVALID": "File type, size, readability, digest or row-link rule failed.",
	"REQ_BLOCKING_FINDINGS": "Submission or authorisation has Blocking findings.",
	"REQ_STALE_VERSION": "Another user changed this Requisition. Reload before continuing.",
	"REQ_SOD_BLOCKED": "You may not complete this decision on this Version.",
	"REQ_HANDOFF_CONSUMED": "Authorisation cannot be revoked because Tender Preparation consumed it.",
	"REQ_FUNDING_UNAVAILABLE": "Budget funding is unavailable for one or more drawdown lines.",
	"REQ_DEPARTMENT_NOT_CONTRIBUTING": "This Organisation Unit is not among the Plan Item's contributing departments.",
	"REQ_IDEMPOTENCY_CONFLICT": "The same idempotency key was reused with a different request.",
}


class ProcurementRequisitionsError(frappe.ValidationError):
	def __init__(self, code: str, message: str, detail: dict | None = None):
		self.code = code
		self.detail = detail or {}
		super().__init__(message)


def fail(code: str, message: str = "", detail: dict | None = None) -> None:
	if code not in ERROR_CODES:
		raise ValueError(
			f"{code!r} is not part of the REQ-CHG-001 v1.6 §11 error contract. "
			f"Map the condition onto one of: {', '.join(sorted(ERROR_CODES))}."
		)
	raise ProcurementRequisitionsError(code, message or MESSAGES[code], detail)
