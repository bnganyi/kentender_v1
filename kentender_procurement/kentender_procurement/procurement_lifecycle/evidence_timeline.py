# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-015 / LV-R3-015-01 — **Evidence timeline service** (cursor pack §9.5).

## Goal

``get_journey_evidence_timeline(journey_code)`` returns a **chronologically ordered list
of evidence events** for a Procurement Journey, drawing from:

1. Handoff cards (primary source — one event per ``Procurement Handoff Card``).
2. ``Tender Addendum`` records linked to the journey's TM2 Tender (when they exist).
3. ``TM2 Tender Audit Event`` rows for the journey's TM2 tender business code (**R7-003 /
   LV-G0-001-05** append-only façade). Rows include ``audit_event_code`` for filtering and
   are ordered after lifecycle handoffs at the same ``occurred_at`` (tie-break).

Sources 4–6 from pack §9.5 (publication snapshots, readiness records, release/approval
certificates, closing/opening readiness records) are surfaced **through** the handoff
card evidence links at this stage; fabricated events from non-existent source records
are never emitted.

## No-fabrication rule

For the base ``TENDER_PUBLISHED`` checkpoint:

- ``CLOSECERT`` and ``OPENREADY`` handoff cards do not exist → no closing/opening events.
- Addendum events are only emitted when real ``Tender Addendum`` records exist in the DB.

## Event shape (pack §9.5)

```python
{
  "occurred_at": str,          # ISO 8601 datetime (from consumed_at > generated_at > creation)
  "module": str,               # source_module of handoff card
  "event_type": str,           # step label for the card's handoff_code; falls back to handoff_title
  "business_label": str,       # human label — "<handoff_title> issued" or "<addendum_code> issued"
  "object_type": str,          # source_object_type
  "object_code": str,          # source_object_code
  "handoff_code": str | None,  # handoff_code (None for addendum / audit lanes)
  "evidence_refs": list[str],  # object_code values from evidence_links_json.links (+ snapshot on audits)
  "handoff_status": str | None,  # Procurement Handoff Card status (handoff lane only)
  "stale_reason": str | None,   # when card is Stale (NEG-PKGREL-STALE-001 / **R7-005**)
  "stale_warning": bool,        # true when stale_reason or status imply staleness for UI
  "audit_event_code": str | None,  # TAE-{tender}-{seq} when event is from TM2 audit (**R7-003**)
}
```

## Ordering

Events are sorted:

1. Primary: ``occurred_at`` ascending (earliest first).
2. Tie-break: step order ascending (handoff cards with a known step are ordered before
   addendum events; among handoff cards, the step_order from
   ``Procurement Journey Step`` is used if available, otherwise original sort position).

## WORKS golden scenario (base checkpoint, 7 handoff cards)

| occurred_at | event_type | handoff_code |
|---|---|---|
| 2026-01-15 | Strategy Priority | STRATREF-MOH-2026-001 |
| 2026-02-10 | Funding Available | BUDCONF-MOH-2026-001 |
| 2026-03-05 | Need Approved | DEMAPP-MOH-2026-001 |
| 2026-04-10 | Procurement Planned | PLANINCL-MOH-2026-001 |
| 2026-04-20 | Package Released | PKGREL-MOH-2026-001 |
| 2026-04-28 | Tender Document Ready | STDREADY-TND-MOH-2026-001 |
| 2026-05-01 | Tender Published | PUBCERT-TND-MOH-2026-001 |

## Error codes

| Code | Condition |
|---|---|
| ``INVALID_JOURNEY_CODE`` | ``journey_code`` is blank or not a string. |
| ``JOURNEY_NOT_FOUND`` | No ``Procurement Journey`` with that code. |
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import frappe


_CLOSING_HANDOFF_PREFIXES = ("CLOSECERT-", "OPENREADY-")


