# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BX3 — Budget control service APIs for Demand Intake (mini-PRD §11–12).

Parent Budget ``status`` (Draft vs Submitted/Approved) is not enforced for reads
or reservations in v1: governance is Budget Line active flag, balances, and
downstream references (see Budget Builder removal rules). Demand finance approval
still requires an active line via ``check_available_budget`` / ``create_reservation``.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime


def _success(data: dict, message: str) -> dict:
	return {"ok": True, "data": data, "message": message}


def _error(error_code: str, message: str) -> dict:
	return {"ok": False, "error_code": error_code, "message": str(message)}


def _line_financials(bl_doc) -> tuple[float, float, float, float]:
	alloc = flt(bl_doc.amount_allocated)
	res = flt(bl_doc.amount_reserved)
	con = flt(bl_doc.amount_consumed or 0)
	avail = flt(alloc - res - con)
	return alloc, res, con, avail


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
	alloc, res, con, avail = _line_financials(bl)
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
			"strategic_plan": bl.strategic_plan,
			"strategic_plan_name": frappe.db.get_value(
				"Strategic Plan", bl.strategic_plan, "strategic_plan_name"
			)
			if bl.strategic_plan
			else "",
			"strategic_plan_code": "",
			"program": bl.program,
			"program_title": frappe.db.get_value("Strategy Program", bl.program, "program_title")
			if bl.program
			else "",
			"program_code": frappe.db.get_value("Strategy Program", bl.program, "program_code")
			if bl.program
			else "",
			"sub_program": bl.sub_program,
			"sub_program_title": frappe.db.get_value("Sub Program", bl.sub_program, "title")
			if bl.sub_program
			else "",
			"sub_program_code": frappe.db.get_value("Sub Program", bl.sub_program, "sub_program_code")
			if bl.sub_program
			else "",
			"output_indicator": bl.output_indicator,
			"output_indicator_title": frappe.db.get_value(
				"Strategy Objective", bl.output_indicator, "objective_title"
			)
			if bl.output_indicator
			else "",
			"output_indicator_code": frappe.db.get_value(
				"Strategy Objective", bl.output_indicator, "objective_code"
			)
			if bl.output_indicator
			else "",
			"performance_target": bl.performance_target,
			"performance_target_title": frappe.db.get_value(
				"Strategy Target", bl.performance_target, "target_title"
			)
			if bl.performance_target
			else "",
			"performance_target_code": frappe.db.get_value(
				"Strategy Target", bl.performance_target, "target_code"
			)
			if bl.performance_target
			else "",
			"amount_allocated": alloc,
			"amount_reserved": res,
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
	_alloc, _res, _con, avail = _line_financials(bl)
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
	alloc, res, con, avail = _line_financials(bl)
	return _success(
		{
			"budget_line_id": bl.name,
			"amount_allocated": alloc,
			"amount_reserved": res,
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
	"""Strict service contract: create reservation atomically."""
	if not budget_line_id:
		return _error("BUDGET_LINE_NOT_FOUND", _("Budget Line is required."))
	if not source_doctype or not source_docname:
		return _error("SOURCE_REFERENCE_INVALID", _("Source document is required."))
	amt = flt(amount)
	if amt <= 0:
		return _error("INVALID_AMOUNT", _("Reservation amount must be greater than zero."))

	frappe.db.sql("""SELECT name FROM `tabBudget Line` WHERE name=%s FOR UPDATE""", (budget_line_id,))
	bl, err = _get_line_doc_or_error(budget_line_id)
	if err:
		return err
	if not bl.is_active:
		return _error("BUDGET_LINE_INACTIVE", _("Budget Line is not active."))
	_alloc, _res, _con, avail = _line_financials(bl)
	active_exists = frappe.db.exists(
		"Budget Reservation",
		{"source_doctype": source_doctype, "source_docname": source_docname, "status": "Active"},
	)
	if active_exists:
		return _error(
			"DUPLICATE_ACTIVE_RESERVATION",
			_("Active reservation already exists for this source document."),
		)
	if amt > avail + 1e-9:
		return _error("INSUFFICIENT_BUDGET", _("Insufficient available budget to create reservation."))

	actor_user = actor or frappe.session.user
	available_after = flt(avail - amt)
	res_doc = frappe.get_doc(
		{
			"doctype": "Budget Reservation",
			"budget_line": budget_line_id,
			"source_doctype": source_doctype,
			"source_docname": source_docname,
			"source_business_id": source_business_id,
			"amount": amt,
			"status": "Active",
			"created_by": actor_user,
			"available_before_reservation": avail,
			"available_after_reservation": available_after,
		}
	)
	try:
		res_doc.insert(ignore_permissions=True)
		bl.reload()
		bl.amount_reserved = flt(bl.amount_reserved) + amt
		frappe.flags.budget_control_service_write = True
		try:
			bl.save(ignore_permissions=True)
		finally:
			frappe.flags.budget_control_service_write = False
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "create_reservation_failed")
		return _error("RESERVATION_CREATE_FAILED", _("Reservation creation failed."))

	return _success(
		{
			"reservation_id": res_doc.reservation_id,
			"reservation_name": res_doc.name,
			"budget_line_id": bl.name,
			"budget_line_code": bl.budget_line_code,
			"source_doctype": source_doctype,
			"source_docname": source_docname,
			"source_business_id": source_business_id,
			"amount": amt,
			"status": "Active",
			"available_before_reservation": avail,
			"available_after_reservation": available_after,
			"currency": bl.currency,
		},
		_("Reservation created successfully"),
	)


@frappe.whitelist()
def release_reservation(reservation_id: str | None = None, reason: str | None = None, actor: str | None = None):
	"""Strict service contract: release reservation atomically."""
	if not reservation_id:
		return _error("RESERVATION_NOT_FOUND", _("Reservation reference is required."))
	release_reason = (reason or "").strip()
	if not release_reason:
		return _error("RELEASE_REASON_REQUIRED", _("Release reason is required."))

	name = frappe.db.exists("Budget Reservation", reservation_id)
	if not name:
		name = frappe.db.get_value(
			"Budget Reservation",
			{"reservation_id": reservation_id},
			"name",
		)
	if not name:
		return _error("RESERVATION_NOT_FOUND", _("Budget Reservation not found."))

	frappe.db.sql("""SELECT name FROM `tabBudget Reservation` WHERE name=%s FOR UPDATE""", (name,))
	res = frappe.get_doc("Budget Reservation", name)
	if res.status != "Active":
		return _error("RESERVATION_NOT_ACTIVE", _("Only an active reservation can be released."))

	frappe.db.sql("""SELECT name FROM `tabBudget Line` WHERE name=%s FOR UPDATE""", (res.budget_line,))
	bl = frappe.get_doc("Budget Line", res.budget_line)
	new_reserved = flt(bl.amount_reserved) - flt(res.amount)
	if new_reserved < -1e-9:
		return _error(
			"RESERVATION_RELEASE_FAILED",
			_("Budget Line reserved amount would become negative."),
		)

	try:
		bl.amount_reserved = new_reserved
		frappe.flags.budget_control_service_write = True
		try:
			bl.save(ignore_permissions=True)
		finally:
			frappe.flags.budget_control_service_write = False
		actor_user = actor or frappe.session.user
		res.reload()
		res.status = "Released"
		res.released_at = now_datetime()
		res.released_by = actor_user
		res.release_reason = release_reason
		res.save(ignore_permissions=True)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "release_reservation_failed")
		return _error("RESERVATION_RELEASE_FAILED", _("Reservation release failed."))

	_alloc, _res, _con, avail_after = _line_financials(bl)
	return _success(
		{
			"reservation_id": res.reservation_id,
			"status": "Released",
			"budget_line_id": bl.name,
			"budget_line_code": bl.budget_line_code,
			"released_amount": flt(res.amount),
			"available_after_release": avail_after,
			"released_at": res.released_at,
			"released_by": res.released_by,
		},
		_("Reservation released successfully"),
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
