# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R5-011 / LV-R5-011-01 — **TM2 Tender desk handoff panel** read-model.

Narrows Procurement Journey aggregate handoffs to business rows shown on TM2 Tender
Forms: Planning Release Package, STD readiness, Publication, and (when requested)
optional closing/opening checkpoint cards wired in WORKS master seed §16.

Navigation aggregate only — ADR-PLC-002; does not mutate source-module records.
"""

from __future__ import annotations

from typing import Any, Final
from urllib.parse import quote

import frappe

from kentender_procurement.procurement_lifecycle.journey_by_object import (
    get_procurement_journey_by_object,
)

_BASE_PANEL_TITLES: Final[frozenset[str]] = frozenset(
    {
        "Planning Release Package",
        "Tender Document Readiness Certificate",
        "Tender Publication Certificate",
    }
)

_OPTIONAL_OPENING_TITLES: Final[frozenset[str]] = frozenset(
    {
        "Tender Closing Certificate",
        "Opening Readiness Record",
    }
)

_PANEL_ORDER: Final[tuple[tuple[int, str], ...]] = (
    (0, "Planning Release Package"),
    (1, "Tender Document Readiness Certificate"),
    (2, "Tender Publication Certificate"),
    (3, "Tender Closing Certificate"),
    (4, "Opening Readiness Record"),
)

_TITLE_RANK: Final[dict[str, int]] = {label: tier for tier, label in _PANEL_ORDER}


def _sort_key(card: dict[str, Any]) -> tuple[int, str]:
    title = str(card.get("handoff_title") or "").strip()
    return (_TITLE_RANK.get(title, 99), str(card.get("handoff_code") or ""))


def _technical_refs_tender_refs(refs: Any) -> set[str]:
    out: set[str] = set()
    if not isinstance(refs, dict):
        return out
    for k in ("tender_code", "tm2_tender_code"):
        raw = refs.get(k)
        if isinstance(raw, str):
            tc = raw.strip()
            if tc:
                out.add(tc)
        elif isinstance(raw, (list, tuple)):
            for item in raw:
                if isinstance(item, str):
                    iv = item.strip()
                    if iv:
                        out.add(iv)
    return out


def _card_links_tender(tc: str, card: dict[str, Any]) -> bool:
    if not tc:
        return False
    sot = str(card.get("source_object_type") or "").strip()
    sor = str(card.get("source_object_code") or "").strip()
    tot = str(card.get("target_object_type") or "").strip()
    tor = str(card.get("target_object_code") or "").strip()
    if sot == "TM2 Tender" and sor == tc:
        return True
    if tot == "TM2 Tender" and tor == tc:
        return True

    refs_tenders = _technical_refs_tender_refs(card.get("technical_refs"))
    if tc in refs_tenders:
        return True
    links = card.get("evidence_links") or []
    if isinstance(links, list):
        for ln in links:
            if isinstance(ln, dict):
                ot = str(ln.get("object_type") or "").strip()
                oc = str(ln.get("object_code") or "").strip()
                if ot == "TM2 Tender" and oc == tc:
                    return True
    hc = str(card.get("handoff_code") or "")
    if tc and hc and tc.upper() in hc.upper():
        return True
    return False


def _eligible_titles(include_optional_opening: bool) -> frozenset[str]:
    base: frozenset[str] = _BASE_PANEL_TITLES
    if include_optional_opening:
        return base | _OPTIONAL_OPENING_TITLES
    return base


def _handoff_route(handoff_code: str) -> str:
    """SPA path to Procurement Handoff Card (autoname = handoff_code)."""
    slug = quote(handoff_code, safe="-_.!")
    return f"/app/procurement-handoff-card/{slug}"


def _summary_lines(card: dict[str, Any]) -> list[str]:
    """Short business-facing snippets (business codes / labels only — no opaque UUIDs)."""
    lines: list[str] = []

    lk = card.get("locked_summary")
    if isinstance(lk, dict):
        pkg = lk.get("package_title")
        if isinstance(pkg, str) and pkg.strip():
            lines.append(pkg.strip())
        tmpl = lk.get("std_template_version")
        if isinstance(tmpl, str) and tmpl.strip():
            lines.append(tmpl.strip())
        deadline = lk.get("submission_deadline")
        if isinstance(deadline, str) and deadline.strip():
            lines.append(frappe._("Submission: {0}").format(deadline.strip()))
        pub = lk.get("publication_snapshot")
        if isinstance(pub, str) and pub.strip():
            lines.append(frappe._("Publication snapshot {0}").format(pub.strip()))
        inst = lk.get("tender_std_instance") or lk.get("published_tender")
        if isinstance(inst, str) and inst.strip():
            lines.append(inst.strip())

    pf = card.get("passed_forward_summary")
    if isinstance(pf, dict):
        ttl = pf.get("tender_title")
        if isinstance(ttl, str) and ttl.strip() and ttl not in lines:
            lines.append(ttl.strip())

    seen: list[str] = []
    for ln in lines:
        if ln and ln not in seen:
            seen.append(ln)
    return seen[:6]


def _slim_panel_row(card: dict[str, Any], *, tender_code: str) -> dict[str, Any]:
    hc = str(card.get("handoff_code") or "").strip()
    return {
        "handoff_code": hc,
        "handoff_title": str(card.get("handoff_title") or "").strip(),
        "status": str(card.get("status") or "").strip(),
        "source_module": str(card.get("source_module") or "").strip(),
        "target_module": str(card.get("target_module") or "").strip(),
        "next_action": card.get("next_action") or "",
        "summary_lines": _summary_lines(card),
        "open_handoff_route": _handoff_route(hc) if hc else "",
        "tender_code": tender_code,
    }


def build_tm2_handoff_panel_payload(
    tender_code: str,
    *,
    include_optional_opening: bool = False,
) -> dict[str, Any] | None:
    """Return trimmed handoffs for TM2 Tender Form panel, or ``None`` when no linked journey."""

    tc = (tender_code or "").strip()
    if not tc:
        raise ValueError(
            "INVALID_TENDER_CODE: tender_code must be a non-empty string",
        )

    agg = get_procurement_journey_by_object("TM2 Tender", tc)
    if not agg:
        return None

    titles = _eligible_titles(include_optional_opening)
    slim: list[dict[str, Any]] = []
    for c in agg.get("handoff_cards") or []:
        if not isinstance(c, dict):
            continue
        ht = str(c.get("handoff_title") or "").strip()
        if ht not in titles:
            continue
        if not _card_links_tender(tc, c):
            continue
        slim.append(_slim_panel_row(c, tender_code=tc))

    slim.sort(key=_sort_key)

    return {
        "tender_code": tc,
        "journey_code": str(agg.get("journey_code") or "").strip(),
        "include_optional_opening": bool(include_optional_opening),
        "handoffs": slim,
    }
