# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""Central budget financial control service.

This module is the single canonical source for all mutations to Budget Line
balances.  No HTTP endpoints live here — see ``api/dia_budget_control.py``
(reserve/release adapter) and ``api/funding_check.py`` (Planning check).

Formula (Budget Domain Revision §3):
  available = allocated − reserved − committed − consumed

All write operations acquire a ``SELECT … FOR UPDATE`` row-level lock before
the read-modify-write cycle so concurrent requests cannot produce balance
corruption.  Every write goes through ``_save_controlled()`` which sets the
``budget_control_service_write`` flag to bypass the Budget Line validator's
direct-edit guard.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, now_datetime


# ── Response helpers ──────────────────────────────────────────────────────────

def _ok(data: dict[str, Any], message: str = "") -> dict[str, Any]:
    return {"ok": True, "data": data, "message": message}


def _err(error_code: str, message: str) -> dict[str, Any]:
    return {"ok": False, "error_code": error_code, "message": str(message)}


# ── Balance snapshot ──────────────────────────────────────────────────────────

@dataclass
class BalanceSnapshot:
    budget_line_id: str
    allocated: float
    reserved: float
    committed: float
    consumed: float
    available: float
    currency: str


def snapshot(budget_line_id: str) -> BalanceSnapshot:
    """Read-only balance snapshot for a Budget Line.

    Does **not** acquire a row lock.  Use this for display and read checks;
    use the row-locking path inside write operations.
    """
    bl = frappe.get_doc("Budget Line", budget_line_id)
    alloc = flt(bl.amount_allocated)
    res   = flt(bl.amount_reserved)
    com   = flt(getattr(bl, "amount_committed", None) or 0)
    con   = flt(bl.amount_consumed or 0)
    return BalanceSnapshot(
        budget_line_id=bl.name,
        allocated=alloc,
        reserved=res,
        committed=com,
        consumed=con,
        available=flt(alloc - res - com - con),
        currency=bl.currency or "KES",
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _lock_and_load_line(budget_line_id: str):
    """Row-lock then reload Budget Line document. Must be inside a transaction."""
    frappe.db.sql(
        "SELECT name FROM `tabBudget Line` WHERE name=%s FOR UPDATE",
        (budget_line_id,),
    )
    return frappe.get_doc("Budget Line", budget_line_id)


def _save_controlled(bl, **fields: float) -> None:
    """Persist balance field updates, bypassing the direct-edit guard."""
    for key, val in fields.items():
        setattr(bl, key, flt(val))
    frappe.flags.budget_control_service_write = True
    try:
        bl.save(ignore_permissions=True)
    finally:
        frappe.flags.budget_control_service_write = False


def _financials(bl) -> tuple[float, float, float, float, float]:
    """Return (allocated, reserved, committed, consumed, available)."""
    alloc = flt(bl.amount_allocated)
    res   = flt(bl.amount_reserved)
    com   = flt(getattr(bl, "amount_committed", None) or 0)
    con   = flt(bl.amount_consumed or 0)
    return alloc, res, com, con, flt(alloc - res - com - con)


# ── Core operations ───────────────────────────────────────────────────────────

def reserve(
    budget_line_id: str,
    source_doctype: str,
    source_docname: str,
    amount: float,
    actor: str | None = None,
    source_business_id: str | None = None,
) -> dict[str, Any]:
    """Create a Budget Reservation and increment ``amount_reserved``.

    Atomic: row-lock → sufficiency check → insert Reservation → update line.
    Returns ``{"ok": True, "data": {...}}`` on success.
    """
    amt = flt(amount)
    if amt <= 0:
        return _err("INVALID_AMOUNT", _("Amount must be greater than zero."))
    if not budget_line_id:
        return _err("BUDGET_LINE_NOT_FOUND", _("Budget Line is required."))
    if not frappe.db.exists("Budget Line", budget_line_id):
        return _err("BUDGET_LINE_NOT_FOUND", _("Budget Line not found."))
    if not source_doctype or not source_docname:
        return _err("SOURCE_REFERENCE_INVALID", _("Source document reference is required."))

    bl = _lock_and_load_line(budget_line_id)
    if not bl.is_active:
        return _err("BUDGET_LINE_INACTIVE", _("Budget Line is not active."))

    _alloc, _res, _com, _con, avail = _financials(bl)

    if frappe.db.exists(
        "Budget Reservation",
        {"source_doctype": source_doctype, "source_docname": source_docname, "status": "Active"},
    ):
        return _err(
            "DUPLICATE_ACTIVE_RESERVATION",
            _("An active reservation already exists for this source document."),
        )

    if amt > avail + 1e-9:
        return _err("INSUFFICIENT_BUDGET", _("Insufficient available budget to create reservation."))

    actor_user = actor or frappe.session.user
    res_doc = frappe.get_doc({
        "doctype": "Budget Reservation",
        "budget_line": budget_line_id,
        "source_doctype": source_doctype,
        "source_docname": source_docname,
        "source_business_id": source_business_id,
        "amount": amt,
        "status": "Active",
        "created_by": actor_user,
        "available_before_reservation": avail,
        "available_after_reservation": flt(avail - amt),
    })
    try:
        res_doc.insert(ignore_permissions=True)
        bl.reload()
        _save_controlled(bl, amount_reserved=flt(bl.amount_reserved) + amt)
    except Exception:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "budget_service.reserve_failed")
        return _err("RESERVE_FAILED", _("Reservation creation failed — see error log."))

    return _ok(
        {
            "reservation_id": res_doc.reservation_id,
            "reservation_name": res_doc.name,
            "budget_line_id": bl.name,
            "budget_line_code": bl.budget_line_code,
            "source_doctype": source_doctype,
            "source_docname": source_docname,
            "source_business_id": source_business_id,
            "amount": amt,
            "available_before": avail,
            "available_after": flt(avail - amt),
            "currency": bl.currency,
        },
        _("Reservation created successfully"),
    )


