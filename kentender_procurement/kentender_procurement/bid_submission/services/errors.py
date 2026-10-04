# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable Bid Submission service errors (BDS-CHG-001 v0.8 §8).

§8 is a closed set of thirty-four codes, each with its user-visible
sentence. `fail()` refuses any code outside it: an invented code is a defect
in the caller, not a new error type. A user-correctable input is returned as
data (`field_errors`, AGENTS.md section 6.10) and never raised. A record the
actor may not see is masked as Not found and never confirmed (§8
"Record-existence masking"). Tenders, STD and Supplier Account codes are
remapped at the gateway boundary, never re-raised."""

from __future__ import annotations

import frappe

MESSAGES: dict[str, str] = {
	"BDS_TENDER_NOT_FOUND": "Tender not found.",
	"BDS_TENDER_NOT_OPEN": "This Tender is not accepting bids.",
	"BDS_SIGN_IN_REQUIRED": "Sign in to start or continue a bid.",
	"BDS_ACCOUNT_REQUIRED": "Set up your supplier account before starting a bid.",
	"BDS_ACCOUNT_SUSPENDED": "This supplier account cannot submit bids.",
	"BDS_ARRANGEMENT_INVALID": "Check the supplier or joint-venture information.",
	"BDS_NOTICE_CONTACT_REQUIRED": "Choose a verified email for Tender notices.",
	"BDS_RESPONSIBILITY_REQUIRED": "An Authorised Signatory must complete this action.",
	"BDS_DEFINITION_UNSUPPORTED": "This bid format is not available.",
	"BDS_ADDENDUM_REVIEW_REQUIRED": "Review the latest addendum and the affected bid responses.",
	"BDS_CLARIFICATION_DEADLINE_PASSED": "The clarification deadline has passed.",
	"BDS_CLARIFICATION_NOT_REGISTERED": "Start a bid before asking a question about this Tender.",
	"BDS_PORTAL_INFORMATION_UNAVAILABLE": "Supplier support information is temporarily unavailable.",
	"BDS_FIELD_INVALID": "Check the highlighted value.",
	"BDS_UNKNOWN_RESPONSE": "This response is not part of the published Tender.",
	"BDS_EVIDENCE_REQUIRED": "Add the required supporting evidence.",
	"BDS_EVIDENCE_REJECTED": "This file could not be accepted.",
	"BDS_SECURITY_PROOF_REQUIRED": "Add the required tender-security proof.",
	"BDS_SECURITY_ORIGINAL_OUTSTANDING": "The physical tender-security original has not been recorded as received.",
	"BDS_MUST_FIX": "Fix the listed items before submitting.",
	"BDS_STALE_VERSION": "Another person changed this bid. Reload before continuing.",
	"BDS_SIGNATORY_REQUIRED": "Only an active Authorised Signatory can submit this bid.",
	"BDS_SIGNATORY_CERTIFICATE_REQUIRED": "A valid digital signature certificate is required before you can submit.",
	"BDS_SIGNATURE_UNAVAILABLE": "Digital signing is temporarily unavailable. Your bid remains saved and has not been submitted.",
	"BDS_SIGNATURE_INVALID": "The digital signature could not be verified for this bid.",
	"BDS_PRODUCTION_SUBMISSION_NOT_ENABLED": "Electronic bid submission is not available yet. Your bid remains saved and has not been submitted.",
	"BDS_SUBMISSION_SERVICE_UNAVAILABLE": "Electronic submission is temporarily unavailable. Your bid remains saved.",
	"BDS_CUSTODY_REJECTED": "The tender box rejected this attempt. Your bid remains saved and was not submitted.",
	"BDS_SUBMISSION_UNCERTAIN": "Submission confirmation is still pending. Do not submit again.",
	"BDS_DEADLINE_PASSED": "The submission deadline has passed. This bid was not submitted.",
	"BDS_ALREADY_SUBMITTED": "This bid Version has already been submitted.",
	"BDS_REPLACEMENT_CONFLICT": "A newer submitted bid already exists.",
	"BDS_WITHDRAWAL_BLOCKED": "This bid can no longer be withdrawn because the deadline has passed.",
	"BDS_IDEMPOTENCY_CONFLICT": "This request was already used with different information. Stop and refresh.",
}
ERROR_CODES: frozenset[str] = frozenset(MESSAGES)


class BidSubmissionError(frappe.ValidationError):
	def __init__(self, code: str, message: str, detail: dict | None = None):
		self.code = code
		self.detail = detail or {}
		super().__init__(message)
		# The portal picks the inline state from the code, never from message
		# text; the response carries it beside Frappe's own error fields.
		response = getattr(getattr(frappe, "local", None), "response", None)
		if response is not None:
			try:
				response["kt_error_code"] = code
				response["kt_error_message"] = message
				response["kt_error_detail"] = self.detail
			except Exception:
				pass


def fail(code: str, message: str = "", detail: dict | None = None) -> None:
	if code not in ERROR_CODES:
		raise ValueError(
			f"{code!r} is not part of the BDS-CHG-001 v0.8 §8 error contract. "
			f"Map the condition onto one of: {', '.join(sorted(ERROR_CODES))}."
		)
	raise BidSubmissionError(code, message or MESSAGES[code], detail)


def field_errors(errors: dict[str, str], code: str = "BDS_FIELD_INVALID") -> dict:
	"""User-correctable input, returned as data (nothing saved). `code` is the
	§8 code whose treatment links the exact field (for example
	`BDS_ARRANGEMENT_INVALID`, `BDS_NOTICE_CONTACT_REQUIRED`)."""
	if code not in ERROR_CODES:
		raise ValueError(f"{code!r} is not part of the BDS-CHG-001 v0.8 §8 error contract.")
	return {"ok": False, "code": code, "message": MESSAGES[code], "errors": dict(errors)}
