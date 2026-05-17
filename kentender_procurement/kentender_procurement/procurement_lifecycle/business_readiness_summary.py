# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-016 / LV-R3-016-01 — **Business readiness summary service** (cursor pack §13).

## Goal

``get_business_readiness_summary(object_type, object_code)`` returns a structured,
**business-readable** readiness summary for a procurement object — mapping the STD
Engine's technical output codes (Bundle, DSM, DOM, DEM, DCM) to plain-English labels
that non-technical procurement officers can understand.

For ``TM2 Tender``, the service returns 5 readiness checks plus a publication snapshot
reference line (6 items total — "6 lines incl. snapshot" per LV-R3-016-01), which
corresponds to the PLC-SMOKE-BE-004 acceptance criterion.

R6-004 / NEG-TND-MISSING-DEM-001: DEM **FAIL** rows may include ``user_blocker_message`` —
a business-readable sentence that does not use machine blocker codes as primary copy.

## Data sources (in priority order)

1. ``PUBCERT-{tender_code}`` handoff card → ``technical_refs_json`` (has all 5 codes
   + ``publication_code``).  ``locked_summary`` has ``publication_snapshot``.
2. ``STDREADY-{tender_code}`` handoff card → ``technical_refs_json`` (has all 5 codes;
   no snapshot).
3. Procurement Journey linked via ``tm2_tender_ref = tender_code`` →
   ``publication_snapshot_ref``.

If no handoff card exists for the tender, all checks return ``result="FAIL"`` with
``blocker_code="PENDING"`` and the overall status is ``"Not Assessed"``.

## Return shape (pack §13)

```python
{
  "object_type": str,              # "TM2 Tender"
  "object_code": str,              # e.g. "TND-MOH-2026-001"
  "summary_label": str,            # "Tender document readiness"
  "status": str,                   # "Ready" | "Blocked" | "Not Assessed"
  "checks": [                      # 5 readiness checks
    {
      "business_label": str,       # Human label shown to procurement officer
      "technical_label": str,      # Bundle | DSM | DOM | DEM | DCM
      "technical_ref": str | None, # Output code (None when FAIL)
      "result": str,               # "PASS" | "FAIL"
      # Only present when result == "FAIL":
      # "blocker_code": str,
      # "owner_module": str,
      # "required_action": str,
      # "user_blocker_message": str,   # optional; DEM R6-004 curated copy for Desk
    },
    ...
  ],
  "snapshot_ref": str | None,      # Publication snapshot code (6th line)
  "technical_details_available": bool,
}
```

## WORKS golden scenario

For ``TND-MOH-2026-001`` (Published, base checkpoint):

- All 5 checks PASS (codes present in PUBCERT ``technical_refs_json``).
- ``snapshot_ref = "PUBSNAP-TND-MOH-2026-001-V2"``.
- ``status = "Ready"``.
- ``technical_details_available = True``.

## Supported object types

| ``object_type`` | Supported |
|---|---|
| ``TM2 Tender`` | Yes |
| Any other | No — raises ``ValueError(UNSUPPORTED_OBJECT_TYPE)`` |

## Error codes

