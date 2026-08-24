# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-002 / LV-R3-002-01 — **Strategy alignment handoff service** (cursor pack §8.2).

## Goal

``create_strategy_alignment_reference(strategy_ref, journey_code)`` produces (or updates)
the ``Procurement Handoff Card`` that records the Strategy → Budget module boundary event.
It resolves the Strategy Objective through kentender_strategy's own published
``get_strategy_lineage`` contract (STR-CHG-001 v1.3 §10) — never a direct read
of a Strategy table — builds a typed payload, and delegates to the generic
``create_or_update_handoff_card`` (R3-001).

STR-CHG-001 v1.3 note (2026-08-24): this rebuild's Strategy Node has no
business "code" field distinct from its generated id (STR-BR-016 — every
identifier is system-generated only). ``strategy_ref`` is therefore the
Strategy Node's real generated id (its docname), not a legacy
``objective_code``-style string. Callers that still pass a pre-rebuild
literal code (e.g. ``OBJ-MOH-HOSP-RENOV``) will get ``OBJECTIVE_NOT_FOUND`` —
a real, correct rejection, not a bug in this function.

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


def _resolve_objective_lineage(strategy_ref: str) -> dict[str, Any] | None:
    """Resolve a Strategy Node id (a Strategic Objective) via
    kentender_strategy's published get_strategy_lineage contract.

    Returns {"name", "title", "programme_title", "programme_id"} or None —
    never touches a Strategy table directly.
    """
    from kentender_strategy.services.strategy_consumer import get_strategy_lineage

    try:
        lineage = get_strategy_lineage(strategy_ref)
    except frappe.DoesNotExistError:
        return None

    path = lineage.get("path") or []
    objective_entry = next((p for p in path if p.get("type") == "Strategic Objective"), None)
    if not objective_entry or objective_entry.get("id") != strategy_ref:
        # strategy_ref resolved to a real Strategy reference, but not to an
        # Objective itself (e.g. an Indicator/Target/Outcome id) — R3-002's
        # own contract is objective-scoped.
        return None
    programme_entry = next((p for p in path if p.get("type") == "Programme"), None)
    return {
        "name": objective_entry["id"],
        "title": objective_entry["title"],
        "programme_title": (programme_entry or {}).get("title") or "",
        "programme_id": (programme_entry or {}).get("id") or "",
    }


def create_strategy_alignment_reference(
    strategy_ref: str, journey_code: str
) -> dict[str, Any]:
    """Upsert the Strategy Alignment Reference handoff card for a journey.

    :param strategy_ref: the Strategy Node's real generated id (a Strategic
        Objective), resolved via kentender_strategy's get_strategy_lineage
        contract.
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

    lineage = _resolve_objective_lineage(obj_code)
    if not lineage:
        raise ValueError(
            f"OBJECTIVE_NOT_FOUND: no Strategy Objective with id = {obj_code!r}"
        )

    obj_name: str = lineage["name"]
    obj_title: str = lineage["title"] or obj_code
    program_title: str = lineage["programme_title"]
    program_code: str = lineage["programme_id"]  # generated id — no separate business code (STR-BR-016)

    # This rebuild's Strategy Node does not expose "the target for an
    # Objective" as a 1:1 relationship (a Target measures an Indicator,
    # which measures an Objective or Outcome — not the Objective directly),
    # so target enrichment is intentionally omitted rather than guessed.
    target_title: str = ""

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
            **({"programme_code": program_code} if program_code else {}),
        },
    }

    return create_or_update_handoff_card(payload)
