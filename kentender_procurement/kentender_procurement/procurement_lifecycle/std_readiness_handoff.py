# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-006 / LV-R3-006-01 — **STD readiness handoff service** (cursor pack §8.2).

## Goal

``create_std_readiness_certificate(tender_code, journey_code)`` produces (or updates)
the ``Procurement Handoff Card`` that records the STD Engine / Tender Management →
Tender Publication module boundary event.  It reads live TM2 Tender data and, when
available, the linked ``Tender STD Instance`` (driven from real TM2/STD outputs per
LV-R3-006-01), builds a typed payload, and delegates to the generic
``create_or_update_handoff_card`` (R3-001).

## Handoff card produced

| Field | Value |
|---|---|
| handoff_code | ``STDREADY-{tender_code}`` (e.g. ``STDREADY-TND-MOH-2026-001``) |
| source_module | ``STD Engine / Tender Management`` |
| target_module | ``Tender Publication`` |
| source_object_type | ``Tender STD Instance`` |
| source_object_code | ``STDINST-{tender_code}`` (canonical) or real name when available |
| target_object_type | ``TM2 Tender`` |
| target_object_code | ``tender_code`` |

## Handoff code derivation

``STDREADY-`` is prepended directly to ``tender_code`` (e.g. ``TND-MOH-2026-001``
→ ``STDREADY-TND-MOH-2026-001``).  This differs from earlier handoffs which strip the
``JRN-`` prefix from the journey code — at this stage the handoff identity is anchored
to the tender, not the journey.

## STD Instance resolution (LV-R3-006-01: driven from real TM2/STD outputs)

The service resolves the ``Tender STD Instance`` via a two-step lookup:

1. **Journey ref** — reads ``Procurement Journey.tender_std_instance_ref`` to get the
   canonical instance code for this journey.  If that code exists as a real
   ``Tender STD Instance`` DocType record, its live fields are used.
