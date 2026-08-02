"""Budget Hub demo seed — purge junk + create clean 3-entity set.

Idempotent.  Safe to re-run.

Keeps:
  BUDGET-MOH-2026 / BUD-MOH-INFRA-2026-001  (WORKS master chain — planning depends on it)

Deletes:
  • Every Budget row whose name ≠ BUD-PE-MOH-2026-.0085 (the canonical WORKS record)
  • Every Budget Line row whose name ≠ BUD-MOH-INFRA-2026-001
  • Every Budget Reservation (all existing ones are orphaned Released records)

Creates (idempotent):
  PE-DOE  Dept. of Education    → BUDGET-DOE-2026  (565 M, 92% consumed)
  PE-SDT  State Dept Transport  → BUDGET-SDT-2026  (3 353 M, 15% consumed)
  + supporting Funding Sources, Strategic Plans, Strategy Programs, Budget Lines

Run::
    bench --site kentender.midas.com execute \\
        kentender_budget.seeds.seed_budget_hub_demo.run
"""
from __future__ import annotations
from typing import Any

import frappe
from frappe.utils import now_datetime

# ── Canonical records to preserve ───────────────────────────────────────────
_KEEP_BUDGET_NAMES = frozenset({"BUDGET-MOH-2026", "BUDGET-DOE-2026", "BUDGET-SDT-2026"})
_KEEP_LINE_CODES = frozenset({"BUD-MOH-INFRA-2026-001", "BUD-DOE-CAP-2026-001", "BUD-SDT-ROAD-2026-001"})