def get_journey_evidence_timeline(journey_code: str) -> list[dict[str, Any]]:
    """Return chronologically ordered evidence events for a Procurement Journey.

    :param journey_code: Procurement Journey identifier.
    :returns: Ordered list of event dicts (may be empty for journeys with no cards).
    :raises ValueError: If ``journey_code`` is blank (``INVALID_JOURNEY_CODE``).
    :raises frappe.DoesNotExistError: If the journey does not exist (``JOURNEY_NOT_FOUND``).
    """
    if not journey_code or not isinstance(journey_code, str) or not journey_code.strip():
        raise ValueError(
            "INVALID_JOURNEY_CODE: journey_code must be a non-empty string"
        )

    code = journey_code.strip()

    if not frappe.db.exists("Procurement Journey", code):
        raise frappe.DoesNotExistError(
            f"JOURNEY_NOT_FOUND: Procurement Journey '{code}' does not exist"
        )

    # --- 1. Build handoff_code → step_label mapping from Journey steps -------
    step_rows = frappe.db.sql(
        """
        SELECT step_key, step_order, label, handoff_code
        FROM `tabProcurement Journey Step`
        WHERE parent = %s AND handoff_code IS NOT NULL AND handoff_code != ''
        ORDER BY step_order ASC
        """,
        (code,),
        as_dict=True,
    )
    # {handoff_code: (step_order, label)}
    step_map: dict[str, tuple[int, str]] = {
        row.handoff_code: (row.step_order, row.label)
        for row in step_rows
        if row.handoff_code
    }

    # --- 2. Load all handoff cards for the journey ---------------------------
    card_rows = frappe.db.sql(
        """
        SELECT
            handoff_code,
            handoff_title,
            source_module,
            source_object_type,
            source_object_code,
            status,
            stale_reason,
            generated_at,
            consumed_at,
            creation,
            evidence_links_json
        FROM `tabProcurement Handoff Card`
        WHERE journey_code = %s
        ORDER BY generated_at ASC
        """,
        (code,),
        as_dict=True,
    )

    events: list[dict[str, Any]] = []

    for card in card_rows:
        hc = card.handoff_code or ""
        occurred_at = _best_timestamp(card.generated_at, card.consumed_at, card.creation)
        event_type, step_order = _derive_event_type(hc, card.handoff_title or "", step_map)
        evidence_refs = _extract_evidence_refs(card.evidence_links_json)

        st = str(card.status or "").strip()
        stale_reason = str(card.stale_reason or "").strip() or None

        events.append(
            {
                "occurred_at": occurred_at,
                "module": card.source_module or "",
                "event_type": event_type,
                "business_label": (card.handoff_title or "") + " issued",
                "object_type": card.source_object_type or "",
                "object_code": card.source_object_code or "",
                "handoff_code": hc or None,
                "evidence_refs": evidence_refs,
                "handoff_status": st or None,
                "stale_reason": stale_reason,
                "stale_warning": bool(
                    stale_reason or st.casefold() == "stale"
                ),
                "audit_event_code": None,
                "_sort_order": step_order,  # removed before return
            }
        )

    # --- 3. Addendum events from Tender Addendum records ---------------------
    tender_code = frappe.db.get_value("Procurement Journey", code, "tm2_tender_ref") or ""
    if tender_code:
        addendum_rows = frappe.db.sql(
            """
            SELECT addendum_code, issued_at, approved_at, creation
            FROM `tabTender Addendum`
            WHERE tender_id = %s
            ORDER BY issued_at ASC
            """,
            (tender_code,),
            as_dict=True,
        )
        for add in addendum_rows:
            occurred_at = _best_timestamp(add.issued_at, add.approved_at, add.creation)
            events.append(
                {
                    "occurred_at": occurred_at,
                    "module": "Tender Management",
                    "event_type": "Addendum Issued",
                    "business_label": f"{add.addendum_code} issued",
                    "object_type": "Tender Addendum",
                    "object_code": add.addendum_code or "",
                    "handoff_code": None,
                    "evidence_refs": [],
                    "handoff_status": None,
                    "stale_reason": None,
                    "stale_warning": False,
                    "audit_event_code": None,
                    "_sort_order": 9999,  # addendum events sort after same-timestamp handoff events
                }
            )

    # --- 3b. TM2 Tender Audit Event rows (LV-G0-001-05 / **R7-003**) ---------
    tender_code_strip = tender_code.strip() if tender_code else ""
    if tender_code_strip:
        audit_rows = frappe.db.sql(
            """
            SELECT
                audit_event_code,
                event_type,
                occurred_at,
                publication_snapshot_code,
                related_object_type,
                related_object_id
            FROM `tabTM2 Tender Audit Event`
            WHERE tender_code = %s
            ORDER BY occurred_at ASC, audit_event_code ASC
            """,
            (tender_code_strip,),
            as_dict=True,
        )
        for i, aud in enumerate(audit_rows or []):
            refs: list[str] = []
            ps = aud.publication_snapshot_code or ""
            if str(ps).strip():
                refs.append(str(ps).strip())
            oid = aud.related_object_id or ""
            if str(oid).strip() and str(oid).strip() not in refs:
                refs.append(str(oid).strip())

            biz = f"{aud.audit_event_code or '?'} · {aud.event_type or 'Audit'}"
            events.append(
                {
                    "occurred_at": _best_timestamp(aud.occurred_at, None, None),
                    "module": "Tender Management",
                    "event_type": aud.event_type or "Audit Event",
                    "business_label": biz,
                    "object_type": aud.related_object_type or "TM2 Tender",
                    "object_code": tender_code_strip,
                    "handoff_code": None,
                    "evidence_refs": refs,
                    "handoff_status": None,
                    "stale_reason": None,
                    "stale_warning": False,
                    "audit_event_code": aud.audit_event_code or "",
                    "_sort_order": 15_000 + i,
                }
            )

    # --- 4. Sort: primarily by occurred_at, tie-break by step order ----------
    events.sort(key=lambda e: (_dt_sort_key(e["occurred_at"]), e["_sort_order"]))

    # Strip internal sort key
    for ev in events:
        del ev["_sort_order"]

    return events


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _best_timestamp(
    primary: datetime | str | None,
    secondary: datetime | str | None,
    fallback: datetime | str | None,
) -> str:
    """Return the best available timestamp as an ISO 8601 string."""
    for ts in (primary, secondary, fallback):
        if ts is not None:
            return _to_iso(ts)
    return ""


