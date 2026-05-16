# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-013 / LV-R3-013-01 — **Step aggregation service** (Cursor pack §9.3).

## Goal

``aggregate_procurement_journey_steps(journey_code)`` returns the ordered list of
``Procurement Journey Step`` child rows for a given journey as serializable dicts.

## Ordering rule

Steps are returned by **``step_order`` ascending** (primary), then **``idx`` ascending**
(secondary, for tie-breaking on duplicate step_order values — which should not occur
in well-formed data but must not crash).

The WORKS master seed materialises 12 child rows in this order (spec §15 /
``WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER``):

| step_order | step_key | Base status_category |
|---|---|---|
| 1 | strategy | Completed |
| 2 | budget | Completed |
| 3 | demand | Completed |
| 4 | planning_inclusion | Completed |
| 5 | package_release | Handed Off |
| 6 | std_readiness | Completed |
| 7 | tender_publication | Completed |
| 8 | tender_closing | Not Started (→ Completed at OPENING_READY) |
| 9 | opening_readiness | Not Started (→ Ready for Handoff at OPENING_READY) |
| 10 | bid_opening | Not Started |
| 11 | evaluation_award | Not Started |
| 12 | contract | Not Started |

For not-yet-implemented modules, future steps are present as ``Not Started`` rows —
**do not invent source objects** for them (cursor pack §9.3, line 827).

## Non-authoritative note (ADR-PLC-002)

Step rows are navigation/visibility artifacts derived from source module state.
This service reads materialized rows only — it does **not** re-derive status from
source modules. Live aggregation from source modules is a future R3-014+ concern.

## Error codes

| Code | Condition |
|---|---|
| ``JOURNEY_NOT_FOUND`` | ``journey_code`` does not exist in ``Procurement Journey``. |
| ``INVALID_JOURNEY_CODE`` | ``journey_code`` is blank or not a string. |
"""

from __future__ import annotations

import json
from typing import Any

import frappe

# Fields to read from child table — must match tabProcurement Journey Step columns.
_STEP_READ_FIELDS = (
    "name",
    "step_key",
    "step_order",
    "label",
    "status_category",
    "raw_status",
    "owner_module",
    "owner_role",
    "source_object_type",
    "source_object_code",
    "handoff_code",
    "last_action",
    "last_action_at",
    "next_action",
    "blocker_count",
    "blockers_json",
    "open_module_route",
    "evidence_route",
    "idx",
)


def _parse_blockers_json(raw: Any) -> dict | list | None:
    """Deserialize blockers_json stored as text/JSON string, or return as-is."""
    if raw is None or raw == "" or raw == {} or raw == []:
        return None
    if isinstance(raw, (dict, list)):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
    return None


def _row_to_dict(row: dict[str, Any]) -> dict[str, Any]:
    """Convert a raw DB row dict to the public step dict shape."""
    return {
        "step_key": (row.get("step_key") or "").strip(),
        "step_order": int(row.get("step_order") or 0),
        "label": (row.get("label") or "").strip(),
        "status_category": (row.get("status_category") or "Not Started").strip(),
        "raw_status": (row.get("raw_status") or None),
        "owner_module": (row.get("owner_module") or "").strip(),
        "owner_role": (row.get("owner_role") or None) or None,
        "source_object_type": (row.get("source_object_type") or None) or None,
        "source_object_code": (row.get("source_object_code") or None) or None,
        "handoff_code": (row.get("handoff_code") or None) or None,
        "last_action": (row.get("last_action") or None) or None,
        "last_action_at": (
            str(row["last_action_at"]) if row.get("last_action_at") else None
        ),
        "next_action": (row.get("next_action") or None) or None,
        "blocker_count": int(row.get("blocker_count") or 0),
        "blockers_json": _parse_blockers_json(row.get("blockers_json")),
        "open_module_route": (row.get("open_module_route") or None) or None,
        "evidence_route": (row.get("evidence_route") or None) or None,
    }


def aggregate_procurement_journey_steps(journey_code: str) -> list[dict[str, Any]]:
    """Return materialized child steps for a journey, ordered by ``step_order`` ascending.

    :param journey_code: The ``Procurement Journey`` name (e.g. ``JRN-MOH-2026-001``).
    :returns: List of step dicts; empty if the journey has no materialized steps.
    :raises ValueError: If ``journey_code`` is blank (``INVALID_JOURNEY_CODE``).
    :raises frappe.DoesNotExistError: If the journey does not exist (``JOURNEY_NOT_FOUND``).

    ## Ordering rule

    Primary: ``step_order`` ascending.
    Secondary: ``idx`` ascending (tie-break for duplicate step_order values).
    """
    if not journey_code or not isinstance(journey_code, str) or not journey_code.strip():
        raise ValueError(
            "INVALID_JOURNEY_CODE: journey_code must be a non-empty string"
        )

    code = journey_code.strip()

    if not frappe.db.exists("Procurement Journey", code):
        frappe.throw(
            f"Procurement Journey {code!r} does not exist.",
            frappe.DoesNotExistError,
            title="JOURNEY_NOT_FOUND",
        )

    rows = frappe.db.get_all(
        "Procurement Journey Step",
        filters={"parent": code, "parenttype": "Procurement Journey"},
        fields=list(_STEP_READ_FIELDS),
        order_by="step_order asc, idx asc",
    )

    return [_row_to_dict(r) for r in (rows or [])]
