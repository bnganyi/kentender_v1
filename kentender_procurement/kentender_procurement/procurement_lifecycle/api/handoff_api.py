# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-018 / LV-R3-018-01 — **Procurement Lifecycle Handoff Card APIs** (pack §10.3).

## Goal

Two Frappe-whitelisted methods covering the handoff card endpoints from pack §10.1:

| Pack endpoint | Function |
|---|---|
| ``GET /api/procurement-lifecycle/handoff-cards/<handoff_code>`` | ``get_handoff_card`` |
| ``POST /api/procurement-lifecycle/handoff-cards/refresh/<handoff_code>`` | ``refresh_handoff_card`` |

## Handoff detail shape (pack §10.3)

```json
{
  "handoff_code": "PKGREL-MOH-2026-001",
  "handoff_title": "Planning Release Package",
  "status": "Consumed",
  "source_module": "Procurement Planning",
  "target_module": "Tender Management",
  "source_object_type": "Procurement Package",
  "source_object_code": "PKG-MOH-2026-001",
  "target_object_type": "TM2 Tender",
  "target_object_code": "TND-MOH-2026-001",
  "journey_code": "JRN-MOH-2026-001",
  "locked_summary": {},
  "passed_forward_summary": {},
  "next_action": "Create and prepare tender using the official Works STD.",
  "evidence_links": [],
  "technical_refs": {},
  "freshness": {
    "fresh": true,
    "stale_reason": null
  }
}
```

## Refresh response shape

```json
{
  "handoff_code": "PKGREL-MOH-2026-001",
  "fresh": true,
  "status": "Consumed",
  "stale_reason": null,
  "required_action": null
}
```

## Permissions (pack §10.4)

| Endpoint | Requirement |
|---|---|
| ``get_handoff_card`` | Authenticated non-Guest; ``read`` on ``Procurement Handoff Card``. |
| ``refresh_handoff_card`` | Authenticated non-Guest; ``write`` on ``Procurement Handoff Card`` (authorised source-module roles or system service). |

## Transport

``frappe.call`` / ``POST /api/method/kentender_procurement.procurement_lifecycle.api.handoff_api.<function_name>``
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_lifecycle.handoff_freshness import (
    validate_handoff_card_freshness,
)
from kentender_procurement.procurement_lifecycle.api.permission_guard import (
    require_handoff_read,
    require_handoff_write,
)


# ---------------------------------------------------------------------------
# 1. get_handoff_card  (pack §10.3)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_handoff_card(handoff_code: str | None = None) -> dict[str, Any]:
    """Return full handoff card detail including live freshness check.

    :param handoff_code: Handoff card identifier (e.g. ``"PKGREL-MOH-2026-001"``).
    :returns: Handoff detail dict matching pack §10.3.
    :raises frappe.PermissionError: If the user lacks read access or is Guest.
    :raises frappe.ValidationError: If ``handoff_code`` is blank.
    :raises frappe.DoesNotExistError: If the card does not exist.
    """
    require_handoff_read("get_handoff_card")

    code = cstr(handoff_code or "").strip()
    if not code:
        frappe.throw("handoff_code is required.", frappe.ValidationError)

    # Load raw record
    card = frappe.db.get_value(
        "Procurement Handoff Card",
        code,
        [
            "handoff_code",
            "handoff_title",
            "status",
            "source_module",
            "target_module",
            "source_object_type",
            "source_object_code",
            "target_object_type",
            "target_object_code",
            "journey_code",
            "next_action",
            "locked_summary",
            "passed_forward_summary",
            "evidence_links_json",
            "technical_refs_json",
        ],
        as_dict=True,
    )
    if not card:
        frappe.throw(
            f"Procurement Handoff Card '{code}' not found.",
            frappe.DoesNotExistError,
        )

    # Parse JSON fields
    locked_summary = _safe_json_dict(card.get("locked_summary"))
    passed_forward_summary = _safe_json_dict(card.get("passed_forward_summary"))
    evidence_links = _extract_links(card.get("evidence_links_json"))
    technical_refs = _safe_json_dict(card.get("technical_refs_json"))

    # Live freshness check (R3-010)
    freshness = _get_freshness(code)

    return {
        "handoff_code": card.handoff_code or code,
        "handoff_title": card.handoff_title or "",
        "status": card.status or "",
        "source_module": card.source_module or "",
        "target_module": card.target_module or "",
        "source_object_type": card.source_object_type or "",
        "source_object_code": card.source_object_code or "",
        "target_object_type": card.target_object_type or "",
        "target_object_code": card.target_object_code or "",
        "journey_code": card.journey_code or "",
        "locked_summary": locked_summary,
        "passed_forward_summary": passed_forward_summary,
        "next_action": card.next_action or "",
        "evidence_links": evidence_links,
        "technical_refs": technical_refs,
        "freshness": freshness,
    }


# ---------------------------------------------------------------------------
# 2. refresh_handoff_card  (pack §10.1, POST)
# ---------------------------------------------------------------------------

@frappe.whitelist(methods=["POST"])
def refresh_handoff_card(handoff_code: str | None = None) -> dict[str, Any]:
    """Re-check freshness for a handoff card and persist any stale status to DB.

    Requires ``write`` permission on ``Procurement Handoff Card`` (authorised
    source module roles or system service — pack §10.4).

    :param handoff_code: Handoff card identifier.
    :returns: Freshness result dict.
    :raises frappe.PermissionError: If the user lacks write access or is Guest.
    :raises frappe.ValidationError: If ``handoff_code`` is blank.
    :raises frappe.DoesNotExistError: If the card does not exist.
    """
    require_handoff_write("refresh_handoff_card")

    code = cstr(handoff_code or "").strip()
    if not code:
        frappe.throw("handoff_code is required.", frappe.ValidationError)

    # Delegate to R3-010 freshness service (mutates DB if stale detected)
    try:
        result = validate_handoff_card_freshness(code)
    except ValueError as exc:
        msg = str(exc)
        if "HANDOFF_NOT_FOUND" in msg:
            frappe.throw(
                f"Procurement Handoff Card '{code}' not found.",
                frappe.DoesNotExistError,
            )
        raise frappe.ValidationError(msg) from exc

    return {
        "handoff_code": result.get("handoff_code", code),
        "fresh": result.get("fresh", True),
        "status": result.get("status", ""),
        "stale_reason": result.get("stale_reason"),
        "required_action": result.get("required_action"),
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _safe_json_dict(raw: str | None) -> dict:
    """Parse a JSON string into a dict; return {} on failure."""
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _extract_links(evidence_links_json: str | None) -> list[dict]:
    """Extract the ``links`` list from evidence_links_json.

    The field stores ``{"links": [...]}``; returns the inner list.
    """
    if not evidence_links_json:
        return []
    try:
        data = json.loads(evidence_links_json)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(data, dict):
        return []
    links = data.get("links", [])
    return links if isinstance(links, list) else []


def _get_freshness(handoff_code: str) -> dict[str, Any]:
    """Run freshness check and return the ``freshness`` sub-dict for the API response.

    Handles errors gracefully — if the freshness check cannot run (e.g. terminal
    status or source not found), returns whatever the service returns; if it raises,
    returns a safe ``{"fresh": true, "stale_reason": null}`` rather than crashing
    the detail view.
    """
    try:
        result = validate_handoff_card_freshness(handoff_code)
        return {
            "fresh": result.get("fresh", True),
            "stale_reason": result.get("stale_reason"),
        }
    except Exception:
        # Freshness is best-effort in the detail view; errors must not crash it.
        return {"fresh": True, "stale_reason": None}
