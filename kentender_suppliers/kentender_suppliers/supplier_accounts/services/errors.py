# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Supplier Account part of the BDS-CHG-001 v0.8 §8 error contract.

Supplier Accounts raises only these codes; their words are §8's own except
where §8's text names a bid for an Account condition (marked ACCOUNT_TEXT,
new copy for review in FU-V08-26). A user-correctable input is returned as
data — `{"ok": False, "errors": {field: message}}` (AGENTS.md section 6.10)
— and never raised. A record the actor may not see is masked as Not found,
never confirmed (§8 "Record-existence masking")."""

from __future__ import annotations

import frappe

MESSAGES: dict[str, str] = {
	"BDS_SIGN_IN_REQUIRED": "Sign in to start or continue a bid.",
	"BDS_ACCOUNT_REQUIRED": "Set up your supplier account before starting a bid.",
	"BDS_ACCOUNT_SUSPENDED": "This supplier account cannot submit bids.",
	"BDS_FIELD_INVALID": "Check the highlighted value.",
	"BDS_RESPONSIBILITY_REQUIRED": "An Authorised Signatory must complete this action.",
	"BDS_EVIDENCE_REJECTED": "This file could not be accepted.",
	"BDS_IDEMPOTENCY_CONFLICT": "This request was already used with different information. Stop and refresh.",
	# ACCOUNT_TEXT: §8's BDS_STALE_VERSION names a bid.
	"BDS_STALE_VERSION": "Another person changed this account. Reload before continuing.",
}
NOT_FOUND_TEXT = "This supplier account is unavailable or you do not have permission to view it."


class AccountError(frappe.ValidationError):
	def __init__(self, code: str, message: str, detail: dict | None = None):
		self.code = code
		self.detail = detail or {}
		super().__init__(message)
		response = getattr(getattr(frappe, "local", None), "response", None)
		if response is not None:
			try:
				response["kt_error_code"] = code
				response["kt_error_message"] = message
				response["kt_error_detail"] = self.detail
			except Exception:
				pass


def fail(code: str, message: str = "", detail: dict | None = None) -> None:
	if code not in MESSAGES:
		raise ValueError(f"{code!r} is not a Supplier Account error code. Use one of: {', '.join(sorted(MESSAGES))}.")
	raise AccountError(code, message or MESSAGES[code], detail)


def not_found() -> None:
	raise frappe.DoesNotExistError(NOT_FOUND_TEXT)


def field_errors(errors: dict[str, str]) -> dict:
	"""User-correctable input, returned as data (nothing saved)."""
	return {"ok": False, "code": "BDS_FIELD_INVALID", "message": MESSAGES["BDS_FIELD_INVALID"], "errors": dict(errors)}
