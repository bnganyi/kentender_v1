# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-017 / LV-R3-017-01, LV-R3-017-02 — **Procurement Lifecycle Journey APIs** (pack §10).

## Goal

Frappe-whitelisted methods exposing the five required Journey endpoints from pack §10.1.
All endpoints require an authenticated non-Guest session and ``read`` permission on
``Procurement Journey``.  They delegate to the existing R3 service layer and add no new
business logic.

## Endpoint equivalents (pack §10.1)

| HTTP path | Whitelisted function |
|---|---|
| ``GET /api/procurement-lifecycle/journeys`` | ``list_journeys`` |
| ``GET /api/procurement-lifecycle/journeys/<code>`` | ``get_journey`` |
| ``GET /api/procurement-lifecycle/journeys/by-object`` | ``get_journey_by_object`` |
| ``GET /api/procurement-lifecycle/journeys/<code>/steps`` | ``get_journey_steps`` |
| ``GET /api/procurement-lifecycle/journeys/<code>/evidence`` | ``get_journey_evidence`` |

## Permissions (pack §10.4)

All journey read APIs require the calling user to have ``read`` permission on
``Procurement Journey``.  A ``frappe.PermissionError`` is raised if the check fails.
Guest users are always denied.

## Transport

In Frappe these are invoked via ``frappe.call`` (JS) or
``/api/method/kentender_procurement.procurement_lifecycle.api.journey_api.<function_name>``
(REST).  Parameters are passed as query string / POST body and automatically cast from
JSON / form-data by Frappe before reaching the handler.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.procurement_lifecycle.journey_aggregate import (
    get_procurement_journey,
    sanitize_journey_steps_open_module_routes,
)
from kentender_procurement.procurement_lifecycle.journey_by_object import (
    get_procurement_journey_by_object,
)
from kentender_procurement.procurement_lifecycle.journey_step_aggregator import (
    aggregate_procurement_journey_steps,
)
from kentender_procurement.procurement_lifecycle.evidence_timeline import (
    get_journey_evidence_timeline,
)
from kentender_procurement.procurement_lifecycle.strategy_node_journeys import (
    build_procurement_links_payload,
)
from kentender_procurement.procurement_lifecycle.budget_line_procurement_use import (
    build_procurement_use_payload,
)
from kentender_procurement.procurement_lifecycle.api.permission_guard import (
    require_journey_read,
)
from kentender_procurement.tender_management.services.tm2_handoff_panel import (
    build_tm2_handoff_panel_payload,
)

