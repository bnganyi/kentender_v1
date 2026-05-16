# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-013 — WORKS master seed conflict report.

## Goal

Scan the live DB for conflicts between the WORKS master seed codes (spec §4) and any
existing records, then produce a structured report that:

1. Identifies records that carry a master business code but **lack ``is_master_seed=1``**
   (non-master ownership conflict — stop for approval unless safe-reset applies).
2. Identifies **legacy sibling codes** that coexist with master codes on the same site
   (e.g. ``BL-MOH-2026-001`` alongside ``BUD-MOH-INFRA-2026-001`` from G0-003 §4.1).
3. Lists the **known non-master seed registry** (files documented in G0-003 that use
   master-adjacent codes) so operators know which seeds to exclude or deprioritize.
4. Applies the **No-Go conditions** (spec §26) and flags any that are violated.

## Conflict severity levels

| Level | Meaning | Operator action |
|---|---|---|
| CRITICAL | Master code used by ``is_master_seed=0`` record or No-Go condition triggered | Stop; obtain PM approval before proceeding |
| WARNING | Legacy sibling code coexists; non-master seed may have run | Acknowledge; safe to proceed with master seed |
| INFO | Expected clean state; record exists and is master-owned | No action needed |

## Safe reset rule (spec §19.4)

A conflict is **safe-auto-reset** when the conflicting record has ``is_master_seed=1``
(re-running with ``reset=True`` will remove and recreate it cleanly).
It is **NOT safe-auto-reset** when the conflicting record has ``is_master_seed=0``
(manually created or non-master seeded data that would be lost on reset).
"""

from __future__ import annotations

from typing import Any, Final

import frappe

# ── Master code registry (spec §4.1) ─────────────────────────────────────────

_JOURNEY_CODE: Final[str] = "JRN-MOH-2026-001"

_HANDOFF_CODES: Final[tuple[str, ...]] = (
    "STRATREF-MOH-2026-001",
    "BUDCONF-MOH-2026-001",
    "DEMAPP-MOH-2026-001",
    "PLANINCL-MOH-2026-001",
    "PKGREL-MOH-2026-001",
    "STDREADY-TND-MOH-2026-001",
    "PUBCERT-TND-MOH-2026-001",
    "CLOSECERT-TND-MOH-2026-001",
    "OPENREADY-TND-MOH-2026-001",
)

# DocTypes where is_master_seed is meaningful (those we set it on)
_IS_MASTER_SEED_DOCTYPES: Final[dict[str, str]] = {
    "Procurement Journey": _JOURNEY_CODE,
    # Handoff cards checked separately below
}

# Business codes that should exist as records and be correctly linked
_BUSINESS_CODE_CHECKS: Final[list[dict[str, Any]]] = [
    {
        "check_id": "CC-001",
        "doctype": "Procurement Journey",
        "name": _JOURNEY_CODE,
        "description": "Master journey JRN-MOH-2026-001",
        "has_is_master_seed": True,
        "no_go_ids": ["SEED-NG-008"],
    },
    {
        "check_id": "CC-002",
        "doctype": "TM2 Tender",
        "name": "TND-MOH-2026-001",
        "description": "Master TM2 Tender",
        "has_is_master_seed": False,
        "no_go_ids": ["SEED-NG-007"],
        "expected_status": "Published",
        "expected_status_field": "status",
    },
    {
        "check_id": "CC-003",
        "doctype": "Procurement Package",
        "name": "PKG-MOH-2026-001",
        "description": "Master Procurement Package",
        "has_is_master_seed": False,
        "no_go_ids": ["SEED-NG-006"],
        "expected_status": "Released to Tender",
        "expected_status_field": "status",
    },
    {
        "check_id": "CC-004",
        "doctype": "Demand",
        "filter_field": "demand_id",
        "filter_value": "DEM-MOH-2026-001",
        "description": "Master Demand DEM-MOH-2026-001",
        "has_is_master_seed": False,
        "no_go_ids": ["SEED-NG-005"],
        "expected_status": "Approved",
        "expected_status_field": "status",
    },
    {
        "check_id": "CC-005",
        "doctype": "Budget Line",
        "name": "BUD-MOH-INFRA-2026-001",
        "description": "Master Budget Line",
        "has_is_master_seed": False,
        "no_go_ids": [],
    },
    {
        "check_id": "CC-006",
        "doctype": "STD Template",
        "name": "KE-PPRA-WORKS-BLDG-2022-04-POC",
        "description": "Master STD Template (POC edition)",
        "has_is_master_seed": False,
        "no_go_ids": ["SEED-NG-004"],
        "expected_status": "Active",
        "expected_status_field": "status",
    },
]

# ── Legacy sibling codes documented in G0-003 §4.1 ───────────────────────────

_LEGACY_SIBLING_CHECKS: Final[list[dict[str, Any]]] = [
    {
        "sibling_id": "SIB-001",
        "description": "Legacy budget line BL-MOH-2026-001 (G0-003: BL-* vs BUD-MOH-* namespace)",
        "doctype": "Budget Line",
        "filter_field": "budget_line_code",
        "filter_value": "BL-MOH-2026-001",
        "g0_reference": "G0-003 §4.1 BUD-MOH-INFRA-2026-001 row: 'BL-MOH-*' parallel namespace",
    },
    {
        "sibling_id": "SIB-002",
        "description": "Smoke test demand namespace DIA-MOH-* (should be absent after cleanup)",
        "doctype": "Demand",
        "filter_field": "demand_id",
        "filter_value": "DIA-MOH_D7_%",
        "filter_operator": "like",
        "g0_reference": "G0-003 §4.1 DEM-MOH-2026-001 row: 'DIA-MOH-*' smoke namespace",
    },
    {
        "sibling_id": "SIB-003",
        "description": "Works-S01 demand namespace DEM-MOH-WORKS-2026-001 (intentional peer)",
        "doctype": "Demand",
        "filter_field": "demand_id",
        "filter_value": "DEM-MOH-WORKS-2026-001",
        "g0_reference": "G0-003 §4.1 DEM-MOH-2026-001 row: 'seed_works_stdint_s01 alias'",
    },
    {
        "sibling_id": "SIB-004",
        "description": "F1/PP3 procurement plan PP-MOH-2026 (non-master plan family)",
        "doctype": "Procurement Plan",
        "filter_by_name": "PP-MOH-2026",
        "g0_reference": "G0-003 §4.1 PLAN-MOH-2026 row: 'F1/PP3 use PP-MOH-2026'",
    },
    {
        "sibling_id": "SIB-005",
        "description": "Smoke test tenders TND-MOH-2029-* (should be absent after cleanup)",
        "doctype": "TM2 Tender",
        "filter_sql": "SELECT COUNT(*) FROM `tabTM2 Tender` WHERE name LIKE 'TND-MOH-2029-%'",
        "g0_reference": "Smoke test cleanup (previously purged)",
    },
]

# ── Known non-master seed registry (G0-003 Appendix A) ───────────────────────

NON_MASTER_SEED_REGISTRY: Final[list[dict[str, str]]] = [
    {
        "seed_id": "NMS-001",
        "module": "kentender_procurement.tender_management.seeds.seed_std_inst_1400",
        "uses_master_codes": "PKG-MOH-2026-001, TND-MOH-2026-001",
        "profile_drift": "WORKS-PROFILE-BUILDING-CIVIL-REV-APR-2022 vs WORKS-PROFILE-BUILDING-CIVIL",
        "disposition": "Non-master smoke seed. Exclude from master journey queries. Do not run in production after R2 seeds are set.",
        "g0_reference": "G0-003 Appendix A row seed_std_inst_1400",
    },
    {
        "seed_id": "NMS-002",
        "module": "kentender_procurement.procurement_planning.seeds.seed_procurement_planning_f1",
        "uses_master_codes": "PKG-MOH-2026-001 (partial: PP-MOH-2026 plan namespace)",
        "disposition": "F1 development seed. Uses PP-MOH-2026 plan, not PLAN-MOH-2026. Non-conflicting plan family.",
        "g0_reference": "G0-003 Appendix A row seed_procurement_planning_f1",
    },
    {
        "seed_id": "NMS-003",
        "module": "kentender_procurement.procurement_planning.seeds.seed_planning_pp3_slice",
        "uses_master_codes": "PKG-MOH-2026-001 (partial)",
        "disposition": "PP3 slice seed. Same disposition as F1.",
        "g0_reference": "G0-003 Appendix A row seed_planning_pp3_slice",
    },
    {
        "seed_id": "NMS-004",
        "module": "kentender_procurement.procurement_planning.seeds.seed_works_stdint_s01",
        "uses_master_codes": "PKG-MOH-2026-001, PLAN-MOH-2026-WORKS-S01 (alias), BL-MOH (alias)",
        "disposition": "WORKS-S01 integration smoke seed. Uses alias codes; demand space DEM-MOH-WORKS-*. Intentional peer — does not conflict on exact master code strings.",
        "g0_reference": "G0-003 Appendix A row seed_works_stdint_s01",
    },
    {
        "seed_id": "NMS-005",
        "module": "kentender_procurement.demand_intake.seeds.seed_dia_basic / extended / exceptions",
        "uses_master_codes": "BL-MOH-2026-001 (legacy budget line alias), DIA-MOH-* demand namespace",
        "disposition": "DIA smoke seeds. Use separate demand_id namespace. Budget line alias BL-* is separate from BUD-MOH-INFRA-*.",
        "g0_reference": "G0-003 Appendix A seed_dia_* rows",
    },
    {
        "seed_id": "NMS-006",
        "module": "docs/audit/planning_tender_handoff_2026-05-03/seeds/*.py",
        "uses_master_codes": "PKG-MOH-2026-001, F1/PP3 constants (duplicate definitions)",
        "disposition": "Audit-only entrypoints. Must not run in production pipelines per G0-003 LV-G0-003-02 rule 5.",
        "g0_reference": "G0-003 LV-G0-003-02 rule 5",
    },
]


# ── Conflict check helpers ────────────────────────────────────────────────────

def _check_master_record(check: dict[str, Any]) -> dict[str, Any]:
    """Run a single master-code DB check and return a result entry."""
    doctype = check["doctype"]
    description = check["description"]
    check_id = check["check_id"]

    # Resolve the record name
    if "name" in check:
        record_name = check["name"]
        exists = bool(frappe.db.exists(doctype, record_name))
    else:
        # filter by a field
        field = check["filter_field"]
        value = check["filter_value"]
        record_name = frappe.db.get_value(doctype, {field: value}, "name")
        exists = bool(record_name)

    if not exists:
        return {
            "check_id": check_id,
            "severity": "WARNING",
            "description": description,
            "doctype": doctype,
            "code": check.get("name") or check.get("filter_value"),
            "exists": False,
            "message": f"{doctype} record does not exist — upstream seed may not have run.",
            "safe_reset": True,
            "no_go_ids": check.get("no_go_ids", []),
        }

    result: dict[str, Any] = {
        "check_id": check_id,
        "severity": "INFO",
        "description": description,
        "doctype": doctype,
        "code": record_name,
        "exists": True,
        "message": "Record exists.",
        "safe_reset": True,
        "no_go_ids": check.get("no_go_ids", []),
    }

    # Check is_master_seed where applicable
    if check.get("has_is_master_seed"):
        ms = frappe.db.get_value(doctype, record_name, "is_master_seed")
        if not ms:
            result["severity"] = "CRITICAL"
            result["message"] = (
                f"{doctype} {record_name!r} exists but is_master_seed=0. "
                "Non-master record occupies master code slot. Stop for approval."
            )
            result["safe_reset"] = False

    # Check expected status
    if check.get("expected_status"):
        field = check["expected_status_field"]
        actual = frappe.db.get_value(doctype, record_name, field)
        if actual != check["expected_status"]:
            result["severity"] = "WARNING"
            result["message"] = (
                f"{doctype} {record_name!r} has {field}={actual!r}, "
                f"expected {check['expected_status']!r}. "
                "Re-running the master seed (idempotent) should correct this."
            )
            result["safe_reset"] = True

    return result


def _check_handoff_cards() -> list[dict[str, Any]]:
    """Check all master handoff card codes for non-master ownership."""
    results = []
    for code in _HANDOFF_CODES:
        if not frappe.db.exists("Procurement Handoff Card", code):
            results.append({
                "check_id": f"CC-HC-{code}",
                "severity": "INFO",
                "description": f"Handoff card {code}",
                "doctype": "Procurement Handoff Card",
                "code": code,
                "exists": False,
                "message": f"Handoff card {code!r} not present — may be optional (e.g. opening checkpoint).",
                "safe_reset": True,
                "no_go_ids": [],
            })
            continue
        ms = frappe.db.get_value("Procurement Handoff Card", code, "is_master_seed")
        if ms:
            results.append({
                "check_id": f"CC-HC-{code}",
                "severity": "INFO",
                "description": f"Handoff card {code}",
                "doctype": "Procurement Handoff Card",
                "code": code,
                "exists": True,
                "message": "Card exists with is_master_seed=1.",
                "safe_reset": True,
                "no_go_ids": [],
            })
        else:
            results.append({
                "check_id": f"CC-HC-{code}",
                "severity": "CRITICAL",
                "description": f"Handoff card {code}",
                "doctype": "Procurement Handoff Card",
                "code": code,
                "exists": True,
                "message": (
                    f"Handoff card {code!r} exists but is_master_seed=0. "
                    "Non-master record occupies master code slot — stop for approval."
                ),
                "safe_reset": False,
                "no_go_ids": ["SEED-NG-009"],
            })
    return results


def _check_siblings() -> list[dict[str, Any]]:
    """Check for legacy sibling codes coexisting with master codes."""
    results = []
    for sib in _LEGACY_SIBLING_CHECKS:
        sibling_id = sib["sibling_id"]
        description = sib["description"]

        count = 0
        if "filter_sql" in sib:
            count = frappe.db.sql(sib["filter_sql"])[0][0]
        elif "filter_by_name" in sib:
            count = 1 if frappe.db.exists(sib["doctype"], sib["filter_by_name"]) else 0
        elif sib.get("filter_operator") == "like":
            field = sib["filter_field"]
            value = sib["filter_value"]
            count = frappe.db.sql(
                f"SELECT COUNT(*) FROM `tab{sib['doctype']}` WHERE `{field}` LIKE %s",
                (value,),
            )[0][0]
        else:
            field = sib["filter_field"]
            value = sib["filter_value"]
            count = 1 if frappe.db.exists(sib["doctype"], {field: value}) else 0

        results.append({
            "sibling_id": sibling_id,
            "description": description,
            "count": count,
            "severity": "WARNING" if count > 0 else "INFO",
            "message": (
                f"Found {count} legacy/sibling record(s). {sib['g0_reference']}"
                if count > 0
                else "Not present on this site."
            ),
            "safe_to_coexist": True,
        })
    return results


# ── Main report entry ─────────────────────────────────────────────────────────

def generate_works_master_conflict_report() -> dict[str, Any]:
    """Scan the DB and produce the R2-013 structured conflict report.

    :returns: Report dict containing ``ok``, ``critical_conflicts``, ``warnings``,
        ``legacy_siblings``, ``non_master_seed_registry``, ``safe_to_proceed``,
        ``no_go_violations``, and a human-readable ``summary``.
    """
    frappe.set_user("Administrator")

    # ── Step 1: Check master DocType records ─────────────────────────────────
    record_checks: list[dict[str, Any]] = []
    for check in _BUSINESS_CODE_CHECKS:
        record_checks.append(_check_master_record(check))
    record_checks.extend(_check_handoff_cards())

    critical = [r for r in record_checks if r["severity"] == "CRITICAL"]
    warnings_list = [r for r in record_checks if r["severity"] == "WARNING"]
    infos = [r for r in record_checks if r["severity"] == "INFO"]

    # ── Step 2: Legacy sibling checks ────────────────────────────────────────
    sibling_results = _check_siblings()
    sibling_warnings = [s for s in sibling_results if s["severity"] == "WARNING"]

    # ── Step 3: No-Go condition check ────────────────────────────────────────
    triggered_no_go: list[str] = []
    for r in critical:
        triggered_no_go.extend(r.get("no_go_ids", []))

    # De-duplicate
    triggered_no_go = sorted(set(triggered_no_go))

    # ── Step 4: Journey step count no-go check (SEED-NG-008) ─────────────────
    if frappe.db.exists("Procurement Journey", _JOURNEY_CODE):
        stage = frappe.db.get_value("Procurement Journey", _JOURNEY_CODE, "current_stage_key") or ""
        if not stage:
            triggered_no_go.append("SEED-NG-008")
            critical.append({
                "check_id": "CC-NG-008",
                "severity": "CRITICAL",
                "description": "Journey current_stage_key is blank",
                "doctype": "Procurement Journey",
                "code": _JOURNEY_CODE,
                "exists": True,
                "message": "Journey current_stage_key is blank — No-Go SEED-NG-008 triggered.",
                "safe_reset": True,
                "no_go_ids": ["SEED-NG-008"],
            })

    safe_to_proceed = len(critical) == 0
    ok = safe_to_proceed

    # ── Build summary text ────────────────────────────────────────────────────
    if ok:
        if sibling_warnings:
            summary = (
                f"No critical conflicts. {len(sibling_warnings)} legacy sibling code(s) detected "
                "(expected per G0-003 — safe to coexist). "
                f"{len(infos)} master records confirmed clean. "
                f"{len(warnings_list)} record warnings (missing upstream seeds or status drift)."
            )
        else:
            summary = (
                f"Clean state. {len(infos)} master records confirmed. "
                f"{len(warnings_list)} record warnings. No conflicts detected."
            )
    else:
        summary = (
            f"{len(critical)} CRITICAL conflict(s) detected. "
            f"No-Go conditions triggered: {', '.join(triggered_no_go) or 'none'}. "
            "Stop and obtain PM approval before proceeding with master seed."
        )

    return {
        "ok": ok,
        "safe_to_proceed": safe_to_proceed,
        "critical_conflicts": critical,
        "record_warnings": warnings_list,
        "clean_records": [r["check_id"] for r in infos],
        "no_go_violations": triggered_no_go,
        "legacy_siblings": sibling_results,
        "non_master_seed_registry": NON_MASTER_SEED_REGISTRY,
        "summary": summary,
    }
