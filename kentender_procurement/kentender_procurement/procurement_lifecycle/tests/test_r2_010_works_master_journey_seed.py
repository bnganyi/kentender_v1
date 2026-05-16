# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R2-010 — WORKS master journey seed tests (spec §14–15).

Tests:
  1. SEED-TEST-R2-010-001 — Seed creates JRN-MOH-2026-001 with all spec §14 header fields.
  2. SEED-TEST-R2-010-002 — Idempotent: second run returns ok=True and no duplicate Journey.
  3. SEED-TEST-R2-010-003 — 12 journey steps exist with correct step_keys per spec §15.
  4. SEED-TEST-R2-010-004 — Key spec §14 ref fields populated (strategy, budget, demand,
     plan, package, tender, std_version).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r2_010_works_master_journey_seed
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cint

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_strategy.seeds.works_master_strategy_hierarchy import (
    upsert_works_master_strategy_hierarchy,
)
from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_procurement.demand_intake.seeds.works_master_demand_seed import (
    upsert_works_master_demand,
)
from kentender_procurement.procurement_planning.seeds.works_master_planning_seed import (
    upsert_works_master_planning,
)
from kentender_procurement.tender_management.seeds.works_master_std_seed import (
    upsert_works_master_std,
)
from kentender_procurement.tender_management.seeds.works_master_tender_seed import (
    upsert_works_master_tender,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import (
    upsert_works_master_journey,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    JOURNEY_CODE,
)
from kentender_procurement.procurement_lifecycle.works_seed_step_contract import (
    WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER,
)

_PE_CODE = "PE-MOH"
_PE_NAME_DISPLAY = "Ministry of Health"


def _clean_journey() -> None:
    """Remove JRN-MOH-2026-001 and its handoff cards (safe reset via loader)."""
    from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
        load_procurement_lifecycle_works_master,
    )
    load_procurement_lifecycle_works_master(reset=True, checkpoint="OPENING_READY")


