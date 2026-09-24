# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable Procurement Requisitions service errors (REQ-CHG-001 v1.11 §11).

§11 defines a closed set of codes. They are stable service results; `fail()`
refuses any code outside the contract — an invented code is a defect in the
caller, not a new error type. `REQ_ROLE_REQUIRED` and `REQ_SCOPE_DENIED` are
deliberately absent (§11): a record outside the actor's authorised
responsibility returns `REQ_NOT_FOUND`, the same non-disclosure
`requisition_authorization.not_found()` already uses.
"""

from __future__ import annotations

import frappe

MESSAGES: dict[str, str] = {
	"REQ_NOT_FOUND": "Requisition not found",
	"REQ_RESPONSIBILITY_REQUIRED": "You do not have the required responsibility for this action.",
	"REQ_PLAN_INELIGIBLE": "This approved purchase is not currently eligible. Refresh Planning status.",
	"REQ_BALANCE_CHANGED": "The amount still available from the approved purchase changed. Refresh the amounts requested.",
	"REQ_OPEN_EXISTS": "This Plan Item already has an open Requisition.",
	"REQ_CONTROL_INVALID": "A value does not match its released type, range or options.",
	"REQ_QUANTITY_MISMATCH": "Item and requested quantities do not reconcile.",
	"REQ_BATCH_ITEM_INVALID": "One or more approved-requirement rows cannot be created or updated as one set. Nothing was changed.",
	"REQ_STANDARD_PROPOSAL_STALE": "The standard requirements changed after they were shown. Review them again before using them.",
	"REQ_PRODUCT_UNSUPPORTED": "This purchase is not supported by the installed IT-equipment Tender format.",
	"REQ_RESERVATION_RULE_UNAVAILABLE": "The applicable reservation rule is not ready for this purchase. Ask your KenTender administrator to complete the rule in System setup.",
	"REQ_REQUIREMENT_RESTRICTIVE": "A brand or restrictive term lacks permitted equivalent treatment.",
	"REQ_FILE_INVALID": "File type, size, readability, digest or row-link rule failed.",
	"REQ_BLOCKING_FINDINGS": "This requisition has issues that must be resolved first.",
	"REQ_STALE_VERSION": "This requisition changed after you opened it. Review the latest version before saving.",
	"REQ_SOD_BLOCKED": "You may not complete this decision on this Version.",
	"REQ_HANDOFF_CONSUMED": "Tender Preparation has already started. This authorisation can no longer be revoked.",
	"REQ_FUNDING_UNAVAILABLE": "Cannot authorise — insufficient funding.",
	"REQ_DEPARTMENT_NOT_CONTRIBUTING": "This department did not contribute to the approved purchase.",
	"REQ_IDEMPOTENCY_CONFLICT": "This request differs from the original attempt. Check the current requisition before trying again.",
	# Planning's own codes, passed through with Planning's exact message (§11).
	"PLN_ITEM_AUTHORISATION_HELD": "New Requisition authorisations for this item are on hold while correction requests remain unresolved.",
	"PLN_ITEM_SCOPE_LOCKED": "This Plan Item already has an authorised Requisition. Create a separate Plan Item for the additional requirement.",
	"REQ_CORRECTION_OUTCOME_PENDING": "Planning response is temporarily unavailable. The stopped requisition has not changed.",
	"REQ_CORRECTION_EVENT_INVALID": "The Planning correction outcome could not be verified. Nothing was changed.",
	"REQ_MONEY_PRECISION_INVALID": "Enter an exact amount in KES with at most 2 decimal places.",
	"REQ_QUANTITY_PRECISION_INVALID": "Enter a whole number of Each.",
	"REQ_LEAD_RECERTIFICATION_REQUIRED": "This requisition must be certified and submitted by the new submitting department before authorisation.",
	"REQ_OWNER_VALIDATION_UNAVAILABLE": "Planning or Budget could not confirm this action. Nothing was committed.",
	"REQ_HANDOFF_CONFLICT": "This handoff is already consumed by another Tender or has been revoked.",
}

#: REQ-CHG-001 v1.11 §11 — the closed error contract.
ERROR_CODES: frozenset[str] = frozenset(MESSAGES)


class ProcurementRequisitionsError(frappe.ValidationError):
	def __init__(self, code: str, message: str, detail: dict | None = None):
		self.code = code
		self.detail = detail or {}
		super().__init__(message)


def fail(code: str, message: str = "", detail: dict | None = None) -> None:
	if code not in ERROR_CODES:
		raise ValueError(
			f"{code!r} is not part of the REQ-CHG-001 v1.11 §11 error contract. "
			f"Map the condition onto one of: {', '.join(sorted(ERROR_CODES))}."
		)
	text = message or MESSAGES[code]
	# The browser needs the code and detail (which row, which field), not only
	# the sentence: they travel on the message log, which Frappe returns as
	# `_server_messages` on the failed request (the call wrapper reads them).
	log = getattr(frappe.local, "message_log", None)
	if log is not None:
		log.append({"message": text, "title": code, "indicator": "red", "kt_req": {"code": code, "detail": _jsonable(detail or {})}})
	raise ProcurementRequisitionsError(code, text, detail)


def _jsonable(value):
	import json

	return json.loads(json.dumps(value, default=str))
