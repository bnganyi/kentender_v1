# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable Tender Preparation service errors (TPR-CHG-001 v0.6 §11.3).

§11.3 defines a closed set of sixteen codes. They are stable service results;
`fail()` refuses any code outside the contract — an invented code is a defect
in the caller, not a new error type. The two codes v0.6 removed (a bare-role
code and a PE/FY-scope code) are deliberately absent (§11.3): a record
outside the actor's authorised responsibility returns `TPR_NOT_FOUND`, the
same non-disclosure `tender_authorization.not_found()` uses.
"""

from __future__ import annotations

import frappe

ERROR_CODES: frozenset[str] = frozenset(
	{
		"TPR_NOT_FOUND",
		"TPR_RESPONSIBILITY_REQUIRED",
		"TPR_HANDOFF_INVALID",
		"TPR_HANDOFF_CONSUMED",
		"TPR_PRODUCT_UNSUPPORTED",
		"TPR_TEMPLATE_UNAVAILABLE",
		"TPR_CONTROL_INVALID",
		"TPR_INHERITED_EDIT",
		"TPR_MAPPING_INCOMPLETE",
		"TPR_FILE_INVALID",
		"TPR_BLOCKING_FINDINGS",
		"TPR_STALE_VERSION",
		"TPR_SOD_BLOCKED",
		"TPR_PUBLICATION_CONSUMED",
		"TPR_IDEMPOTENCY_CONFLICT",
		"TPR_MILESTONE_ACTUAL_REJECTED",
	}
)

MESSAGES: dict[str, str] = {
	"TPR_NOT_FOUND": "Tender not found.",
	"TPR_RESPONSIBILITY_REQUIRED": "You do not have the required responsibility for this action.",
	"TPR_HANDOFF_INVALID": "The source Requisition is no longer available for Tender Preparation.",
	"TPR_HANDOFF_CONSUMED": "This Requisition is already linked to a Tender.",
	"TPR_PRODUCT_UNSUPPORTED": "This Requisition is not supported by the IT-equipment Tender pattern.",
	"TPR_TEMPLATE_UNAVAILABLE": "This Tender template is not available for new Tenders.",
	"TPR_CONTROL_INVALID": "A value does not match its exact control type, range or options.",
	"TPR_INHERITED_EDIT": "Inherited and generated values cannot be changed in Tender Preparation.",
	"TPR_MAPPING_INCOMPLETE": "A published structured row lacks a required downstream mapping.",
	"TPR_FILE_INVALID": "A linked file failed its security, readability, digest or treatment check.",
	"TPR_BLOCKING_FINDINGS": "Submission or approval has Blocking findings.",
	"TPR_STALE_VERSION": "Another user changed this Tender. Reload before continuing.",
	"TPR_SOD_BLOCKED": "The Procurement Officer who prepared this Version cannot approve it.",
	"TPR_PUBLICATION_CONSUMED": "Reopen is no longer permitted; use the later addendum process.",
	"TPR_IDEMPOTENCY_CONFLICT": "The same idempotency key was reused with a different request.",
	"TPR_MILESTONE_ACTUAL_REJECTED": "The publication acknowledgment could not be matched to an approved Tender awaiting consumption.",
}


class TenderPreparationError(frappe.ValidationError):
	def __init__(self, code: str, message: str, detail: dict | None = None):
		self.code = code
		self.detail = detail or {}
		super().__init__(message)


def fail(code: str, message: str = "", detail: dict | None = None) -> None:
	if code not in ERROR_CODES:
		raise ValueError(
			f"{code!r} is not part of the TPR-CHG-001 v0.6 §11.3 error contract. "
			f"Map the condition onto one of: {', '.join(sorted(ERROR_CODES))}."
		)
	raise TenderPreparationError(code, message or MESSAGES[code], detail)
