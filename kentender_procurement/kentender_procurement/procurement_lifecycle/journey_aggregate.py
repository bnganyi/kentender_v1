# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-011 / LV-R3-011-01 — **Journey aggregate service** (cursor pack §9.1).

## Goal

``get_procurement_journey(journey_code)`` returns a single comprehensive view of a
``Procurement Journey``, combining:

- Stored journey header fields (title, category, method, stage, status).
- Aggregated step list from R3-013 (``aggregate_procurement_journey_steps``).
- All associated ``Procurement Handoff Card`` records in a compact summary shape.
- A lightweight evidence summary derived from handoff cards (ordered chronologically).
- Re-derived blocker counts from live step data (overrides stored counts for accuracy).

This is the primary read API for the Journey Detail view and any module that displays
a Journey Context Header.

## Response shape (pack §9.1)

```json
{
  "journey_code": "JRN-MOH-2026-001",
  "title": "District Hospital Renovation Works",
  "procuring_entity_code": "PE-MOH",
  "category": "Works",
  "method": "Open Tender",
  "current_stage": "Tender Published",
  "current_status": "Completed",
  "next_action": "Await tender closing / prepare bid opening readiness",
  "blocker_count": 0,
  "critical_blocker_count": 0,
  "steps": [...],
  "handoff_cards": [...],
  "evidence_summary": [...]
}
```

## Design notes

- **``current_stage`` / ``current_status`` / ``next_action``**: read from the stored
  ``current_stage_label``, ``current_status_category``, and ``next_action`` fields on
  the ``Procurement Journey`` DocType (written by the seed loader and future R3-014
  update hooks). Live re-calculation from source objects is a **R3-014** concern.

- **Blocker counts**: re-derived from the live step list (sum of step ``blocker_count``
  values; ``critical_blocker_count`` = number of steps with
  ``status_category == "Blocked"``). This overrides the stored Journey field values.

- **handoff_cards**: compact summary — not calling ``validate_handoff_card_freshness``
  inline (that would be expensive per-card; call the refresh endpoint explicitly for
  freshness checks). Cards include parsed JSON for ``locked_summary``,
  ``passed_forward_summary``, ``evidence_links``, and ``technical_refs``.

- **evidence_summary**: one entry per handoff card, ordered by ``generated_at``
  ascending, in the event shape from pack §9.5.

## Error codes

