# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-010 / LV-R3-010-01 — **Handoff freshness / staleness detection** (cursor pack §8.3).

## Goal

``validate_handoff_card_freshness(handoff_code)`` checks whether the source object
captured in a ``Procurement Handoff Card`` has changed materially since the card was
generated. If it has, the card is marked ``Stale`` (handoff-only mutation — the source
DocType is never touched, per ADR-PLC-002 / R1-010).

## Non-negotiable (pack §8.3)

A stale handoff card **must not** be treated as valid evidence for downstream action
unless the source module explicitly revalidates or regenerates it.

## Staleness detection strategy

The service uses a **two-tier** approach:

1. **Fingerprint comparison** (preferred) — if the card stores a ``source_state_hash``
   (a SHA-1 hex digest of the material fields at handoff time), compute the live
   fingerprint of the same fields and compare. Any divergence → ``Stale``.

2. **Modified-timestamp fallback** — if no ``source_state_hash`` is stored (most seed
   cards do not carry one), compare ``source.modified`` with ``handoff.modified``. If
   the source record was modified *after* the handoff card was last written, the card is
   **tentatively stale** (reason: ``"source_modified_after_handoff"``) and updated.

3. **Source-not-found** — if the source object no longer exists (deleted / renamed),
   the card is immediately marked Stale with reason ``"source_object_not_found"``.

## Terminal-status exemption

Cards in terminal states (``Cancelled``, ``Superseded``, ``Audit Only``) are considered
**not subject to freshness checks** — they are historical records. The function returns
``fresh=True`` for these cards (semantically "freshness check not applicable").

## Mutation constraint

This service calls ``frappe.db.set_value`` **only** on ``Procurement Handoff Card``.
It never saves to source-module DocTypes (Demand, Procurement Package, TM2 Tender, …).

## Source-type fingerprint mapping

| source_object_type | Frappe DocType | code_field | material_fields |
|---|---|---|---|
| Strategy Objective | Strategy Objective | objective_code | objective_code |
| Budget Line | Budget Line | budget_line_code | amount_allocated, is_active |
| Demand | Demand | demand_id | status, estimated_value |
| Procurement Package | Procurement Package | package_code | procurement_method, status |
| STD Instance | Tender STD Instance | (by name) | readiness_status, instance_status |
| TM2 Tender | TM2 Tender | tender_code | status, procurement_category |
| TM2 Tender Closing Record | TM2 Tender Closing Record | closing_code | closing_status |
| Opening Readiness Record | TM2 Opening Readiness Record | opening_readiness_code | readiness_status |

## Response shape

Fresh:
```json
{"handoff_code": "PKGREL-MOH-2026-001", "fresh": true, "status": "Handed Off", "stale_reason": null}
```

Stale:
```json
{
  "handoff_code": "PKGREL-MOH-2026-001",
  "fresh": false,
  "status": "Stale",
  "stale_reason": "Source Procurement Package method/category/scope changed after handoff.",
  "required_action": "Regenerate or reapprove Planning Release Package."
}
```

## Error codes

| Code | Condition |
|---|---|
| ``INVALID_HANDOFF_CODE`` | ``handoff_code`` is blank or not a string. |
| ``HANDOFF_NOT_FOUND`` | No ``Procurement Handoff Card`` with the given code. |
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe

from kentender_procurement.procurement_lifecycle.source_module_authority import (
    handoff_fields_for_stale_mark,
    recommend_handoff_stale_for_source_fingerprint_drift,
)

# ---------------------------------------------------------------------------
# Terminal statuses — freshness check not applicable
# ---------------------------------------------------------------------------

_TERMINAL_STATUSES: frozenset[str] = frozenset({"Cancelled", "Superseded", "Audit Only"})

# ---------------------------------------------------------------------------
# Per source_object_type configuration
# ---------------------------------------------------------------------------

# Maps source_object_type label (as stored in handoff card) to:
#   doctype: actual Frappe DocType name
#   code_field: field used for lookup by source_object_code
#   material_fields: fields that determine "material state"
_SOURCE_CONFIG: dict[str, dict[str, Any]] = {
    "Strategy Objective": {
        "doctype": "Strategy Objective",
        "code_field": "objective_code",
        "material_fields": ["objective_code"],
    },
    "Procurement Budget Line": {
        "doctype": "Procurement Budget Line",
        "code_field": "budget_line_code",
        "material_fields": ["amount_allocated", "is_active"],
    },
    "Demand": {
        "doctype": "Demand",
        "code_field": "demand_id",
        "material_fields": ["status"],
    },
    "Procurement Package": {
        "doctype": "Procurement Package",
        "code_field": "package_code",
        "material_fields": ["procurement_method", "status"],
    },
    # STD Instance is stored by Frappe `name` (auto-generated); code_field=None triggers
    # Frappe-name lookup only.
    "STD Instance": {
        "doctype": "Tender STD Instance",
        "code_field": None,
        "material_fields": ["readiness_status", "instance_status"],
    },
    "TM2 Tender": {
        "doctype": "TM2 Tender",
        "code_field": "tender_code",
        "material_fields": ["status", "procurement_category"],
    },
    "TM2 Tender Closing Record": {
        "doctype": "TM2 Tender Closing Record",
        "code_field": "closing_code",
        "material_fields": ["closing_status"],
    },
    "Opening Readiness Record": {
        "doctype": "TM2 Opening Readiness Record",
        "code_field": "opening_readiness_code",
        "material_fields": ["readiness_status"],
    },
}

