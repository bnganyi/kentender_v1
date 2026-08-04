# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Budget control adapters — neutralized by MVP-1 Budget preparatory teardown.

Legacy Budget / Budget Line / Reservation DocTypes are gone. Callers and tests
may still import these symbols; every entry returns a skip / permissive stub
until the MVP-1 Budget rebuild restores real funding control.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _


def _skipped(data: dict[str, Any] | None = None, message: str | None = None) -> dict[str, Any]:
	return {
		"ok": True,
		"skipped": True,
		"reason": "mvp1-budget-teardown",
		"data": data or {},
		"message": message or _("Budget control unavailable (MVP-1 teardown)."),
	}


@frappe.whitelist()
def get_budget_line_context(budget_line_id: str | None = None):
	"""Stub context — no Budget Line DocType.

	Omits ``procuring_entity`` so Demand readiness PE mismatch checks do not fail.
	"""
	bl = (budget_line_id or "").strip()
	return _skipped(
		{
			"budget_line_id": bl or None,
			"budget_line_code": bl,
			"budget_line_name": bl,
			"budget": None,
			"budget_id": None,
			"budget_name": "",
			"budget_code": "",
			"procuring_entity_name": "",
			"procuring_entity_code": "",
			"fiscal_year": None,
			"currency": "KES",
			"funding_source": None,
			"funding_source_title": "",
			"funding_source_code": "",
			"strategic_plan": None,
			"program": None,
			"sub_program": None,
			"output_indicator": None,
			"performance_target": None,
			"is_active": 1,
			"amount_allocated": 0,
			"amount_reserved": 0,
			"amount_committed": 0,
			"amount_consumed": 0,
			"amount_available": 0,
		}
	)


@frappe.whitelist()
def check_available_budget(budget_line_id: str | None = None, amount: float | None = None):
	"""Permissive stub — funding gate skipped during teardown."""
	_ = budget_line_id, amount
	return _skipped(
		{
			"available": True,
			"amount_available": 999_999_999,
			"is_sufficient": True,
			"sufficient": True,
			"currency": "KES",
		}
	)


@frappe.whitelist()
def get_available_budget(budget_line_id: str | None = None):
	_ = budget_line_id
	return _skipped({"amount_available": 0})


@frappe.whitelist()
def create_reservation(*args, **kwargs):
	"""Accept legacy positional/keyword shapes; always skip."""
	_ = args, kwargs
	return _skipped({"reservation_id": None, "status": "Skipped"})


@frappe.whitelist()
def release_reservation(
	reservation_id: str | None = None, reason: str | None = None, actor: str | None = None
):
	_ = reservation_id, reason, actor
	return _skipped({"status": "Skipped"})


@frappe.whitelist()
def get_active_reservation_for_source(
	source_doctype: str | None = None, source_docname: str | None = None
):
	_ = source_doctype, source_docname
	return _skipped({"reservation": None})


@frappe.whitelist()
def list_reservations_for_budget_line(budget_line_id: str | None = None):
	_ = budget_line_id
	return _skipped({"reservations": []})


@frappe.whitelist()
def search_budget_lines(
	query: str | None = None,
	budget_id: str | None = None,
	procuring_entity: str | None = None,
	limit: int = 10,
):
	_ = query, budget_id, procuring_entity, limit
	return _skipped({"results": []})


@frappe.whitelist()
def get_budgets_for_picker(
	query: str | None = None, procuring_entity: str | None = None, limit: int = 20
):
	_ = query, procuring_entity, limit
	return _skipped({"results": []})


def get_budget_line_availability(budget_line_id: str | None = None) -> dict[str, Any]:
	"""Non-whitelisted helper used by Home portfolio (best-effort)."""
	_ = budget_line_id
	return {"available": 0, "amount_available": 0, "skipped": True}
