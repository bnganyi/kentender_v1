# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Portfolio Hub mock-data seed (dev/UAT).

Deletes all existing Strategic Plans and their hierarchy, then creates three
realistic plans that cover the existing Demand dataset with a full KPI
hierarchy for weighted success score computation:

  Plan 1 — Ministry of Health Strategic Plan 2026–2030  (Active)
    • Medical Supply Chain Management   → 2 objectives, 5 KPI targets
    • Healthcare Infrastructure Dev     → 2 objectives, 5 KPI targets
    • Digital Health & ICT              → 1 objective,  3 KPI targets
    → linked to all 65 Demands

  Plan 2 — Public Health Promotion Strategy 2024–2028   (Archived)
  Plan 3 — Primary Health Care Expansion Plan 2026–2031 (Submitted)

Usage::

    bench --site kentender.midas.com execute \\
      kentender_strategy.seeds.seed_portfolio_hub_mockdata.run
"""

from __future__ import annotations

import frappe


# ── Demand title prefixes → program assignment ──────────────────────────────
DEMAND_PROGRAM_MAP = {
    "Medical Supplies Q1": "PROG-MOH-MEDSUPP",
    "Hospital Equipment Upgrade": "PROG-MOH-INFRA",
    "IT Infrastructure Phase II": "PROG-MOH-ICT",
}

PROGRAMS = [
    {
        "code": "PROG-MOH-MEDSUPP",
        "title": "Medical Supply Chain Management",
        "description": (
            "Strategic procurement and management of essential medicines and medical "
            "consumables to ensure uninterrupted supply across all MOH facilities."
        ),
        "order_index": 10,
        "weight": 1.0,
    },
    {
        "code": "PROG-MOH-INFRA",
        "title": "Healthcare Infrastructure Development",
        "description": (
            "Renovation, equipping, and commissioning of district and referral hospital "
            "facilities to improve access and quality of inpatient care."
        ),
        "order_index": 20,
        "weight": 1.0,
    },
    {
        "code": "PROG-MOH-ICT",
        "title": "Digital Health & ICT Infrastructure",
        "description": (
            "Deployment and upgrade of health information systems, connectivity, and "
            "ICT equipment to support data-driven healthcare delivery."
        ),
        "order_index": 30,
        "weight": 1.0,
    },
]

# ── Full KPI hierarchy definition ────────────────────────────────────────────
# Each program has: sub_programs → objectives → targets
# Target schema keys: title, code, mtype (measurement_type), direction
#   (measurement_direction), target_val, actual_val, is_complete, weight, unit
HIERARCHY = {
    "PROG-MOH-MEDSUPP": [
        {
            "sub_code": "SUB-MEDSUPP-001",
            "sub_title": "Medicines Procurement & Distribution",
            "objectives": [
                {
                    "title": "Essential Medicines Availability",
                    "code": "OBJ-MEDSUPP-001",
                    "weight": 1.0,
                    "targets": [
                        {
                            "title": "Achieve 85% medicines stock availability",
                            "code": "TGT-MEDSUPP-001",
                            "mtype": "Percentage",
                            "direction": "Higher is Better",
                            "target_val": 85.0,
                            "actual_val": 72.0,
                            "is_complete": 0,
                            "weight": 40.0,
                            "unit": "%",
                        },
                        {
                            "title": "Reduce stockout rate to 5%",
                            "code": "TGT-MEDSUPP-002",
                            "mtype": "Numeric",
                            "direction": "Lower is Better",
                            "target_val": 5.0,
                            "actual_val": 8.0,
                            "is_complete": 0,
                            "weight": 30.0,
                            "unit": "%",
                        },
                        {
                            "title": "Approve Q1 procurement plan",
                            "code": "TGT-MEDSUPP-003",
                            "mtype": "Milestone",
                            "direction": "Higher is Better",
                            "target_val": None,
                            "target_text": "Q1 plan approved by Finance",
                            "actual_val": 0.0,
                            "is_complete": 1,
                            "weight": 30.0,
                            "unit": "approval",
                        },
                    ],
                },
                {
                    "title": "Supplier Performance",
                    "code": "OBJ-MEDSUPP-002",
                    "weight": 1.0,
                    "targets": [
                        {
                            "title": "Achieve 90% on-time supplier delivery",
                            "code": "TGT-MEDSUPP-004",
                            "mtype": "Percentage",
                            "direction": "Higher is Better",
                            "target_val": 90.0,
                            "actual_val": 78.0,
                            "is_complete": 0,
                            "weight": 50.0,
                            "unit": "%",
                        },
                        {
                            "title": "Reduce procurement cycle time to 45 days",
                            "code": "TGT-MEDSUPP-005",
                            "mtype": "Numeric",
                            "direction": "Lower is Better",
                            "target_val": 45.0,
                            "actual_val": 52.0,
                            "is_complete": 0,
                            "weight": 50.0,
                            "unit": "days",
                        },
                    ],
                },
            ],
        },
    ],
    "PROG-MOH-INFRA": [
        {
            "sub_code": "SUB-INFRA-001",
            "sub_title": "District Hospital Renovation",
            "objectives": [
                {
                    "title": "Hospital Renovation Completion",
                    "code": "OBJ-INFRA-001",
                    "weight": 1.0,
                    "targets": [
                        {
                            "title": "Renovate 18 priority district hospitals",
                            "code": "TGT-INFRA-001",
                            "mtype": "Numeric",
                            "direction": "Higher is Better",
                            "target_val": 18.0,
                            "actual_val": 12.0,
                            "is_complete": 0,
                            "weight": 50.0,
                            "unit": "hospitals",
                        },
                        {
                            "title": "Construction completion rate at 70%",
                            "code": "TGT-INFRA-002",
                            "mtype": "Percentage",
                            "direction": "Higher is Better",
                            "target_val": 70.0,
                            "actual_val": 65.0,
                            "is_complete": 0,
                            "weight": 30.0,
                            "unit": "%",
                        },
                        {
                            "title": "Commissioning approval obtained",
                            "code": "TGT-INFRA-003",
                            "mtype": "Milestone",
                            "direction": "Higher is Better",
                            "target_val": None,
                            "target_text": "Commissioning certificate issued",
                            "actual_val": 0.0,
                            "is_complete": 0,
                            "weight": 20.0,
                            "unit": "approval",
                        },
                    ],
                },
                {
                    "title": "Medical Equipment Procurement",
                    "code": "OBJ-INFRA-002",
                    "weight": 1.0,
                    "targets": [
                        {
                            "title": "Procure 300 critical medical devices",
                            "code": "TGT-INFRA-004",
                            "mtype": "Numeric",
                            "direction": "Higher is Better",
                            "target_val": 300.0,
                            "actual_val": 280.0,
                            "is_complete": 0,
                            "weight": 60.0,
                            "unit": "devices",
                        },
                        {
                            "title": "Achieve 90% equipment budget absorption",
                            "code": "TGT-INFRA-005",
                            "mtype": "Percentage",
                            "direction": "Higher is Better",
                            "target_val": 90.0,
                            "actual_val": 85.0,
                            "is_complete": 0,
                            "weight": 40.0,
                            "unit": "%",
                        },
                    ],
                },
            ],
        },
    ],
    "PROG-MOH-ICT": [
        {
            "sub_code": "SUB-ICT-001",
            "sub_title": "HMIS & Connectivity",
            "objectives": [
                {
                    "title": "HMIS Deployment & Uptime",
                    "code": "OBJ-ICT-001",
                    "weight": 1.0,
                    "targets": [
                        {
                            "title": "Deploy HMIS in 50 health facilities",
                            "code": "TGT-ICT-001",
                            "mtype": "Numeric",
                            "direction": "Higher is Better",
                            "target_val": 50.0,
                            "actual_val": 35.0,
                            "is_complete": 0,
                            "weight": 40.0,
                            "unit": "facilities",
                        },
                        {
                            "title": "Achieve 95% system uptime",
                            "code": "TGT-ICT-002",
                            "mtype": "Percentage",
                            "direction": "Higher is Better",
                            "target_val": 95.0,
                            "actual_val": 92.0,
                            "is_complete": 0,
                            "weight": 35.0,
                            "unit": "%",
                        },
                        {
                            "title": "ICT infrastructure approval",
                            "code": "TGT-ICT-003",
                            "mtype": "Milestone",
                            "direction": "Higher is Better",
                            "target_val": None,
                            "target_text": "ICT infrastructure plan approved",
                            "actual_val": 0.0,
                            "is_complete": 1,
                            "weight": 25.0,
                            "unit": "approval",
                        },
                    ],
                },
            ],
        },
    ],
}


def _resolve_pe_moh() -> str | None:
    for code in ("PE-MOH", "MOH"):
        name = frappe.db.get_value("Procuring Entity", {"entity_code": code}, "name")
        if name:
            return name
    return None


def _delete_all_strategy_hierarchy() -> dict:
    """Hard-delete all plans and linked hierarchy via raw SQL; clear demand links."""
    deleted: dict[str, int] = {}

    # Null out demand strategy links first
    frappe.db.sql(
        "UPDATE `tabDemand` SET strategic_plan=NULL, program=NULL, sub_program=NULL, "
        "output_indicator=NULL, performance_target=NULL"
    )
    deleted["demands_unlinked"] = frappe.db.sql("SELECT ROW_COUNT()")[0][0]

    # Delete hierarchy bottom-up using raw SQL to bypass controller guards
    for doctype, table in (
        ("Strategy Target", "tabStrategy Target"),
        ("Strategy Objective", "tabStrategy Objective"),
        ("Sub Program", "tabSub Program"),
        ("Strategy Program", "tabStrategy Program"),
        ("Strategic Plan", "tabStrategic Plan"),
    ):
        if not frappe.db.exists("DocType", doctype):
            continue
        count = frappe.db.sql(f"SELECT COUNT(*) FROM `{table}`")[0][0]
        frappe.db.sql(f"DELETE FROM `{table}`")
        deleted[doctype] = count

    frappe.db.commit()
    return deleted


def _create_plan(pe: str, title: str, start_year: int, end_year: int, status: str, description: str) -> str:
    doc = frappe.get_doc({
        "doctype": "Strategic Plan",
        "strategic_plan_name": title,
        "procuring_entity": pe,
        "start_year": start_year,
        "end_year": end_year,
        "status": "Draft",
        "version_no": 1,
        "is_current_version": 1,
        "description": description,
    })
    doc.insert(ignore_permissions=True)
    if status != "Draft":
        frappe.db.sql("UPDATE `tabStrategic Plan` SET status=%s WHERE name=%s", (status, doc.name))
    return doc.name


def _create_program(plan_name: str, code: str, title: str, description: str, order_index: int, weight: float = 1.0) -> str:
    doc = frappe.get_doc({
        "doctype": "Strategy Program",
        "strategic_plan": plan_name,
        "program_code": code,
        "program_title": title,
        "description": description,
        "order_index": order_index,
        "weight": weight,
    })
    doc.insert(ignore_permissions=True)
    return doc.name


def _build_hierarchy(plan_name: str, prog_map: dict[str, str]) -> dict:
    """Create Sub Programs, Objectives, and Targets for plan_name (must be Draft)."""
    created = {"sub_programs": 0, "objectives": 0, "targets": 0}

    for prog_code, sub_program_defs in HIERARCHY.items():
        prog_name = prog_map.get(prog_code)
        if not prog_name:
            continue

        for sp_def in sub_program_defs:
            sp_doc = frappe.get_doc({
                "doctype": "Sub Program",
                "strategic_plan": plan_name,
                "program": prog_name,
                "title": sp_def["sub_title"],
                "sub_program_code": sp_def["sub_code"],
            })
            sp_doc.insert(ignore_permissions=True)
            sp_name = sp_doc.name
            created["sub_programs"] += 1

            for obj_def in sp_def["objectives"]:
                obj_doc = frappe.get_doc({
                    "doctype": "Strategy Objective",
                    "strategic_plan": plan_name,
                    "program": prog_name,
                    "sub_program": sp_name,
                    "objective_title": obj_def["title"],
                    "objective_code": obj_def["code"],
                    "order_index": 10,
                    "weight": obj_def.get("weight", 1.0),
                })
                obj_doc.insert(ignore_permissions=True)
                obj_name = obj_doc.name
                created["objectives"] += 1

                for tgt_def in obj_def["targets"]:
                    is_milestone = tgt_def["mtype"] in ("Milestone", "Boolean")
                    tgt_doc = frappe.get_doc({
                        "doctype": "Strategy Target",
                        "strategic_plan": plan_name,
                        "program": prog_name,
                        "objective": obj_name,
                        "target_title": tgt_def["title"],
                        "target_code": tgt_def["code"],
                        "measurement_type": tgt_def["mtype"],
                        "measurement_direction": tgt_def.get("direction", "Higher is Better"),
                        # Numeric fields — only for non-Milestone types
                        "target_value_numeric": None if is_milestone else tgt_def.get("target_val"),
                        "target_value_text": tgt_def.get("target_text") if is_milestone else None,
                        "target_unit": tgt_def.get("unit", ""),
                        "actual_value_numeric": None if is_milestone else tgt_def.get("actual_val", 0.0),
                        "actual_is_complete": tgt_def.get("is_complete", 0),
                        "weight": tgt_def.get("weight", 1.0),
                        "order_index": 10,
                        "target_period_type": "Annual",
                        "target_year": 2026,
                    })
                    tgt_doc.insert(ignore_permissions=True)
                    created["targets"] += 1

    return created


def _link_demands(plan_name: str, program_name: str, title_prefix: str) -> int:
    all_demands = frappe.db.sql(
        "SELECT name FROM `tabDemand` WHERE title LIKE %(prefix)s",
        {"prefix": f"{title_prefix}%"},
        as_dict=True,
    )
    names = [r.name for r in all_demands]
    if not names:
        return 0
    frappe.db.sql(
        "UPDATE `tabDemand` SET strategic_plan=%(plan)s, program=%(prog)s "
        "WHERE name IN %(names)s",
        {"plan": plan_name, "prog": program_name, "names": tuple(names)},
    )
    return len(names)


def run() -> dict:
    frappe.set_user("Administrator")

    pe = _resolve_pe_moh()
    if not pe:
        return {"ok": False, "error": "No Procuring Entity with entity_code PE-MOH or MOH found."}

    # Step 1 — wipe everything
    deleted = _delete_all_strategy_hierarchy()

    # Step 2 — Plan 1: Main Active plan (keep Draft while building hierarchy)
    plan1 = _create_plan(
        pe=pe,
        title="Ministry of Health Strategic Plan 2026\u20132030",
        start_year=2026,
        end_year=2030,
        status="Draft",
        description=(
            "Five-year strategic plan anchoring MOH procurement activities across "
            "medical supply chain, healthcare infrastructure, and digital health. "
            "Covers FY 2026/27 through FY 2029/30."
        ),
    )

    # Programs under Plan 1 (plan must be Draft)
    prog_map: dict[str, str] = {}
    for p in PROGRAMS:
        prog_name = _create_program(
            plan_name=plan1,
            code=p["code"],
            title=p["title"],
            description=p["description"],
            order_index=p["order_index"],
            weight=p.get("weight", 1.0),
        )
        prog_map[p["code"]] = prog_name

    # Full KPI hierarchy: sub-programs → objectives → targets (plan still Draft)
    hierarchy_created = _build_hierarchy(plan1, prog_map)

    # Promote to Active now that hierarchy is complete
    frappe.db.sql("UPDATE `tabStrategic Plan` SET status='Active' WHERE name=%s", plan1)

    # Link demands to programs
    demand_linked: dict[str, int] = {}
    for demand_prefix, prog_code in DEMAND_PROGRAM_MAP.items():
        prog_name = prog_map[prog_code]
        n = _link_demands(plan1, prog_name, demand_prefix)
        demand_linked[demand_prefix] = n

    # Step 3 — Plan 2: Archived (historical, no demands)
    plan2 = _create_plan(
        pe=pe,
        title="Public Health Promotion Strategy 2024\u20132028",
        start_year=2024,
        end_year=2028,
        status="Archived",
        description=(
            "Completed strategic plan covering preventive health, community outreach, "
            "and immunisation programmes. Superseded by the 2026–2030 plan."
        ),
    )

    # Step 4 — Plan 3: Submitted (awaiting approval, no demands)
    plan3 = _create_plan(
        pe=pe,
        title="Primary Health Care Expansion Plan 2026\u20132031",
        start_year=2026,
        end_year=2031,
        status="Submitted",
        description=(
            "Proposed five-year plan to expand primary health care coverage, "
            "strengthen community health worker networks, and reduce maternal mortality. "
            "Awaiting ministerial approval."
        ),
    )

    frappe.db.commit()

    return {
        "ok": True,
        "procuring_entity": pe,
        "deleted": deleted,
        "plans_created": {"active": plan1, "archived": plan2, "submitted": plan3},
        "programs_created": prog_map,
        "hierarchy_created": hierarchy_created,
        "demands_linked": demand_linked,
        "total_demands_linked": sum(demand_linked.values()),
    }
