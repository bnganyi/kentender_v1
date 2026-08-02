# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BX3 — Budget control HTTP adapters for Demand Intake (mini-PRD §11–12).

Thin HTTP layer over ``kentender_budget.services.budget_service``.
All balance mutations delegate to the service; this module only handles
HTTP-layer concerns (whitelist decoration, response shaping).

Parent Budget ``status`` is not enforced for reads or reservations in v1:
governance is Budget Line active flag, balances, and downstream references.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime

from kentender_budget.services.budget_service import (
    release as _svc_release,
    reserve as _svc_reserve,
    snapshot as _svc_snapshot,
)


def _success(data: dict, message: str) -> dict:
	return {"ok": True, "data": data, "message": message}


def _error(error_code: str, message: str) -> dict:
	return {"ok": False, "error_code": error_code, "message": str(message)}


def _line_financials(bl_doc) -> tuple[float, float, float, float, float]:
	"""Return (allocated, reserved, committed, consumed, available).

	Formula (per Budget Domain Revision):
	  available = allocated − reserved − committed − consumed
	"""
	alloc = flt(bl_doc.amount_allocated)
	res   = flt(bl_doc.amount_reserved)
	com   = flt(getattr(bl_doc, "amount_committed", None) or 0)
	con   = flt(bl_doc.amount_consumed or 0)
	avail = flt(alloc - res - com - con)
	return alloc, res, com, con, avail


def _get_line_doc_or_error(budget_line_id: str | None):
	if not budget_line_id:
		return None, _error("BUDGET_LINE_NOT_FOUND", _("Budget Line is required."))
	if not frappe.db.exists("Budget Line", budget_line_id):
		return None, _error("BUDGET_LINE_NOT_FOUND", _("Budget Line not found."))
	return frappe.get_doc("Budget Line", budget_line_id), None


@frappe.whitelist()
def get_budget_line_context(budget_line_id: str | None = None):
	"""Strict service contract: load Budget Line operational context."""
	bl, err = _get_line_doc_or_error(budget_line_id)
	if err:
		return err
	if not bl.is_active:
		return _error("BUDGET_LINE_INACTIVE", _("Budget Line is not active (BL-015)."))
	alloc, res, com, con, avail = _line_financials(bl)
	return _success(
		{
			"budget_line_id": bl.name,
			"budget_line_code": bl.budget_line_code,
			"budget_line_name": bl.budget_line_name,
			"budget": bl.budget,
			"budget_id": bl.budget,
			"budget_name": frappe.db.get_value("Budget", bl.budget, "budget_name") if bl.budget else "",
			"budget_code": bl.budget,
			"procuring_entity": bl.procuring_entity,
			"procuring_entity_name": frappe.db.get_value(
				"Procuring Entity", bl.procuring_entity, "entity_name"
			)
			if bl.procuring_entity
			else "",
			"procuring_entity_code": frappe.db.get_value(
				"Procuring Entity", bl.procuring_entity, "entity_code"
			)
			if bl.procuring_entity
			else "",
			"fiscal_year": cint(bl.fiscal_year),
			"currency": bl.currency,
			"funding_source": bl.funding_source,
			"funding_source_title": bl.funding_source or "",
			"funding_source_code": "",
			# Strategy linkage removed (MVP-1 teardown); keep empty keys for API shape.
			"strategic_plan": None,
			"strategic_plan_name": "",
			"strategic_plan_code": "",
			"program": None,
			"program_title": "",
			"program_code": "",
			"sub_program": None,
			"sub_program_title": "",
			"sub_program_code": "",
			"output_indicator": None,
			"output_indicator_title": "",
			"output_indicator_code": "",
			"performance_target": None,
			"performance_target_title": "",
			"performance_target_code": "",
			"amount_allocated": alloc,
			"amount_reserved": res,
			"amount_committed": com,
			"amount_consumed": con,
			"amount_available": avail,
			"is_active": bool(bl.is_active),
		},
		_("Budget line context loaded"),
	)


