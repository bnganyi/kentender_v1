# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-012 — WORKS master seed full runner with spec §20 summary output.

## Goal

Run all upstream seeds (R2-004 through R2-011/R2-011A) in the §19.2 order and return the
canonical spec §20 summary including:

* counts per record category (``created_or_updated``)
* evidence timeline event count (``evidence_events``)
* aggregated ``warnings`` from all stages
* ``status``, ``ok``, ``checkpoint``, ``current_stage``, ``next_action``

## Spec §20 counts — canonical constants for this master seed

| Category | Base | Opening |
|---|---|---|
| procuring_entities | 1 | — |
| strategy_records | 4 | — |
| budget_records | 2 | — |
| demand_records | 3 | — |
| planning_records | 4 | — |
| std_reference_records | 3 | — |
| tm2_reference_records | 5 | — |
| journey_records | 1 | — |
| journey_steps | 12 | — |
| handoff_cards | 7 | 9 |
| evidence_events | 8 | 10 |

``demand_records = 3`` counts: Demand header + Demand Item + Demand Approval Record (spec §10.3).
``planning_records = 4`` counts: Procurement Plan + Planning Inclusion + Package + Package Line.
``std_reference_records = 3`` counts: STD Template + STD Template Version + STD Applicability Profile (§12).
``tm2_reference_records = 5`` counts: TM2 Tender + Timeline + STD Binding + Publication Record + Addendum (§13.1–13.5).
``evidence_events`` = handoff card count + 1 (addendum event in §17 shares a handoff code with PUBCERT).

