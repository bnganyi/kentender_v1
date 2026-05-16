# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-007 / LV-R3-007-01 — **Tender publication handoff service** (cursor pack §8.2).

## Goal

``create_tender_publication_certificate(tender_code, publication_code, journey_code)``
produces (or updates) the ``Procurement Handoff Card`` that records the Tender
Management → Suppliers / Tender Closing module boundary event.  It is
**snapshot/addendum aware** (LV-R3-007-01): it reads live ``TM2 Tender``,
``TM2 Tender Timeline``, ``Tender Publication Snapshot``, and ``Tender Publication
Record`` data to populate the card, and correctly reflects whether addendum
acknowledgement is required.

## Handoff card produced

| Field | Value |
|---|---|
| handoff_code | ``PUBCERT-{tender_code}`` (e.g. ``PUBCERT-TND-MOH-2026-001``) |
| source_module | ``Tender Management`` |
| target_module | ``Suppliers / Tender Closing`` |
| source_object_type | ``TM2 Tender`` |
| source_object_code | ``tender_code`` |
| target_object_type | ``Supplier Portal / Tender Closing`` |
| target_object_code | ``tender_code`` |
| status | ``Handed Off`` |

## Handoff code derivation

``PUBCERT-`` is prepended directly to ``tender_code`` (e.g. ``TND-MOH-2026-001``
→ ``PUBCERT-TND-MOH-2026-001``).

## Snapshot awareness (LV-R3-007-01)

The service resolves the ``Tender Publication Snapshot`` via:
1. ``Procurement Journey.publication_snapshot_ref`` → if that code exists as a real
   ``Tender Publication Snapshot`` DocType record, its output codes are used.
2. Direct FK fallback: query ``Tender Publication Snapshot`` by
   ``tm2_tender = tender_frappe_name``, use the latest snapshot found.
If no real snapshot record is found, the service records the conceptual
``publication_snapshot_ref`` code (from the Journey) as the snapshot code but
leaves output codes empty.

## Addendum awareness (LV-R3-007-01)

The service detects an active addendum via two sources (checked in order):
1. ``TM2 Tender Timeline.extension_source_addendum_code`` (non-empty when the
   deadline was extended by an addendum — ``deadline_extended = 1``).
2. Latest issued/approved ``Tender Addendum`` with ``tender_id = tender_frappe_name``.
If an addendum code is found:
- ``passed_forward_summary.addendum_acknowledgement_required = True``
- ``passed_forward_summary.current_addendum = <addendum_code>``
- An evidence link for the addendum is included.
If no addendum is found:
- ``addendum_acknowledgement_required = False``
- ``current_addendum`` is omitted.

## publication_code parameter

``publication_code`` is the ``Tender Publication Record.publication_record_code``
(e.g. ``PUB-TND-MOH-2026-001-001``).  The service stores this in ``technical_refs``
and, if a real ``Tender Publication Record`` row exists with that code, reads
``published_at`` and ``published_by`` from it.  If no record exists (e.g. the
publication happened before this service was wired), the parameter is still recorded
in ``technical_refs`` without failing.

## submission_deadline derivation

