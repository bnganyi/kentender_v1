# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-008 / LV-R3-008-01 — **Tender closing handoff service** (cursor pack §8.2).

## Goal

``create_tender_closing_certificate(tender_code, closing_code, journey_code)`` produces
(or updates) the ``Procurement Handoff Card`` that records the Tender Management →
Bid Opening module boundary event once the submission window closes.

## CRITICAL constraint (cursor pack §8.2)

This service **must only be called when a real ``TM2 Tender Closing Record`` already
exists**.  It must **not fabricate** a closing record for the base ``TENDER_PUBLISHED``
checkpoint.  If no ``TM2 Tender Closing Record`` with the given ``closing_code`` exists,
the service raises ``ValueError: CLOSING_RECORD_NOT_FOUND`` and does not create a card.

This service is intended for:
- The optional ``OPENING_READY`` checkpoint (when the WORKS master seed loads with
  ``checkpoint="OPENING_READY"``), or
- Live production flows where tender closing has actually occurred.

## Handoff card produced

| Field | Value |
|---|---|
| handoff_code | ``CLOSECERT-{tender_code}`` (e.g. ``CLOSECERT-TND-MOH-2026-001``) |
| source_module | ``Tender Management`` |
| target_module | ``Bid Opening`` |
| source_object_type | ``Tender Closing Record`` |
| source_object_code | ``closing_code`` (the ``TM2 Tender Closing Record.closing_code``) |
| target_object_type | ``Opening Readiness Record`` (if linked record found) |
| target_object_code | ``opening_readiness_code`` (from linked ``TM2 Opening Readiness Record``) |
| status | ``Consumed`` |

## Opening readiness linkage

The service looks up the ``TM2 Opening Readiness Record`` linked to the closing record
via ``tm2_tender_closing_record`` FK.  If found, its ``opening_readiness_code`` is set
as ``target_object_code``.  If not yet created, ``target_object_code`` is omitted.

## locked_summary fields

- ``submission_deadline``: ISO datetime from ``TM2 Tender Closing Record.submission_deadline_at``
  (falls back to ``TM2 Tender Timeline.submission_deadline_at``).
- ``closed_at``: ISO datetime from ``TM2 Tender Closing Record.closed_at``.
- ``official_time_source``: always ``"Server Time"`` — time is derived from server clock.
- ``submission_window_closed``: always ``True`` (closing record exists → window is closed).

## passed_forward_summary fields

- ``valid_submission_count``: from ``TM2 Tender Closing Record.valid_submission_count``.
- ``late_attempt_count``: from ``TM2 Tender Closing Record.late_attempt_count``.
- ``sealed_submission_refs_available``: ``True`` if ``valid_submission_count > 0``.

## technical_refs fields

- ``tender_code``: the tender's business code.
- ``publication_snapshot_code``: from ``Procurement Journey.publication_snapshot_ref``
  (or empty if not set).

## Error codes

| Code | Condition |
|---|---|
| ``INVALID_TENDER_CODE`` | ``tender_code`` is blank or not a string. |
| ``INVALID_CLOSING_CODE`` | ``closing_code`` is blank or not a string. |
| ``INVALID_JOURNEY_CODE`` | ``journey_code`` is blank or not a string. |
| ``TENDER_NOT_FOUND`` | No ``TM2 Tender`` with the given ``tender_code``. |
| ``CLOSING_RECORD_NOT_FOUND`` | No ``TM2 Tender Closing Record`` with ``closing_code``. |
| ``JOURNEY_NOT_FOUND`` | ``journey_code`` does not exist (raised by R3-001). |
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_lifecycle.handoff_card_service import (
    create_or_update_handoff_card,
)

_CLOSING_RECORD_DESK_ROUTE_PREFIX = "/app/tm2-tender-closing-record"


def _handoff_code(tender_code: str) -> str:
    """Derive CLOSECERT handoff code from a tender code.

    ``TND-MOH-2026-001`` → ``CLOSECERT-TND-MOH-2026-001``.
    """
    return f"CLOSECERT-{tender_code}"


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


def _find_closing_record(closing_code: str) -> dict[str, Any] | None:
    """Return TM2 Tender Closing Record by ``closing_code`` field or None.

    ``TM2 Tender Closing Record.closing_code`` is a unique business identifier.
    """
    rows = frappe.db.get_all(
        "TM2 Tender Closing Record",
        filters={"closing_code": closing_code},
        fields=[
            "name",
            "closing_code",
            "tender_code",
            "tm2_tender",
            "submission_deadline_at",
            "closed_at",
            "closed_by",
            "closing_status",
            "valid_submission_count",
            "late_attempt_count",
        ],
        limit=1,
        order_by="creation asc",
    )
    return rows[0] if rows else None


def _find_opening_readiness_record(closing_frappe_name: str) -> dict[str, Any] | None:
    """Return TM2 Opening Readiness Record linked to this closing record, or None."""
    rows = frappe.db.get_all(
        "TM2 Opening Readiness Record",
        filters={"tm2_tender_closing_record": closing_frappe_name},
        fields=["name", "opening_readiness_code", "readiness_status"],
        limit=1,
        order_by="creation asc",
    )
    return rows[0] if rows else None


def _get_timeline_deadline(tm2_tender_frappe_name: str) -> str:
    """Return formatted submission_deadline_at from TM2 Tender Timeline as fallback."""
    rows = frappe.db.get_all(
        "TM2 Tender Timeline",
        filters={"tm2_tender": tm2_tender_frappe_name},
        fields=["submission_deadline_at"],
        limit=1,
        order_by="creation asc",
    )
    if rows:
        return _format_iso(rows[0].get("submission_deadline_at"))
    return ""


