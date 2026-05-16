# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-009 / LV-R3-009-01 — **Opening readiness handoff service** (cursor pack §8.2).

## Goal

``create_opening_readiness_handoff(tender_code, opening_readiness_code, journey_code)``
produces (or updates) the ``Procurement Handoff Card`` that records the Tender
Management → Bid Opening module boundary event once opening readiness is confirmed.
The card passes the sealed submission references and opening configuration to the Bid
Opening module.

## CRITICAL constraint (cursor pack §8.2 / PLC-CURSOR-014)

This service **must only be called when a real ``TM2 Opening Readiness Record``
already exists**.  It must **not fabricate** an opening readiness record for the base
``TENDER_PUBLISHED`` checkpoint.  If no ``TM2 Opening Readiness Record`` with the
given ``opening_readiness_code`` exists, the service raises
``ValueError: OPENING_READINESS_NOT_FOUND`` and does not create a card.

This service is intended for:
- The optional ``OPENING_READY`` checkpoint (when the WORKS master seed loads with
  ``checkpoint="OPENING_READY"``), or
- Live production flows where opening readiness has actually been confirmed.

## Handoff card produced

| Field | Value |
|---|---|
| handoff_code | ``OPENREADY-{tender_code}`` (e.g. ``OPENREADY-TND-MOH-2026-001``) |
| source_module | ``Tender Management`` |
| target_module | ``Bid Opening`` |
| source_object_type | ``Opening Readiness Record`` |
| source_object_code | ``opening_readiness_code`` |
| target_object_type | ``Bid Opening Session`` |
| target_object_code | ``null`` (not yet created at the time of handoff) |
| status | ``Handed Off`` |

## locked_summary fields

- ``opening_model``: ``TM2 Opening Readiness Record.dom_output_code`` — the Desk Opening
  Model output code used to drive the opening session.
- ``publication_snapshot``: ``Procurement Journey.publication_snapshot_ref`` — the snapshot
  code for traceability.
- ``opening_scheduled_at``: ISO datetime from ``TM2 Tender Timeline.opening_scheduled_at``.
- ``arithmetic_correction_at_opening``: always ``False`` — arithmetic correction happens
  at evaluation, not at bid opening for sealed tenders under KenTender's opening rules.

## passed_forward_summary fields

- ``sealed_submission_refs``: list of bid reference codes from
  ``TM2 Opening Readiness Record.sealed_submission_refs`` (stored as JSON array string).
  Empty list ``[]`` if not set.
- ``opening_register_rules_ready``: ``True`` when
  ``TM2 Opening Readiness Record.readiness_status == "Ready"``.
- ``display_submitted_total_only``: always ``True`` — at opening only the total tendered
  price is shown, not individual BoQ line amounts.

## technical_refs fields

- ``dom_output_code``: from ``TM2 Opening Readiness Record.dom_output_code``.
- ``publication_snapshot_code``: from ``Procurement Journey.publication_snapshot_ref``.

## Error codes

