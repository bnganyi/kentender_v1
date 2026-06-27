# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""Funding check endpoint for Procurement Planning (package/demand readiness).

Provides a single, Planning-oriented HTTP endpoint that answers:
  "Is there sufficient budget on this line for a package/demand of this value?"

This is a read-only check — it does NOT create or modify a reservation.
Use ``kentender_budget.api.dia_budget_control.create_reservation`` (or
``kentender_budget.services.budget_service.reserve``) to create an actual hold.

Endpoint consumed by:
  - PP2 package readiness service (pre-release funding gate)
  - DIA demand readiness checker
  - Planning workbench budget-context drawer
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from kentender_budget.services.budget_service import snapshot


def _ok(data: dict, message: str = "") -> dict:
    return {"ok": True, "data": data, "message": message}


def _err(code: str, message: str) -> dict:
    return {"ok": False, "error_code": code, "message": str(message)}


@frappe.whitelist()
def check_package_funding(
    budget_line_id: str | None = None,
    amount: float | None = None,
    source_doctype: str | None = None,
    source_docname: str | None = None,
) -> dict:
    """Check whether a Budget Line has sufficient available funds.

    Args:
        budget_line_id: Name / code of the Budget Line to check.
        amount: Estimated value of the package or demand (positive float).
        source_doctype: Optional — the calling DocType (e.g. "Procurement Package").
        source_docname: Optional — the calling document name for traceability.

    Returns a structured dict::

        {
          "ok": True,
          "data": {
            "budget_line_id": str,
            "budget_line_code": str,
            "budget_line_name": str,
            "requested_amount": float,
            "amount_allocated": float,
            "amount_reserved": float,
            "amount_committed": float,
            "amount_consumed": float,
            "amount_available": float,
            "is_sufficient": bool,
            "shortfall": float,         # 0 when is_sufficient=True
            "currency": str,
            "source_doctype": str | None,
            "source_docname": str | None,
          }
        }
    """
    if not budget_line_id:
        return _err("BUDGET_LINE_NOT_FOUND", _("Budget Line is required."))

    amt = flt(amount)
    if amt <= 0:
        return _err("INVALID_AMOUNT", _("Amount must be greater than zero."))

    if not frappe.db.exists("Budget Line", budget_line_id):
        return _err("BUDGET_LINE_NOT_FOUND", _("Budget Line not found."))

    bl = frappe.get_doc("Budget Line", budget_line_id)
    if not bl.is_active:
        return _err("BUDGET_LINE_INACTIVE", _("Budget Line is not active."))

    snap = snapshot(budget_line_id)
    shortfall = flt(max(0.0, amt - snap.available))
    is_sufficient = snap.available + 1e-9 >= amt

    return _ok(
        {
            "budget_line_id": bl.name,
            "budget_line_code": bl.budget_line_code,
            "budget_line_name": bl.budget_line_name,
            "requested_amount": amt,
            "amount_allocated": snap.allocated,
            "amount_reserved": snap.reserved,
            "amount_committed": snap.committed,
            "amount_consumed": snap.consumed,
            "amount_available": snap.available,
            "is_sufficient": is_sufficient,
            "shortfall": shortfall,
            "currency": snap.currency,
            "source_doctype": source_doctype,
            "source_docname": source_docname,
        },
        _("Funding check complete"),
    )