def release(
    reservation_id: str,
    reason: str,
    actor: str | None = None,
) -> dict[str, Any]:
    """Release an Active Budget Reservation and restore ``amount_reserved``.

    Atomic: lock Reservation + line → update line → mark Released.
    """
    if not (reason or "").strip():
        return _err("RELEASE_REASON_REQUIRED", _("Release reason is required."))

    name = frappe.db.exists("Budget Reservation", reservation_id) or frappe.db.get_value(
        "Budget Reservation", {"reservation_id": reservation_id}, "name"
    )
    if not name:
        return _err("RESERVATION_NOT_FOUND", _("Budget Reservation not found."))

    frappe.db.sql(
        "SELECT name FROM `tabBudget Reservation` WHERE name=%s FOR UPDATE", (name,)
    )
    res = frappe.get_doc("Budget Reservation", name)
    if res.status != "Active":
        return _err("RESERVATION_NOT_ACTIVE", _("Only Active reservations can be released."))

    bl = _lock_and_load_line(res.budget_line)
    new_reserved = flt(bl.amount_reserved) - flt(res.amount)
    if new_reserved < -1e-9:
        return _err("RELEASE_FAILED", _("Budget Line reserved amount would become negative."))

    actor_user = actor or frappe.session.user
    try:
        _save_controlled(bl, amount_reserved=new_reserved)
        bl.reload()
        res.reload()
        res.status = "Released"
        res.released_at = now_datetime()
        res.released_by = actor_user
        res.release_reason = reason.strip()
        res.save(ignore_permissions=True)
    except Exception:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "budget_service.release_failed")
        return _err("RELEASE_FAILED", _("Reservation release failed — see error log."))

    _a, _r, _c, _co, avail_after = _financials(bl)
    return _ok(
        {
            "reservation_id": res.reservation_id,
            "status": "Released",
            "released_amount": flt(res.amount),
            "available_after_release": avail_after,
            "released_at": str(res.released_at),
            "released_by": res.released_by,
            "currency": bl.currency,
        },
        _("Reservation released successfully"),
    )