def _to_iso(ts: datetime | str) -> str:
    """Convert a datetime or string to ISO 8601 format (``YYYY-MM-DDTHH:MM:SS``)."""
    if isinstance(ts, datetime):
        return ts.isoformat(timespec="seconds")
    s = str(ts)
    # Frappe DB returns "YYYY-MM-DD HH:MM:SS" — normalise to ISO
    return s.replace(" ", "T", 1)[:19] if " " in s else s[:19]


def _dt_sort_key(iso_str: str) -> str:
    """Return a sortable key from an ISO timestamp (lexicographic sort works for ISO)."""
    return iso_str or ""


def _derive_event_type(
    handoff_code: str,
    handoff_title: str,
    step_map: dict[str, tuple[int, str]],
) -> tuple[str, int]:
    """Return (event_type_label, sort_order) for a handoff code."""
    if handoff_code in step_map:
        order, label = step_map[handoff_code]
        return label, order
    # Fall back to handoff_title as event type
    return handoff_title, 9998


def _extract_evidence_refs(evidence_links_json: str | None) -> list[str]:
    """Extract a flat list of ``object_code`` values from the evidence_links_json field."""
    if not evidence_links_json:
        return []
    try:
        data = json.loads(evidence_links_json)
    except (json.JSONDecodeError, TypeError):
        return []
    links = data.get("links", []) if isinstance(data, dict) else []
    return [
        str(link.get("object_code", ""))
        for link in links
        if isinstance(link, dict) and link.get("object_code")
    ]
