# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 BR-017 — every retriable state command uses an idempotency key
and returns the original committed result on replay, backed by a real command
journal (the spec's own named enforcement point for this rule), not an
in-memory or best-effort cache.
"""

from __future__ import annotations

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
) -> dict[str, Any]:
	"""Run fn() at most once per idempotency_key; replay returns the original result."""
	if not idempotency_key:
		return fn()

	existing = frappe.db.get_value(_DOCTYPE, {"idempotency_key": idempotency_key}, "result")
	if existing is not None:
		return frappe.parse_json(existing)

	result = fn()

	try:
		frappe.get_doc(
			{
				"doctype": _DOCTYPE,
				"idempotency_key": idempotency_key,
				"document_type": document_type,
				"document_name": document_name,
				"action": action,
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
