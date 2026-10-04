# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable Bid Evaluation errors (EVL-CHG-001 v0.4 §8), verbatim.

§8 is a closed set of fifteen blocking codes plus two nonblocking
conditions. The exact message is rendered with separate contextual detail
(names, dates, reasons and recovery). Every applicable guard reason is
returned together, with its owner and recovery, never as serial blockers
(§8 opening paragraph): collect them with `Guards` and raise once.
Proceedings errors are shown in Evaluation's words (`from_prc`;
`reconciliation/error_contract.md`)."""

from __future__ import annotations

from typing import Any

import frappe

MESSAGES: dict[str, str] = {
	"EVL_SOURCE_INCOMPLETE": "Some opened bid information could not be loaded.",
	"EVL_RULE_UNAVAILABLE": "This requirement needs review because its evaluation rule is unavailable.",
	"EVL_MEMBER_INELIGIBLE": "This person cannot serve on this evaluation committee.",
	"EVL_DECLARATION_REQUIRED": "Complete your declaration before viewing bids.",
	"EVL_MEMBERS_ABSENT": "All members of the current eligible committee must be present to record this conclusion.",
	"EVL_REPORT_INCOMPLETE": "Review the listed issues before sending the report for signing.",
	"EVL_TARGET_CHANGED": "The report changed. Review the latest version before signing.",
	"EVL_SIGNATURE_UNCONFIRMED": "Your signature has not been confirmed. Check its status before trying again.",
	"EVL_VERSION_CONFLICT": "This record changed while you were working. Refresh it and try again.",
	"EVL_REPLY_CLOSED": "This clarification is closed. Your saved reply has not been sent.",
	"EVL_SUSPENDED": "Evaluation is paused by the recorded instruction.",
	"EVL_CANCELLED": "Evaluation ended",
	"EVL_REPORT_DELIVERY_FAILED": "The signed report could not be delivered.",
	"EVL_CLARIFICATION_NOTICE_FAILED": "The clarification notice could not be delivered.",
	"EVL_DECISION_STATUS_UNKNOWN": "The later decision could not be checked.",
}
#: §8 nonblocking conditions: shown through the same guidance contract, never
#: a refusal, a lifecycle state or an automatic rejection.
CONDITIONS: dict[str, str] = {
	"EVL_REPLY_OVERDUE": "The reply deadline has passed.",
	"EVL_EVALUATION_OVERDUE": "The evaluation deadline has passed.",
}
ERROR_CODES: frozenset[str] = frozenset(MESSAGES)

#: PRC-CHG-001 v0.9 §8 → Evaluation copy (reconciliation/error_contract.md).
PRC_MAP: dict[str, str] = {
	"PRC_VERSION_CONFLICT": "EVL_VERSION_CONFLICT",
	"PRC_TARGET_CHANGED": "EVL_TARGET_CHANGED",
	"PRC_PROOF_UNVERIFIED": "EVL_SIGNATURE_UNCONFIRMED",
	"PRC_START_BLOCKED": "EVL_VERSION_CONFLICT",
	"PRC_OWNER_UNAVAILABLE": "EVL_VERSION_CONFLICT",
	"PRC_ALREADY_FINALIZED": "EVL_VERSION_CONFLICT",
	"PRC_MEMBER_REQUIRED": "EVL_DECLARATION_REQUIRED",
}


class EvaluationError(frappe.ValidationError):
	"""`reasons` lists every applicable guard: [{code, message, detail}]."""

	def __init__(self, code: str, message: str, detail: dict | None = None, reasons: list[dict[str, Any]] | None = None):
		self.code = code
		self.detail = detail or {}
		self.reasons = reasons or [{"code": code, "message": message, "detail": self.detail}]
		super().__init__(message)


def message(code: str) -> str:
	if code in MESSAGES:
		return MESSAGES[code]
	if code in CONDITIONS:
		return CONDITIONS[code]
	raise ValueError(f"{code!r} is not part of the EVL-CHG-001 v0.4 §8 error contract.")


def reason(code: str, **detail) -> dict[str, Any]:
	if code not in ERROR_CODES:
		raise ValueError(f"{code!r} is not a blocking EVL-CHG-001 v0.4 §8 code.")
	return {"code": code, "message": MESSAGES[code], "detail": detail}


def fail(code: str, detail: dict | None = None, **facts) -> None:
	one = reason(code, **{**(detail or {}), **facts})
	raise EvaluationError(code, one["message"], one["detail"])


class Guards:
	"""Collect every applicable refusal, then raise them together."""

	def __init__(self) -> None:
		self.reasons: list[dict[str, Any]] = []

	def add(self, code: str, **detail) -> "Guards":
		self.reasons.append(reason(code, **detail))
		return self

	def __bool__(self) -> bool:
		return bool(self.reasons)

	def raise_if_any(self) -> None:
		if self.reasons:
			first = self.reasons[0]
			raise EvaluationError(first["code"], first["message"], first["detail"], self.reasons)


def from_prc(code: str, detail: dict | None = None) -> str:
	"""The Evaluation code for a Proceedings error; a missing roster presence is
	EVL_MEMBERS_ABSENT, any other missing evidence EVL_REPORT_INCOMPLETE."""
	if code == "PRC_EVIDENCE_INCOMPLETE":
		return "EVL_MEMBERS_ABSENT" if (detail or {}).get("absent") else "EVL_REPORT_INCOMPLETE"
	return PRC_MAP.get(code, "EVL_VERSION_CONFLICT")


def as_data(exc: EvaluationError) -> dict[str, Any]:
	"""A refusal returned as data by the API (plan D3, BOP precedent)."""
	return {"ok": False, "code": exc.code, "message": str(exc), "detail": exc.detail, "reasons": exc.reasons}


class InputError(frappe.ValidationError):
	"""A form value to correct (a missing reason, an unknown choice). Not a §8
	guard: it is shown beside the field and the rest of the form is kept."""

	def __init__(self, fields: dict[str, str]):
		self.code = "EVL_INPUT"
		self.fields = fields
		self.detail = {"fields": fields}
		self.reasons = []
		super().__init__("; ".join(fields.values()))


def invalid(fields: dict[str, str]) -> None:
	if fields:
		raise InputError(fields)
