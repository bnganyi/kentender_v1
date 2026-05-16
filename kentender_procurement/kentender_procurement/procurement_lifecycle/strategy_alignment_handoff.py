# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-002 / LV-R3-002-01 — **Strategy alignment handoff service** (cursor pack §8.2).

## Goal

``create_strategy_alignment_reference(strategy_ref, journey_code)`` produces (or updates)
the ``Procurement Handoff Card`` that records the Strategy → Budget module boundary event.
It reads live Strategy module data (``Strategy Objective``, ``Strategy Program``,
``Strategy Target``), builds a typed payload, and delegates to the generic
``create_or_update_handoff_card`` (R3-001).

## Handoff card produced

| Field | Value |
|---|---|
| handoff_code | ``STRATREF-{journey_suffix}`` (e.g. ``STRATREF-MOH-2026-001``) |
| source_module | ``Strategy`` |
| target_module | ``Budget`` |
| source_object_type | ``Strategy Objective`` |
| source_object_code | ``strategy_ref`` (the objective_code) |

## Handoff code derivation

``JRN-MOH-2026-001`` → strip ``JRN-`` prefix → ``STRATREF-MOH-2026-001``.
If the journey_code does not start with ``JRN-`` the full code is used as suffix.

## Idempotency

Re-running with the same ``(strategy_ref, journey_code)`` pair updates the existing
card in place and returns ``action="updated"`` (or ``"created"`` on first run).

## Error codes

| Code | Condition |
|---|---|
| ``INVALID_STRATEGY_REF`` | ``strategy_ref`` is blank or not a string. |
| ``INVALID_JOURNEY_CODE`` | ``journey_code`` is blank or not a string. |
| ``OBJECTIVE_NOT_FOUND`` | No ``Strategy Objective`` with ``objective_code = strategy_ref``. |
| ``JOURNEY_NOT_FOUND`` | ``journey_code`` does not exist (raised by R3-001 generic service). |
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_lifecycle.handoff_card_service import (
    create_or_update_handoff_card,
)

# Desk URL prefix for Strategy Objective — used to build the evidence link ``route``.
_OBJ_DESK_ROUTE_PREFIX = "/app/strategy-objective"


def _handoff_code(journey_code: str) -> str:
    """Derive STRATREF handoff code from a journey code.

    ``JRN-MOH-2026-001`` → ``STRATREF-MOH-2026-001``.
    Non-``JRN-`` prefixed codes are used as-is after the ``STRATREF-`` prefix.
    """
    suffix = journey_code[4:] if journey_code.upper().startswith("JRN-") else journey_code
    return f"STRATREF-{suffix}"


def _find_objective_by_code(objective_code: str) -> dict[str, Any] | None:
    """Return the first Strategy Objective row matching ``objective_code``.

    Returns a dict with ``name``, ``objective_title``, ``strategic_plan``, ``program``.
    """
    rows = frappe.db.get_all(
        "Strategy Objective",
        filters={"objective_code": objective_code},
        fields=["name", "objective_title", "strategic_plan", "program"],
        limit=1,
        order_by="creation asc",
    )
    return rows[0] if rows else None


def create_strategy_alignment_reference(
    strategy_ref: str, journey_code: str
) -> dict[str, Any]:
    """Upsert the Strategy Alignment Reference handoff card for a journey.

    :param strategy_ref: ``Strategy Objective`` code (``objective_code`` field,
        e.g. ``OBJ-MOH-HOSP-RENOV``).  Also accepted as a direct Frappe DocType
        ``name`` (auto-detected if no match on ``objective_code``).
    :param journey_code: Procurement Journey code (e.g. ``JRN-MOH-2026-001``).
    :returns: Result dict from ``create_or_update_handoff_card``.
    :raises ValueError: If inputs are blank or the objective is not found.
    """
    if not strategy_ref or not isinstance(strategy_ref, str) or not strategy_ref.strip():
        raise ValueError(
            "INVALID_STRATEGY_REF: strategy_ref must be a non-empty string (objective_code)"
        )
    if not journey_code or not isinstance(journey_code, str) or not journey_code.strip():
        raise ValueError(
            "INVALID_JOURNEY_CODE: journey_code must be a non-empty string"
        )

    obj_code = strategy_ref.strip()
    jrn_code = journey_code.strip()

    # Locate the Strategy Objective — prefer objective_code lookup, fall back to name
    obj_row = _find_objective_by_code(obj_code)
    if obj_row is None:
        # Try direct name lookup (Frappe docname)
        if frappe.db.exists("Strategy Objective", obj_code):
            obj_row = frappe.db.get_value(
                "Strategy Objective",
                obj_code,
                ["name", "objective_title", "strategic_plan", "program"],
                as_dict=True,
            )
    if not obj_row:
        raise ValueError(
            f"OBJECTIVE_NOT_FOUND: no Strategy Objective with objective_code or name = {obj_code!r}"
        )

    obj_name: str = str(obj_row["name"])
    obj_title: str = str(obj_row.get("objective_title") or obj_code)
    plan_name: str = str(obj_row.get("strategic_plan") or "")
    program_frappe_name: str = str(obj_row.get("program") or "")

    # Resolve programme code + title from Strategy Program
    program_code: str = ""
    program_title: str = ""
    if program_frappe_name:
        prog = frappe.db.get_value(
            "Strategy Program",
            program_frappe_name,
            ["program_code", "program_title"],
            as_dict=True,
        )
        if prog:
            program_code = str(prog.get("program_code") or "")
            program_title = str(prog.get("program_title") or "")

    # Resolve target (first one for this objective)
    target_code: str = ""
    target_title: str = ""
    target_rows = frappe.db.get_all(
        "Strategy Target",
        filters={"objective": obj_name},
        fields=["target_code", "target_title"],
        limit=1,
        order_by="creation asc",
    )
    if target_rows:
        target_code = str(target_rows[0].get("target_code") or "")
        target_title = str(target_rows[0].get("target_title") or "")

    # Evidence link route for the Strategy Objective desk page
    obj_route = f"{_OBJ_DESK_ROUTE_PREFIX}/{obj_name}"

    payload: dict[str, Any] = {
        "handoff_code": _handoff_code(jrn_code),
        "handoff_title": "Strategy Alignment Reference",
        "journey_code": jrn_code,
        "source_module": "Strategy",
        "target_module": "Budget",
        "source_object_type": "Strategy Objective",
        "source_object_code": obj_code,
        "status": "Consumed",
        "generated_by": frappe.session.user or "system",
        "next_action": (
            "Fund this strategic infrastructure priority through an approved budget line."
        ),
        "locked_summary": {
            "strategy_plan": plan_name,
            "programme": program_code,
            "objective": obj_code,
        },
        "passed_forward_summary": {
            "strategic_priority": obj_title,
            **({"target": target_title} if target_title else {}),
            **({"recommended_budget_area": program_title} if program_title else {}),
        },
        "evidence_links": [
            {
                "label": "Strategy Objective",
                "object_type": "Strategy Objective",
                "object_code": obj_code,
                "module": "Strategy",
                "route": obj_route,
                "visibility": "Internal",
            }
        ],
        "technical_refs": {
            **({"strategy_plan_code": plan_name} if plan_name else {}),
            **({"programme_code": program_code} if program_code else {}),
            **({"target_code": target_code} if target_code else {}),
        },
    }

    return create_or_update_handoff_card(payload)