class TestR2010WorksMasterJourneySeed(IntegrationTestCase):
    """R2-010 — Journey seed alignment (spec §14–15)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        cls.pe_name = ensure_procuring_entity(_PE_CODE, _PE_NAME_DISPLAY)

        # R2-004: strategy chain
        strat = upsert_works_master_strategy_hierarchy()
        assert strat.get("ok"), f"Strategy prerequisite failed: {strat}"

        # R2-005: budget chain
        budget = upsert_works_master_budget()
        assert budget.get("ok"), f"Budget prerequisite failed: {budget}"

        # R2-006: demand
        demand = upsert_works_master_demand()
        assert demand.get("ok"), f"Demand prerequisite failed: {demand}"

        # R2-007: planning
        planning = upsert_works_master_planning()
        assert planning.get("ok"), f"Planning prerequisite failed: {planning}"

        # R2-008: STD template
        std = upsert_works_master_std()
        assert std.get("ok"), f"STD prerequisite failed: {std}"

        # R2-009: TM2 Tender
        tender = upsert_works_master_tender()
        assert tender.get("ok"), f"Tender prerequisite failed: {tender}"

    def tearDown(self):
        _clean_journey()

    # ── Test 1: spec §14 header fields ────────────────────────────────────────
    def test_001_fresh_seed_creates_journey_with_spec14_fields(self):
        """SEED-TEST-R2-010-001: Seed creates JRN-MOH-2026-001 with all spec §14 header fields."""
        out = upsert_works_master_journey()

        self.assertTrue(out.get("ok"), f"Seed returned error: {out}")
        self.assertIn(out.get("action"), ("created",))
        self.assertEqual(out["journey_code"], JOURNEY_CODE)

        # Document must exist
        self.assertTrue(
            frappe.db.exists("Procurement Journey", JOURNEY_CODE),
            "Procurement Journey JRN-MOH-2026-001 must exist",
        )

        j = frappe.get_doc("Procurement Journey", JOURNEY_CODE)

        # §14 header assertions
        self.assertEqual(j.journey_title, "District Hospital Renovation Works")
        self.assertEqual(j.procuring_entity_code, "PE-MOH")
        self.assertEqual(j.fiscal_year, "2026/2027")
        self.assertEqual(j.procurement_category, "Works")
        self.assertEqual(j.procurement_method, "Open Tender")
        self.assertEqual(j.current_stage_label, "Tender Published")
        self.assertEqual(j.current_status_category, "Completed")
        self.assertEqual(j.current_owner_module, "Tender Management")
        self.assertEqual(cint(j.blocker_count), 0)
        self.assertEqual(cint(j.critical_blocker_count), 0)
        self.assertEqual(cint(j.is_master_seed), 1)

    # ── Test 2: idempotency ───────────────────────────────────────────────────
    def test_002_idempotent_second_run_no_duplicate(self):
        """SEED-TEST-R2-010-002: Running twice returns ok=True and exactly one Journey."""
        first = upsert_works_master_journey()
        self.assertTrue(first.get("ok"), f"First run error: {first}")

        second = upsert_works_master_journey()
        self.assertTrue(second.get("ok"), f"Second run error: {second}")
        self.assertEqual(second.get("action"), "existing", "Second run must report 'existing'")
        self.assertEqual(second["journey_code"], JOURNEY_CODE)

        count = frappe.db.sql(
            "SELECT COUNT(*) FROM `tabProcurement Journey` WHERE journey_code=%s",
            (JOURNEY_CODE,),
        )[0][0]
        self.assertEqual(count, 1, "Expected exactly one Procurement Journey with this code")

    # ── Test 3: 12 steps with correct step_keys ───────────────────────────────
    def test_003_journey_has_12_steps_matching_spec15(self):
        """SEED-TEST-R2-010-003: Journey has 12 ordered steps per spec §15."""
        upsert_works_master_journey()

        j = frappe.get_doc("Procurement Journey", JOURNEY_CODE)
        steps = sorted(j.steps or [], key=lambda r: r.step_order)

        self.assertEqual(
            len(steps),
            len(WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER),
            f"Expected {len(WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER)} steps, got {len(steps)}",
        )

        actual_keys = tuple(r.step_key for r in steps)
        self.assertEqual(
            actual_keys,
            WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER,
            "Step keys must match WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER in order",
        )

        # Completed steps 1–7 have handoff codes; steps 8–12 are Not Started
        for row in steps:
            if row.step_key in (
                "strategy",
                "budget",
                "demand",
                "planning_inclusion",
                "package_release",
                "std_readiness",
                "tender_publication",
            ):
                self.assertEqual(
                    row.status_category,
                    "Completed" if row.step_key != "package_release" else "Handed Off",
                    f"Step {row.step_key!r} must be Completed/Handed Off",
                )
                self.assertTrue(row.handoff_code, f"Step {row.step_key!r} must have a handoff_code")
            else:
                self.assertEqual(
                    row.status_category,
                    "Not Started",
                    f"Step {row.step_key!r} must be Not Started",
                )

    # ── Test 4: ref fields populated per spec §14 ─────────────────────────────
    def test_004_spec14_ref_fields_populated(self):
        """SEED-TEST-R2-010-004: All spec §14 ref fields are populated correctly."""
        upsert_works_master_journey()

        j = frappe.get_doc("Procurement Journey", JOURNEY_CODE)

        self.assertEqual(j.strategy_ref, "OBJ-MOH-HOSP-RENOV", "strategy_ref §14")
        self.assertEqual(j.budget_line_ref, "BUD-MOH-INFRA-2026-001", "budget_line_ref §14")
        self.assertEqual(j.demand_ref, "DEM-MOH-2026-001", "demand_ref §14")
        self.assertEqual(j.procurement_plan_ref, "PLAN-MOH-2026", "procurement_plan_ref §14")
        self.assertEqual(j.procurement_package_ref, "PKG-MOH-2026-001", "procurement_package_ref §14")
        self.assertEqual(
            j.std_template_version_ref,
            "STDTV-WORKS-BUILDING-CIVIL-APR2022",
            "std_template_version_ref §14",
        )
        self.assertEqual(j.tm2_tender_ref, "TND-MOH-2026-001", "tm2_tender_ref §14")
        self.assertEqual(
            j.publication_snapshot_ref,
            "PUBSNAP-TND-MOH-2026-001-V2",
            "publication_snapshot_ref §14",
        )
