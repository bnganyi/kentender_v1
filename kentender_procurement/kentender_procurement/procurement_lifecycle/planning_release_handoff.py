# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-005 / LV-R3-005-01 — **Planning release handoff service** (cursor pack §8.2).

## Goal

``create_planning_release_package(package_code, journey_code)`` produces (or updates)
the ``Procurement Handoff Card`` that records the Procurement Planning →
Tender Management module boundary event.  It reads live Procurement Planning data
(``Procurement Package``, ``Procurement Package Line``, ``Procurement Plan``) and, when
available, the downstream ``TM2 Tender`` that consumed the package, building a typed
payload and delegating to the generic ``create_or_update_handoff_card`` (R3-001).

## Handoff card produced

| Field | Value |
|---|---|
| handoff_code | ``PKGREL-{journey_suffix}`` (e.g. ``PKGREL-MOH-2026-001``) |
| source_module | ``Procurement Planning`` |
| target_module | ``Tender Management`` |
| source_object_type | ``Procurement Package`` |
| source_object_code | ``package_code`` |

## Handoff code derivation

``JRN-MOH-2026-001`` → strip ``JRN-`` prefix → ``PKGREL-MOH-2026-001``.

## Linkage to TM2 on consume (LV-R3-005-01)

When a ``TM2 Tender`` references this package via
``TM2 Tender.procurement_package_code = package_code``, the service:

* Sets ``target_object_code`` to the tender's ``tender_code``.
* Adds the tender as a second evidence link ("Created TM2 Tender").
* Includes ``tm2_tender_code`` in ``technical_refs``.

If no tender has been created yet the ``target_object_code`` and tender evidence link
are omitted — the card can be re-run (idempotent update) once the tender exists.

## Procurement category resolution

``Procurement Package`` has no ``procurement_category`` field.  The service resolves
the category from the linked ``TM2 Tender.procurement_category`` when a tender exists,
otherwise from the first ``Procurement Package Line``'s linked ``Demand.requisition_type``.

## Budget line resolution

Sourced from the first ``Procurement Package Line.budget_line_id`` (which equals the
``Budget Line.budget_line_code`` / ``name`` in the WORKS master scenario).

## Error codes

| Code | Condition |
|---|---|
| ``INVALID_PACKAGE_CODE`` | ``package_code`` is blank or not a string. |
| ``INVALID_JOURNEY_CODE`` | ``journey_code`` is blank or not a string. |
| ``PACKAGE_NOT_FOUND`` | No ``Procurement Package`` with the given code. |
| ``JOURNEY_NOT_FOUND`` | ``journey_code`` does not exist (raised by R3-001). |
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_lifecycle.handoff_card_service import (
    create_or_update_handoff_card,
)

_PKG_DESK_ROUTE_PREFIX = "/app/procurement-package"
_TM2_DESK_ROUTE_PREFIX = "/app/tm2-tender"


def _handoff_code(journey_code: str) -> str:
    """Derive PKGREL handoff code from a journey code.

    ``JRN-MOH-2026-001`` → ``PKGREL-MOH-2026-001``.
    """
    suffix = journey_code[4:] if journey_code.upper().startswith("JRN-") else journey_code
    return f"PKGREL-{suffix}"


def _find_package(package_code: str) -> dict[str, Any] | None:
    """Return Procurement Package row dict or None.

    ``Procurement Package.name`` == ``package_code`` in normal naming; also searches
    by the ``package_code`` field for edge-case naming series divergence.
    """
    fields = [
        "name",
        "package_code",
        "package_name",
        "plan_id",
        "procurement_method",
        "contract_type",
        "currency",
        "estimated_value",
        "status",
    ]
    if frappe.db.exists("Procurement Package", package_code):
        row = frappe.db.get_value("Procurement Package", package_code, fields, as_dict=True)
        if row:
            return row
    rows = frappe.db.get_all(
        "Procurement Package",
        filters={"package_code": package_code},
        fields=fields,
        limit=1,
        order_by="creation asc",
    )
    return rows[0] if rows else None


def _find_tm2_tender(package_code: str) -> dict[str, Any] | None:
    """Return first TM2 Tender that references this package (by ``procurement_package_code``)."""
    rows = frappe.db.get_all(
        "TM2 Tender",
        filters={"procurement_package_code": package_code},
        fields=[
            "name",
            "tender_code",
            "tender_title",
            "tender_description",
            "procurement_category",
            "procurement_plan_code",
        ],
        limit=1,
        order_by="creation asc",
    )
    return rows[0] if rows else None


def _find_first_package_line(package_code: str) -> dict[str, Any] | None:
    """Return the first Procurement Package Line for a package (ascending creation/idx)."""
    rows = frappe.db.get_all(
        "Procurement Package Line",
        filters={"package_id": package_code},
        fields=["name", "package_line_code", "demand_id", "budget_line_id", "amount"],
        limit=1,
        order_by="creation asc",
    )
    return rows[0] if rows else None


def _get_demand_category(demand_frappe_name: str) -> str:
    """Return ``Demand.requisition_type`` as a proxy for procurement category."""
    if not demand_frappe_name:
        return ""
    val = frappe.db.get_value("Demand", demand_frappe_name, "requisition_type")
    return str(val or "")


def _get_budget_line_code(budget_line_frappe_name: str) -> str:
    """Return Budget Line business code (generated_reference; legacy budget_line_code fallback)."""
    if not budget_line_frappe_name:
        return ""
    val = frappe.db.get_value("Budget Line", budget_line_frappe_name, "generated_reference")
    if not val:
        try:
            val = frappe.db.get_value("Budget Line", budget_line_frappe_name, "budget_line_code")
        except Exception:
            val = None
    return str(val or budget_line_frappe_name)


