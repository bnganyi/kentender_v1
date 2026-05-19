# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-007 — WORKS master procurement planning seed (seed data specification §11).

Creates:
  - Procurement Plan ``PLAN-MOH-2026`` (status Approved, fiscal_year 2026, procuring_entity MOH/PE-MOH)
  - Procurement Package ``PKG-MOH-2026-001`` (Works, Open Tender, Released to Tender)
  - Procurement Package Line ``PKGLINE-MOH-2026-001-001`` linking DEM-MOH-2026-001 / BUD-MOH-INFRA-2026-001
  - Supporting profiles and template (idempotent, R2-007-scoped codes)

Status promotions are performed via ``frappe.db.set_value`` to bypass lifecycle guards that would
require live packages-approved checks and workflow role restrictions (same pattern as R2-005/006).

Prerequisites (must exist before this seed runs):
  - Procuring Entity MOH or PE-MOH (R2-003 / LV-R2-001-03)
  - Demand DEM-MOH-2026-001 in Approved status (R2-006 / LV-R2-001-06)
  - Budget Line BUD-MOH-INFRA-2026-001 (R2-005 / LV-R2-001-05)
  - Currency KES

Error codes:
  - ``MISSING_PROCURING_ENTITY`` — neither MOH nor PE-MOH entity exists
  - ``MISSING_DEMAND``           — DEM-MOH-2026-001 not found or not Approved
  - ``MISSING_BUDGET_LINE``      — BUD-MOH-INFRA-2026-001 not found

Run::

    bench --site kentender.midas.com execute \\
        kentender_procurement.procurement_planning.seeds.works_master_planning_seed.upsert_works_master_planning
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import now_datetime

# ---------------------------------------------------------------------------
# Business constants (spec §11)
# ---------------------------------------------------------------------------

PLAN_CODE = "PLAN-MOH-2026"
PLAN_NAME = "Ministry of Health Procurement Plan FY 2026/2027"
FISCAL_YEAR = 2026

PKG_CODE = "PKG-MOH-2026-001"
PKG_NAME = "District Hospital Renovation Works"
PKG_LINE_CODE = "PKGLINE-MOH-2026-001-001"

DEMAND_ID = "DEM-MOH-2026-001"
BUDGET_LINE_CODE = "BUD-MOH-INFRA-2026-001"
ESTIMATED_VALUE = 98_000_000.0

# Spec audit stamps
_U_PLAN = "planner@moh.test"
_PLAN_APPROVED_AT = "2026-04-10 10:00:00"
_PKG_APPROVED_AT = "2026-04-18 16:00:00"
_PKG_RELEASED_AT = "2026-04-20 10:15:00"

# R2-007 scoped codes for supporting records
_TEMPLATE_CODE = "PTPL-WORKS-OPEN-R2007"
_RISK_CODE = "RISK-WORKS-R2007"
_KPI_CODE = "KPI-WORKS-R2007"
_CRIT_CODE = "CRIT-WORKS-R2007"
_VM_CODE = "VM-WORKS-R2007"

# Candidate entity names for MOH (same resolution as R2-005/006)
_MOH_CANDIDATES = ("MOH", "PE-MOH")


# ---------------------------------------------------------------------------
# Prerequisite resolution
# ---------------------------------------------------------------------------


def resolve_procuring_entity_moh() -> str | None:
    """Return the first existing Procuring Entity name for MOH, or None."""
    for code in _MOH_CANDIDATES:
        if frappe.db.exists("Procuring Entity", code):
            return code
    for code in _MOH_CANDIDATES:
        name = frappe.db.get_value("Procuring Entity", {"entity_code": code}, "name")
        if name:
            return name
    return None


def _resolve_demand() -> str | None:
    """Return the Frappe docname of Demand with demand_id=DEM-MOH-2026-001."""
    return frappe.db.get_value("Demand", {"demand_id": DEMAND_ID}, "name")