def _get_journey_pub_snapshot_ref(journey_code: str) -> str:
    """Return Procurement Journey.publication_snapshot_ref for the journey."""
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


def create_tender_closing_certificate(
    tender_code: str, closing_code: str, journey_code: str
) -> dict[str, Any]:
    """Upsert the Tender Closing Certificate handoff card for a journey.

    **CRITICAL:** Only call this when a real ``TM2 Tender Closing Record`` exists.
    This service will not fabricate a closing record.

    :param tender_code: ``TM2 Tender`` code (``tender_code`` field / Frappe ``name``,
        e.g. ``TND-MOH-2026-001``).
    :param closing_code: ``TM2 Tender Closing Record.closing_code``
        (e.g. ``CLS-TND-MOH-2026-001``).
    :param journey_code: Procurement Journey code (e.g. ``JRN-MOH-2026-001``).
    :returns: Result dict from ``create_or_update_handoff_card``.
    :raises ValueError: If inputs are blank, tender not found, or closing record not found.
    """
    if not tender_code or not isinstance(tender_code, str) or not tender_code.strip():
        raise ValueError("INVALID_TENDER_CODE: tender_code must be a non-empty string")
    if not closing_code or not isinstance(closing_code, str) or not closing_code.strip():
        raise ValueError("INVALID_CLOSING_CODE: closing_code must be a non-empty string")
    if not journey_code or not isinstance(journey_code, str) or not journey_code.strip():
        raise ValueError("INVALID_JOURNEY_CODE: journey_code must be a non-empty string")

    tnd_code = tender_code.strip()
    cls_code = closing_code.strip()
    jrn_code = journey_code.strip()

    # 1. Locate TM2 Tender (required for validation)
    tm2 = _find_tm2_tender(tnd_code)
    if tm2 is None:
        raise ValueError(
            f"TENDER_NOT_FOUND: no TM2 Tender with tender_code or name = {tnd_code!r}"
        )
    tm2_frappe_name: str = str(tm2["name"])

    # 2. Locate the real TM2 Tender Closing Record — no fabrication
    closing = _find_closing_record(cls_code)
    if closing is None:
        raise ValueError(
            f"CLOSING_RECORD_NOT_FOUND: no TM2 Tender Closing Record with "
            f"closing_code = {cls_code!r}. "
            "create_tender_closing_certificate must only be called when a real "
            "closing record exists (optional OPENING_READY checkpoint or live production)."
        )

    closing_frappe_name: str = str(closing["name"])
    valid_submission_count: int = int(closing.get("valid_submission_count") or 0)
    late_attempt_count: int = int(closing.get("late_attempt_count") or 0)
    closed_at_iso: str = _format_iso(closing.get("closed_at"))
    closed_by: str = str(closing.get("closed_by") or "SYSTEM")

    # submission_deadline from closing record; fallback to TM2 Timeline
    submission_deadline_iso: str = _format_iso(closing.get("submission_deadline_at"))
    if not submission_deadline_iso:
        submission_deadline_iso = _get_timeline_deadline(tm2_frappe_name)

    # 3. Look for linked TM2 Opening Readiness Record
    opening_readiness = _find_opening_readiness_record(closing_frappe_name)
    opening_readiness_code: str = ""
    if opening_readiness:
        opening_readiness_code = str(opening_readiness.get("opening_readiness_code") or "")

    # 4. publication_snapshot_code from Journey
    pub_snapshot_code: str = _get_journey_pub_snapshot_ref(jrn_code)

    # 5. locked_summary (spec §16.9)
    locked_summary: dict[str, Any] = {
        "submission_window_closed": True,
        "official_time_source": "Server Time",
    }
    if submission_deadline_iso:
        locked_summary["submission_deadline"] = submission_deadline_iso
    if closed_at_iso:
        locked_summary["closed_at"] = closed_at_iso

    # 6. passed_forward_summary (spec §16.9)
    passed_forward: dict[str, Any] = {
        "valid_submission_count": valid_submission_count,
        "late_attempt_count": late_attempt_count,
        "sealed_submission_refs_available": valid_submission_count > 0,
    }

    # 7. Evidence link — TM2 Tender Closing Record
    cls_route = f"{_CLOSING_RECORD_DESK_ROUTE_PREFIX}/{closing_frappe_name}"
    evidence_links: list[dict[str, str]] = [
        {
            "label": "Tender Closing Record",
            "object_type": "Tender Closing Record",
            "object_code": cls_code,
            "module": "Tender Management",
            "route": cls_route,
            "visibility": "Internal",
        }
    ]

    # 8. technical_refs (spec §16.9)
    technical_refs: dict[str, str] = {
        "tender_code": tnd_code,
    }
    if pub_snapshot_code:
        technical_refs["publication_snapshot_code"] = pub_snapshot_code

    payload: dict[str, Any] = {
        "handoff_code": _handoff_code(tnd_code),
        "handoff_title": "Tender Closing Certificate",
        "journey_code": jrn_code,
        "source_module": "Tender Management",
        "target_module": "Bid Opening",
        "source_object_type": "Tender Closing Record",
        "source_object_code": cls_code,
        "status": "Consumed",
        "generated_by": closed_by,
        "next_action": "Prepare opening readiness using the opening register rules.",
        "locked_summary": locked_summary,
        "passed_forward_summary": passed_forward,
        "evidence_links": evidence_links,
        "technical_refs": technical_refs,
    }

    # Set target when opening readiness record is linked
    if opening_readiness_code:
        payload["target_object_type"] = "Opening Readiness Record"
        payload["target_object_code"] = opening_readiness_code

    return create_or_update_handoff_card(payload)