# Status categories considered "terminal / not active"
_INACTIVE_STATUSES: frozenset[str] = frozenset(
    {"Cancelled", "Superseded", "Audit Only"}
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_journey_read_permission() -> None:
    """Raise PermissionError if the session user cannot read Procurement Journey.

    Delegates to the centralised ``permission_guard`` module (R3-019).
    """
    require_journey_read()


def _primary_object_code(row: dict) -> str:
    """Derive the primary object code for a journey list item."""
    return (
        row.get("tm2_tender_ref")
        or row.get("procurement_package_ref")
        or row.get("demand_ref")
        or ""
    )


# ---------------------------------------------------------------------------
# 1. list_journeys  (pack §10.2)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def list_journeys(
    scope: str | None = None,
    status: str | None = None,
    search: str | None = None,
    limit: int | str | None = None,
) -> dict[str, Any]:
    """Return a filtered list of Procurement Journeys plus aggregate counts.

    :param scope: Optional filter — ``"my-work"`` restricts to journeys for the
        session user's procuring entity (via ``User Permission`` on
        ``Procuring Entity``, if present) or their assigned entity.  Other values
        are ignored (returns all accessible journeys).
    :param status: Optional filter — one of ``"active"``, ``"blocked"``,
        ``"needs_action"``, ``"ready_for_handoff"``, ``"completed"``.
    :param search: Optional free-text search on ``journey_title`` and
        ``journey_code`` (case-insensitive contains).
    :param limit: Maximum items to return (default 100, max 500).
    :returns: ``{items: [...], counts: {...}}`` matching pack §10.2.
    :raises frappe.PermissionError: If the user lacks read access.
    """
    _require_journey_read_permission()

    limit_val = min(int(limit or 100), 500)
    status_arg = cstr(status or "").strip().lower()
    search_arg = cstr(search or "").strip()
    scope_arg = cstr(scope or "").strip().lower()

    # --- Build base filters ---------------------------------------------------
    conditions: list[str] = ["docstatus != 2"]  # not deleted
    values: list[Any] = []

    # status filter → map to status_category
    if status_arg == "active":
        conditions.append(
            "current_status_category NOT IN ('Cancelled','Superseded','Audit Only')"
        )
    elif status_arg == "blocked":
        conditions.append("(blocker_count > 0 OR critical_blocker_count > 0)")
    elif status_arg == "needs_action":
        conditions.append("current_status_category = 'Needs Action'")
    elif status_arg == "ready_for_handoff":
        conditions.append("current_status_category = 'Ready for Handoff'")
    elif status_arg == "completed":
        conditions.append(
            "(current_stage_key = 'contract' AND current_status_category = 'Completed')"
        )

    # search filter
    if search_arg:
        conditions.append(
            "(journey_title LIKE %s OR journey_code LIKE %s)"
        )
        like = f"%{search_arg}%"
        values.extend([like, like])

    # scope = my-work: restrict by user permissions (User Permission on entity)
    if scope_arg == "my-work":
        entity_codes = _user_entity_codes(frappe.session.user)
        if entity_codes:
            placeholders = ",".join(["%s"] * len(entity_codes))
            conditions.append(f"procuring_entity_code IN ({placeholders})")
            values.extend(entity_codes)

    where_clause = " AND ".join(conditions)

    # --- Fetch list items -------------------------------------------------------
    rows = frappe.db.sql(
        f"""
        SELECT
            journey_code,
            journey_title,
            procuring_entity_code,
            current_stage_label,
            current_status_category,
            next_action,
            blocker_count,
            critical_blocker_count,
            tm2_tender_ref,
            procurement_package_ref,
            demand_ref
        FROM `tabProcurement Journey`
        {"WHERE " + where_clause if where_clause else ""}
        ORDER BY modified DESC
        LIMIT %s
        """,
        values + [limit_val],
        as_dict=True,
    )

    items = [
        {
            "journey_code": r.journey_code or r.name,
            "journey_title": r.journey_title or "",
            "procuring_entity_code": r.procuring_entity_code or "",
            "current_stage_label": r.current_stage_label or "",
            "current_status_category": r.current_status_category or "Not Started",
            "next_action": r.next_action or "",
            "blocker_count": int(r.blocker_count or 0),
            "critical_blocker_count": int(r.critical_blocker_count or 0),
            "primary_object_code": _primary_object_code(r),
            "open_route": (
                f"/desk/plc-procurement-journey/{cstr(r.journey_code or r.name).strip()}"
                if (r.journey_code or r.name)
                else "/desk/plc-procurement-journey"
            ),
        }
        for r in rows
    ]

    # --- Aggregate counts (always across all accessible journeys) ---------------
    counts = _compute_journey_counts()

    return {"items": items, "counts": counts}


# ---------------------------------------------------------------------------
# 2. get_journey  (pack §9.1)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_journey(journey_code: str | None = None) -> dict[str, Any]:
    """Return the full aggregated Procurement Journey view (pack §9.1).

    :param journey_code: Journey identifier.
    :returns: Full journey aggregate dict.
    :raises frappe.PermissionError: If the user lacks read access.
    :raises ValueError: If ``journey_code`` is blank.
    :raises frappe.DoesNotExistError: If the journey does not exist.
    """
    _require_journey_read_permission()
    code = cstr(journey_code or "").strip()
    if not code:
        frappe.throw("journey_code is required.", frappe.ValidationError)
    return get_procurement_journey(code)