@frappe.whitelist()
def check_available_budget(budget_line_id: str | None = None, amount: float | None = None):
	"""Strict service contract: check sufficiency without mutation."""
	amt = flt(amount)
	if amt <= 0:
		return _error("INVALID_AMOUNT", _("Amount must be greater than zero."))
	bl, err = _get_line_doc_or_error(budget_line_id)
	if err:
		return err
	if not bl.is_active:
		return _error("BUDGET_LINE_INACTIVE", _("Budget Line is not active."))
	_alloc, _res, _com, _con, avail = _line_financials(bl)
	shortfall = flt(max(0.0, amt - avail))
	return _success(
		{
			"budget_line_id": bl.name,
			"requested_amount": amt,
			"amount_available": avail,
			"currency": bl.currency,
			"is_sufficient": bool(avail + 1e-9 >= amt),
			"shortfall": shortfall,
		},
		_("Budget availability checked"),
	)


@frappe.whitelist()
def get_available_budget(budget_line_id: str | None = None):
	"""Strict service contract: authoritative Budget Line snapshot (active lines only)."""
	bl, err = _get_line_doc_or_error(budget_line_id)
	if err:
		return err
	if not bl.is_active:
		return _error("BUDGET_LINE_INACTIVE", _("Budget Line is not active."))
	alloc, res, com, con, avail = _line_financials(bl)
	return _success(
		{
			"budget_line_id": bl.name,
			"amount_allocated": alloc,
			"amount_reserved": res,
			"amount_committed": com,
			"amount_consumed": con,
			"amount_available": avail,
			"currency": bl.currency,
		},
		_("Available budget loaded"),
	)


@frappe.whitelist()
def create_reservation(
	budget_line_id: str | None = None,
	source_doctype: str | None = None,
	source_docname: str | None = None,
	amount: float | None = None,
	actor: str | None = None,
	source_business_id: str | None = None,
):
	"""Strict service contract: create reservation atomically. Delegates to budget_service."""
	return _svc_reserve(
		budget_line_id=budget_line_id or "",
		source_doctype=source_doctype or "",
		source_docname=source_docname or "",
		amount=flt(amount),
		actor=actor,
		source_business_id=source_business_id,
	)


@frappe.whitelist()
def release_reservation(reservation_id: str | None = None, reason: str | None = None, actor: str | None = None):
	"""Strict service contract: release reservation atomically. Delegates to budget_service."""
	return _svc_release(
		reservation_id=reservation_id or "",
		reason=reason or "",
		actor=actor,
	)


@frappe.whitelist()
def get_active_reservation_for_source(source_doctype: str | None = None, source_docname: str | None = None):
	"""Lookup active reservation by source transaction."""
	if not (source_doctype or "").strip() or not (source_docname or "").strip():
		return _error("SOURCE_REFERENCE_INVALID", _("Source reference is required."))
	name = frappe.db.get_value(
		"Budget Reservation",
		{"source_doctype": source_doctype, "source_docname": source_docname, "status": "Active"},
		"name",
	)
	if not name:
		return _success({"reservation_id": None, "status": None}, _("Active reservation lookup complete"))
	row = frappe.get_doc("Budget Reservation", name)
	bl_code = frappe.db.get_value("Budget Line", row.budget_line, "budget_line_code")
	return _success(
		{
			"reservation_id": row.reservation_id,
			"status": row.status,
			"amount": flt(row.amount),
			"budget_line_id": row.budget_line,
			"budget_line_code": bl_code,
		},
		_("Active reservation lookup complete"),
	)


