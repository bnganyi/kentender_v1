# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-012 / LV-R3-012-01 — **Journey by object lookup — full aggregate** (cursor pack §9.2).

## Goal

``get_procurement_journey_by_object(object_type, object_code)`` resolves a source
module object (Demand, Procurement Package, TM2 Tender, etc.) to its parent
``Procurement Journey`` and returns the **full aggregated journey view** (same shape as
``get_procurement_journey`` from R3-011).

This is the primary entry point for module-context headers (R5-001) and any API call
that needs the complete journey state from a source object reference (e.g. the TM2
Tender detail page showing which journey it belongs to).

## Relation to R1-009 ``get_procurement_journey_by_object``

The R1-009 version in ``journey_object_lookup.py`` was explicitly marked as returning
a **minimal** dict "until R3 wires full aggregation". R3-012 is that wiring.

R1-009 functions (``resolve_journey_code_for_object``, ``ref_field_for_object_type``,
``JOURNEY_OBJECT_LOOKUP_REF_FIELDS``) remain unchanged — they handle the index/lookup
layer. This module adds the aggregate layer on top.

## Supported object types

All types registered in ``_OBJECT_TYPE_TO_REF_FIELD`` in ``journey_object_lookup.py``:

| object_type (case-insensitive) | Examples |
|---|---|
| ``Demand`` | ``DEM-MOH-2026-001`` |
| ``Procurement Package`` | ``PKG-MOH-2026-001`` |
| ``TM2 Tender`` | ``TND-MOH-2026-001`` |
| ``Budget Line`` | ``BUD-MOH-INFRA-2026-001`` |
| ``Strategic Plan / Programme / Objective`` | ``OBJ-MOH-HOSP-RENOV`` |
| ``Procurement Plan`` | ``PLAN-MOH-2026`` |
| ``STD Template Version`` | ``STDTV-WORKS-BUILDING-CIVIL-APR2022`` |
| ``Tender STD Instance`` | ``STDINST-TND-MOH-2026-001`` |
| ``Publication Snapshot`` | ``PUBSNAP-TND-MOH-2026-001-V2`` |
| ``TM2 Opening Readiness Record`` / ``Opening Readiness`` | ``ORR-TND-MOH-2026-001`` |

## Response

Returns the same dict as ``get_procurement_journey`` on success — the full journey
aggregate per pack §9.1.

Returns ``None`` when:
- ``object_type`` is not mapped (unknown type)
- ``object_code`` is blank
- No ``Procurement Journey`` references the given object

## Error codes

| Code | Condition |
|---|---|
| ``INVALID_OBJECT_TYPE`` | ``object_type`` is blank or not a string. |
| ``INVALID_OBJECT_CODE`` | ``object_code`` is blank or not a string. |
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_lifecycle.journey_object_lookup import (
    resolve_journey_code_for_object,
    ref_field_for_object_type,
)
from kentender_procurement.procurement_lifecycle.journey_aggregate import (
    get_procurement_journey,
)


def get_procurement_journey_by_object(
    object_type: str, object_code: str
) -> dict[str, Any] | None:
    """Return the full journey aggregate for a given source object, or ``None``.

    :param object_type: One of the supported source object type labels (case-insensitive).
        See module docstring for the full list.
    :param object_code: The business code / Frappe ``name`` of the source object.
    :returns: Full journey aggregate dict (same as ``get_procurement_journey``) or
        ``None`` if no journey is linked to this object.
    :raises ValueError: If ``object_type`` or ``object_code`` is blank.
    """
    if not object_type or not isinstance(object_type, str) or not object_type.strip():
        raise ValueError(
            "INVALID_OBJECT_TYPE: object_type must be a non-empty string"
        )
    if not object_code or not isinstance(object_code, str) or not object_code.strip():
        raise ValueError(
            "INVALID_OBJECT_CODE: object_code must be a non-empty string"
        )

    obj_type = object_type.strip()
    obj_code = object_code.strip()

    # 1. Resolve journey code using indexed ref field lookup (R1-009 layer)
    journey_code = resolve_journey_code_for_object(obj_type, obj_code)
    if not journey_code:
        return None

    # 2. Return full aggregate (R3-011 layer)
    try:
        return get_procurement_journey(journey_code)
    except frappe.DoesNotExistError:
        # Edge case: ref field pointed to a journey that was since deleted
        return None


def is_object_type_supported(object_type: str) -> bool:
    """Return whether ``object_type`` is mapped to a ``Procurement Journey`` ref field."""
    return ref_field_for_object_type(object_type) is not None