# ---------------------------------------------------------------------------
# 3. get_journey_by_object  (pack §9.2)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_journey_by_object(
    object_type: str | None = None,
    object_code: str | None = None,
) -> dict[str, Any] | None:
    """Return the full journey aggregate for an object's associated journey.

    :param object_type: Source module object type (e.g. ``"TM2 Tender"``).
    :param object_code: Source module object code.
    :returns: Full journey aggregate dict, or ``None`` if no journey is linked.
    :raises frappe.PermissionError: If the user lacks read access.
    """
    _require_journey_read_permission()
    otype = cstr(object_type or "").strip()
    ocode = cstr(object_code or "").strip()
    if not otype:
        frappe.throw("object_type is required.", frappe.ValidationError)
    if not ocode:
        frappe.throw("object_code is required.", frappe.ValidationError)
    return get_procurement_journey_by_object(otype, ocode)


# ---------------------------------------------------------------------------
# 3b. get_tm2_handoff_panel — TM2 Tender Form (R5-011 / LV-R5-011-01)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_tm2_handoff_panel(
    tender_code: str | None = None,
    include_optional_opening: str | int | bool | None = None,
) -> dict[str, Any] | None:
    """Return lifecycle handoffs relevant to ``tender_code`` for TM2 desk panel.

    :param tender_code: Business code / TM2 document name.
    :param include_optional_opening: When truthy (``1``, ``True``),
        include Tender Closing Certificate + Opening Readiness Record summaries
        when present on the linked journey aggregate.
    :returns: Payload with ``handoffs`` list or ``None`` when the tender /
        linkage is missing or inaccessible.
    :raises frappe.PermissionError: If the caller cannot read Procurement
        Journey or the TM2 tender document.
    """
    _require_journey_read_permission()
    tc = cstr(tender_code or "").strip()
    if not tc:
        frappe.throw("tender_code is required.", frappe.ValidationError)
    if not frappe.db.exists("TM2 Tender", tc):
        return None
    if not frappe.has_permission("TM2 Tender", "read", doc=tc):
        frappe.throw(
            frappe._("You are not permitted to read this TM2 Tender."),
            frappe.PermissionError,
        )

    include_open = False
    raw = include_optional_opening
    if isinstance(raw, bool):
        include_open = raw
    elif isinstance(raw, (int, float)) and raw:
        include_open = True
    elif raw not in (None, ""):
        rs = str(raw).strip().lower()
        include_open = (
            rs not in {"", "false", "0", "none", "no"}
            and (rs in {"true", "yes", "1", "on"} or bool(cint(raw)))
        )

    return build_tm2_handoff_panel_payload(
        tc,
        include_optional_opening=include_open,
    )


# ---------------------------------------------------------------------------
# 4. get_journey_steps  (pack §9.3)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_journey_steps(journey_code: str | None = None) -> list[dict[str, Any]]:
    """Return the ordered step list for a Procurement Journey (pack §9.3).

    :param journey_code: Journey identifier.
    :returns: Ordered list of step dicts.
    :raises frappe.PermissionError: If the user lacks read access.
    :raises ValueError: If ``journey_code`` is blank.
    :raises frappe.DoesNotExistError: If the journey does not exist.
    """
    _require_journey_read_permission()
    code = cstr(journey_code or "").strip()
    if not code:
        frappe.throw("journey_code is required.", frappe.ValidationError)
    return sanitize_journey_steps_open_module_routes(
        aggregate_procurement_journey_steps(code),
    )


# ---------------------------------------------------------------------------
# 5. get_journey_evidence  (pack §9.5)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_journey_evidence(journey_code: str | None = None) -> list[dict[str, Any]]:
    """Return the chronological evidence timeline for a Procurement Journey (pack §9.5).

    :param journey_code: Journey identifier.
    :returns: Ordered list of evidence event dicts.
    :raises frappe.PermissionError: If the user lacks read access.
    :raises ValueError: If ``journey_code`` is blank.
    :raises frappe.DoesNotExistError: If the journey does not exist.
    """
    _require_journey_read_permission()
    code = cstr(journey_code or "").strip()
    if not code:
        frappe.throw("journey_code is required.", frappe.ValidationError)
    return get_journey_evidence_timeline(code)


