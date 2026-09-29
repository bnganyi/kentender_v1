# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable Proceedings errors (PRC-CHG-001 v0.9 §8).

§8 is a closed set of eight codes, each with its user-visible sentence.
`fail()` refuses any other code. The owner (Bid Opening) maps these to its
own copy (BOP-CHG-001 v0.10 §7.1 "Product vocabulary") and returns the
concrete guard reasons and fixes; the `detail` here carries the facts it
needs (missing events, missing targets, the state), never bid content."""

from __future__ import annotations

import frappe

MESSAGES: dict[str, str] = {
	"PRC_OWNER_UNAVAILABLE": "This opening record is not available.",
	"PRC_START_BLOCKED": "The opening session cannot start yet. Review the opening requirement shown here.",
	"PRC_MEMBER_REQUIRED": "You are not an appointed member for this opening.",
	"PRC_TARGET_CHANGED": "The opening record changed. Review the latest version before signing.",
	"PRC_PROOF_UNVERIFIED": "We could not verify your signature. Follow the steps shown here.",
	"PRC_EVIDENCE_INCOMPLETE": "Some opening details are still missing. Review the items shown here.",
	"PRC_VERSION_CONFLICT": "This record changed while you were working. Refresh it and try again.",
	"PRC_ALREADY_FINALIZED": "This record is final. Add a correction if a fact needs to change.",
}
ERROR_CODES: frozenset[str] = frozenset(MESSAGES)


class ProceedingsError(frappe.ValidationError):
	def __init__(self, code: str, message: str, detail: dict | None = None):
		self.code = code
		self.detail = detail or {}
		super().__init__(message)


def fail(code: str, detail: dict | None = None) -> None:
	if code not in ERROR_CODES:
		raise ValueError(f"{code!r} is not part of the PRC-CHG-001 v0.9 §8 error contract. Use one of: {', '.join(sorted(ERROR_CODES))}.")
	raise ProceedingsError(code, MESSAGES[code], detail)


def unverified(detail: dict) -> dict:
	"""A failed proof is committed evidence (PRC-CHG-001 v0.9 §12), so it is
	returned as data rather than raised and rolled back."""
	return {"ok": False, "code": "PRC_PROOF_UNVERIFIED", "message": MESSAGES["PRC_PROOF_UNVERIFIED"], **detail}