These are **spec constants**, not runtime queries, because several spec entities (Demand Approval,
STD Template Version, STD Applicability Profile, Publication Record, Addendum) are embedded in
parent documents or represented by handoff cards rather than independent DocTypes.
"""

from __future__ import annotations

from typing import Any, Final

import frappe

from kentender_core.seeds._common import ensure_currency_kes, ensure_moh_entity_permission_aliases, ensure_procuring_entity
from kentender_core.seeds import constants as C
from kentender_strategy.seeds.works_master_strategy_hierarchy import (
    upsert_works_master_strategy_hierarchy,
)
from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_procurement.procurement_planning.seeds.works_master_planning_seed import (
    upsert_works_master_planning,
)
from kentender_procurement.tender_management.seeds.works_master_std_seed import (
    upsert_works_master_std,
)
from kentender_procurement.tender_management.seeds.works_master_tender_seed import (
    upsert_works_master_tender,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    BASE_HANDOFF_CODES,
    JOURNEY_CODE,
    OPENING_HANDOFF_CODES,
)

# ── Spec §20 canonical count constants ───────────────────────────────────────

_PE_CODE: Final[str] = "PE-MOH"
_PE_DISPLAY: Final[str] = "Ministry of Health"

_SPEC_COUNTS_BASE: Final[dict[str, int]] = {
    "procuring_entities": 1,
    "strategy_records": 4,
    "budget_records": 2,
    "demand_records": 3,
    "planning_records": 4,
    "std_reference_records": 3,
    "tm2_reference_records": 5,
    "journey_records": 1,
    "journey_steps": 12,
    "handoff_cards": 7,
    "evidence_events": 8,
}

_SPEC_COUNTS_OPENING: Final[dict[str, int]] = {
    "handoff_cards": 9,
    "evidence_events": 10,
}

_SUPPORTED_CHECKPOINTS: Final[frozenset[str]] = frozenset({"TENDER_PUBLISHED", "OPENING_READY"})


def _summary_counts(*, include_opening: bool) -> dict[str, int]:
    """Return the spec §20 canonical counts for the WORKS master seed summary.

    The base counts are fixed constants defined in the spec.  Opening checkpoint
    overrides the two fields that grow (``handoff_cards``, ``evidence_events``).

    Dynamic counts (``journey_steps``, ``handoff_cards``) are queried from the DB
    so the output is accurate even on idempotent re-runs.  All other categories use
    spec constants because several spec entities are embedded in parent documents or
    represented only by handoff cards rather than standalone DocType rows.
    """
    # Journey steps: query actual child row count
    jrn_steps = 0
    if frappe.db.exists("Procurement Journey", JOURNEY_CODE):
        jrn_steps = int(
            frappe.db.count("Procurement Journey Step", filters={"parent": JOURNEY_CODE}) or 0
        )

    # Handoff cards: count only the known master codes that exist
    expected_codes = list(BASE_HANDOFF_CODES) + (
        list(OPENING_HANDOFF_CODES) if include_opening else []
    )
    cards = sum(1 for c in expected_codes if frappe.db.exists("Procurement Handoff Card", c))

    # Evidence events = handoff cards + 1 (addendum event from §17 row 8 shares PUBCERT code)
    ev = cards + 1 if cards > 0 else 0

    counts = {**_SPEC_COUNTS_BASE, "journey_steps": jrn_steps, "handoff_cards": cards, "evidence_events": ev}
    return counts


def run_works_master_full_seed(
    *, checkpoint: str = "TENDER_PUBLISHED", reset: bool = False
) -> dict[str, Any]:
    """Run all WORKS master seeds in spec §19.2 order and return the §20 summary.

    :param checkpoint: ``TENDER_PUBLISHED`` (default) or ``OPENING_READY``.
    :param reset: Passed to the PLC loader to force re-seed of master PLC rows.
    :returns: Spec §20-compliant summary dict.
    """
    cp = (checkpoint or "TENDER_PUBLISHED").strip().upper()
    if cp not in _SUPPORTED_CHECKPOINTS:
        return {
            "ok": False,
            "error_code": "UNSUPPORTED_CHECKPOINT",
            "message": "Supported checkpoints are TENDER_PUBLISHED and OPENING_READY.",
            "checkpoint": cp,
        }

    frappe.set_user("Administrator")
    warnings: list[str] = []
    include_opening = cp == "OPENING_READY"

    # ── Step 1-2: currency + procuring entity ────────────────────────────────
    ensure_currency_kes()
    ensure_procuring_entity(_PE_CODE, _PE_DISPLAY)
    for email, _full_name, _role, _dept in C.SEED_USERS:
        if frappe.db.exists("User", email):
            ensure_moh_entity_permission_aliases(email, C.ENTITY_MOH)

    # ── Step 3: strategy ─────────────────────────────────────────────────────
    strat = upsert_works_master_strategy_hierarchy()
    if not strat.get("ok"):
        return {**strat, "stage_failed": "strategy", "warnings": warnings}
    warnings.extend(strat.get("warnings") or [])

    # ── Step 4: budget ───────────────────────────────────────────────────────
    bud = upsert_works_master_budget()
    if not bud.get("ok"):
        return {**bud, "stage_failed": "budget", "warnings": warnings}
    warnings.extend(bud.get("warnings") or [])

    # ── Step 5-6: demand (retired with DIA preparatory teardown) ─────────────
    dem = {
        "ok": False,
        "skipped": True,
        "reason": "DEMAND_MODULE_RETIRED",
        "message": (
            "Demand Intake retired pending Demands MVP-1 rebuild; "
            "WORKS demand seed stage skipped."
        ),
    }
    warnings.append(dem["message"])
    return {**dem, "stage_failed": "demand", "warnings": warnings}

    # ── Step 7-9: planning ───────────────────────────────────────────────────
    pln = upsert_works_master_planning()
    if not pln.get("ok"):
        return {**pln, "stage_failed": "planning", "warnings": warnings}
    warnings.extend(pln.get("warnings") or [])

    # ── Step 10: STD references ──────────────────────────────────────────────
    std = upsert_works_master_std()
    if not std.get("ok"):
        return {**std, "stage_failed": "std", "warnings": warnings}
    warnings.extend(std.get("warnings") or [])

    # ── Step 11: TM2 tender ──────────────────────────────────────────────────
    tm2 = upsert_works_master_tender()
    if not tm2.get("ok"):
        return {**tm2, "stage_failed": "tender", "warnings": warnings}
    warnings.extend(tm2.get("warnings") or [])

    # ── Steps 12-14: PLC (journey + steps + handoffs) ────────────────────────
    from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
        load_procurement_lifecycle_works_master,
    )
    plc = load_procurement_lifecycle_works_master(reset=reset, checkpoint=cp)
    if not plc.get("ok"):
        return {**plc, "stage_failed": "plc", "warnings": warnings}
    warnings.extend(plc.get("warnings") or [])

    # ── Step 17: summary output ──────────────────────────────────────────────
    counts = _summary_counts(include_opening=include_opening)

    summary: dict[str, Any] = {
        "ok": True,
        "checkpoint": cp,
        "journey_code": JOURNEY_CODE,
        "master_scenario": "District Hospital Renovation Works",
        "created_or_updated": counts,
        "current_stage": "Tender Published" if cp == "TENDER_PUBLISHED" else "Opening Ready",
        "next_action": (
            "Await tender closing / prepare bid opening readiness after submission deadline."
            if cp == "TENDER_PUBLISHED"
            else "Conduct bid opening session using the opening register rules."
        ),
        "warnings": warnings,
        "status": "loaded",
    }
    return summary