def create_planning_release_package(
    package_code: str, journey_code: str
) -> dict[str, Any]:
    """Upsert the Planning Release Package handoff card for a journey.

    :param package_code: ``Procurement Package`` code (``package_code`` field /
        Frappe ``name``, e.g. ``PKG-MOH-2026-001``).
    :param journey_code: Procurement Journey code (e.g. ``JRN-MOH-2026-001``).
    :returns: Result dict from ``create_or_update_handoff_card``.
    :raises ValueError: If inputs are blank or the package is not found.
    """
    if not package_code or not isinstance(package_code, str) or not package_code.strip():
        raise ValueError(
            "INVALID_PACKAGE_CODE: package_code must be a non-empty string"
        )
    if not journey_code or not isinstance(journey_code, str) or not journey_code.strip():
        raise ValueError(
            "INVALID_JOURNEY_CODE: journey_code must be a non-empty string"
        )

    pkg_code = package_code.strip()
    jrn_code = journey_code.strip()

    pkg = _find_package(pkg_code)
    if pkg is None:
        raise ValueError(
            f"PACKAGE_NOT_FOUND: no Procurement Package with code {pkg_code!r}"
        )

    pkg_frappe_name: str = str(pkg["name"])
    pkg_name_display: str = str(pkg.get("package_name") or "")
    plan_id: str = str(pkg.get("plan_id") or "")
    procurement_method: str = str(pkg.get("procurement_method") or "")
    currency: str = str(pkg.get("currency") or "")
    estimated_value: float = float(pkg.get("estimated_value") or 0)

    # Resolve linked TM2 Tender (consume linkage — LV-R3-005-01)
    tm2 = _find_tm2_tender(pkg_code)
    tm2_tender_code: str = str((tm2 or {}).get("tender_code") or "")
    tender_title: str = str((tm2 or {}).get("tender_title") or pkg_name_display)
    tender_description: str = str((tm2 or {}).get("tender_description") or "")
    procurement_category: str = str((tm2 or {}).get("procurement_category") or "")

    # First package line → budget_line_code, package_line_code, demand for category fallback
    line = _find_first_package_line(pkg_code)
    budget_line_frappe: str = str((line or {}).get("budget_line_id") or "")
    budget_line_code: str = _get_budget_line_code(budget_line_frappe)
    package_line_code: str = str((line or {}).get("package_line_code") or "")

    # Fall back to demand category if TM2 tender not found
    if not procurement_category and line:
        demand_frappe = str(line.get("demand_id") or "")
        procurement_category = _get_demand_category(demand_frappe)

    # Plan code (plan_id == plan_code == Frappe name for Procurement Plan)
    plan_code: str = plan_id  # plan_id on Package == Procurement Plan.name == plan_code

    # locked_summary (spec §16.6)
    locked_summary: dict[str, Any] = {
        "package_code": pkg_code,
        "package_title": pkg_name_display,
    }
    if procurement_method:
        locked_summary["procurement_method"] = procurement_method
    if procurement_category:
        locked_summary["procurement_category"] = procurement_category
    if budget_line_code:
        locked_summary["budget_line"] = budget_line_code
    if estimated_value > 0:
        locked_summary["estimated_value"] = estimated_value
    if currency:
        locked_summary["currency"] = currency

    # passed_forward_summary (spec §16.6)
    passed_forward: dict[str, Any] = {
        "tender_title": tender_title,
    }
    if procurement_category:
        passed_forward["required_std_category"] = procurement_category
    if tender_description:
        passed_forward["package_scope"] = tender_description

    # Evidence links — Package always present; TM2 Tender added when linked
    pkg_route = f"{_PKG_DESK_ROUTE_PREFIX}/{pkg_frappe_name}"
    evidence_links: list[dict[str, str]] = [
        {
            "label": "Released Procurement Package",
            "object_type": "Procurement Package",
            "object_code": pkg_code,
            "module": "Procurement Planning",
            "route": pkg_route,
            "visibility": "Internal",
        },
    ]
    if tm2_tender_code:
        tm2_route = f"{_TM2_DESK_ROUTE_PREFIX}/{tm2_tender_code}"
        evidence_links.append(
            {
                "label": "Created TM2 Tender",
                "object_type": "TM2 Tender",
                "object_code": tm2_tender_code,
                "module": "Tender Management",
                "route": tm2_route,
                "visibility": "Internal",
            }
        )

    # technical_refs (spec §16.6)
    technical_refs: dict[str, str] = {}
    if plan_code:
        technical_refs["procurement_plan_code"] = plan_code
    if package_line_code:
        technical_refs["package_line_code"] = package_line_code
    if tm2_tender_code:
        technical_refs["tm2_tender_code"] = tm2_tender_code

    payload: dict[str, Any] = {
        "handoff_code": _handoff_code(jrn_code),
        "handoff_title": "Planning Release Package",
        "journey_code": jrn_code,
        "source_module": "Procurement Planning",
        "target_module": "Tender Management",
        "source_object_type": "Procurement Package",
        "source_object_code": pkg_code,
        "status": "Consumed",
        "generated_by": frappe.session.user or "system",
        "next_action": "Create and prepare tender using the official Works STD.",
        "locked_summary": locked_summary,
        "passed_forward_summary": passed_forward,
        "evidence_links": evidence_links,
        "technical_refs": technical_refs,
    }

    # Set target when TM2 tender is known
    if tm2_tender_code:
        payload["target_object_type"] = "TM2 Tender"
        payload["target_object_code"] = tm2_tender_code

    return create_or_update_handoff_card(payload)