# Stale reason + required action per source_object_type
_STALE_MESSAGES: dict[str, tuple[str, str]] = {
    "Strategy Objective": (
        "Source Strategy Objective state changed after handoff.",
        "Review strategy alignment and regenerate the handoff.",
    ),
    "Procurement Budget Line": (
        "Source Budget Line allocation or active status changed after handoff.",
        "Regenerate Budget Funding Confirmation.",
    ),
    "Demand": (
        "Source Demand status or estimated value changed after handoff.",
        "Regenerate Demand Approval Certificate.",
    ),
    "Procurement Package": (
        "Source Procurement Package method/category/scope changed after handoff.",
        "Regenerate or reapprove Planning Release Package.",
    ),
    "STD Instance": (
        "Source STD Instance readiness status changed after handoff.",
        "Regenerate STD Readiness Certificate.",
    ),
    "TM2 Tender": (
        "Source Tender status or procurement category changed after handoff.",
        "Review Tender and regenerate relevant handoff.",
    ),
    "TM2 Tender Closing Record": (
        "Source Tender Closing Record status changed after handoff.",
        "Review closing record and regenerate Tender Closing Certificate.",
    ),
    "Opening Readiness Record": (
        "Source Opening Readiness Record status changed after handoff.",
        "Review opening readiness and regenerate Opening Readiness Handoff.",
    ),
}

# Default messages for unmapped source types
_DEFAULT_STALE_REASON = "Source object state changed after handoff."
_DEFAULT_REQUIRED_ACTION = "Review source object and regenerate the handoff."


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _fingerprint(data: dict[str, Any]) -> str:
    """Compute a short SHA-1 hex fingerprint of a dict of material field values."""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha1(canonical.encode("utf-8"), usedforsecurity=False).hexdigest()


def _find_source_record(source_object_type: str, source_object_code: str) -> dict[str, Any] | None:
    """Locate the source record and return material field values, or None if not found."""
    cfg = _SOURCE_CONFIG.get(source_object_type)
    if cfg is None:
        return None

    doctype: str = cfg["doctype"]
    code_field: str | None = cfg["code_field"]
    material_fields: list[str] = cfg["material_fields"]

    # Defensive: ensure all material fields are requested; add "name" for existence check.
    fields = list({*material_fields, "name", "modified"})

    # Try Frappe name first (most DocTypes in this suite auto-name from business code)
    if frappe.db.exists(doctype, source_object_code):
        row = frappe.db.get_value(doctype, source_object_code, fields, as_dict=True)
        if row:
            return dict(row)

    # Fallback: lookup by business code field (if mapped)
    if code_field:
        rows = frappe.db.get_all(
            doctype,
            filters={code_field: source_object_code},
            fields=fields,
            limit=1,
            order_by="creation asc",
        )
        if rows:
            return dict(rows[0])

    return None


def _live_fingerprint(source_object_type: str, source_object_code: str) -> str | None:
    """Return a fingerprint string of the source record's material fields, or None."""
    cfg = _SOURCE_CONFIG.get(source_object_type)
    if cfg is None:
        return None
    material_fields: list[str] = cfg["material_fields"]
    record = _find_source_record(source_object_type, source_object_code)
    if record is None:
        return None
    material_data = {f: record.get(f) for f in material_fields}
    return _fingerprint(material_data)


def _source_modified(source_object_type: str, source_object_code: str) -> Any | None:
    """Return the ``modified`` timestamp of the source record, or None."""
    record = _find_source_record(source_object_type, source_object_code)
    if record is None:
        return None
    return record.get("modified")


def _stale_reason_for_type(source_object_type: str) -> tuple[str, str]:
    """Return (stale_reason_text, required_action_text) for a given source type."""
    return _STALE_MESSAGES.get(source_object_type, (_DEFAULT_STALE_REASON, _DEFAULT_REQUIRED_ACTION))


