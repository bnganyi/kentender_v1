# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-004 / LV-R3-004-01 — **Demand approval handoff service** (cursor pack §8.2).

## Goal

``create_demand_approval_certificate(demand_code, journey_code)`` produces (or updates)
the ``Procurement Handoff Card`` that records the Demand Intake and Approval →
Procurement Planning module boundary event.  It reads live Demand module data
(``Demand``, ``Demand Item``, ``Procuring Department``, ``Budget Line``), builds a
typed payload, and delegates to the generic ``create_or_update_handoff_card`` (R3-001).

## Handoff card produced

| Field | Value |
|---|---|
| handoff_code | ``DEMAPP-{journey_suffix}`` (e.g. ``DEMAPP-MOH-2026-001``) |
| source_module | ``Demand Intake and Approval`` |
| target_module | ``Procurement Planning`` |
| source_object_type | ``Demand`` |
| source_object_code | ``demand_code`` (``demand_id`` field value) |

## Handoff code derivation

``JRN-MOH-2026-001`` → strip ``JRN-`` prefix → ``DEMAPP-MOH-2026-001``.

## Demand lookup

``demand_code`` is treated as the ``demand_id`` field (e.g. ``DEM-MOH-2026-001``).
The service looks up ``Demand`` by ``demand_id = demand_code`` first; if no match it
falls back to a direct Frappe ``name`` lookup.  This handles both the live scenario
(where demand_id == name) and edge cases where the naming series diverges.

## Evidence links (two)

1. **Approved Demand** — ``Demand`` DocType, routes to the Demand desk page.
2. **Demand Approval Record** — conceptual approval certificate; the approval code is
   derived as ``DEMAPPROVAL-{demand_id_suffix}`` (strips the ``DEM-`` prefix from
   ``demand_id``).  No separate ``Demand Approval`` DocType exists; this is a
   traceable approval reference consistent with spec §16.4.

## Fiscal year / currency resolution

Currency is resolved from the linked ``Budget Line``.  If no budget line is linked,
``currency`` defaults to empty string.

## Error codes

| Code | Condition |
|---|---|
| ``INVALID_DEMAND_CODE`` | ``demand_code`` is blank or not a string. |
| ``INVALID_JOURNEY_CODE`` | ``journey_code`` is blank or not a string. |
| ``DEMAND_NOT_FOUND`` | No ``Demand`` with the given ``demand_id`` / ``name``. |
| ``DEMAND_NOT_APPROVED`` | Demand ``status`` is not ``Approved``. |
| ``JOURNEY_NOT_FOUND`` | ``journey_code`` does not exist (raised by R3-001). |
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_lifecycle.handoff_card_service import (
    create_or_update_handoff_card,
)

_DEMAND_DESK_ROUTE_PREFIX = "/app/demand"
_APPROVED_STATUS = "Approved"


def _handoff_code(journey_code: str) -> str:
    """Derive DEMAPP handoff code from a journey code.

    ``JRN-MOH-2026-001`` → ``DEMAPP-MOH-2026-001``.
    """
    suffix = journey_code[4:] if journey_code.upper().startswith("JRN-") else journey_code
    return f"DEMAPP-{suffix}"


def _approval_code_from_demand_id(demand_id: str) -> str:
    """Derive a Demand Approval reference code from the demand_id.

    ``DEM-MOH-2026-001`` → ``DEMAPPROVAL-MOH-2026-001``.
    """
    suffix = demand_id[4:] if demand_id.upper().startswith("DEM-") else demand_id
    return f"DEMAPPROVAL-{suffix}"


def _find_demand(demand_code: str) -> dict[str, Any] | None:
    """Return Demand row dict or None.

    Searches first by ``demand_id`` field, then falls back to Frappe ``name``.
    """
    fields = [
        "name",
        "demand_id",
        "title",
        "status",
        "total_amount",
        "budget_line",
        "requesting_department",
        "requisition_type",
        "finance_approved_at",
    ]
    # Primary: lookup by demand_id field
    rows = frappe.db.get_all(
        "Demand",
        filters={"demand_id": demand_code},
        fields=fields,
        limit=1,
        order_by="creation asc",
    )
    if rows:
        return rows[0]
    # Fallback: direct name lookup
    if frappe.db.exists("Demand", demand_code):
        return frappe.db.get_value("Demand", demand_code, fields, as_dict=True)
    return None


def _get_department_name(dept_frappe_name: str) -> str:
    """Return the business display name for a Procuring Department row."""
    if not dept_frappe_name:
        return ""
    val = frappe.db.get_value("Procuring Department", dept_frappe_name, "department_name")
    return str(val or "")


def _get_budget_line_currency(budget_line_frappe_name: str) -> str:
    """Return the currency from a Budget Line record."""
    if not budget_line_frappe_name:
        return ""
    val = frappe.db.get_value("Budget Line", budget_line_frappe_name, "currency")
    return str(val or "")


def _get_budget_line_code(budget_line_frappe_name: str) -> str:
    """Return the budget_line_code from a Budget Line record."""
    if not budget_line_frappe_name:
        return ""
    # Budget Line.name == budget_line_code in most cases; also check the field
    val = frappe.db.get_value("Budget Line", budget_line_frappe_name, "budget_line_code")
    return str(val or budget_line_frappe_name)


