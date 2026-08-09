# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-003 / LV-R3-003-01 — **Budget funding handoff service** (cursor pack §8.2).

## Goal

``create_budget_funding_confirmation(budget_line_code, journey_code)`` produces (or
updates) the ``Procurement Handoff Card`` that records the Budget → Demand Intake and
Approval module boundary event.  It reads live Budget module data (``Budget Line``,
parent ``Budget``), resolves the linked Strategy Objective via the shared programme
reference, builds a typed payload, and delegates to the generic
``create_or_update_handoff_card`` (R3-001).

## Handoff card produced

| Field | Value |
|---|---|
| handoff_code | ``BUDCONF-{journey_suffix}`` (e.g. ``BUDCONF-MOH-2026-001``) |
| source_module | ``Budget`` |
| target_module | ``Demands`` |
| source_object_type | ``Budget Line`` |
| source_object_code | ``budget_line_code`` |

## Handoff code derivation

``JRN-MOH-2026-001`` → strip ``JRN-`` prefix → ``BUDCONF-MOH-2026-001``.
If the journey_code does not start with ``JRN-`` the full code is used as suffix.

## Strategy Objective resolution

The Budget Line carries a ``program`` FK to ``Strategy Program``. The service looks
up the first ``Strategy Objective`` for that programme (ascending creation order) to
surface the ``strategic_objective`` code in ``passed_forward_summary`` and
``technical_refs``.  If no objective is found the field is omitted — this is
non-fatal (budget lines may pre-date the strategy hierarchy in some scenarios).

## Fiscal year formatting

The ``Budget Line.fiscal_year`` integer (e.g. ``2026``) is formatted as
``"2026/2027"`` for the ``locked_summary``.

## Idempotency

Re-running with the same ``(budget_line_code, journey_code)`` pair updates the
existing card and returns ``action="updated"``.

## Error codes

| Code | Condition |
|---|---|
| ``INVALID_BUDGET_LINE_CODE`` | ``budget_line_code`` is blank or not a string. |
| ``INVALID_JOURNEY_CODE`` | ``journey_code`` is blank or not a string. |
| ``BUDGET_LINE_NOT_FOUND`` | No ``Budget Line`` with the given code. |
| ``JOURNEY_NOT_FOUND`` | ``journey_code`` does not exist (raised by R3-001). |
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_lifecycle.handoff_card_service import (
    create_or_update_handoff_card,
)

_BUDGET_LINE_DESK_ROUTE_PREFIX = "/app/budget-line"


def _handoff_code(journey_code: str) -> str:
    """Derive BUDCONF handoff code from a journey code.

    ``JRN-MOH-2026-001`` → ``BUDCONF-MOH-2026-001``.
    """
    suffix = journey_code[4:] if journey_code.upper().startswith("JRN-") else journey_code
    return f"BUDCONF-{suffix}"


def _format_fiscal_year(fy_int: int | None) -> str:
    """Format fiscal year integer as ``"YYYY/YYYY+1"`` string (e.g. 2026 → "2026/2027")."""
    if not fy_int:
        return ""
    try:
        y = int(fy_int)
        return f"{y}/{y + 1}"
    except (TypeError, ValueError):
        return str(fy_int)


def _find_budget_line(budget_line_code: str) -> dict[str, Any] | None:
    """Return Budget Line row dict or None.

    Frappe auto-names Budget Line with ``budget_line_code`` so the ``name`` field
    equals the code; we try a direct name lookup first, then fall back to a field
    filter on ``budget_line_code``.
    """
    fields = [
        "name",
        "budget_line_code",
        "budget_line_name",
        "budget",
        "amount_allocated",
        "amount_reserved",
        "amount_available",
        "currency",
        "funding_source",
        "fiscal_year",
        "strategic_plan",
        "program",
        "is_active",
    ]
    # Direct name lookup (fast path — name == budget_line_code in most cases)
    if frappe.db.exists("Budget Line", budget_line_code):
        row = frappe.db.get_value("Budget Line", budget_line_code, fields, as_dict=True)
        if row:
            return row
    # Field-based fallback for cases where naming series differs
    rows = frappe.db.get_all(
        "Budget Line",
        filters={"budget_line_code": budget_line_code},
        fields=fields,
        limit=1,
        order_by="creation asc",
    )
    return rows[0] if rows else None