def _resolve_budget_line() -> str | None:
    """Return the Frappe docname of Budget Line with budget_line_code=BUD-MOH-INFRA-2026-001."""
    return frappe.db.get_value("Budget Line", {"budget_line_code": BUDGET_LINE_CODE}, "name")


# ---------------------------------------------------------------------------
# Profile + template helpers (idempotent)
# ---------------------------------------------------------------------------


def _ensure_profile(doctype: str, *, code: str, name: str, extra: dict) -> str:
    existing = frappe.db.get_value(doctype, {"profile_code": code}, "name")
    if existing:
        return existing
    doc = frappe.get_doc(
        {
            "doctype": doctype,
            "profile_code": code,
            "profile_name": name,
            **extra,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def _ensure_profiles() -> dict[str, str]:
    """Create (or retrieve) R2-007-scoped risk/KPI/criteria/VM profiles."""
    risk = _ensure_profile(
        "Risk Profile",
        code=_RISK_CODE,
        name="Works Master Risk Profile (R2-007)",
        extra={
            "risk_level": "High",
            "risks": json.dumps(
                [{"risk": "Site disruption", "mitigation": "Phased delivery approach"}]
            ),
        },
    )
    kpi = _ensure_profile(
        "KPI Profile",
        code=_KPI_CODE,
        name="Works Master KPI Profile (R2-007)",
        extra={"metrics": json.dumps(["Milestone delivery", "Cost variance", "Quality compliance"])},
    )
    crit = _ensure_profile(
        "Decision Criteria Profile",
        code=_CRIT_CODE,
        name="Works Master Decision Criteria Profile (R2-007)",
        extra={
            "criteria": json.dumps(
                [
                    {"criterion": "Technical", "weight": 70},
                    {"criterion": "Price", "weight": 30},
                ]
            )
        },
    )
    vm = _ensure_profile(
        "Vendor Management Profile",
        code=_VM_CODE,
        name="Works Master VM Profile (R2-007)",
        extra={
            "monitoring_rules": json.dumps({"cadence": ["Monthly"]}),
            "escalation_rules": json.dumps({"paths": ["Standard"]}),
        },
    )
    return {
        "risk_profile_id": risk,
        "kpi_profile_id": kpi,
        "decision_criteria_profile_id": crit,
        "vendor_management_profile_id": vm,
    }


def _ensure_template(profiles: dict[str, str]) -> str:
    """Create (or retrieve) the R2-007 procurement template."""
    existing = frappe.db.get_value(
        "Procurement Template", {"template_code": _TEMPLATE_CODE}, "name"
    )
    if existing:
        return existing
    doc = frappe.get_doc(
        {
            "doctype": "Procurement Template",
            "template_code": _TEMPLATE_CODE,
            "template_name": "Works Open Tender Template (WORKS Master R2-007)",
            "category": "works",
            "is_active": 1,
            "default_method": "Open Tender",
            "allowed_methods": json.dumps(["Open Tender"]),
            "default_contract_type": "Fixed Price",
            "applicable_requisition_types": json.dumps(["Works"]),
            "applicable_demand_types": json.dumps(["Planned", "Unplanned", "Emergency"]),
            "grouping_strategy": json.dumps({"group_by": []}),
            "override_requires_justification": 1,
            "high_risk_escalation_required": 0,
            "schedule_required": 0,
            **profiles,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------


def _ensure_plan(entity: str) -> tuple[str, bool]:
    """Insert Procurement Plan as Draft, then promote to Approved via db.set_value.

    Returns (plan_name, created). Plan name == PLAN_CODE (autoname: field:plan_code).
    """
    if frappe.db.exists("Procurement Plan", PLAN_CODE):
        return PLAN_CODE, False

    doc = frappe.get_doc(
        {
            "doctype": "Procurement Plan",
            "plan_code": PLAN_CODE,
            "plan_name": PLAN_NAME,
            "fiscal_year": FISCAL_YEAR,
            "procuring_entity": entity,
            "currency": "KES",
            "status": "Draft",
            "is_active": 1,
        }
    )
    doc.flags.ignore_mandatory = True
    doc.insert(ignore_permissions=True)

    # Promote to Approved bypassing lifecycle (no packages yet; seed acts as historical fact)
    frappe.db.set_value(
        "Procurement Plan",
        PLAN_CODE,
        {
            "status": "Approved",
            "approved_by": _U_PLAN,
            "approved_at": _PLAN_APPROVED_AT,
        },
        update_modified=False,
    )
    return PLAN_CODE, True


# ---------------------------------------------------------------------------
# Package
# ---------------------------------------------------------------------------


def _ensure_package(profiles: dict[str, str], template_name: str) -> tuple[str, bool]:
    """Insert Procurement Package under PLAN-MOH-2026 as Draft.

    Returns (pkg_name, created). Package name == PKG_CODE (autoname: field:package_code;
    Administrator can set package_code directly).
    Status promotion to Released to Tender is deferred until after the package line is inserted.
    """
    existing = frappe.db.get_value(
        "Procurement Package", {"package_code": PKG_CODE}, "name"
    )
    if existing:
        return existing, False

    doc = frappe.get_doc(
        {
            "doctype": "Procurement Package",
            "package_code": PKG_CODE,
            "package_name": PKG_NAME,
            "plan_id": PLAN_CODE,
            "template_id": template_name,
            "procurement_method": "Open Tender",
            "contract_type": "Fixed Price",
            "method_override_flag": 0,
            "currency": "KES",
            "status": "Draft",
            "is_active": 1,
            "is_emergency": 0,
            "schedule_start": "2026-05-01",
            "schedule_end": "2026-06-20",
            "planner_notes": "WORKS master seed R2-007 — District Hospital Renovation Works.",
            **profiles,
        }
    )
    doc.flags.ignore_mandatory = True
    doc.insert(ignore_permissions=True)
    return PKG_CODE, True


def _promote_package_released(pkg_name: str) -> None:
    """Advance package to Released to Tender with spec audit stamps."""
    frappe.db.set_value(
        "Procurement Package",
        pkg_name,
        {
            "status": "Released to Tender",
            "approved_by": _U_PLAN,
            "approved_at": _PKG_APPROVED_AT,
            "released_to_tender_at": _PKG_RELEASED_AT,
        },
        update_modified=False,
    )


# ---------------------------------------------------------------------------
# Package line
# ---------------------------------------------------------------------------


def _ensure_package_line(
    pkg_name: str, demand_name: str, budget_line_name: str
) -> bool:
    """Insert or repair Package Line while Package is still Draft. Returns True if created."""
    existing = frappe.db.get_value(
        "Procurement Package Line",
        {"package_line_code": PKG_LINE_CODE},
        ["name", "package_id", "demand_id", "budget_line_id"],
        as_dict=True,
    )
    if existing:
        patch: dict[str, str] = {}
        if (existing.get("package_id") or "") != pkg_name:
            patch["package_id"] = pkg_name
        if (existing.get("demand_id") or "") != demand_name:
            patch["demand_id"] = demand_name
        if (existing.get("budget_line_id") or "") != budget_line_name:
            patch["budget_line_id"] = budget_line_name
        if patch:
            frappe.db.set_value("Procurement Package Line", existing.name, patch, update_modified=False)
        return False

    doc = frappe.get_doc(
        {
            "doctype": "Procurement Package Line",
            "package_id": pkg_name,
            "package_line_code": PKG_LINE_CODE,
            "demand_id": demand_name,
            "budget_line_id": budget_line_name,
            "amount": ESTIMATED_VALUE,
            "quantity": 1.0,
            "priority": "High",
            "department": "Infrastructure and Facilities Directorate",
            "is_active": 1,
        }
    )
    doc.insert(ignore_permissions=True)
    return True


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def upsert_works_master_planning() -> dict:
    """Idempotent upsert of Procurement Plan + Package + Package Line for WORKS master seed.

    Returns a result dict with ``ok``, ``idempotent``, and field-level evidence.
    """
    # --- Prerequisite checks ---
    entity = resolve_procuring_entity_moh()
    if not entity:
        return {
            "ok": False,
            "error_code": "MISSING_PROCURING_ENTITY",
            "message": "No Procuring Entity found with code MOH or PE-MOH. Run R2-003 seed first.",
        }

    demand_name = _resolve_demand()
    if not demand_name:
        return {
            "ok": False,
            "error_code": "MISSING_DEMAND",
            "message": f"Demand with demand_id={DEMAND_ID!r} not found. Run R2-006 seed first.",
        }
    demand_status = frappe.db.get_value("Demand", demand_name, "status") or ""
    if demand_status not in ("Approved", "Planning Ready"):
        return {
            "ok": False,
            "error_code": "MISSING_DEMAND",
            "message": (
                f"Demand {DEMAND_ID} exists but is not Approved/Planning Ready "
                f"(got {demand_status!r}). Run R2-006 seed first."
            ),
        }

    budget_line_name = _resolve_budget_line()
    if not budget_line_name:
        return {
            "ok": False,
            "error_code": "MISSING_BUDGET_LINE",
            "message": (
                f"Budget Line with budget_line_code={BUDGET_LINE_CODE!r} not found. "
                "Run R2-005 seed first."
            ),
        }

    # --- Idempotency check ---
    plan_exists = frappe.db.exists("Procurement Plan", PLAN_CODE)
    pkg_name_existing = frappe.db.get_value(
        "Procurement Package", {"package_code": PKG_CODE}, "name"
    )
    line_exists = frappe.db.exists(
        "Procurement Package Line", {"package_line_code": PKG_LINE_CODE}
    )
    if plan_exists and pkg_name_existing and line_exists:
        _ensure_package_line(pkg_name_existing, demand_name, budget_line_name)
        return {
            "ok": True,
            "idempotent": True,
            "plan": PLAN_CODE,
            "plan_code": PLAN_CODE,
            "plan_created": False,
            "package": pkg_name_existing,
            "package_code": PKG_CODE,
            "package_created": False,
            "package_line_created": False,
            "plan_status": frappe.db.get_value("Procurement Plan", PLAN_CODE, "status"),
            "package_status": frappe.db.get_value(
                "Procurement Package", pkg_name_existing, "status"
            ),
        }

    # --- Build supporting infrastructure ---
    profiles = _ensure_profiles()
    template_name = _ensure_template(profiles)

    # --- Plan ---
    plan_name, plan_created = _ensure_plan(entity)

    # --- Package (insert as Draft; package_line insert requires Draft/Completed/Returned) ---
    pkg_name, pkg_created = _ensure_package(profiles, template_name)

    # --- Package Line (while package is still Draft) ---
    line_created = _ensure_package_line(pkg_name, demand_name, budget_line_name)

    # --- Promote Package to Released to Tender ---
    current_pkg_status = frappe.db.get_value("Procurement Package", pkg_name, "status") or ""
    if current_pkg_status != "Released to Tender":
        _promote_package_released(pkg_name)

    # Ensure plan is Approved (may already be if re-entered after partial run)
    current_plan_status = frappe.db.get_value("Procurement Plan", plan_name, "status") or ""
    if current_plan_status != "Approved":
        frappe.db.set_value(
            "Procurement Plan",
            plan_name,
            {
                "status": "Approved",
                "approved_by": _U_PLAN,
                "approved_at": _PLAN_APPROVED_AT,
            },
            update_modified=False,
        )

    final_plan_status = frappe.db.get_value("Procurement Plan", plan_name, "status")
    final_pkg_status = frappe.db.get_value("Procurement Package", pkg_name, "status")

    return {
        "ok": True,
        "idempotent": False,
        "plan": plan_name,
        "plan_code": PLAN_CODE,
        "plan_created": plan_created,
        "package": pkg_name,
        "package_code": PKG_CODE,
        "package_created": pkg_created,
        "package_line_created": line_created,
        "plan_status": final_plan_status,
        "package_status": final_pkg_status,
        "entity": entity,
        "template": template_name,
    }