@frappe.whitelist()
def list_reservations_for_budget_line(budget_line_id: str | None = None):
	"""List Budget Reservation records for a budget line, newest first."""
	_checked_line, err = _get_line_doc_or_error(budget_line_id)
	if err:
		return err
	rows = frappe.get_all(
		"Budget Reservation",
		filters={"budget_line": budget_line_id},
		fields=[
			"reservation_id",
			"source_doctype",
			"source_docname",
			"source_business_id",
			"amount",
			"status",
			"created_at",
		],
		order_by="creation desc",
		limit=200,
	)
	return _success({"budget_line_id": budget_line_id, "reservations": rows}, _("Reservation history loaded"))


@frappe.whitelist()
def search_budget_lines(query: str | None = None, budget_id: str | None = None, procuring_entity: str | None = None, limit: int = 10):
	"""Search active Budget Lines by name or code for the Finance Reviewer picker.
	Optionally filter by budget_id and/or procuring_entity for the 2-step cascade picker."""
	q = (query or "").strip()
	bid = (budget_id or "").strip()
	pe = (procuring_entity or "").strip()

	filters: dict = {"is_active": 1}
	if bid:
		filters["budget"] = bid
	if pe:
		filters["procuring_entity"] = pe

	if q:
		rows = frappe.db.get_all(
			"Budget Line",
			fields=["name", "budget_line_code", "budget_line_name", "amount_allocated",
					"amount_reserved", "amount_committed", "amount_consumed"],
			filters=filters,
			or_filters=[
				["budget_line_name", "like", f"%{q}%"],
				["budget_line_code", "like", f"%{q}%"],
			],
			order_by="budget_line_name asc",
			limit=int(limit),
		)
	else:
		rows = frappe.db.get_all(
			"Budget Line",
			fields=["name", "budget_line_code", "budget_line_name", "amount_allocated",
					"amount_reserved", "amount_committed", "amount_consumed"],
			filters=filters,
			order_by="budget_line_name asc",
			limit=int(limit),
		)

	# Compute available for each line
	for r in rows:
		r["amount_available"] = (
			flt(r.get("amount_allocated")) - flt(r.get("amount_reserved"))
			- flt(r.get("amount_committed")) - flt(r.get("amount_consumed"))
		)
	return {"ok": True, "results": rows}


@frappe.whitelist()
def get_budgets_for_picker(query: str | None = None, procuring_entity: str | None = None, limit: int = 20):
	"""Return budgets that have at least one active Budget Line, for the cascade picker.
	Filtered to the demand's procuring entity when provided."""
	q = (query or "").strip()
	pe = (procuring_entity or "").strip()

	line_filters: dict = {"is_active": 1}
	if pe:
		line_filters["procuring_entity"] = pe

	having_lines = frappe.db.get_all("Budget Line", filters=line_filters, pluck="budget")
	budget_ids = list(set(having_lines))
	if not budget_ids:
		return {"ok": True, "results": []}

	filters: dict = {"name": ["in", budget_ids]}
	if pe:
		filters["procuring_entity"] = pe
	if q:
		rows = frappe.db.get_all(
			"Budget",
			fields=["name", "budget_name", "fiscal_year", "status", "procuring_entity"],
			filters=filters,
			or_filters=[["budget_name", "like", f"%{q}%"]],
			order_by="fiscal_year desc, budget_name asc",
			limit=int(limit),
		)
	else:
		rows = frappe.db.get_all(
			"Budget",
			fields=["name", "budget_name", "fiscal_year", "status", "procuring_entity"],
			filters=filters,
			order_by="fiscal_year desc, budget_name asc",
			limit=int(limit),
		)

	pe_names = list({r["procuring_entity"] for r in rows if r.get("procuring_entity")})
	if pe_names:
		pe_map = {
			r["name"]: r["entity_name"]
			for r in frappe.db.get_all(
				"Procuring Entity",
				filters={"name": ["in", pe_names]},
				fields=["name", "entity_name"],
			)
		}
		for r in rows:
			r["entity_name"] = pe_map.get(r["procuring_entity"], r["procuring_entity"])

	return {"ok": True, "results": rows}
