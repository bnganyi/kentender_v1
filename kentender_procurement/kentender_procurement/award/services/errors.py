# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable Award errors (AWD-CHG-001 v0.4 §8), verbatim.

§8 is a closed set of thirteen codes. The message is shown as written; names,
dates and recovery travel separately in `detail`. Every applicable reason is
returned together (collect with `Guards`, raise once). Messages never show
table names, payloads, hashes or stack traces (§8 last paragraph)."""

from __future__ import annotations

from typing import Any

import frappe

MESSAGES: dict[str, str] = {
	"AWD_SOURCE_INCOMPLETE": "The evaluation report is incomplete. The Head of Procurement has been notified.",
	"AWD_RECORD_CHANGED": "This record has changed. Review the latest version before continuing.",
	"AWD_AUTHORITY_REQUIRED": "You are not authorised to take this action.",
	"AWD_SIGNATURE_UNAVAILABLE": "Signing is unavailable. Your draft has been saved.",
	"AWD_NO_SUPPORTED_AWARD": "An award cannot be made from the current report. Review the recorded reasons.",
	"AWD_VALIDITY_EXPIRED": "Tender validity has expired. No award can proceed.",
	"AWD_NOTICE_FAILED": "A required notice is not yet confirmed.",
	"AWD_ON_HOLD": "This award is on hold. Review the reason and responsible officer.",
	"AWD_RESPONSE_LATE": "Your response was received after the deadline. It cannot be used to proceed with this award.",
	"AWD_NOTICE_CHANGED": "The award notice has changed. Review the current notice before replying.",
	"AWD_RULE_UNVERIFIED": "The applicable rules have not been confirmed. The award cannot proceed yet.",
	"AWD_CONTRACTING_UNAVAILABLE": "Contracting is unavailable. KenTender will check that the award can still proceed before sending it.",
	"AWD_STATUS_UNAVAILABLE": "The current tender status could not be confirmed. The system will check again when service is restored.",
}
ERROR_CODES: frozenset[str] = frozenset(MESSAGES)


class AwardError(frappe.ValidationError):
	"""`reasons` lists every applicable guard: [{code, message, detail}]."""

	def __init__(self, code: str, message: str, detail: dict | None = None, reasons: list[dict[str, Any]] | None = None):
		self.code = code
		self.detail = detail or {}
		self.reasons = reasons or [{"code": code, "message": message, "detail": self.detail}]
		super().__init__(message)


def reason(code: str, **detail) -> dict[str, Any]:
	if code not in ERROR_CODES:
		raise ValueError(f"{code!r} is not part of the AWD-CHG-001 v0.4 §8 error contract.")
	return {"code": code, "message": MESSAGES[code], "detail": detail}


def fail(code: str, detail: dict | None = None, **facts) -> None:
	one = reason(code, **{**(detail or {}), **facts})
	raise AwardError(code, one["message"], one["detail"])


class Guards:
	"""Collect every applicable refusal, then raise them together."""

	def __init__(self) -> None:
		self.reasons: list[dict[str, Any]] = []

	def add(self, code: str, **detail) -> "Guards":
		if not any(r["code"] == code and r["detail"] == detail for r in self.reasons):
			self.reasons.append(reason(code, **detail))
		return self

	def __bool__(self) -> bool:
		return bool(self.reasons)

	def raise_if_any(self) -> None:
		if self.reasons:
			first = self.reasons[0]
			raise AwardError(first["code"], first["message"], first["detail"], self.reasons)


def as_data(exc: AwardError) -> dict[str, Any]:
	"""A refusal returned as data by the API."""
	return {"ok": False, "code": exc.code, "message": str(exc), "detail": exc.detail, "reasons": exc.reasons}


class InputError(frappe.ValidationError):
	"""A form value to correct (a missing reason, an unknown choice). Not a §8
	guard: it is shown beside the field and the rest of the form is kept."""

	def __init__(self, fields: dict[str, str]):
		self.code = "AWD_INPUT"
		self.fields = fields
		self.detail = {"fields": fields}
		self.reasons = []
		super().__init__("; ".join(fields.values()))


def invalid(fields: dict[str, str]) -> None:
	fields = {k: v for k, v in fields.items() if v}
	if fields:
		raise InputError(fields)


def required(**values) -> None:
	"""Every named value must be non-blank; the message names the field."""
	invalid({k: f"Enter the {k.replace('_', ' ')}." for k, v in values.items() if not str(v or "").strip()})