| Code | Condition |
|---|---|
| ``INVALID_TENDER_CODE`` | ``tender_code`` is blank or not a string. |
| ``INVALID_OPENING_READINESS_CODE`` | ``opening_readiness_code`` is blank or not a string. |
| ``INVALID_JOURNEY_CODE`` | ``journey_code`` is blank or not a string. |
| ``TENDER_NOT_FOUND`` | No ``TM2 Tender`` with the given ``tender_code``. |
| ``OPENING_READINESS_NOT_FOUND`` | No ``TM2 Opening Readiness Record`` with the given code. |
| ``JOURNEY_NOT_FOUND`` | ``journey_code`` does not exist (raised by R3-001). |
"""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.procurement_lifecycle.handoff_card_service import (
    create_or_update_handoff_card,
)

_ORR_DESK_ROUTE_PREFIX = "/app/tm2-opening-readiness-record"

_READY_STATUS = "Ready"


def _handoff_code(tender_code: str) -> str:
    """Derive OPENREADY handoff code from a tender code.

    ``TND-MOH-2026-001`` → ``OPENREADY-TND-MOH-2026-001``.
    """
    return f"OPENREADY-{tender_code}"


def _find_tm2_tender(tender_code: str) -> dict[str, Any] | None:
    """Return TM2 Tender row dict or None."""
    fields = ["name", "tender_code", "status"]
    if frappe.db.exists("TM2 Tender", tender_code):
        row = frappe.db.get_value("TM2 Tender", tender_code, fields, as_dict=True)
        if row:
            return row
    rows = frappe.db.get_all(
        "TM2 Tender",
        filters={"tender_code": tender_code},
        fields=fields,
        limit=1,
        order_by="creation asc",
    )
    return rows[0] if rows else None


def _find_opening_readiness_record(orr_code: str) -> dict[str, Any] | None:
    """Return TM2 Opening Readiness Record by ``opening_readiness_code`` or None."""
    rows = frappe.db.get_all(
        "TM2 Opening Readiness Record",
        filters={"opening_readiness_code": orr_code},
        fields=[
            "name",
            "opening_readiness_code",
            "tender_code",
            "dom_output_code",
            "tender_std_instance_code",
            "sealed_submission_refs",
            "valid_submission_count",
            "readiness_status",
            "prepared_by",
            "prepared_at",
        ],
        limit=1,
        order_by="creation asc",
    )
    return rows[0] if rows else None


def _get_timeline(tm2_tender_frappe_name: str) -> dict[str, Any] | None:
    """Return TM2 Tender Timeline row for the given TM2 Tender Frappe name."""
    rows = frappe.db.get_all(
        "TM2 Tender Timeline",
        filters={"tm2_tender": tm2_tender_frappe_name},
        fields=["opening_scheduled_at", "timezone"],
        limit=1,
        order_by="creation asc",
    )
    return rows[0] if rows else None


def _get_journey_pub_snapshot_ref(journey_code: str) -> str:
    """Return Procurement Journey.publication_snapshot_ref."""
    val = frappe.db.get_value("Procurement Journey", journey_code, "publication_snapshot_ref")
    return str(val or "")


def _format_iso(dt_val: Any) -> str:
    """Format a datetime value as ISO 8601 with +03:00 offset."""
    if not dt_val:
        return ""
    s = str(dt_val).replace(" ", "T")
    if "+" not in s and "Z" not in s:
        s += "+03:00"
    return s


def _parse_sealed_submission_refs(raw: Any) -> list[str]:
    """Parse the sealed_submission_refs JSON field into a list of strings.

    The field stores a JSON *object* with a ``refs`` key (TM2-ORR-004):
    ``{"refs": ["BID-...", "BID-..."]}``

    Older/raw list form is also handled defensively.
    """
    if not raw:
        return []

    parsed: Any = raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return []

    # Canonical envelope form: {"refs": [...]}
    if isinstance(parsed, dict):
        inner = parsed.get("refs")
        if isinstance(inner, list):
            return [str(r) for r in inner if r]
        return []

    # Defensive: bare list (legacy / test)
    if isinstance(parsed, list):
        return [str(r) for r in parsed if r]

    return []


def create_opening_readiness_handoff(
    tender_code: str, opening_readiness_code: str, journey_code: str
) -> dict[str, Any]:
    """Upsert the Opening Readiness handoff card for a journey.

    **CRITICAL:** Only call this when a real ``TM2 Opening Readiness Record`` exists.
    This service will not fabricate an opening readiness record.

    :param tender_code: ``TM2 Tender`` code (``tender_code`` field / Frappe ``name``,
        e.g. ``TND-MOH-2026-001``).
    :param opening_readiness_code: ``TM2 Opening Readiness Record.opening_readiness_code``
        (e.g. ``ORR-TND-MOH-2026-001``).
    :param journey_code: Procurement Journey code (e.g. ``JRN-MOH-2026-001``).
    :returns: Result dict from ``create_or_update_handoff_card``.
    :raises ValueError: If inputs are blank, tender not found, or ORR not found.
    """
    if not tender_code or not isinstance(tender_code, str) or not tender_code.strip():
        raise ValueError("INVALID_TENDER_CODE: tender_code must be a non-empty string")
    if (
        not opening_readiness_code
        or not isinstance(opening_readiness_code, str)
        or not opening_readiness_code.strip()
    ):
        raise ValueError(
            "INVALID_OPENING_READINESS_CODE: opening_readiness_code must be a non-empty string"
        )
    if not journey_code or not isinstance(journey_code, str) or not journey_code.strip():
        raise ValueError("INVALID_JOURNEY_CODE: journey_code must be a non-empty string")

    tnd_code = tender_code.strip()
    orr_code = opening_readiness_code.strip()
    jrn_code = journey_code.strip()

    # 1. Locate TM2 Tender (required for validation + timeline lookup)
    tm2 = _find_tm2_tender(tnd_code)
    if tm2 is None:
        raise ValueError(
            f"TENDER_NOT_FOUND: no TM2 Tender with tender_code or name = {tnd_code!r}"
        )
    tm2_frappe_name: str = str(tm2["name"])

    # 2. Locate the real TM2 Opening Readiness Record — no fabrication
    orr = _find_opening_readiness_record(orr_code)
    if orr is None:
        raise ValueError(
            f"OPENING_READINESS_NOT_FOUND: no TM2 Opening Readiness Record with "
            f"opening_readiness_code = {orr_code!r}. "
            "create_opening_readiness_handoff must only be called when a real "
            "opening readiness record exists (optional OPENING_READY checkpoint or "
            "live production)."
        )

    orr_frappe_name: str = str(orr["name"])
    dom_output_code: str = str(orr.get("dom_output_code") or "")
    sealed_refs_raw = orr.get("sealed_submission_refs")
    sealed_refs: list[str] = _parse_sealed_submission_refs(sealed_refs_raw)
    readiness_status: str = str(orr.get("readiness_status") or "Not Ready")
    prepared_by: str = str(orr.get("prepared_by") or "SYSTEM")

    # 3. Fetch timeline for opening_scheduled_at
    timeline = _get_timeline(tm2_frappe_name)
    opening_scheduled_iso: str = ""
    if timeline:
        opening_scheduled_iso = _format_iso(timeline.get("opening_scheduled_at"))

    # 4. Get publication_snapshot_ref from Journey
    pub_snapshot_code: str = _get_journey_pub_snapshot_ref(jrn_code)

    is_ready: bool = readiness_status == _READY_STATUS

    # 5. locked_summary (spec §16.10)
    locked_summary: dict[str, Any] = {
        "arithmetic_correction_at_opening": False,
    }
    if dom_output_code:
        locked_summary["opening_model"] = dom_output_code
    if pub_snapshot_code:
        locked_summary["publication_snapshot"] = pub_snapshot_code
    if opening_scheduled_iso:
        locked_summary["opening_scheduled_at"] = opening_scheduled_iso

    # 6. passed_forward_summary (spec §16.10)
    passed_forward: dict[str, Any] = {
        "opening_register_rules_ready": is_ready,
        "display_submitted_total_only": True,
    }
    if sealed_refs:
        passed_forward["sealed_submission_refs"] = sealed_refs

    # 7. Evidence link — TM2 Opening Readiness Record
    orr_route = f"{_ORR_DESK_ROUTE_PREFIX}/{orr_frappe_name}"
    evidence_links: list[dict[str, str]] = [
        {
            "label": "Opening Readiness Record",
            "object_type": "Opening Readiness Record",
            "object_code": orr_code,
            "module": "Tender Management",
            "route": orr_route,
            "visibility": "Internal",
        }
    ]

    # 8. technical_refs (spec §16.10)
    technical_refs: dict[str, str] = {}
    if dom_output_code:
        technical_refs["dom_output_code"] = dom_output_code
    if pub_snapshot_code:
        technical_refs["publication_snapshot_code"] = pub_snapshot_code

    payload: dict[str, Any] = {
        "handoff_code": _handoff_code(tnd_code),
        "handoff_title": "Opening Readiness Record",
        "journey_code": jrn_code,
        "source_module": "Tender Management",
        "target_module": "Bid Opening",
        "source_object_type": "Opening Readiness Record",
        "source_object_code": orr_code,
        "target_object_type": "Bid Opening Session",
        "status": "Handed Off",
        "generated_by": prepared_by,
        "next_action": "Conduct bid opening session using the opening register rules.",
        "locked_summary": locked_summary,
        "passed_forward_summary": passed_forward,
        "evidence_links": evidence_links,
        "technical_refs": technical_refs,
    }

    return create_or_update_handoff_card(payload)