def _get_first_demand_item(demand_frappe_name: str) -> dict[str, Any] | None:
    """Return the first Demand Item child row for a demand, or None."""
    rows = frappe.db.get_all(
        "Demand Item",
        filters={"parent": demand_frappe_name, "parenttype": "Demand"},
        fields=["name", "item_description", "category"],
        limit=1,
        order_by="idx asc",
    )
    return rows[0] if rows else None


def create_demand_approval_certificate(
    demand_code: str, journey_code: str
) -> dict[str, Any]:
    """Upsert the Demand Approval Certificate handoff card for a journey.

    :param demand_code: ``Demand`` identifier (``demand_id`` field, e.g.
        ``DEM-MOH-2026-001``).  Also accepted as a direct Frappe DocType ``name``.
    :param journey_code: Procurement Journey code (e.g. ``JRN-MOH-2026-001``).
    :returns: Result dict from ``create_or_update_handoff_card``.
    :raises ValueError: If inputs are blank, demand not found, or demand not approved.
    """
    if not demand_code or not isinstance(demand_code, str) or not demand_code.strip():
        raise ValueError(
            "INVALID_DEMAND_CODE: demand_code must be a non-empty string"
        )
    if not journey_code or not isinstance(journey_code, str) or not journey_code.strip():
        raise ValueError(
            "INVALID_JOURNEY_CODE: journey_code must be a non-empty string"
        )

    dem_code = demand_code.strip()
    jrn_code = journey_code.strip()

    demand = _find_demand(dem_code)
    if demand is None:
        raise ValueError(
            f"DEMAND_NOT_FOUND: no Demand with demand_id or name = {dem_code!r}"
        )

    demand_status = str(demand.get("status") or "")
    if demand_status != _APPROVED_STATUS:
        raise ValueError(
            f"DEMAND_NOT_APPROVED: Demand {dem_code!r} has status {demand_status!r}; "
            "only Approved demands can produce a handoff certificate."
        )

    demand_frappe_name: str = str(demand["name"])
    demand_id: str = str(demand.get("demand_id") or dem_code)
    demand_title: str = str(demand.get("title") or "")
    total_amount: float = float(demand.get("total_amount") or 0)
    budget_line_frappe_name: str = str(demand.get("budget_line") or "")
    dept_frappe_name: str = str(demand.get("requesting_department") or "")
    requisition_type: str = str(demand.get("requisition_type") or "")

    # Resolve display values
    department_name = _get_department_name(dept_frappe_name)
    currency = _get_budget_line_currency(budget_line_frappe_name)
    budget_line_code = _get_budget_line_code(budget_line_frappe_name)

    # First demand item for approved_need and technical ref
    first_item = _get_first_demand_item(demand_frappe_name)
    approved_need: str = str((first_item or {}).get("item_description") or "").strip()
    demand_item_name: str = str((first_item or {}).get("name") or "")

    # Derive codes
    approval_code = _approval_code_from_demand_id(demand_id)
    demand_desk_route = f"{_DEMAND_DESK_ROUTE_PREFIX}/{demand_frappe_name}"

    # locked_summary (spec §16.4)
    locked_summary: dict[str, Any] = {
        "demand_code": demand_id,
        "demand_title": demand_title,
        "approved_estimated_value": total_amount,
    }
    if currency:
        locked_summary["currency"] = currency
    if budget_line_code:
        locked_summary["budget_line"] = budget_line_code
    if requisition_type:
        locked_summary["procurement_category"] = requisition_type

    # passed_forward_summary (spec §16.4)
    passed_forward: dict[str, Any] = {
        "planning_action": "Create procurement package",
    }
    if approved_need:
        passed_forward["approved_need"] = approved_need
    if department_name:
        passed_forward["requesting_department"] = department_name

    # Evidence links (two per spec §16.4)
    evidence_links: list[dict[str, str]] = [
        {
            "label": "Approved Demand",
            "object_type": "Demand",
            "object_code": demand_id,
            "module": "Demand Intake and Approval",
            "route": demand_desk_route,
            "visibility": "Internal",
        },
        {
            "label": "Demand Approval Record",
            "object_type": "Demand Approval",
            "object_code": approval_code,
            "module": "Demand Intake and Approval",
            "route": demand_desk_route,  # Routes to demand page; approval is embedded
            "visibility": "Internal",
        },
    ]

    # technical_refs (spec §16.4)
    technical_refs: dict[str, str] = {}
    if demand_item_name:
        technical_refs["demand_item_code"] = demand_item_name
    if budget_line_code:
        technical_refs["budget_line_code"] = budget_line_code

    payload: dict[str, Any] = {
        "handoff_code": _handoff_code(jrn_code),
        "handoff_title": "Demand Approval Certificate",
        "journey_code": jrn_code,
        "source_module": "Demand Intake and Approval",
        "target_module": "Procurement Planning",
        "source_object_type": "Demand",
        "source_object_code": demand_id,
        "status": "Consumed",
        "generated_by": frappe.session.user or "system",
        "next_action": (
            "Include the approved Works demand in the procurement plan "
            "and package it for tendering."
        ),
        "locked_summary": locked_summary,
        "passed_forward_summary": passed_forward,
        "evidence_links": evidence_links,
        "technical_refs": technical_refs,
    }

    return create_or_update_handoff_card(payload)
