# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 BR-017 idempotency-key handling, modeled exactly on
kentender_core.services.reference_data_idempotency.py (CFG-CHG-002)."""

from __future__ import annotations

from typing import Callable

import frappe


def run_idempotent(
	idempotency_key: str | None,
	document_type: str,
	document_name: str,
	action: str,
	fn: Callable[[], dict],
) -> dict:
	if not idempotency_key:
		return fn()

	existing = frappe.db.get_value("Strategy Command Journal", {"idempotency_key": idempotency_key}, "result")
	if existing is not None:
		return frappe.parse_json(existing)

	result = fn()
	try:
		frappe.get_doc(
			{
				"doctype": "Strategy Command Journal",
				"idempotency_key": idempotency_key,
				"document_type": document_type,
				"document_name": document_name,
				"action": action,
				"result": frappe.as_json(result),
			}
		).insert(ignore_permissions=True)
	except frappe.DuplicateEntryError:
		# Concurrent identical retry — return the winner's journaled result.
		existing = frappe.db.get_value(
			"Strategy Command Journal", {"idempotency_key": idempotency_key}, "result"
		)
		return frappe.parse_json(existing)
	return result