def _find_objective_code_for_program(program_frappe_name: str) -> str:
    """Return the ``objective_code`` for the first Strategy Objective in a programme."""
    if not program_frappe_name:
        return ""
    rows = frappe.db.get_all(
        "Strategy Objective",
        filters={"program": program_frappe_name},
        fields=["objective_code"],
        limit=1,
        order_by="creation asc",
    )
    if rows:
        return str(rows[0].get("objective_code") or "")
    return ""


def create_budget_funding_confirmation(
    budget_line_code: str, journey_code: str
) -> dict[str, Any]:
    """Upsert the Budget Funding Confirmation handoff card for a journey.

    :param budget_line_code: ``Budget Line`` code (``budget_line_code`` field /
        Frappe ``name``, e.g. ``BUD-MOH-INFRA-2026-001``).
    :param journey_code: Procurement Journey code (e.g. ``JRN-MOH-2026-001``).
    :returns: Result dict from ``create_or_update_handoff_card``.
    :raises ValueError: If inputs are blank or the budget line is not found.
    """
    if not budget_line_code or not isinstance(budget_line_code, str) or not budget_line_code.strip():
        raise ValueError(
            "INVALID_BUDGET_LINE_CODE: budget_line_code must be a non-empty string"
        )
    if not journey_code or not isinstance(journey_code, str) or not journey_code.strip():
        raise ValueError(
            "INVALID_JOURNEY_CODE: journey_code must be a non-empty string"
        )

    bl_code = budget_line_code.strip()
    jrn_code = journey_code.strip()

    bl = _find_budget_line(bl_code)
    if bl is None:
        raise ValueError(
            f"BUDGET_LINE_NOT_FOUND: no Budget Line with code {bl_code!r}"
        )

    # Resolve parent Budget name (used as budget_code in technical_refs)
    budget_frappe_name: str = str(bl.get("budget") or "")
    budget_code: str = ""
    if budget_frappe_name:
        budget_name_field = frappe.db.get_value("Budget", budget_frappe_name, "budget_name")
        budget_code = str(budget_name_field or budget_frappe_name)

    # Resolve Strategy Objective via shared programme
    program_frappe_name: str = str(bl.get("program") or "")
    objective_code: str = _find_objective_code_for_program(program_frappe_name)

    # Fiscal year formatting
    fiscal_year_str = _format_fiscal_year(bl.get("fiscal_year"))

    # Build locked_summary (spec §16.3)
    locked_summary: dict[str, Any] = {
        "budget_line": bl_code,
        "approved_amount": float(bl.get("amount_allocated") or 0),
        "currency": str(bl.get("currency") or ""),
    }
    if bl.get("funding_source"):
        locked_summary["funding_source"] = str(bl["funding_source"])
    if fiscal_year_str:
        locked_summary["fiscal_year"] = fiscal_year_str

    # Build passed_forward_summary (spec §16.3)
    passed_forward: dict[str, Any] = {
        "available_for_procurement_request": bool(bl.get("is_active", True)),
    }
    amount_reserved = float(bl.get("amount_reserved") or 0)
    if amount_reserved > 0:
        passed_forward["reserved_for_master_demand"] = amount_reserved
    if objective_code:
        passed_forward["strategic_objective"] = objective_code

    # Build evidence link with Desk route
    bl_route = f"{_BUDGET_LINE_DESK_ROUTE_PREFIX}/{str(bl['name'])}"
    evidence_links = [
        {
            "label": "Budget Line",
            "object_type": "Budget Line",
            "object_code": bl_code,
            "module": "Budget",
            "route": bl_route,
            "visibility": "Internal",
        }
    ]

    # Build technical_refs (spec §16.3)
    technical_refs: dict[str, str] = {}
    if budget_code:
        technical_refs["budget_code"] = budget_code
    if objective_code:
        technical_refs["strategy_objective_code"] = objective_code

    payload: dict[str, Any] = {
        "handoff_code": _handoff_code(jrn_code),
        "handoff_title": "Budget Funding Confirmation",
        "journey_code": jrn_code,
        "source_module": "Budget",
        "target_module": "Demands",
        "source_object_type": "Budget Line",
        "source_object_code": bl_code,
        "status": "Consumed",
        "generated_by": frappe.session.user or "system",
        "next_action": "Raise demand against the approved infrastructure budget line.",
        "locked_summary": locked_summary,
        "passed_forward_summary": passed_forward,
        "evidence_links": evidence_links,
        "technical_refs": technical_refs,
    }

    return create_or_update_handoff_card(payload)