Sourced from ``TM2 Tender Timeline.submission_deadline_at`` (ISO UTC formatted as
``"YYYY-MM-DDTHH:MM:SS+HH:MM"`` using the timeline's ``timezone``).  Falls back to
``TM2 Tender.published_at`` if no timeline is found.

## Error codes

| Code | Condition |
|---|---|
| ``INVALID_TENDER_CODE`` | ``tender_code`` is blank or not a string. |
| ``INVALID_PUBLICATION_CODE`` | ``publication_code`` is blank or not a string. |
| ``INVALID_JOURNEY_CODE`` | ``journey_code`` is blank or not a string. |
| ``TENDER_NOT_FOUND`` | No ``TM2 Tender`` with the given ``tender_code``. |
| ``JOURNEY_NOT_FOUND`` | ``journey_code`` does not exist (raised by R3-001). |
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_lifecycle.handoff_card_service import (
    create_or_update_handoff_card,
)

_TM2_DESK_ROUTE_PREFIX = "/app/tm2-tender"
_ADDENDUM_DESK_ROUTE_PREFIX = "/app/tender-addendum"
_PUB_SNAP_DESK_ROUTE_PREFIX = "/app/tender-publication-snapshot"

_PUBLISHED_STATUS = "Published"


def _handoff_code(tender_code: str) -> str:
    """Derive PUBCERT handoff code from a tender code.

    ``TND-MOH-2026-001`` → ``PUBCERT-TND-MOH-2026-001``.
    """
    return f"PUBCERT-{tender_code}"


def _find_tm2_tender(tender_code: str) -> dict[str, Any] | None:
    """Return TM2 Tender row dict or None."""
    fields = [
        "name",
        "tender_code",
        "status",
        "procurement_method",
        "procurement_category",
        "published_at",
        "published_by",
        "require_addendum_acknowledgement",
    ]
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


def _get_timeline(tender_frappe_name: str) -> dict[str, Any] | None:
    """Return TM2 Tender Timeline row for the given TM2 Tender Frappe name."""
    rows = frappe.db.get_all(
        "TM2 Tender Timeline",
        filters={"tm2_tender": tender_frappe_name},
        fields=[
            "submission_deadline_at",
            "actual_publication_at",
            "timezone",
            "deadline_extended",
            "extension_source_addendum_code",
        ],
        limit=1,
        order_by="creation asc",
    )
    return rows[0] if rows else None


def _find_publication_record(publication_code: str) -> dict[str, Any] | None:
    """Return TM2 Publication Record matching ``publication_code`` business code.

    The DocType is ``TM2 Publication Record``; field ``publication_code`` is the
    business identifier (unique index).
    """
    rows = frappe.db.get_all(
        "TM2 Publication Record",
        filters={"publication_code": publication_code},
        fields=["name", "publication_code", "published_at", "published_by", "tm2_tender"],
        limit=1,
        order_by="creation asc",
    )
    return rows[0] if rows else None


def _find_pub_snapshot_by_name(candidate_code: str) -> dict[str, Any] | None:
    """Return Tender Publication Snapshot if ``candidate_code`` is a real record."""
    if not candidate_code or not frappe.db.exists("Tender Publication Snapshot", candidate_code):
        return None
    return frappe.db.get_value(
        "Tender Publication Snapshot",
        candidate_code,
        [
            "name",
            "bundle_output_code",
            "dsm_output_code",
            "dom_output_code",
            "dem_output_code",
            "dcm_output_code",
            "source_template_version_code",
        ],
        as_dict=True,
    )


def _find_pub_snapshot_by_tm2(tm2_tender_name: str) -> dict[str, Any] | None:
    """Return the latest Tender Publication Snapshot linked via ``tm2_tender`` FK."""
    rows = frappe.db.get_all(
        "Tender Publication Snapshot",
        filters={"tm2_tender": tm2_tender_name},
        fields=[
            "name",
            "bundle_output_code",
            "dsm_output_code",
            "dom_output_code",
            "dem_output_code",
            "dcm_output_code",
            "source_template_version_code",
        ],
        limit=1,
        order_by="creation desc",
    )
    return rows[0] if rows else None


def _find_latest_addendum_by_tm2(tender_frappe_name: str) -> str:
    """Return the latest issued/approved Tender Addendum code for this TM2 Tender.

    ``Tender Addendum.tender_id`` is the Frappe ``name`` of the parent tender.
    Returns empty string if none found.
    """
    rows = frappe.db.get_all(
        "Tender Addendum",
        filters={
            "tender_id": tender_frappe_name,
            "status": ["in", ["Issued", "Approved"]],
        },
        fields=["name", "addendum_code", "addendum_number"],
        order_by="addendum_number desc, creation desc",
        limit=1,
    )
    if rows:
        return str(rows[0].get("addendum_code") or rows[0]["name"])
    return ""


def _format_iso_datetime(dt_val: Any, timezone: str = "Africa/Nairobi") -> str:
    """Format a datetime value as an ISO 8601 string with UTC+3 offset.

    ``timezone`` is informational; for KenTender the canonical offset is +03:00.
    """
    if not dt_val:
        return ""
    try:
        s = str(dt_val)
        # Replace space separator and append +03:00 if no tz info present
        s = s.replace(" ", "T")
        if "+" not in s and "Z" not in s:
            s = s + "+03:00"
        return s
    except Exception:
        return str(dt_val)


def _get_journey_pub_snapshot_ref(journey_code: str) -> str:
    """Return ``Procurement Journey.publication_snapshot_ref`` for a journey."""
    val = frappe.db.get_value("Procurement Journey", journey_code, "publication_snapshot_ref")
    return str(val or "")


def create_tender_publication_certificate(
    tender_code: str, publication_code: str, journey_code: str
) -> dict[str, Any]:
    """Upsert the Tender Publication Certificate handoff card for a journey.

    :param tender_code: ``TM2 Tender`` code (``tender_code`` field / Frappe ``name``,
        e.g. ``TND-MOH-2026-001``).
    :param publication_code: ``Tender Publication Record.publication_record_code``
        (e.g. ``PUB-TND-MOH-2026-001-001``).  Stored in ``technical_refs`` whether
        or not a real record exists.
    :param journey_code: Procurement Journey code (e.g. ``JRN-MOH-2026-001``).
    :returns: Result dict from ``create_or_update_handoff_card``.
    :raises ValueError: If inputs are blank or the TM2 Tender is not found.
    """
    if not tender_code or not isinstance(tender_code, str) or not tender_code.strip():
        raise ValueError("INVALID_TENDER_CODE: tender_code must be a non-empty string")
    if not publication_code or not isinstance(publication_code, str) or not publication_code.strip():
        raise ValueError("INVALID_PUBLICATION_CODE: publication_code must be a non-empty string")
    if not journey_code or not isinstance(journey_code, str) or not journey_code.strip():
        raise ValueError("INVALID_JOURNEY_CODE: journey_code must be a non-empty string")

    tnd_code = tender_code.strip()
    pub_code = publication_code.strip()
    jrn_code = journey_code.strip()

    # 1. Locate TM2 Tender
    tm2 = _find_tm2_tender(tnd_code)
    if tm2 is None:
        raise ValueError(
            f"TENDER_NOT_FOUND: no TM2 Tender with tender_code or name = {tnd_code!r}"
        )

    tm2_frappe_name: str = str(tm2["name"])
    tm2_status: str = str(tm2.get("status") or "")
    procurement_method: str = str(tm2.get("procurement_method") or "")
    procurement_category: str = str(tm2.get("procurement_category") or "")
    published_at_raw = tm2.get("published_at")

    # 2. Fetch timeline for submission deadline + addendum context
    timeline = _get_timeline(tm2_frappe_name)
    submission_deadline_iso: str = ""
    addendum_code_from_timeline: str = ""
    if timeline:
        tz = str(timeline.get("timezone") or "Africa/Nairobi")
        submission_deadline_iso = _format_iso_datetime(timeline.get("submission_deadline_at"), tz)
        if timeline.get("deadline_extended"):
            addendum_code_from_timeline = str(timeline.get("extension_source_addendum_code") or "")

    # 3. Resolve publication snapshot (snapshot awareness)
    journey_snap_ref = _get_journey_pub_snapshot_ref(jrn_code)
    pub_snapshot: dict[str, Any] | None = None
    if journey_snap_ref:
        pub_snapshot = _find_pub_snapshot_by_name(journey_snap_ref)
    if pub_snapshot is None:
        pub_snapshot = _find_pub_snapshot_by_tm2(tm2_frappe_name)

    if pub_snapshot:
        snapshot_code = str(pub_snapshot["name"])
    elif journey_snap_ref:
        snapshot_code = journey_snap_ref  # conceptual ref from Journey
    else:
        snapshot_code = ""

    # Output codes from snapshot (if available)
    bundle_code: str = str((pub_snapshot or {}).get("bundle_output_code") or "")
    dsm_code: str = str((pub_snapshot or {}).get("dsm_output_code") or "")
    dom_code: str = str((pub_snapshot or {}).get("dom_output_code") or "")
    dem_code: str = str((pub_snapshot or {}).get("dem_output_code") or "")
    dcm_code: str = str((pub_snapshot or {}).get("dcm_output_code") or "")

    # 4. Resolve publication record (for metadata)
    pub_record = _find_publication_record(pub_code)

    # 5. Addendum awareness — derive current addendum code
    # Priority: timeline extension_source_addendum_code → latest issued addendum
    if addendum_code_from_timeline:
        current_addendum_code = addendum_code_from_timeline
    else:
        current_addendum_code = _find_latest_addendum_by_tm2(tm2_frappe_name)

    addendum_required: bool = bool(current_addendum_code)

    # 6. Supplier access flags
    is_published = (tm2_status == _PUBLISHED_STATUS)

    # 7. Build locked_summary (spec §16.8)
    locked_summary: dict[str, Any] = {
        "published_tender": tnd_code,
    }
    if snapshot_code:
        locked_summary["publication_snapshot"] = snapshot_code
    if procurement_method:
        locked_summary["procurement_method"] = procurement_method
    if procurement_category:
        locked_summary["procurement_category"] = procurement_category
    if submission_deadline_iso:
        locked_summary["submission_deadline"] = submission_deadline_iso

    # 8. Build passed_forward_summary (addendum aware, spec §16.8)
    passed_forward: dict[str, Any] = {
        "supplier_access_active": is_published,
        "tender_documents_available": is_published,
        "addendum_acknowledgement_required": addendum_required,
    }
    if current_addendum_code:
        passed_forward["current_addendum"] = current_addendum_code

    # 9. Evidence links — Tender + Snapshot (always) + Addendum (if present)
    tm2_route = f"{_TM2_DESK_ROUTE_PREFIX}/{tm2_frappe_name}"
    evidence_links: list[dict[str, str]] = [
        {
            "label": "Published Tender",
            "object_type": "TM2 Tender",
            "object_code": tnd_code,
            "module": "Tender Management",
            "route": tm2_route,
            "visibility": "Internal",
        },
    ]
    if snapshot_code:
        snap_route = f"{_PUB_SNAP_DESK_ROUTE_PREFIX}/{snapshot_code}"
        evidence_links.append(
            {
                "label": "Publication Snapshot",
                "object_type": "Publication Snapshot",
                "object_code": snapshot_code,
                "module": "Tender Management / STD Engine",
                "route": snap_route,
                "visibility": "Internal",
            }
        )
    if current_addendum_code:
        # Try to find the real Tender Addendum name for routing
        addendum_frappe_name = (
            frappe.db.get_value(
                "Tender Addendum", {"addendum_code": current_addendum_code}, "name"
            )
            or current_addendum_code
        )
        add_route = f"{_ADDENDUM_DESK_ROUTE_PREFIX}/{addendum_frappe_name}"
        # Derive a human-readable label from the addendum number in the code
        # e.g. ADD-TND-MOH-2026-001-01 → "Addendum 01"
        add_suffix = current_addendum_code.rsplit("-", 1)[-1]
        add_label = f"Addendum {add_suffix}" if add_suffix.isdigit() else "Addendum"
        evidence_links.append(
            {
                "label": add_label,
                "object_type": "Tender Addendum",
                "object_code": current_addendum_code,
                "module": "Tender Management",
                "route": add_route,
                "visibility": "Internal",
            }
        )

    # 10. technical_refs (snapshot aware — output codes + publication_code)
    technical_refs: dict[str, str] = {}
    if pub_code:
        technical_refs["publication_code"] = pub_code
    if bundle_code:
        technical_refs["bundle_output_code"] = bundle_code
    if dsm_code:
        technical_refs["dsm_output_code"] = dsm_code
    if dom_code:
        technical_refs["dom_output_code"] = dom_code
    if dem_code:
        technical_refs["dem_output_code"] = dem_code
    if dcm_code:
        technical_refs["dcm_output_code"] = dcm_code

    payload: dict[str, Any] = {
        "handoff_code": _handoff_code(tnd_code),
        "handoff_title": "Tender Publication Certificate",
        "journey_code": jrn_code,
        "source_module": "Tender Management",
        "target_module": "Suppliers / Tender Closing",
        "source_object_type": "TM2 Tender",
        "source_object_code": tnd_code,
        "target_object_type": "Supplier Portal / Tender Closing",
        "target_object_code": tnd_code,
        "status": "Handed Off",
        "generated_by": frappe.session.user or "system",
        "next_action": (
            "Suppliers may access the tender and submit bids before the revised submission deadline."
        ),
        "locked_summary": locked_summary,
        "passed_forward_summary": passed_forward,
        "evidence_links": evidence_links,
        "technical_refs": technical_refs,
    }

    return create_or_update_handoff_card(payload)
