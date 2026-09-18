# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable Tenders service errors (TPR-CHG-001 v0.8 §8).

§8 defines a closed set of twenty-eight codes. They are stable service
results; `fail()` refuses any code outside the contract — an invented code is
a defect in the caller, not a new error type. Record-existence masking follows
AUTH-ADR-001: a record outside the actor's authorised responsibility is
`TND_NOT_FOUND`, never a scope code. Sibling-module codes (`AUTH_*`, `REQ_*`,
`PLN_*`, `CFG_*`) are remapped at the gateway boundary, never re-raised.
"""

from __future__ import annotations

import frappe

ERROR_CODES: frozenset[str] = frozenset(
	{
		"TND_NOT_FOUND",
		"TND_RESPONSIBILITY_REQUIRED",
		"TND_HANDOFF_INVALID",
		"TND_HANDOFF_CONFLICT",
		"TND_PRODUCT_UNSUPPORTED",
		"TND_TEMPLATE_UNAVAILABLE",
		"TND_CONTROL_INVALID",
		"TND_INHERITED_EDIT",
		"TND_MAPPING_INCOMPLETE",
		"TND_FILE_INVALID",
		"TND_MUST_FIX",
		"TND_STALE_VERSION",
		"TND_SOD_BLOCKED",
		"TND_PUBLICATION_STARTED",
		"TND_PUBLICATION_RULE_UNAVAILABLE",
		"TND_PUBLICATION_PERIOD_INVALID",
		"TND_PUBLICATION_CONFIRMATION_INCOMPLETE",
		"TND_PUBLICATION_EVIDENCE_INVALID",
		"TND_PUBLICATION_DIGEST_MISMATCH",
		"TND_PUBLICATION_ALREADY_CONFIRMED",
		"TND_PUBLICATION_WITHDRAWAL_BLOCKED",
		"TND_ADDENDUM_STALE",
		"TND_ADDENDUM_MATERIAL",
		"TND_ADDENDUM_DEADLINE_REQUIRED",
		"TND_INQUIRY_LATE",
		"TND_CANCELLATION_GROUND_INVALID",
		"TND_CANCELLED",
		"TND_IDEMPOTENCY_CONFLICT",
	}
)

MESSAGES: dict[str, str] = {
	"TND_NOT_FOUND": "Tender not found.",
	"TND_RESPONSIBILITY_REQUIRED": "This action requires a responsibility you do not hold.",
	"TND_HANDOFF_INVALID": "The authorised requisition is no longer available to start this Tender.",
	"TND_HANDOFF_CONFLICT": "A Tender has already been started for this requisition.",
	"TND_PRODUCT_UNSUPPORTED": "This requisition is not supported by the current IT-equipment Tender format.",
	"TND_TEMPLATE_UNAVAILABLE": "The standard IT-equipment Tender format is not available.",
	"TND_CONTROL_INVALID": "Check the highlighted value.",
	"TND_INHERITED_EDIT": "Authorised requisition information cannot be changed here.",
	"TND_MAPPING_INCOMPLETE": "A published requirement is not fully connected to supplier response, evaluation and contract records.",
	"TND_FILE_INVALID": "A supporting file could not be verified.",
	"TND_MUST_FIX": "Fix the listed items before continuing.",
	"TND_STALE_VERSION": "Another user changed this Tender. Reload before continuing.",
	"TND_SOD_BLOCKED": "Another authorised officer must complete this decision.",
	"TND_PUBLICATION_STARTED": "Publication has started. This Tender can no longer be reopened.",
	"TND_PUBLICATION_RULE_UNAVAILABLE": "The publication rule is not configured for this Tender.",
	"TND_PUBLICATION_PERIOD_INVALID": "The submission deadline does not allow the required preparation period after publication.",
	"TND_PUBLICATION_CONFIRMATION_INCOMPLETE": "Complete the publication confirmation for this channel.",
	"TND_PUBLICATION_EVIDENCE_INVALID": "The publication evidence could not be accepted.",
	"TND_PUBLICATION_DIGEST_MISMATCH": "This confirmation does not match the approved Tender package.",
	"TND_PUBLICATION_ALREADY_CONFIRMED": "Publication through this channel is already confirmed.",
	"TND_PUBLICATION_WITHDRAWAL_BLOCKED": "Publication authorisation cannot be withdrawn because at least one channel is already confirmed.",
	"TND_ADDENDUM_STALE": "The published wording has changed. Reload before preparing this addendum.",
	"TND_ADDENDUM_MATERIAL": "This change is too significant for an addendum. Cancel and start a newly governed Tender if procurement must continue.",
	"TND_ADDENDUM_DEADLINE_REQUIRED": "Set a lawful revised submission deadline for this addendum.",
	"TND_INQUIRY_LATE": "The inquiry deadline has passed.",
	"TND_CANCELLATION_GROUND_INVALID": "Select an applicable cancellation ground.",
	"TND_CANCELLED": "This Tender has been cancelled and cannot accept further work.",
	"TND_IDEMPOTENCY_CONFLICT": "This request was already used with different information. Stop and refresh.",
}


class TendersError(frappe.ValidationError):
	def __init__(self, code: str, message: str, detail: dict | None = None):
		self.code = code
		self.detail = detail or {}
		super().__init__(message)


def fail(code: str, message: str = "", detail: dict | None = None) -> None:
	if code not in ERROR_CODES:
		raise ValueError(
			f"{code!r} is not part of the TPR-CHG-001 v0.8 §8 error contract. "
			f"Map the condition onto one of: {', '.join(sorted(ERROR_CODES))}."
		)
	raise TendersError(code, message or MESSAGES[code], detail)