| Code | Condition |
|---|---|
| ``INVALID_JOURNEY_CODE`` | ``journey_code`` is blank or not a string. |
| ``JOURNEY_NOT_FOUND`` | No ``Procurement Journey`` with the given code. |
"""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.procurement_lifecycle.journey_step_aggregator import (
    aggregate_procurement_journey_steps,
)

# Fields fetched from Procurement Journey
_JOURNEY_FIELDS = (
    "name",
    "journey_code",
    "journey_title",
    "procuring_entity_code",
    "fiscal_year",
    "procurement_category",
    "procurement_method",
    "current_stage_key",
    "current_stage_label",
    "current_status_category",
    "current_owner_module",
    "current_owner_role",
    "next_action",
    "blocker_count",
    "critical_blocker_count",
    "strategy_ref",
    "budget_line_ref",
    "demand_ref",
    "procurement_plan_ref",
    "procurement_package_ref",
    "std_template_version_ref",
    "tender_std_instance_ref",
    "tm2_tender_ref",
    "publication_snapshot_ref",
    "opening_readiness_ref",
    "is_master_seed",
    "created_at",
    "updated_at",
)

# Fields fetched from Procurement Handoff Card
_CARD_FIELDS = (
    "name",
    "handoff_code",
    "handoff_title",
    "status",
    "source_module",
    "target_module",
    "source_object_type",
    "source_object_code",
    "target_object_type",
    "target_object_code",
    "generated_by",
    "generated_at",
    "consumed_by",
    "consumed_at",
    "next_action",
    "locked_summary",
    "passed_forward_summary",
    "evidence_links_json",
    "technical_refs_json",
    "stale_reason",
)


def _safe_json(raw: Any) -> Any:
    """Parse a JSON string, returning the parsed value or the original on failure."""
    if raw is None:
        return None
    if isinstance(raw, (dict, list)):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            pass
    return None


def _parse_evidence_links(raw: Any) -> list[dict]:
    """Unwrap the ``{"links": [...]}`` envelope used by evidence_links_json."""
    parsed = _safe_json(raw)
    if parsed is None:
        return []
    if isinstance(parsed, dict):
        inner = parsed.get("links", [])
        return inner if isinstance(inner, list) else []
    if isinstance(parsed, list):
        return parsed
    return []


def _card_to_summary(card: dict[str, Any]) -> dict[str, Any]:
    """Convert a DB row for a handoff card to a compact summary dict."""
    return {
        "handoff_code": str(card.get("handoff_code") or ""),
        "handoff_title": str(card.get("handoff_title") or ""),
        "status": str(card.get("status") or "Draft"),
        "source_module": str(card.get("source_module") or ""),
        "target_module": str(card.get("target_module") or ""),
        "source_object_type": card.get("source_object_type") or None,
        "source_object_code": card.get("source_object_code") or None,
        "target_object_type": card.get("target_object_type") or None,
        "target_object_code": card.get("target_object_code") or None,
        "generated_by": card.get("generated_by") or None,
        "generated_at": str(card["generated_at"]) if card.get("generated_at") else None,
        "consumed_by": card.get("consumed_by") or None,
        "consumed_at": str(card["consumed_at"]) if card.get("consumed_at") else None,
        "next_action": card.get("next_action") or None,
        "locked_summary": _safe_json(card.get("locked_summary")) or {},
        "passed_forward_summary": _safe_json(card.get("passed_forward_summary")) or {},
        "evidence_links": _parse_evidence_links(card.get("evidence_links_json")),
        "technical_refs": _safe_json(card.get("technical_refs_json")) or {},
        "stale_reason": card.get("stale_reason") or None,
    }


def _card_to_evidence_event(card: dict[str, Any]) -> dict[str, Any] | None:
    """Convert a handoff card to an evidence timeline event (pack §9.5 shape).

    Returns ``None`` if essential fields are missing.
    """
    handoff_code = str(card.get("handoff_code") or "").strip()
    source_module = str(card.get("source_module") or "").strip()
    if not handoff_code or not source_module:
        return None

    occurred_at = str(card["generated_at"]) if card.get("generated_at") else None
    source_type = str(card.get("source_object_type") or "").strip() or None
    source_code = str(card.get("source_object_code") or "").strip() or None
    title = str(card.get("handoff_title") or "").strip()

    # Derive evidence_refs from evidence_links (first external link code, or source code)
    links = _parse_evidence_links(card.get("evidence_links_json"))
    evidence_refs = [lnk["object_code"] for lnk in links if lnk.get("object_code")]

    return {
        "occurred_at": occurred_at,
        "module": source_module,
        "event_type": title,
        "business_label": f"{title} issued",
        "object_type": source_type,
        "object_code": source_code,
        "handoff_code": handoff_code,
        "evidence_refs": evidence_refs,
    }


def _derive_blocker_counts(steps: list[dict[str, Any]]) -> tuple[int, int]:
    """Re-derive (blocker_count, critical_blocker_count) from live step data.

    - ``blocker_count``: sum of all step ``blocker_count`` fields.
    - ``critical_blocker_count``: count of steps whose ``status_category`` is
      ``"Blocked"``.
    """
    total_blockers = sum(int(s.get("blocker_count") or 0) for s in steps)
    critical_blockers = sum(
        1 for s in steps if str(s.get("status_category") or "").strip() == "Blocked"
    )
    return total_blockers, critical_blockers


def get_procurement_journey(journey_code: str) -> dict[str, Any]:
    """Return the aggregated journey view for a given ``Procurement Journey`` code.

    :param journey_code: Procurement Journey identifier (e.g. ``JRN-MOH-2026-001``).
    :returns: Full journey aggregate dict (see module docstring for shape).
    :raises ValueError: If ``journey_code`` is blank (``INVALID_JOURNEY_CODE``).
    :raises frappe.DoesNotExistError: If the journey does not exist (``JOURNEY_NOT_FOUND``).
    """
    if not journey_code or not isinstance(journey_code, str) or not journey_code.strip():
        raise ValueError(
            "INVALID_JOURNEY_CODE: journey_code must be a non-empty string"
        )

    code = journey_code.strip()

    # 1. Load journey header from DB
    journey = frappe.db.get_value(
        "Procurement Journey",
        {"journey_code": code},
        list(_JOURNEY_FIELDS),
        as_dict=True,
    )
    if journey is None:
        # Try by Frappe name (in case journey_code == name)
        if frappe.db.exists("Procurement Journey", code):
            journey = frappe.db.get_value(
                "Procurement Journey",
                code,
                list(_JOURNEY_FIELDS),
                as_dict=True,
            )
    if journey is None:
        frappe.throw(
            f"Procurement Journey {code!r} does not exist.",
            frappe.DoesNotExistError,
            title="JOURNEY_NOT_FOUND",
        )

    # 2. Aggregate steps (R3-013)
    steps = aggregate_procurement_journey_steps(code)

    # 3. Re-derive blocker counts from live steps
    blocker_count, critical_blocker_count = _derive_blocker_counts(steps)

    # 4. Read all handoff cards for this journey
    raw_cards = frappe.db.get_all(
        "Procurement Handoff Card",
        filters={"journey_code": code},
        fields=list(_CARD_FIELDS),
        order_by="generated_at asc",
    )

    handoff_cards = [_card_to_summary(c) for c in (raw_cards or [])]

    # 5. Build evidence summary (one event per non-stale handoff card, ordered by generated_at)
    evidence_summary: list[dict[str, Any]] = []
    for card_row in (raw_cards or []):
        evt = _card_to_evidence_event(card_row)
        if evt is not None:
            evidence_summary.append(evt)
    # evidence_summary is already ordered by generated_at asc (from the DB query above)

    # 6. Build the primary object ref (latest non-null ref in journey spine order)
    _spine_refs = (
        "tm2_tender_ref",
        "procurement_package_ref",
        "demand_ref",
        "budget_line_ref",
        "strategy_ref",
    )
    primary_object_code: str | None = None
    for ref_field in _spine_refs:
        val = str(journey.get(ref_field) or "").strip()
        if val:
            primary_object_code = val
            break

    return {
        "journey_code": str(journey.get("journey_code") or code),
        "title": str(journey.get("journey_title") or ""),
        "procuring_entity_code": str(journey.get("procuring_entity_code") or ""),
        "fiscal_year": journey.get("fiscal_year"),
        "category": str(journey.get("procurement_category") or ""),
        "method": str(journey.get("procurement_method") or ""),
        "current_stage": str(journey.get("current_stage_label") or ""),
        "current_stage_key": str(journey.get("current_stage_key") or ""),
        "current_status": str(journey.get("current_status_category") or "Not Started"),
        "current_owner_module": journey.get("current_owner_module") or None,
        "current_owner_role": journey.get("current_owner_role") or None,
        "next_action": str(journey.get("next_action") or ""),
        "blocker_count": blocker_count,
        "critical_blocker_count": critical_blocker_count,
        "primary_object_code": primary_object_code,
        "refs": {
            "strategy_ref": journey.get("strategy_ref") or None,
            "budget_line_ref": journey.get("budget_line_ref") or None,
            "demand_ref": journey.get("demand_ref") or None,
            "procurement_plan_ref": journey.get("procurement_plan_ref") or None,
            "procurement_package_ref": journey.get("procurement_package_ref") or None,
            "std_template_version_ref": journey.get("std_template_version_ref") or None,
            "tender_std_instance_ref": journey.get("tender_std_instance_ref") or None,
            "tm2_tender_ref": journey.get("tm2_tender_ref") or None,
            "publication_snapshot_ref": journey.get("publication_snapshot_ref") or None,
            "opening_readiness_ref": journey.get("opening_readiness_ref") or None,
        },
        "is_master_seed": bool(journey.get("is_master_seed")),
        "created_at": str(journey["created_at"]) if journey.get("created_at") else None,
        "updated_at": str(journey["updated_at"]) if journey.get("updated_at") else None,
        "steps": steps,
        "handoff_cards": handoff_cards,
        "evidence_summary": evidence_summary,
    }
