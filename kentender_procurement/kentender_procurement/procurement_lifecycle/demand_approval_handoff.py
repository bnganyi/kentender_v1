# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-INT-007 — approved MVP Demand → Procurement Planning handoff.

## Goal

``create_demand_approval_certificate`` reads the canonical MVP ``Demand``, standalone
``Demand Item`` and confirmed ``Demand Funding Allocation`` records. It remains live
whenever the Demand DocType exists, independently of the migration flag.

## Handoff card produced

| Field | Value |
|---|---|
| handoff_code | ``DEMAPP-{journey_suffix}`` (e.g. ``DEMAPP-MOH-2026-001``) |
| source_module | ``Demands`` |
| target_module | ``Procurement Planning`` |
| source_object_type | ``Demand`` |
| source_object_code | ``Demand.demand_code`` |

## Handoff code derivation

``JRN-MOH-2026-001`` → strip ``JRN-`` prefix → ``DEMAPP-MOH-2026-001``.

## Demand lookup

The service looks up ``Demand.demand_code`` first and accepts the internal document
name only as an API compatibility fallback.

## Evidence links (two)

1. **Approved Demand** — ``Demand`` DocType, routes to the Demand desk page.
2. **Demand Approval** — conceptual approval certificate linked to the approved Demand.

## Fiscal year / currency resolution

Planning funding identity is resolved through the confirmed Demand Funding Allocation.

## Error codes

| Code | Condition |
|---|---|
| ``INVALID_DEMAND_CODE`` | ``demand_code`` is blank or not a string. |
| ``INVALID_JOURNEY_CODE`` | ``journey_code`` is blank or not a string. |
| ``DEMAND_NOT_FOUND`` | No Demand with the given business code / name. |
| ``DEMAND_NOT_APPROVED`` | Demand is not Approved and planning-ready. |
| ``JOURNEY_NOT_FOUND`` | ``journey_code`` does not exist (raised by R3-001). |
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import flt
from kentender_procurement.procurement_lifecycle.demand_module_gate import (
    RETIRED_MESSAGE,
    demand_doctype_available,
)

from kentender_procurement.procurement_lifecycle.handoff_card_service import (
    create_or_update_handoff_card,
)

_DEMAND_DETAIL_ROUTE_PREFIX = "/desk/demand-detail"


def _handoff_code(journey_code: str) -> str:
    """Derive DEMAPP handoff code from a journey code.

    ``JRN-MOH-2026-001`` → ``DEMAPP-MOH-2026-001``.
    """
    suffix = journey_code[4:] if journey_code.upper().startswith("JRN-") else journey_code
    return f"DEMAPP-{suffix}"


def _approval_code_from_demand_code(demand_code: str) -> str:
    """Derive a stable approval reference from an MVP Demand business code."""
    suffix = demand_code[4:] if demand_code.upper().startswith(("DMD-", "DEM-")) else demand_code
    return f"DEMAPPROVAL-{suffix}"