2. **Direct FK fallback** — queries ``Tender STD Instance`` by ``tm2_tender = tender_name``
   (TM2 Tender's Frappe ``name``).  If exactly one non-cancelled instance is found, it is
   used as the authoritative source for ``readiness_status`` and output codes.

If neither lookup finds a real record the service falls back to the conceptual
reference code (``STDINST-{tender_code}``) and derives ``readiness_status`` from
``TM2 Tender.std_readiness_status`` with a default of ``"Not Assessed"``.

## passed_forward_summary readiness flags

When ``readiness_status == "Ready"`` all five readiness flags are ``True``.  For any
other value all flags are ``False``.  These flags are derived — not stored on individual
sub-fields in the current schema — so the service computes them from the overall status.

## STD template version

Resolution order:
1. Real ``Tender STD Instance.template_version_code``
2. ``TM2 Tender.template_version``
3. ``Procurement Journey.std_template_version_ref``
4. Empty string (non-fatal)

## Error codes

| Code | Condition |
|---|---|
| ``INVALID_TENDER_CODE`` | ``tender_code`` is blank or not a string. |
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

_STD_INSTANCE_DESK_ROUTE_PREFIX = "/app/tender-std-instance"

# Sentinel for a "Ready" STD instance.
_READY_STATUS = "Ready"

# Cancelled-equivalent instance statuses to skip during direct FK lookup.
_TERMINAL_INSTANCE_STATUSES = frozenset({"Cancelled", "Superseded"})


def _handoff_code(tender_code: str) -> str:
    """Derive STDREADY handoff code from a tender code.

    ``TND-MOH-2026-001`` → ``STDREADY-TND-MOH-2026-001``.
    """
    return f"STDREADY-{tender_code}"


def _stdinst_canonical_code(tender_code: str) -> str:
    """Return the canonical STD Instance business code for a tender.

    ``TND-MOH-2026-001`` → ``STDINST-TND-MOH-2026-001``.
    """
    return f"STDINST-{tender_code}"


def _find_tm2_tender(tender_code: str) -> dict[str, Any] | None:
    """Return TM2 Tender row dict or None.

    ``TM2 Tender.name == tender_code`` in the canonical naming series; also
    tries a field-based fallback for edge cases.
    """
    fields = [
        "name",
        "tender_code",
        "tender_title",
        "std_readiness_status",
        "template_version",
        "procurement_method",
        "procurement_category",
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


def _find_std_instance_by_name(candidate_code: str) -> dict[str, Any] | None:
    """Return Tender STD Instance row dict if ``candidate_code`` is a real DB record."""
    if not candidate_code or not frappe.db.exists("Tender STD Instance", candidate_code):
        return None
    return frappe.db.get_value(
        "Tender STD Instance",
        candidate_code,
        [
            "name",
            "readiness_status",
            "instance_status",
            "template_version_code",
            "current_bundle_output_code",
            "current_dsm_output_code",
            "current_dom_output_code",
            "current_dem_output_code",
            "current_dcm_output_code",
        ],
        as_dict=True,
    )


def _find_std_instance_by_tm2_tender(tm2_tender_name: str) -> dict[str, Any] | None:
    """Return the active Tender STD Instance linked via ``tm2_tender`` FK."""
    if not tm2_tender_name:
        return None
    rows = frappe.db.get_all(
        "Tender STD Instance",
        filters={
            "tm2_tender": tm2_tender_name,
            "instance_status": ["not in", list(_TERMINAL_INSTANCE_STATUSES)],
        },
        fields=[
            "name",
            "readiness_status",
            "instance_status",
            "template_version_code",
            "current_bundle_output_code",
            "current_dsm_output_code",
            "current_dom_output_code",
            "current_dem_output_code",
            "current_dcm_output_code",
        ],
        limit=2,
        order_by="creation asc",
    )
    if not rows:
        return None
    # Return first active instance (multi-instance edge case: use earliest)
    return rows[0]


def _get_journey_std_refs(journey_code: str) -> tuple[str, str]:
    """Return (std_template_version_ref, tender_std_instance_ref) from the Journey."""
    result = frappe.db.get_value(
        "Procurement Journey",
        journey_code,
        ["std_template_version_ref", "tender_std_instance_ref"],
        as_dict=True,
    )
    if not result:
        return "", ""
    return (
        str(result.get("std_template_version_ref") or ""),
        str(result.get("tender_std_instance_ref") or ""),
    )


def _readiness_flags(is_ready: bool) -> dict[str, bool]:
    """Return the five readiness flag fields for passed_forward_summary."""
    return {
        "tender_document_package_ready": is_ready,
        "supplier_submission_checklist_ready": is_ready,
        "opening_register_rules_ready": is_ready,
        "evaluation_rules_ready": is_ready,
        "contract_carry_forward_terms_ready": is_ready,
    }


def create_std_readiness_certificate(
    tender_code: str, journey_code: str
) -> dict[str, Any]:
    """Upsert the Tender Document Readiness Certificate handoff card for a journey.

    :param tender_code: ``TM2 Tender`` code (``tender_code`` field / Frappe ``name``,
        e.g. ``TND-MOH-2026-001``).
    :param journey_code: Procurement Journey code (e.g. ``JRN-MOH-2026-001``).
    :returns: Result dict from ``create_or_update_handoff_card``.
    :raises ValueError: If inputs are blank or the TM2 Tender is not found.
    """
    if not tender_code or not isinstance(tender_code, str) or not tender_code.strip():
        raise ValueError(
            "INVALID_TENDER_CODE: tender_code must be a non-empty string"
        )
    if not journey_code or not isinstance(journey_code, str) or not journey_code.strip():
        raise ValueError(
            "INVALID_JOURNEY_CODE: journey_code must be a non-empty string"
        )

    tnd_code = tender_code.strip()
    jrn_code = journey_code.strip()

    # 1. Locate the TM2 Tender
    tm2 = _find_tm2_tender(tnd_code)
    if tm2 is None:
        raise ValueError(
            f"TENDER_NOT_FOUND: no TM2 Tender with tender_code or name = {tnd_code!r}"
        )

    tm2_frappe_name: str = str(tm2["name"])
    tm2_template_version: str = str(tm2.get("template_version") or "")
    tm2_std_readiness: str = str(tm2.get("std_readiness_status") or "Not Assessed")

    # 2. Get Journey STD refs
    journey_template_version_ref, journey_stdinst_ref = _get_journey_std_refs(jrn_code)

    # 3. Resolve the Tender STD Instance — priority: journey ref → direct FK
    real_instance: dict[str, Any] | None = None
    if journey_stdinst_ref:
        real_instance = _find_std_instance_by_name(journey_stdinst_ref)
    if real_instance is None:
        real_instance = _find_std_instance_by_tm2_tender(tm2_frappe_name)

    # 4. Determine canonical STD instance code for the handoff
    if real_instance:
        stdinst_code = str(real_instance["name"])
    elif journey_stdinst_ref:
        stdinst_code = journey_stdinst_ref
    else:
        stdinst_code = _stdinst_canonical_code(tnd_code)

    # 5. Resolve readiness_status
    if real_instance:
        readiness_status: str = str(real_instance.get("readiness_status") or "Not Ready")
    else:
        readiness_status = tm2_std_readiness

    # 6. Resolve STD template version code (resolution order per docstring)
    std_template_version: str = ""
    if real_instance:
        std_template_version = str(real_instance.get("template_version_code") or "")
    if not std_template_version:
        std_template_version = tm2_template_version
    if not std_template_version:
        std_template_version = journey_template_version_ref

    # 7. Collect output codes from real instance (if available)
    bundle_code: str = ""
    dsm_code: str = ""
    dom_code: str = ""
    dem_code: str = ""
    dcm_code: str = ""
    if real_instance:
        bundle_code = str(real_instance.get("current_bundle_output_code") or "")
        dsm_code = str(real_instance.get("current_dsm_output_code") or "")
        dom_code = str(real_instance.get("current_dom_output_code") or "")
        dem_code = str(real_instance.get("current_dem_output_code") or "")
        dcm_code = str(real_instance.get("current_dcm_output_code") or "")

    is_ready = (readiness_status == _READY_STATUS)

    # 8. Build locked_summary (spec §16.7)
    locked_summary: dict[str, Any] = {
        "tender_std_instance": stdinst_code,
        "readiness_status": readiness_status,
    }
    if std_template_version:
        locked_summary["std_template_version"] = std_template_version

    # 9. Build passed_forward_summary — boolean readiness flags (spec §16.7)
    passed_forward: dict[str, Any] = _readiness_flags(is_ready)

    # 10. Evidence link — Tender STD Instance desk page
    stdinst_route = f"{_STD_INSTANCE_DESK_ROUTE_PREFIX}/{stdinst_code}"
    evidence_links = [
        {
            "label": "Tender STD Instance",
            "object_type": "Tender STD Instance",
            "object_code": stdinst_code,
            "module": "STD Engine",
            "route": stdinst_route,
            "visibility": "Internal",
        }
    ]

    # 11. technical_refs — document output codes (spec §16.7)
    technical_refs: dict[str, str] = {}
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
        "handoff_title": "Tender Document Readiness Certificate",
        "journey_code": jrn_code,
        "source_module": "STD Engine / Tender Management",
        "target_module": "Tender Publication",
        "source_object_type": "Tender STD Instance",
        "source_object_code": stdinst_code,
        "target_object_type": "TM2 Tender",
        "target_object_code": tnd_code,
        "status": "Consumed",
        "generated_by": frappe.session.user or "system",
        "next_action": "Submit tender for publication review.",
        "locked_summary": locked_summary,
        "passed_forward_summary": passed_forward,
        "evidence_links": evidence_links,
        "technical_refs": technical_refs,
    }

    return create_or_update_handoff_card(payload)