# ── Demo entity definitions ──────────────────────────────────────────────────
ENTITIES = [
    {
        "entity_code": "PE-DOE",
        "entity_name": "Department of Education",
        "plan_title": "Dept. of Education Strategic Plan 2026–2030",
        "program_code": "PROG-DOE-CAP",
        "program_title": "Capitation & Learning Resources",
        "budget_name": "BUDGET-DOE-2026",
        "budget_title": "Dept. of Education Budget FY 2026/2027",
        "funding_source": "Government of Kenya Recurrent Budget",
        "funding_source_code": "GKE-RECURRENT",
        "funding_source_type": "Exchequer",
        "line_code": "BUD-DOE-CAP-2026-001",
        "line_title": "Primary School Capitation Grants FY 2026/2027",
        "amount_allocated": 565_000_000.0,
        # 80% committed + 12% reserved = 92% consumed; available ≈ 8% = 45.2M
        "amount_reserved": 67_800_000.0,
        "amount_committed": 452_000_000.0,
        "amount_consumed": 0.0,
        "status": "Active",
        "line_status": "Active",
        "order_index": 2,
    },
    {
        "entity_code": "PE-SDT",
        "entity_name": "State Department for Transport",
        "plan_title": "State Dept. Transport Strategic Plan 2026–2030",
        "program_code": "PROG-SDT-ROAD",
        "program_title": "Rural Access Roads Development",
        "budget_name": "BUDGET-SDT-2026",
        "budget_title": "State Dept. Transport Budget FY 2026/2027",
        "funding_source": "Government of Kenya Development Budget",
        "funding_source_code": "GKE-DEVT",
        "funding_source_type": "Exchequer",
        "line_code": "BUD-SDT-ROAD-2026-001",
        "line_title": "Rural Access Roads Construction & Rehabilitation",
        "amount_allocated": 3_352_941_176.0,
        # 10% committed + 5% reserved = 15% consumed; available ≈ 85% = 2.85B
        "amount_reserved": 167_647_059.0,
        "amount_committed": 335_294_118.0,
        "amount_consumed": 0.0,
        "status": "Active",
        "line_status": "Active",
        "order_index": 3,
    },
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _ensure_currency_kes() -> None:
    if not frappe.db.exists("Currency", "KES"):
        frappe.get_doc({
            "doctype": "Currency", "currency_name": "KES",
            "symbol": "KES", "enabled": 1,
        }).insert(ignore_permissions=True)


def _ensure_pe(entity_code: str, entity_name: str) -> str:
    existing = frappe.db.get_value("Procuring Entity", {"entity_code": entity_code}, "name")
    if existing:
        return existing
    doc = frappe.get_doc({
        "doctype": "Procuring Entity",
        "entity_code": entity_code,
        "entity_name": entity_name,
    })
    doc.insert(ignore_permissions=True)
    return doc.name


def _ensure_funding_source(title: str, code: str, source_type: str) -> str:
    if frappe.db.exists("Funding Source", title):
        return title
    frappe.get_doc({
        "doctype": "Funding Source",
        "title": title,
        "source_code": code,
        "source_type": source_type,
        "is_active": 1,
    }).insert(ignore_permissions=True)
    return title


def _ensure_budget(pe_name: str, cfg: dict) -> tuple[str, bool]:
    existing = frappe.db.get_value(
        "Budget",
        {"budget_name": cfg["budget_name"], "procuring_entity": pe_name, "fiscal_year": 2026},
        "name",
    )
    if existing:
        cur = frappe.db.get_value("Budget", existing, "status")
        if cur != cfg["status"]:
            frappe.db.set_value("Budget", existing, "status", cfg["status"])
        return existing, False

    _ensure_currency_kes()
    doc = frappe.get_doc({
        "doctype": "Budget",
        "budget_name": cfg["budget_name"],
        "procuring_entity": pe_name,
        "fiscal_year": 2026,
        "currency": "KES",
        "total_budget_amount": cfg["amount_allocated"],
        "status": "Draft",
        "version_no": 1,
        "is_current_version": 1,
        "order_index": cfg["order_index"],
        "notes": f"Budget Hub demo seed. Entity: {cfg['entity_name']}. FY 2026/2027.",
    })
    doc.insert(ignore_permissions=True)
    frappe.db.set_value("Budget", doc.name, "status", cfg["status"])
    return doc.name, True


def _ensure_budget_line(pe_name: str, budget_doc: str, funding_source: str, cfg: dict) -> tuple[str, bool]:
    if frappe.db.exists("Budget Line", cfg["line_code"]):
        # Relink to the canonical budget if it was recreated under a new doc name
        current_budget = frappe.db.get_value("Budget Line", cfg["line_code"], "budget")
        if current_budget != budget_doc and frappe.db.exists("Budget", budget_doc):
            frappe.db.set_value("Budget Line", cfg["line_code"], "budget", budget_doc, update_modified=False)
        return cfg["line_code"], False

    _ensure_currency_kes()
    doc = frappe.get_doc({
        "doctype": "Budget Line",
        "budget_line_code": cfg["line_code"],
        "budget_line_name": cfg["line_title"],
        "budget": budget_doc,
        "procuring_entity": pe_name,
        "fiscal_year": 2026,
        "amount_allocated": cfg["amount_allocated"],
        "amount_reserved": cfg["amount_reserved"],
        "amount_committed": cfg["amount_committed"],
        "amount_consumed": cfg["amount_consumed"],
        "currency": "KES",
        "funding_source": funding_source,
        "is_active": 1,
        "line_status": cfg["line_status"],
    })
    doc.insert(ignore_permissions=True)
    return doc.name, True


# ── Purge ────────────────────────────────────────────────────────────────────

def _purge_junk() -> dict[str, int]:
    counts = {"budgets": 0, "lines": 0, "reservations": 0}

    # Delete Budget Reservations — direct DB to skip any controller checks
    res_names = frappe.get_all("Budget Reservation", pluck="name")
    for r in res_names:
        frappe.db.sql("DELETE FROM `tabBudget Reservation` WHERE name = %s", r)
        counts["reservations"] += 1

    # Delete junk Budget Lines — keep only the three canonical lines
    frappe.flags.budget_line_force_delete = True
    try:
        all_lines = frappe.db.sql(
            "SELECT name, budget_line_code FROM `tabBudget Line`", as_dict=1
        )
        for line in all_lines:
            if line.budget_line_code in _KEEP_LINE_CODES:
                continue
            frappe.db.sql("DELETE FROM `tabBudget Line` WHERE name = %s", line.name)
            counts["lines"] += 1
    finally:
        frappe.flags.budget_line_force_delete = False

    # Delete junk Budgets — keep by budget_name (business code), not doc name
    all_budgets = frappe.db.sql(
        "SELECT name, budget_name FROM `tabBudget`", as_dict=1
    )
    for bud in all_budgets:
        if bud.budget_name in _KEEP_BUDGET_NAMES:
            continue
        frappe.db.sql("DELETE FROM `tabBudget` WHERE name = %s", bud.name)
        counts["budgets"] += 1

    frappe.db.commit()
    return counts


# ── Public entry ─────────────────────────────────────────────────────────────

def run() -> dict[str, Any]:
    """Purge junk data and seed clean 3-entity Budget Hub demo set."""
    results: dict[str, Any] = {"ok": True, "purged": {}, "created": []}

    # 1. Purge
    results["purged"] = _purge_junk()

    # 2. Ensure GKE Development Budget funding source (shared by MoH too)
    _ensure_funding_source(
        "Government of Kenya Development Budget", "GKE-DEVT", "Exchequer"
    )

    # 3. Create Education + Transport entities (no Strategy docs — MVP-1 teardown)
    for cfg in ENTITIES:
        pe_name = _ensure_pe(cfg["entity_code"], cfg["entity_name"])
        fs_name = _ensure_funding_source(
            cfg["funding_source"], cfg["funding_source_code"], cfg["funding_source_type"]
        )
        budget_doc, b_created = _ensure_budget(pe_name, cfg)
        line_doc, l_created = _ensure_budget_line(pe_name, budget_doc, fs_name, cfg)
        results["created"].append({
            "entity": cfg["entity_code"],
            "budget": cfg["budget_name"],
            "line": cfg["line_code"],
            "budget_created": b_created,
            "line_created": l_created,
        })

    frappe.db.commit()
    return results
