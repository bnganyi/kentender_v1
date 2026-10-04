# Copyright (c) 2026, KenTender and contributors
"""§13.2 "Every command requires... idempotency key." Modeled exactly on
Strategy's strategy_idempotency.py / kentender_core's reference_data_idempotency.py
(CFG-CHG-002's original) — same shape, third app to adopt it unchanged."""

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

	existing = frappe.db.get_value(
		"STD Cfg Command Journal", {"idempotency_key": idempotency_key}, "result"
	)
	if existing is not None:
		return frappe.parse_json(existing)

	result = fn()
	try:
		frappe.get_doc(
			{
				"doctype": "STD Cfg Command Journal",
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
			"STD Cfg Command Journal", {"idempotency_key": idempotency_key}, "result"
		)
		return frappe.parse_json(existing)
	return result
