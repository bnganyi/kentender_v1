# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R2-006 — WORKS master demand seed (spec §10 / VAL-SEED-005, VAL-SEED-006).

Creates **DEM-MOH-2026-001** — District Hospital Renovation Works demand — with one approved item
(KES 98 M, Works / Lot) linked to BUD-MOH-INFRA-2026-001.

Status lifecycle is materialised via direct ``frappe.db.set_value`` after insert (same pattern as
R2-005 budget seed), bypassing ``approve_finance`` which performs a live budget availability
check. The budget line has ``amount_available = 22 M`` against a demand of 98 M — insufficient
for a live approval but correct for historical WORKS master seed data.

Prerequisite chain:
    LV-R2-001-03  →  Procuring Entity PE-MOH
    LV-R2-001-04  →  Strategy records (R2-004)
    LV-R2-001-05  →  Budget + Budget Line BUD-MOH-INFRA-2026-001 (R2-005)
"""

from __future__ import annotations

import frappe
from frappe import _

from kentender_core.seeds._common import ensure_department

DEMAND_ID = "DEM-MOH-2026-001"
BUDGET_LINE_CODE = "BUD-MOH-INFRA-2026-001"
DEPT_INFRA = "Infrastructure and Facilities Directorate"
DEMAND_TITLE = "District Hospital Renovation Works"
ESTIMATED_UNIT_COST = 98_000_000.0

_U_REQ = "requisitioner@moh.test"
_U_HOD = "hod.approver@moh.test"
_U_FIN = "finance.reviewer@moh.test"

_SPEC_SUBMITTED_AT = "2026-03-03 09:20:00"
_SPEC_HOD_APPROVED_AT = "2026-03-04 10:00:00"
_SPEC_APPROVED_AT = "2026-03-05 14:30:00"
_SPEC_REQUEST_DATE = "2026-03-03"
_SPEC_REQUIRED_BY_DATE = "2026-12-31"


def resolve_procuring_entity_moh() -> str | None:
    """Return the Frappe docname of PE-MOH (or MOH fallback) procuring entity."""
    for code in ("PE-MOH", "MOH"):
        name = frappe.db.get_value("Procuring Entity", {"entity_code": code}, "name")
        if name:
            return name
    return None


def _resolve_budget_line() -> str | None:
    """Return the Frappe docname of BUD-MOH-INFRA-2026-001."""
    return frappe.db.get_value("Budget Line", {"budget_line_code": BUDGET_LINE_CODE}, "name")


def _ensure_infra_department(entity: str) -> str:
    """Idempotently create the Infrastructure and Facilities Directorate department."""
    return ensure_department(DEPT_INFRA, entity)


def _insert_demand(entity: str, dept: str, budget_line: str) -> frappe.model.document.Document:
    """Insert a Draft Demand and force demand_id to DEMAND_ID after insert."""
    row = {
        "doctype": "Demand",
        "title": DEMAND_TITLE,
        "demand_id": DEMAND_ID,
        "procuring_entity": entity,
        "requesting_department": dept,
        "requested_by": _U_REQ,
        "created_by": _U_REQ,
        "request_date": _SPEC_REQUEST_DATE,
        "required_by_date": _SPEC_REQUIRED_BY_DATE,
        "priority_level": "High",
        "demand_type": "Planned",
        "requisition_type": "Works",
        "budget_line": budget_line,
        "specification_summary": (
            "Request to renovate and restore critical building and associated civil engineering "
            "works at Makutano District Hospital."
        ),
        "beneficiary_summary": (
            "Patients and healthcare staff at Makutano District Hospital requiring restored "
            "facilities for clinical and outpatient services."
        ),
        "delivery_location": "Makutano District Hospital, Kenya",
        "items": [
            {
                "item_description": (
                    "Renovation of wards, outpatient areas, structural repairs, plumbing and "
                    "associated civil works at Makutano District Hospital."
                ),
                "category": "Works",
                "uom": "Lot",
                "quantity": 1.0,
                "estimated_unit_cost": ESTIMATED_UNIT_COST,
                "notes": "Building and associated civil engineering renovation works.",
            }
        ],
        "status": "Draft",
        "reservation_status": "None",
        "planning_status": "Not Planned",
    }
    d = frappe.get_doc(row)
    d.flags.ignore_mandatory = True
    d.insert(ignore_permissions=True)
    # The Demand controller generates a DIA-* demand_id during validate if demand_id is not
    # pre-set, but we pre-set it. Force an explicit set_value as a safety net.
    if frappe.db.get_value("Demand", d.name, "demand_id") != DEMAND_ID:
        frappe.db.set_value("Demand", d.name, "demand_id", DEMAND_ID, update_modified=False)
    return frappe.get_doc("Demand", d.name)


def _promote_to_approved(demand_name: str) -> None:
    """Directly materialise the Approved state and audit trail via set_value.

    Bypasses ``approve_finance`` because the live budget availability check would reject the
    seed (BUD-MOH-INFRA-2026-001 amount_available = 22 M < demand total_amount = 98 M). This is
    intentional for WORKS master seed: the spec §9 pre-reserves 98 M on the budget line as part
    of the scenario, so the demand seed treats status as historical fact.
    """
    frappe.db.set_value(
        "Demand",
        demand_name,
        {
            "status": "Approved",
            "submitted_by": _U_REQ,
            "submitted_at": _SPEC_SUBMITTED_AT,
            "hod_approved_by": _U_HOD,
            "hod_approved_at": _SPEC_HOD_APPROVED_AT,
            "finance_approved_by": _U_FIN,
            "finance_approved_at": _SPEC_APPROVED_AT,
        },
        update_modified=False,
    )


def upsert_works_master_demand() -> dict:
    """Idempotent upsert of DEM-MOH-2026-001 (spec §10).

    Returns dict with keys: ok, demand, demand_id, demand_created, idempotent, status.
    On error returns ok=False, error_code, message.
    """
    frappe.only_for(("System Manager", "Administrator"))

    entity = resolve_procuring_entity_moh()
    if not entity:
        return {
            "ok": False,
            "error_code": "MISSING_PROCURING_ENTITY",
            "message": "Procuring Entity PE-MOH (or MOH) not found. Run entity seed first.",
        }

    budget_line = _resolve_budget_line()
    if not budget_line:
        return {
            "ok": False,
            "error_code": "MISSING_BUDGET_LINE",
            "message": (
                f"Budget Line {BUDGET_LINE_CODE} not found. "
                "Run R2-005 budget seed first (LV-R2-001-05)."
            ),
        }

    # Derive the entity from the budget line itself — entity code variants PE-MOH / MOH must match
    # what the budget line stores, or the Demand controller's _apply_budget_line_strategy will
    # throw "Selected budget line belongs to a different procuring entity."
    budget_line_entity = frappe.db.get_value("Budget Line", budget_line, "procuring_entity")
    if budget_line_entity:
        entity = budget_line_entity

    existing_name = frappe.db.get_value("Demand", {"demand_id": DEMAND_ID}, "name")
    if existing_name:
        status = frappe.db.get_value("Demand", existing_name, "status") or ""
        return {
            "ok": True,
            "demand": existing_name,
            "demand_id": DEMAND_ID,
            "demand_created": False,
            "idempotent": True,
            "status": status,
        }

    dept = _ensure_infra_department(entity)
    doc = _insert_demand(entity, dept, budget_line)
    _promote_to_approved(doc.name)

    status = frappe.db.get_value("Demand", doc.name, "status") or ""
    return {
        "ok": True,
        "demand": doc.name,
        "demand_id": DEMAND_ID,
        "demand_created": True,
        "idempotent": False,
        "status": status,
    }