| Code | Condition |
|---|---|
| ``INVALID_OBJECT_TYPE`` | ``object_type`` is blank or not a string. |
| ``INVALID_OBJECT_CODE`` | ``object_code`` is blank or not a string. |
| ``UNSUPPORTED_OBJECT_TYPE`` | ``object_type`` not in supported set. |
| ``OBJECT_NOT_FOUND`` | No ``TM2 Tender`` with the given code exists. |
"""

from __future__ import annotations

import json
from typing import Any

import frappe

# Supported object types
_SUPPORTED_TYPES = frozenset({"TM2 Tender"})

# ------------------------------------------------------------------
# Check definitions: (technical_label, business_label, tech_ref_key,
#                     blocker_code, owner_module, required_action)
# ------------------------------------------------------------------
_TM2_CHECKS: tuple[tuple[str, str, str, str, str, str], ...] = (
    (
        "Bundle",
        "Tender document package ready",
        "bundle_output_code",
        "BUNDLE_MISSING_OR_STALE",
        "STD Engine",
        "Regenerate tender document bundle after updating STD parameters.",
    ),
    (
        "DSM",
        "Supplier submission checklist ready",
        "dsm_output_code",
        "DSM_MISSING_OR_STALE",
        "STD Engine",
        "Generate supplier submission model after completing tender parameters.",
    ),
    (
        "DOM",
        "Opening register rules ready",
        "dom_output_code",
        "DOM_MISSING_OR_STALE",
        "STD Engine",
        "Generate opening management model after completing tender timeline.",
    ),
    (
        "DEM",
        "Evaluation rules ready",
        "dem_output_code",
        "DEM_MISSING_OR_STALE",
        "STD Engine",
        "Generate evaluation rules after completing Evaluation and Qualification Criteria.",
    ),
    (
        "DCM",
        "Contract carry-forward terms ready",
        "dcm_output_code",
        "DCM_MISSING_OR_STALE",
        "STD Engine",
        "Generate contract carry-forward terms after evaluation parameters are set.",
    ),
)


def get_business_readiness_summary(object_type: str, object_code: str) -> dict[str, Any]:
    """Return a business-readable readiness summary for a procurement object.

    :param object_type: Must be ``"TM2 Tender"`` (the only supported type at this stage).
    :param object_code: The tender code (e.g. ``"TND-MOH-2026-001"``).
    :returns: Readiness summary dict (see module docstring for shape).
    :raises ValueError: For invalid/blank inputs or unsupported object types.
    :raises frappe.DoesNotExistError: If the TM2 Tender does not exist.
    """
    # --- Input validation --------------------------------------------------
    if not object_type or not isinstance(object_type, str) or not object_type.strip():
        raise ValueError("INVALID_OBJECT_TYPE: object_type must be a non-empty string")
    if not object_code or not isinstance(object_code, str) or not object_code.strip():
        raise ValueError("INVALID_OBJECT_CODE: object_code must be a non-empty string")

    otype = object_type.strip()
    ocode = object_code.strip()

    if otype not in _SUPPORTED_TYPES:
        raise ValueError(
            f"UNSUPPORTED_OBJECT_TYPE: '{otype}' is not supported. "
            f"Supported types: {sorted(_SUPPORTED_TYPES)}"
        )

    # --- TM2 Tender readiness -----------------------------------------------
    return _tm2_tender_readiness(ocode)


def is_object_type_supported(object_type: str) -> bool:
    """Return True if the given object_type has a readiness summary implementation."""
    return str(object_type or "").strip() in _SUPPORTED_TYPES


# ---------------------------------------------------------------------------
# TM2 Tender implementation
# ---------------------------------------------------------------------------

def _tm2_tender_readiness(tender_code: str) -> dict[str, Any]:
    """Build readiness summary for a TM2 Tender."""
    # Check TM2 Tender exists
    if not frappe.db.exists("TM2 Tender", {"tender_code": tender_code}):
        raise frappe.DoesNotExistError(
            f"OBJECT_NOT_FOUND: TM2 Tender with code '{tender_code}' does not exist"
        )

    # --- 1. Load technical refs from PUBCERT (primary) or STDREADY (fallback) ---
    pubcert_code = f"PUBCERT-{tender_code}"
    stdready_code = f"STDREADY-{tender_code}"

    tech_refs: dict[str, str | None] = {}
    snapshot_ref: str | None = None
    handoff_source: str | None = None

    # Try PUBCERT first
    card = frappe.db.get_value(
        "Procurement Handoff Card",
        pubcert_code,
        ["technical_refs_json", "locked_summary"],
        as_dict=True,
    )
    if card:
        tech_refs = _parse_tech_refs(card.get("technical_refs_json"))
        snapshot_ref = _extract_snapshot_from_locked_summary(card.get("locked_summary"))
        handoff_source = pubcert_code

    # Fallback: STDREADY
    if not tech_refs:
        std_card = frappe.db.get_value(
            "Procurement Handoff Card",
            stdready_code,
            ["technical_refs_json"],
            as_dict=True,
        )
        if std_card:
            tech_refs = _parse_tech_refs(std_card.get("technical_refs_json"))
            handoff_source = stdready_code

    # --- 2. Publication snapshot: from Journey if not already found ----------
    if not snapshot_ref:
        snapshot_ref = (
            frappe.db.get_value(
                "Procurement Journey",
                {"tm2_tender_ref": tender_code},
                "publication_snapshot_ref",
            )
            or None
        )

    # --- 3. Build checks ----------------------------------------------------
    checks: list[dict[str, Any]] = []
    any_pass = False
    any_fail = False

    for tech_label, biz_label, ref_key, blocker_code, owner_module, required_action in _TM2_CHECKS:
        ref_val = tech_refs.get(ref_key) if tech_refs else None
        ref_str = str(ref_val).strip() if ref_val else None

        if ref_str:
            checks.append(
                {
                    "business_label": biz_label,
                    "technical_label": tech_label,
                    "technical_ref": ref_str,
                    "result": "PASS",
                }
            )
            any_pass = True
        else:
            eff_blocker = blocker_code if handoff_source else "PENDING"
            row: dict[str, Any] = {
                "business_label": biz_label,
                "technical_label": tech_label,
                "technical_ref": None,
                "result": "FAIL",
                "blocker_code": eff_blocker,
                "owner_module": owner_module,
                "required_action": required_action,
            }
            if tech_label == "DEM":
                umsg = _user_facing_dem_blocker(eff_blocker)
                if umsg:
                    row["user_blocker_message"] = umsg
            checks.append(row)
            any_fail = True

    # --- 4. Determine overall status ----------------------------------------
    if not handoff_source:
        status = "Not Assessed"
    elif any_fail:
        status = "Blocked"
    else:
        status = "Ready"

    return {
        "object_type": "TM2 Tender",
        "object_code": tender_code,
        "summary_label": "Tender document readiness",
        "status": status,
        "checks": checks,
        "snapshot_ref": snapshot_ref,
        "technical_details_available": any_pass,
    }


# ---------------------------------------------------------------------------
# R6-004 — DEM missing / stale: business-readable blocker (never raw code as UX)
# ---------------------------------------------------------------------------

def _user_facing_dem_blocker(blocker_code: str | None) -> str | None:
    """Return procurement-facing copy for DEM failures (NEG-TND-MISSING-DEM-001).

    Machine codes (``DEM_MISSING_OR_STALE``) stay on ``blocker_code`` for integration;
    the Desk shows ``user_blocker_message`` instead of foregrounding the token.
    """
    bc = str(blocker_code or "").strip()
    if bc == "DEM_MISSING_OR_STALE":
        return frappe._(
            "Evaluation rules are not ready: the evaluation model is missing or out of date. "
            "Complete Evaluation and Qualification Criteria, then generate or refresh the "
            "evaluation rules in the STD Engine."
        )
    if bc == "PENDING":
        return frappe._(
            "Evaluation rules are not assessed yet. Complete tender document readiness so "
            "the evaluation model can be produced."
        )
    return None


def _parse_tech_refs(technical_refs_json: str | None) -> dict[str, str | None]:
    """Parse the ``technical_refs_json`` field into a flat key→value dict."""
    if not technical_refs_json:
        return {}
    try:
        data = json.loads(technical_refs_json)
    except (json.JSONDecodeError, TypeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if isinstance(v, str) and v.strip()}


def _extract_snapshot_from_locked_summary(locked_summary: str | None) -> str | None:
    """Extract ``publication_snapshot`` from the locked_summary JSON field."""
    if not locked_summary:
        return None
    try:
        data = json.loads(locked_summary)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    val = data.get("publication_snapshot") or data.get("publication_snapshot_code")
    return str(val).strip() if val else None