def convert_to_commitment(
    reservation_id: str,
    commitment_amount: float | None = None,
    commitment_source_doctype: str | None = None,
    commitment_source_docname: str | None = None,
    actor: str | None = None,
) -> dict[str, Any]:
    """Convert an Active reservation to a Commitment (Award / Contract stage).

    Moves the reservation amount from ``amount_reserved`` to ``amount_committed``
    on the Budget Line.  If ``commitment_amount`` differs from the reservation
    amount (contract value < estimate), the difference is freed back to available.
    ``commitment_amount`` must not exceed the original reservation amount.

    Marks the Budget Reservation status as ``Converted``.
    """
    name = frappe.db.exists("Budget Reservation", reservation_id) or frappe.db.get_value(
        "Budget Reservation", {"reservation_id": reservation_id}, "name"
    )
    if not name:
        return _err("RESERVATION_NOT_FOUND", _("Budget Reservation not found."))

    frappe.db.sql(
        "SELECT name FROM `tabBudget Reservation` WHERE name=%s FOR UPDATE", (name,)
    )
    res = frappe.get_doc("Budget Reservation", name)
    if res.status != "Active":
        return _err("RESERVATION_NOT_ACTIVE", _("Only Active reservations can be converted."))

    reserved_amt = flt(res.amount)
    commit_amt = flt(commitment_amount) if commitment_amount is not None else reserved_amt
    if commit_amt <= 0:
        return _err("INVALID_AMOUNT", _("Commitment amount must be greater than zero."))
    if commit_amt > reserved_amt + 1e-9:
        return _err(
            "COMMITMENT_EXCEEDS_RESERVATION",
            _("Commitment amount ({0}) cannot exceed the reservation amount ({1}).").format(
                commit_amt, reserved_amt
            ),
        )

    bl = _lock_and_load_line(res.budget_line)
    _alloc, cur_reserved, cur_committed, _con, _avail = _financials(bl)

    # reserved decreases by the full reservation amount; committed increases by
    # the (potentially smaller) contract value; the delta is freed.
    new_reserved  = flt(cur_reserved  - reserved_amt)
    new_committed = flt(cur_committed + commit_amt)

    actor_user = actor or frappe.session.user
    try:
        _save_controlled(bl, amount_reserved=new_reserved, amount_committed=new_committed)
        bl.reload()
        res.reload()
        res.status = "Converted"
        res.converted_at = now_datetime()
        res.converted_by = actor_user
        res.commitment_amount = commit_amt
        if commitment_source_doctype:
            res.commitment_source_doctype = commitment_source_doctype
        if commitment_source_docname:
            res.commitment_source_docname = commitment_source_docname
        res.save(ignore_permissions=True)
    except Exception:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "budget_service.convert_to_commitment_failed")
        return _err("CONVERT_FAILED", _("Commitment conversion failed — see error log."))

    _a, r_after, c_after, _co, avail_after = _financials(bl)
    delta_freed = flt(reserved_amt - commit_amt)
    return _ok(
        {
            "reservation_id": res.reservation_id,
            "status": "Converted",
            "reserved_amount": reserved_amt,
            "commitment_amount": commit_amt,
            "delta_freed": delta_freed,
            "reserved_after": r_after,
            "committed_after": c_after,
            "available_after": avail_after,
            "budget_line_id": bl.name,
            "currency": bl.currency,
        },
        _("Reservation converted to commitment successfully"),
    )


def record_consumption(
    budget_line_id: str,
    amount: float,
    source_doctype: str | None = None,
    source_docname: str | None = None,
    actor: str | None = None,
) -> dict[str, Any]:
    """Record actual spend (Payment / Invoice) on a Budget Line.

    Increments ``amount_consumed`` and decrements ``amount_committed`` by the
    same value — a payment discharges the corresponding commitment.

    ``amount`` must not exceed ``amount_committed`` (cannot consume more than
    the legally committed budget).
    """
    amt = flt(amount)
    if amt <= 0:
        return _err("INVALID_AMOUNT", _("Consumption amount must be greater than zero."))
    if not budget_line_id:
        return _err("BUDGET_LINE_NOT_FOUND", _("Budget Line is required."))
    if not frappe.db.exists("Budget Line", budget_line_id):
        return _err("BUDGET_LINE_NOT_FOUND", _("Budget Line not found."))

    bl = _lock_and_load_line(budget_line_id)
    if not bl.is_active:
        return _err("BUDGET_LINE_INACTIVE", _("Budget Line is not active."))

    _alloc, _res, cur_committed, cur_consumed, _avail = _financials(bl)

    if amt > cur_committed + 1e-9:
        return _err(
            "CONSUMPTION_EXCEEDS_COMMITTED",
            _("Consumption amount ({0}) exceeds current committed balance ({1}).").format(
                amt, cur_committed
            ),
        )

    new_committed = flt(cur_committed - amt)
    new_consumed  = flt(cur_consumed  + amt)

    actor_user = actor or frappe.session.user
    try:
        _save_controlled(bl, amount_committed=new_committed, amount_consumed=new_consumed)
        bl.reload()
    except Exception:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "budget_service.record_consumption_failed")
        return _err("CONSUMPTION_FAILED", _("Consumption recording failed — see error log."))

    _a, _r, c_after, co_after, avail_after = _financials(bl)
    return _ok(
        {
            "budget_line_id": bl.name,
            "budget_line_code": bl.budget_line_code,
            "consumed_amount": amt,
            "committed_after": c_after,
            "consumed_after": co_after,
            "available_after": avail_after,
            "source_doctype": source_doctype,
            "source_docname": source_docname,
            "recorded_by": actor_user,
            "currency": bl.currency,
        },
        _("Consumption recorded successfully"),
    )