def _find_demand(demand_code: str) -> dict[str, Any] | None:
    """Return an MVP Demand by business code, with a name fallback."""
    fields = [
        "name",
        "demand_code",
        "title",
        "status",
        "procuring_entity",
        "owner_org_unit",
        "procurement_category",
        "confirmed_estimate",
        "planning_ready",
        "planning_usage",
        "approved_baseline_version",
        "modified",
    ]
    rows = frappe.db.get_all(
        "Demand",
        filters={"demand_code": demand_code},
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


def _get_budget_line_code(budget_line_frappe_name: str) -> str:
    """Return the business code from a Budget Line record (generated_reference)."""
    if not budget_line_frappe_name:
        return ""
    val = frappe.db.get_value("Budget Line", budget_line_frappe_name, "generated_reference")
    if not val:
        try:
            val = frappe.db.get_value("Budget Line", budget_line_frappe_name, "budget_line_code")
        except Exception:
            val = None
    return str(val or budget_line_frappe_name)


def _get_first_demand_item(demand_frappe_name: str) -> dict[str, Any] | None:
    """Return the first standalone MVP Demand Item."""
    rows = frappe.db.get_all(
        "Demand Item",
        filters={"demand": demand_frappe_name},
        fields=["name", "item_code", "description"],
        limit=1,
        order_by="creation asc",
    )
    return rows[0] if rows else None


def _get_confirmed_funding_allocation(demand_name: str) -> dict[str, Any]:
    rows = frappe.db.get_all(
        "Demand Funding Allocation",
        filters={"demand": demand_name, "bo_confirmation_status": "Confirmed"},
        fields=["budget_line", "allocation_amount", "funding_reservation"],
        limit=1,
        order_by="creation asc",
    )
    return dict(rows[0]) if rows else {}


def _source_state_hash(payload: dict[str, Any]) -> str:
    serialised = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(serialised.encode()).hexdigest()


def create_demand_approval_certificate(
    demand_code: str, journey_code: str
) -> dict[str, Any]:
    """Upsert the Demand Approval Certificate handoff card for a journey.

    :param demand_code: ``Demand.demand_code``; an internal name is also accepted.
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

    if not demand_doctype_available():
        raise ValueError(f"DEMAND_MODULE_RETIRED: {RETIRED_MESSAGE}")

    demand = _find_demand(dem_code)
    if demand is None:
        raise ValueError(
            f"DEMAND_NOT_FOUND: no Demand with demand_code or name = {dem_code!r}"
        )

    demand_status = str(demand.get("status") or "")
    if demand_status != "Approved" or not int(demand.get("planning_ready") or 0):
        raise ValueError(
            f"DEMAND_NOT_APPROVED: Demand {dem_code!r} must be Approved and planning_ready."
        )

    demand_frappe_name: str = str(demand["name"])
    demand_business_code: str = str(demand.get("demand_code") or dem_code)
    demand_title: str = str(demand.get("title") or "")
    confirmed_estimate = flt(demand.get("confirmed_estimate") or 0)

    funding = _get_confirmed_funding_allocation(demand_frappe_name)
    budget_line_frappe_name = str(funding.get("budget_line") or "")
    budget_line_code = _get_budget_line_code(budget_line_frappe_name)

    first_item = _get_first_demand_item(demand_frappe_name)
    approved_need = str((first_item or {}).get("description") or demand_title).strip()
    demand_item_code = str((first_item or {}).get("item_code") or "")

    approval_code = _approval_code_from_demand_code(demand_business_code)
    demand_desk_route = f"{_DEMAND_DETAIL_ROUTE_PREFIX}/{demand_frappe_name}"

    locked_summary: dict[str, Any] = {
        "demand_code": demand_business_code,
        "demand_title": demand_title,
        "status": demand_status,
        "planning_ready": int(demand.get("planning_ready") or 0),
        "planning_usage": str(demand.get("planning_usage") or "Not taken up"),
        "approved_baseline_version": int(demand.get("approved_baseline_version") or 0),
        "approved_estimated_value": confirmed_estimate,
        "budget_line": budget_line_code,
        "procurement_category": str(demand.get("procurement_category") or ""),
    }

    passed_forward: dict[str, Any] = {
        "approved_need": approved_need,
        "owner_org_unit": str(demand.get("owner_org_unit") or ""),
        "planning_action": "Include in Procurement Planning",
    }

    evidence_links: list[dict[str, str]] = [
        {
            "label": "Approved Demand",
            "object_type": "Demand",
            "object_code": demand_business_code,
            "module": "Demands",
            "route": demand_desk_route,
            "visibility": "Internal",
        },
        {
            "label": "Demand Approval",
            "object_type": "Demand Approval",
            "object_code": approval_code,
            "module": "Demands",
            "route": demand_desk_route,
            "visibility": "Internal",
        },
    ]

    technical_refs = {
        "demand_item_code": demand_item_code,
        "budget_line_code": budget_line_code,
        "funding_reservation": str(funding.get("funding_reservation") or ""),
    }

    payload: dict[str, Any] = {
        "handoff_code": _handoff_code(jrn_code),
        "handoff_title": "Demand Approval Certificate",
        "journey_code": jrn_code,
        "source_module": "Demands",
        "target_module": "Procurement Planning",
        "source_object_type": "Demand",
        "source_object_code": demand_business_code,
        "status": "Consumed",
        "generated_by": frappe.session.user or "system",
        "next_action": (
            "Review the approved Demand and include it in Procurement Planning."
        ),
        "locked_summary": locked_summary,
        "passed_forward_summary": passed_forward,
        "evidence_links": evidence_links,
        "technical_refs": technical_refs,
        "source_state_hash": _source_state_hash(
            {"demand": demand, "item": first_item or {}, "funding": funding}
        ),
    }

    return create_or_update_handoff_card(payload)