# ---------------------------------------------------------------------------
# 6. get_procurement_journeys_for_strategy_node  (R5-002 / LV-R5-002-02)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_procurement_journeys_for_strategy_node(
    strategy_node_doctype: str | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    """Return linked procurement journeys and budget lines for a strategy node.

    Read-only aggregate for Strategy Objective / Strategy Target desk panels (R5-002).

    :param strategy_node_doctype: ``Strategy Objective`` or ``Strategy Target``.
    :param name: Document name (primary key).
    :raises frappe.PermissionError: If the user cannot read Procurement Journey.
    :raises frappe.ValidationError: If doctype is not supported (after non-empty checks).
    """
    _require_journey_read_permission()
    dt = cstr(strategy_node_doctype or "").strip()
    nm = cstr(name or "").strip()
    if not dt or not nm:
        frappe.throw(
            "strategy_node_doctype and name are required.",
            frappe.ValidationError,
        )
    return build_procurement_links_payload(dt, nm)


@frappe.whitelist()
def get_procurement_use_for_budget_line(
    budget_line_name: str | None = None,
) -> dict[str, Any]:
    """Return funding confirmation and linked procurement objects for a Budget Line.

    Read-only aggregate for Budget Line desk panel (R5-003 / LV-R5-003-02).

    :param budget_line_name: Frappe ``name`` (primary key) of the ``Budget Line`` document.
    :raises frappe.PermissionError: If the user cannot read Procurement Journey.
    :raises frappe.ValidationError: If ``budget_line_name`` is blank.
    """
    _require_journey_read_permission()
    nm = cstr(budget_line_name or "").strip()
    if not nm:
        frappe.throw("budget_line_name is required.", frappe.ValidationError)
    return build_procurement_use_payload(nm)


@frappe.whitelist()
def get_demand_planning_status(
    demand_name: str | None = None,
) -> dict[str, Any]:
    """Retired with the Demands module. The module-level import of the deleted
    ``demand_planning_status`` helper had left this whole API module (and every
    test importing it) unimportable; honest retirement per the house pattern.

    :raises frappe.ValidationError: Always — the Demand model no longer exists.
    """
    _require_journey_read_permission()
    frappe.throw(
        "JOURNEY_DEMANDS_RETIRED: the Demand model was retired; "
        "planning status now derives from PLN-CHG-001 v1.2 records.",
        frappe.ValidationError,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _compute_journey_counts() -> dict[str, int]:
    """Compute aggregate journey counts for the list response (pack §10.2)."""
    rows = frappe.db.sql(
        """
        SELECT
            current_status_category,
            current_stage_key,
            blocker_count,
            critical_blocker_count
        FROM `tabProcurement Journey`
        WHERE docstatus != 2
        """,
        as_dict=True,
    )

    active = 0
    needs_action = 0
    blocked = 0
    ready_for_handoff = 0
    completed = 0

    for r in rows:
        sc = r.current_status_category or "Not Started"
        bc = int(r.blocker_count or 0) + int(r.critical_blocker_count or 0)

        if sc not in _INACTIVE_STATUSES:
            active += 1
        if sc == "Needs Action":
            needs_action += 1
        if bc > 0 or sc == "Blocked":
            blocked += 1
        if sc == "Ready for Handoff":
            ready_for_handoff += 1
        if r.current_stage_key == "contract" and sc == "Completed":
            completed += 1

    return {
        "active": active,
        "needs_action": needs_action,
        "blocked": blocked,
        "ready_for_handoff": ready_for_handoff,
        "completed": completed,
    }


def _user_entity_codes(user: str) -> list[str]:
    """Return procuring entity codes for the user from User Permission records."""
    rows = frappe.db.sql(
        """
        SELECT for_value
        FROM `tabUser Permission`
        WHERE user = %s
          AND allow = 'Procuring Entity'
          AND is_default = 1
        """,
        (user,),
        as_list=True,
    )
    return [r[0] for r in rows if r[0]]