def _mark_card_stale(card_frappe_name: str, stale_reason: str) -> None:
    """Persist Stale status + reason on the handoff card (handoff-only mutation)."""
    frappe.db.set_value(
        "Procurement Handoff Card",
        card_frappe_name,
        {
            "status": "Stale",
            "stale_reason": stale_reason,
        },
        update_modified=False,
    )
    frappe.db.commit()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_handoff_card_freshness(handoff_code: str) -> dict[str, Any]:
    """Check and update staleness for a ``Procurement Handoff Card``.

    If the source object has changed materially since the card was generated, the card
    is marked ``Stale`` (handoff-only mutation) and a stale result dict is returned.

    :param handoff_code: Unique code identifying the ``Procurement Handoff Card``.
    :returns: Freshness result dict (see module docstring for schema).
    :raises ValueError: For blank/invalid ``handoff_code`` or missing card.
    """
    if not handoff_code or not isinstance(handoff_code, str) or not handoff_code.strip():
        raise ValueError("INVALID_HANDOFF_CODE: handoff_code must be a non-empty string")

    code = handoff_code.strip()

    # 1. Load the handoff card
    card = frappe.db.get_value(
        "Procurement Handoff Card",
        {"handoff_code": code},
        [
            "name",
            "handoff_code",
            "status",
            "source_object_type",
            "source_object_code",
            "source_state_hash",
            "stale_reason",
            "modified",
        ],
        as_dict=True,
    )
    if not card:
        raise ValueError(
            f"HANDOFF_NOT_FOUND: no Procurement Handoff Card with handoff_code = {code!r}"
        )

    card_name: str = str(card["name"])
    current_status: str = str(card.get("status") or "Draft").strip()
    source_type: str = str(card.get("source_object_type") or "").strip()
    source_code: str = str(card.get("source_object_code") or "").strip()
    stored_hash: str | None = str(card.get("source_state_hash") or "").strip() or None
    existing_stale_reason: str | None = str(card.get("stale_reason") or "").strip() or None
    card_modified: Any = card.get("modified")

    # 2. Terminal status — freshness check not applicable
    if current_status in _TERMINAL_STATUSES:
        return {
            "handoff_code": code,
            "fresh": True,
            "status": current_status,
            "stale_reason": None,
        }

    # 3. Already stale — return existing stale info (no re-marking needed)
    if current_status == "Stale":
        stale_reason_text, required_action = _stale_reason_for_type(source_type)
        return {
            "handoff_code": code,
            "fresh": False,
            "status": "Stale",
            "stale_reason": existing_stale_reason or stale_reason_text,
            "required_action": required_action,
        }

    # 4. No source object info — cannot check, return fresh
    if not source_type or not source_code:
        return {
            "handoff_code": code,
            "fresh": True,
            "status": current_status,
            "stale_reason": None,
        }

    stale_reason_text, required_action = _stale_reason_for_type(source_type)

    # 5. Source-not-found check (object deleted / renamed)
    record = _find_source_record(source_type, source_code)
    if record is None and source_type in _SOURCE_CONFIG:
        # Object was deleted → definitely stale
        not_found_reason = "source_object_not_found"
        _mark_card_stale(card_name, not_found_reason)
        return {
            "handoff_code": code,
            "fresh": False,
            "status": "Stale",
            "stale_reason": f"Source {source_type} with code {source_code!r} no longer exists.",
            "required_action": required_action,
        }

    # 6. Fingerprint comparison (tier-1 — only when stored_hash is available)
    if stored_hash and source_type in _SOURCE_CONFIG:
        live_hash = _live_fingerprint(source_type, source_code)
        stale_rec = recommend_handoff_stale_for_source_fingerprint_drift(
            handoff_status=current_status,
            snapshot_fingerprint=stored_hash,
            live_fingerprint=live_hash,
        )
        if stale_rec:
            _mark_card_stale(card_name, stale_reason_text)
            return {
                "handoff_code": code,
                "fresh": False,
                "status": "Stale",
                "stale_reason": stale_reason_text,
                "required_action": required_action,
            }
        # Hash matched — fresh
        return {
            "handoff_code": code,
            "fresh": True,
            "status": current_status,
            "stale_reason": None,
        }

    # 7. Modified-timestamp fallback (tier-2 — no stored hash)
    if record is not None and card_modified and source_type in _SOURCE_CONFIG:
        source_modified = record.get("modified")
        if source_modified and source_modified > card_modified:
            # Source was updated after the handoff was last written → tentatively stale
            ts_drift_reason = "source_modified_after_handoff"
            _mark_card_stale(card_name, ts_drift_reason)
            return {
                "handoff_code": code,
                "fresh": False,
                "status": "Stale",
                "stale_reason": stale_reason_text,
                "required_action": required_action,
            }

    # 8. No drift detected (or unsupported source type)
    return {
        "handoff_code": code,
        "fresh": True,
        "status": current_status,
        "stale_reason": None,
    }
