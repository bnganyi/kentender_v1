# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Budget control adapters for Demand/Planning — thin shims over MVP-1 contracts.

Preserves legacy response shapes (`ok` / `data` / `sufficient`) used by DIA
lifecycle and readiness while delegating to `check_funding` / `reserve_funding`.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt


def _ok(data: dict[str, Any] | None = None, message: str | None = None) -> dict[str, Any]:
	return {
		"ok": True,
		"skipped": False,
		"data": data or {},
		"message": message or "",
	}


def _fail(message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
	return {
		"ok": False,
		"skipped": False,
		"data": data or {},
		"message": message,
	}


@frappe.whitelist()
def get_budget_line_context(budget_line_id: str | None = None):
	"""Real Budget Line context for Demand PE / readiness checks."""
	from kentender_budget.services.budget_check_reserve_contracts import _resolve_line

	bl = (budget_line_id or "").strip()
	if not bl:
		return _fail(_("Budget Line is required"))
	try:
		line = _resolve_line(bl)
		bud = frappe.get_doc("Budget", line.budget)
	except Exception as exc:
		return _fail(str(exc) or _("Budget Line not found"))

	pe = bud.procuring_entity or ""
	pe_code = frappe.db.get_value("Procuring Entity", pe, "entity_code") or pe
	pe_name = frappe.db.get_value("Procuring Entity", pe, "entity_name") or pe_code
	available = flt(line.approved_amount) - flt(line.amount_reserved) - flt(line.amount_committed)
	return _ok(
		{
			"budget_line_id": line.name,
			"budget_line_code": line.generated_reference or "",
			"budget_line_name": line.title or line.generated_reference or "",
			"budget": bud.name,
			"budget_id": bud.name,
			"budget_name": bud.title or "",
			"budget_code": bud.generated_reference or "",
			"procuring_entity": pe,
			"procuring_entity_name": pe_name,
			"procuring_entity_code": pe_code,
			"fiscal_year": bud.fiscal_period,
			"currency": bud.currency or "KES",
			"funding_source": None,
			"funding_source_title": line.funding_source_name or "",
			"funding_source_code": "",
			"strategic_plan": None,
			"program": None,
			"sub_program": None,
			"performance_target": line.primary_target_code or None,
			"is_active": 1 if line.is_active else 0,
			"amount_allocated": flt(line.approved_amount),
			"amount_reserved": flt(line.amount_reserved),
			"amount_committed": flt(line.amount_committed),
			"amount_consumed": flt(line.amount_actual),
			"amount_available": available,
		}
	)


@frappe.whitelist()
def get_budget_lines_context(budget_line_ids: list[str] | str | None = None):
	"""Return bounded identity context for several Budget Lines in two queries.

	Consumers use this published adapter instead of importing Budget DocType
	internals or resolving one line per projected row.
	"""
	values = budget_line_ids
	if isinstance(values, str):
		try:
			values = json.loads(values)
		except json.JSONDecodeError:
			values = [part.strip() for part in values.split(",")]
	ids = list(dict.fromkeys(str(value).strip() for value in (values or []) if str(value).strip()))
	if not ids:
		return _ok({})
	lines = frappe.get_all(
		"Budget Line",
		filters={"name": ["in", ids]},
		fields=["name", "budget", "generated_reference", "title", "currency", "is_active"],
		limit=len(ids),
	)
	budget_ids = list({row.budget for row in lines if row.budget})
	budgets = {
		row.name: row
		for row in frappe.get_all(
			"Budget",
			filters={"name": ["in", budget_ids]},
			fields=["name", "procuring_entity", "fiscal_period", "currency", "status"],
			limit=len(budget_ids),
		)
	} if budget_ids else {}
	data: dict[str, dict[str, Any]] = {}
	for line in lines:
		budget = budgets.get(line.budget)
		data[line.name] = {
			"budget_line_id": line.name,
			"budget_line_code": line.generated_reference or "",
			"budget_line_name": line.title or line.generated_reference or line.name,
			"budget": line.budget,
			"procuring_entity": budget.procuring_entity if budget else "",
			"fiscal_year": budget.fiscal_period if budget else "",
			"currency": (line.currency or (budget.currency if budget else "") or "KES"),
			"is_active": 1 if line.is_active and budget and budget.status == "Active" else 0,
		}
	return _ok(data)


@frappe.whitelist()
def check_available_budget(budget_line_id: str | None = None, amount: float | None = None):
	"""Map to check_funding — ok=False when insufficient (readiness + approve_finance)."""
	from kentender_budget.services.budget_check_reserve_contracts import check_funding

	try:
		dto = check_funding(budget_line=budget_line_id, requested_amount=amount)
	except frappe.PermissionError:
		raise
	except Exception as exc:
		return _fail(str(exc) or _("Funding check failed"))

	data = {
		"available": dto["sufficient"],
		"amount_available": dto["available_before"],
		"is_sufficient": dto["sufficient"],
		"sufficient": dto["sufficient"],
		"currency": (dto.get("budget") or {}).get("currency") or "KES",
		"shortfall": dto["shortfall"],
		"decision": dto["decision"],
		"available_before_display": dto["available_before_display"],
		"requested_display": dto["requested_display"],
	}
	if not dto["sufficient"]:
		return _fail(
			_("Insufficient funding. Shortfall: {0}").format(dto["shortfall_display"]),
			data,
		)
	return _ok(data)


@frappe.whitelist()
def get_available_budget(budget_line_id: str | None = None):
	from kentender_budget.services.budget_check_reserve_contracts import _resolve_line

	try:
		line = _resolve_line(budget_line_id or "")
		available = flt(line.approved_amount) - flt(line.amount_reserved) - flt(line.amount_committed)
		return _ok({"amount_available": available})
	except Exception as exc:
		return _fail(str(exc), {"amount_available": 0})


_PLAN_ITEM_SOURCE_DOCTYPES = ("Procurement Plan Item", "Plan Item")


@frappe.whitelist()
def create_reservation(*args, **kwargs):
	"""Accept legacy positional/keyword shapes; delegate to reserve_funding.

	Legacy: create_reservation(budget_line, source_doctype, source_docname, amount, actor=..., source_business_id=...)

	BUD-FR-009/010 — a reservation requires a Plan Item reference. When
	`source_doctype` names a Plan Item, `source_docname` is taken as the Plan
	Item code directly; otherwise callers must pass `plan_item_code` explicitly
	(a bare Demand-shaped source, on its own, is no longer sufficient).
	"""
	from kentender_budget.services.budget_check_reserve_contracts import reserve_funding

	budget_line = kwargs.get("budget_line") or kwargs.get("budget_line_id")
	source_doctype = kwargs.get("source_doctype")
	source_docname = kwargs.get("source_docname") or kwargs.get("demand_name")
	amount = kwargs.get("amount") or kwargs.get("requested_amount")
	actor = kwargs.get("actor")
	source_business_id = kwargs.get("source_business_id")
	idempotency_key = kwargs.get("idempotency_key")
	plan_item_code = kwargs.get("plan_item_code")

	if args:
		if len(args) >= 1 and not budget_line:
			budget_line = args[0]
		if len(args) >= 2 and not source_doctype:
			source_doctype = args[1]
		if len(args) >= 3 and not source_docname:
			source_docname = args[2]
		if len(args) >= 4 and amount is None:
			amount = args[3]

	if not plan_item_code and source_doctype in _PLAN_ITEM_SOURCE_DOCTYPES:
		plan_item_code = source_docname

	demand_name = None if source_doctype in _PLAN_ITEM_SOURCE_DOCTYPES else (source_docname or source_business_id)
	if source_business_id and not idempotency_key:
		idempotency_key = f"Demand:{source_business_id}:{budget_line}:{flt(amount):.2f}"
	elif source_docname and not idempotency_key:
		idempotency_key = f"{source_doctype or 'Demand'}:{source_docname}:{budget_line}:{flt(amount):.2f}"

	try:
		result = reserve_funding(
			budget_line=budget_line,
			plan_item_code=plan_item_code,
			demand_name=demand_name,
			requested_amount=amount,
			idempotency_key=idempotency_key,
			actor=actor,
		)
	except frappe.PermissionError:
		raise
	except Exception as exc:
		return _fail(str(exc) or _("Reservation creation failed"))

	return _ok(
		{
			"reservation_id": result.get("reservation_code") or result.get("reservation_id"),
			"reservation_name": result.get("reservation_id"),
			"status": result.get("status") or "Reserved",
			"reused": result.get("reused"),
			"original_amount": result.get("original_amount"),
		}
	)


@frappe.whitelist()
def release_reservation(
	reservation_id: str | None = None, reason: str | None = None, actor: str | None = None
):
	"""MVP-1: mark reservation Released and restore line reserved balance."""
	from kentender_budget.services.budget_check_reserve_contracts import (
		release_reservation as _release_reservation,
	)

	key = (reservation_id or "").strip()
	if not key:
		return _fail(_("Reservation is required"))
	try:
		result = _release_reservation(reservation=key, reason=reason, actor=actor)
	except frappe.PermissionError:
		raise
	except Exception as exc:
		return _fail(str(exc) or _("Reservation not found"))
	return _ok({"status": result.get("status") or "Released", "reservation_id": result.get("reservation_code")})


@frappe.whitelist()
def get_active_reservation_for_source(
	source_doctype: str | None = None, source_docname: str | None = None
):
	_ = source_doctype
	code = (source_docname or "").strip()
	if not code:
		return _ok({"reservation": None})
	# Match demand name or business code.
	name = frappe.db.get_value(
		"Funding Reservation",
		{"demand_code": code, "status": ["in", ["Reserved", "Partially converted"]]},
		"name",
	)
	if not name and frappe.db.exists("Demand", code):
		biz = frappe.db.get_value("Demand", code, "demand_id") or code
		name = frappe.db.get_value(
			"Funding Reservation",
			{"demand_code": biz, "status": ["in", ["Reserved", "Partially converted"]]},
			"name",
		)
	if not name:
		return _ok({"reservation": None})
	doc = frappe.get_doc("Funding Reservation", name)
	return _ok(
		{
			"reservation": {
				"name": doc.name,
				"code": doc.generated_reference,
				"status": doc.status,
				"remaining_reserved": flt(doc.remaining_reserved),
			}
		}
	)


@frappe.whitelist()
def list_reservations_for_budget_line(budget_line_id: str | None = None):
	from kentender_budget.services.budget_check_reserve_contracts import _resolve_line

	try:
		line = _resolve_line(budget_line_id or "")
	except Exception as exc:
		return _fail(str(exc), {"reservations": []})
	rows = frappe.get_all(
		"Funding Reservation",
		filters={"budget_line": line.name},
		fields=["name", "generated_reference", "status", "remaining_reserved", "demand_code"],
		order_by="event_date desc",
	)
	return _ok({"reservations": rows})


@frappe.whitelist()
def search_budget_lines(
	query: str | None = None,
	budget_id: str | None = None,
	procuring_entity: str | None = None,
	limit: int = 10,
):
	from kentender_budget.services.budget_check_reserve_contracts import list_eligible_budget_lines

	rows = list_eligible_budget_lines(procuring_entity=procuring_entity)
	q = (query or "").strip().lower()
	if budget_id:
		rows = [r for r in rows if r.get("budget") == budget_id]
	if q:
		rows = [
			r
			for r in rows
			if q in (r.get("name") or "").lower() or q in (r.get("code") or "").lower()
		]
	return _ok({"results": rows[: max(1, int(limit or 10))]})


@frappe.whitelist()
def get_budgets_for_picker(
	query: str | None = None, procuring_entity: str | None = None, limit: int = 20
):
	from kentender_budget.services.budget_contracts import resolve_scoped_entity
	from kentender_budget.services.budget_permissions import entity_for_user

	pe = resolve_scoped_entity(procuring_entity or entity_for_user() or None)
	filters: dict[str, Any] = {"status": "Active"}
	if pe:
		filters["procuring_entity"] = pe
	rows = frappe.get_all(
		"Budget",
		filters=filters,
		fields=["name", "generated_reference", "title", "fiscal_period"],
		order_by="modified desc",
		limit_page_length=max(1, int(limit or 20)),
	)
	q = (query or "").strip().lower()
	if q:
		rows = [
			r
			for r in rows
			if q in (r.title or "").lower() or q in (r.generated_reference or "").lower()
		]
	return _ok(
		{
			"results": [
				{
					"id": r.name,
					"code": r.generated_reference,
					"name": r.title,
					"fiscal_period": r.fiscal_period,
				}
				for r in rows
			]
		}
	)


def get_budget_line_availability(budget_line_id: str | None = None) -> dict[str, Any]:
	"""Non-whitelisted helper used by Home portfolio (best-effort)."""
	try:
		from kentender_budget.services.budget_check_reserve_contracts import _resolve_line

		line = _resolve_line(budget_line_id or "")
		available = flt(line.approved_amount) - flt(line.amount_reserved) - flt(line.amount_committed)
		return {"available": available, "amount_available": available, "skipped": False}
	except Exception:
		return {"available": 0, "amount_available": 0, "skipped": True}
