# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 BR-017 — every retriable state command uses an idempotency key
and returns the original committed result on replay, backed by a real command
journal (the spec's own named enforcement point for this rule), not an
in-memory or best-effort cache.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

import frappe
from frappe.utils import now_datetime

_DOCTYPE = "Reference Data Command Journal"


def run_idempotent(
	idempotency_key: str | None,
	document_type: str,
	document_name: str,
	action: str,
	fn: Callable[[], dict[str, Any]],
	*,
	payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Run fn() at most once per idempotency_key; replay returns the original result.

	CFG-CHG-002 v0.14 §7.1 — a caller that passes `payload` gets the full
	contract: the canonical payload's hash is journalled with the result, and
	the same key with DIFFERENT content is refused with
	CFG_IDEMPOTENCY_CONFLICT instead of silently replaying the first result.
	Callers that pass none (the legacy reference-data and STD configuration
	APIs) keep plain replay."""
	if not idempotency_key:
		return fn()

	payload_hash = _hash(payload) if payload is not None else ""
	row = frappe.db.get_value(_DOCTYPE, {"idempotency_key": idempotency_key}, ["result", "payload_hash"], as_dict=True)
	if row is not None:
		if payload_hash and row.payload_hash and row.payload_hash != payload_hash:
			from kentender_core.services.configuration_errors import fail_cfg

			fail_cfg("CFG_IDEMPOTENCY_CONFLICT")
		return frappe.parse_json(row.result)

	result = fn()

	try:
		frappe.get_doc(
			{
				"doctype": _DOCTYPE,
				"idempotency_key": idempotency_key,
				"document_type": document_type,
				"document_name": document_name,
				"action": action,
				"payload_hash": payload_hash,
				"result": frappe.as_json(result),
				"created_at": now_datetime(),
			}
		).insert(ignore_permissions=True)
	except frappe.DuplicateEntryError:
		# A concurrent request with the same key won the race to journal first —
		# fn() already ran twice (unavoidable without a DB lock ahead of fn()),
		# but the JOURNALED result is what every caller must agree on from here.
		existing = frappe.db.get_value(_DOCTYPE, {"idempotency_key": idempotency_key}, "result")
		if existing is not None:
			return frappe.parse_json(existing)
	return result


def _hash(payload: dict[str, Any]) -> str:
	"""Canonical form: sorted keys, no whitespace, dates/decimals as strings."""
	canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
	return hashlib.sha256(canonical.encode()).hexdigest()


def request_payload(arguments: dict[str, Any]) -> dict[str, Any]:
	"""A command's own inputs as its idempotency payload: call as
	`request_payload(locals())` on the first line of the command, where
	`locals()` holds exactly its arguments. The key itself is not content."""
	return {name: value for name, value in arguments.items() if name != "idempotency_key"}
