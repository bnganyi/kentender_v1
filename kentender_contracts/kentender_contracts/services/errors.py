# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable Contract Management errors (CM-CHG-001 v0.8 §8), verbatim.

§8 is a closed set of seventeen codes. The message is shown as written; names, amounts and recovery travel separately in
`detail`, and each code's fix and holder (the third column of §8) travels with it. Every applicable reason is returned
together (collect with `Guards`, raise once). Business messages never show internal tables, hashes or stack traces (§8 last
paragraph). A form value to correct is an `InputError`, not one of the 17 codes."""

from __future__ import annotations

from typing import Any

import frappe

MESSAGES: dict[str, str] = {
	"CM_SOURCE": "The contract details do not match the source record.",
	"CM_CHANGED": "This record has changed. Review the latest version before continuing.",
	"CM_AUTHORITY": "You are not authorised to take this action.",
	"CM_RULE": "The applicable requirement has not been confirmed.",
	"CM_HOLD": "This action is on hold.",
	"CM_SIGNING": "Signing is unavailable. Your work has been saved.",
	"CM_INCOMPLETE": "Some required observations are missing.",
	"CM_QUANTITY": "These quantities do not match the delivery record.",
	"CM_POSTING": "The record is signed. The stock update is still pending.",
	"CM_INVOICE": "This invoice needs review before certification.",
	"CM_DUPLICATE": "This submission may already be recorded.",
	"CM_CLOSURE": "The contract still has obligations that prevent close-out.",
	"CM_FUNDING": "The contract funding update needs attention.",
	"CM_APPOINTMENT": "The inspectors are not ready to act on this contract.",
	"CM_SEGREGATION": "Another authorised person must take this action.",
	"CM_RECONCILE": "The correction must be reconciled before this action can proceed.",
	"CM_REPORT": "This report is incomplete because a source could not be read.",
}

FIXES: dict[str, str] = {
	"CM_SOURCE": "HOP reviews source issue; View issue",
	"CM_CHANGED": "Reload current comparison; retain unsaved text",
	"CM_AUTHORITY": "Shared access page; current holder where disclosure permits",
	"CM_RULE": "HOP/legal owner; View issue",
	"CM_HOLD": "Show specific reason and holder; View issue",
	"CM_SIGNING": "Technical recovery of original attempt",
	"CM_INCOMPLETE": "Inspector; Review missing observations",
	"CM_QUANTITY": "Chair/receiver; View quantity comparison",
	"CM_POSTING": "Technical owner; View update status",
	"CM_INVOICE": "Finance/HOP issue owner; Review differences",
	"CM_DUPLICATE": "View existing submission; Finance reviews ambiguity",
	"CM_CLOSURE": "View remaining obligations; named holder per item",
	"CM_FUNDING": "HOP/Budget owner; View funding issue; do not ask for new signatures",
	"CM_APPOINTMENT": "AO/HOP/missing declarer; show missing appointment or declarations",
	"CM_SEGREGATION": "Name eligible capacity without revealing protected assignments",
	"CM_RECONCILE": "Current Finance/stock/Budget owner; View affected records",
	"CM_REPORT": "Daniel; View update status; submission absent",
}
ERROR_CODES: frozenset[str] = frozenset(MESSAGES)


class ContractError(frappe.ValidationError):
	"""`reasons` lists every applicable guard: [{code, message, fix, detail}]."""

	def __init__(self, code: str, message: str, detail: dict | None = None, reasons: list[dict[str, Any]] | None = None):
		self.code = code
		self.detail = detail or {}
		self.reasons = reasons or [{"code": code, "message": message, "fix": FIXES.get(code, ""), "detail": self.detail}]
		super().__init__(message)


def reason(code: str, **detail) -> dict[str, Any]:
	if code not in ERROR_CODES:
		raise ValueError(f"{code!r} is not part of the CM-CHG-001 v0.8 §8 error contract.")
	return {"code": code, "message": MESSAGES[code], "fix": FIXES[code], "detail": detail}


def fail(code: str, detail: dict | None = None, **facts) -> None:
	one = reason(code, **{**(detail or {}), **facts})
	raise ContractError(code, one["message"], one["detail"], [one])


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
			raise ContractError(first["code"], first["message"], first["detail"], self.reasons)


def as_data(exc: ContractError) -> dict[str, Any]:
	"""A refusal returned as data by the API."""
	return {"ok": False, "code": exc.code, "message": str(exc), "detail": exc.detail, "reasons": exc.reasons}


class InputError(frappe.ValidationError):
	"""A form value to correct (a missing reason, an unknown choice). Not a §8 guard: it is shown beside the field and the
	rest of the form is kept."""

	def __init__(self, fields: dict[str, str]):
		self.code = "CM_INPUT"
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
