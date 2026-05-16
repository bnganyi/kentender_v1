# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R2-007 — WORKS master procurement planning seed tests (spec §11 / VAL-SEED-007, 008, 009).

Tests:
  1. SEED-TEST-R2-007-001 — Fresh seed creates Plan and Package with correct spec values.
  2. SEED-TEST-R2-007-002 — Idempotent: second run does not duplicate records.
  3. SEED-TEST-R2-007-003 — Missing PE returns MISSING_PROCURING_ENTITY error code.
  4. SEED-TEST-R2-007-004 — Missing Demand returns MISSING_DEMAND error code.
  5. SEED-TEST-R2-007-005 — Missing Budget Line returns MISSING_BUDGET_LINE error code.
  6. SEED-TEST-R2-007-006 — VAL-SEED-007/008/009: Plan exists, package line links demand +
     budget line, package status is Released to Tender.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_planning.tests.test_r2_007_works_master_planning_seed
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_strategy.seeds.works_master_strategy_hierarchy import (
    upsert_works_master_strategy_hierarchy,
)
from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_procurement.demand_intake.seeds.works_master_demand_seed import (
    upsert_works_master_demand,
)
from kentender_procurement.procurement_planning.seeds.works_master_planning_seed import (
    BUDGET_LINE_CODE,
    DEMAND_ID,
    ESTIMATED_VALUE,
    FISCAL_YEAR,
    PKG_CODE,
    PKG_LINE_CODE,
    PKG_NAME,
    PLAN_CODE,
    PLAN_NAME,
    upsert_works_master_planning,
)

_PE_CODE = "PE-MOH"
_PE_NAME_DISPLAY = "Ministry of Health"


def _clean_planning() -> None:
    """Remove seed planning records in dependency order (line → package → plan)."""
    # Package Line
    ln_name = frappe.db.get_value(
        "Procurement Package Line", {"package_line_code": PKG_LINE_CODE}, "name"
    )
    if ln_name:
        frappe.flags.skip_package_line_rollup = True
        try:
            frappe.delete_doc(
                "Procurement Package Line", ln_name, force=True, ignore_permissions=True
            )
        finally:
            frappe.flags.skip_package_line_rollup = False

    # Package (use direct SQL in case status guard triggers)
    if frappe.db.exists("Procurement Package", PKG_CODE):
        frappe.db.delete("Procurement Package", {"name": PKG_CODE})

    # Plan
    if frappe.db.exists("Procurement Plan", PLAN_CODE):
        frappe.db.delete("Procurement Plan", {"name": PLAN_CODE})


class TestR2007WorksMasterPlanningSeed(IntegrationTestCase):
    """R2-007 — Planning seed alignment (spec §11)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        cls.pe_name = ensure_procuring_entity(_PE_CODE, _PE_NAME_DISPLAY)

        # Ensure §8 strategy chain (R2-004 prerequisite).
        strat = upsert_works_master_strategy_hierarchy()
        assert strat.get("ok"), f"Strategy prerequisite failed: {strat}"

        # Ensure §9 budget chain (R2-005 prerequisite).
        budget = upsert_works_master_budget()
        assert budget.get("ok"), f"Budget prerequisite failed: {budget}"

        # Ensure §10 demand (R2-006 prerequisite).
        demand = upsert_works_master_demand()
        assert demand.get("ok"), f"Demand prerequisite failed: {demand}"

        # Resolve canonical docnames for VAL assertions
        cls.demand_name = frappe.db.get_value(
            "Demand", {"demand_id": DEMAND_ID}, "name"
        )
        cls.budget_line_name = frappe.db.get_value(
            "Budget Line", {"budget_line_code": BUDGET_LINE_CODE}, "name"
        )
        assert cls.demand_name, "Demand DEM-MOH-2026-001 must exist after R2-006 setup"
        assert cls.budget_line_name, "Budget Line BUD-MOH-INFRA-2026-001 must exist after R2-005 setup"

    def tearDown(self):
        _clean_planning()

    # ── Test 1: fresh seed shape and values ───────────────────────────────────
    def test_001_fresh_seed_creates_plan_and_package_with_spec_values(self):
        """SEED-TEST-R2-007-001: First run creates Plan and Package with correct spec values."""
        out = upsert_works_master_planning()

        self.assertTrue(out.get("ok"), f"Seed returned error: {out}")
        self.assertFalse(out.get("idempotent"))
        self.assertTrue(out.get("plan_created"))
        self.assertTrue(out.get("package_created"))

        # --- Plan assertions ---
        self.assertEqual(out["plan_code"], PLAN_CODE)
        plan = frappe.get_doc("Procurement Plan", PLAN_CODE)
        self.assertEqual(plan.plan_code, PLAN_CODE)
        self.assertEqual(plan.plan_name, PLAN_NAME)
        self.assertEqual(plan.fiscal_year, FISCAL_YEAR)
        self.assertEqual(plan.status, "Approved")
        self.assertEqual(plan.currency, "KES")
        self.assertIsNotNone(plan.procuring_entity)
        self.assertIsNotNone(plan.approved_by)
        self.assertIsNotNone(plan.approved_at)

        # --- Package assertions ---
        self.assertEqual(out["package_code"], PKG_CODE)
        pkg = frappe.get_doc("Procurement Package", PKG_CODE)
        self.assertEqual(pkg.package_code, PKG_CODE)
        self.assertEqual(pkg.package_name, PKG_NAME)
        self.assertEqual(pkg.plan_id, PLAN_CODE)
        self.assertEqual(pkg.procurement_method, "Open Tender")
        self.assertEqual(pkg.contract_type, "Fixed Price")
        self.assertEqual(pkg.currency, "KES")
        self.assertEqual(pkg.status, "Released to Tender")
        self.assertIsNotNone(pkg.released_to_tender_at)
        self.assertIsNotNone(pkg.risk_profile_id)
        self.assertIsNotNone(pkg.kpi_profile_id)
        self.assertIsNotNone(pkg.decision_criteria_profile_id)
        self.assertIsNotNone(pkg.vendor_management_profile_id)

        # --- Package Line assertions ---
        self.assertTrue(out.get("package_line_created"))
        ln_name = frappe.db.get_value(
            "Procurement Package Line", {"package_line_code": PKG_LINE_CODE}, "name"
        )
        self.assertIsNotNone(ln_name, "Package Line must exist")
        ln = frappe.get_doc("Procurement Package Line", ln_name)
        self.assertEqual(ln.package_id, PKG_CODE)
        self.assertEqual(ln.demand_id, self.demand_name)
        self.assertEqual(ln.budget_line_id, self.budget_line_name)
        self.assertAlmostEqual(flt(ln.amount), ESTIMATED_VALUE, places=2)
        self.assertEqual(ln.priority, "High")
        self.assertTrue(ln.is_active)

        # --- Package estimated_value auto-rolled-up ---
        pkg_ev = flt(frappe.db.get_value("Procurement Package", PKG_CODE, "estimated_value"))
        self.assertAlmostEqual(pkg_ev, ESTIMATED_VALUE, places=2)

    # ── Test 2: idempotency ───────────────────────────────────────────────────
    def test_002_idempotent_second_run_does_not_duplicate(self):
        """SEED-TEST-R2-007-002: Running twice must not create duplicate records."""
        first = upsert_works_master_planning()
        self.assertTrue(first.get("ok"), f"First run error: {first}")

        second = upsert_works_master_planning()
        self.assertTrue(second.get("ok"), f"Second run error: {second}")
        self.assertTrue(second.get("idempotent"), "Second run must be idempotent")
        self.assertFalse(second.get("plan_created"))
        self.assertFalse(second.get("package_created"))

        # Confirm no duplicates
        plan_count = len(frappe.get_all("Procurement Plan", filters={"plan_code": PLAN_CODE}))
        self.assertEqual(plan_count, 1, "Expected exactly one Procurement Plan with this code")

        pkg_count = len(
            frappe.get_all("Procurement Package", filters={"package_code": PKG_CODE})
        )
        self.assertEqual(pkg_count, 1, "Expected exactly one Procurement Package with this code")

        line_count = len(
            frappe.get_all(
                "Procurement Package Line", filters={"package_line_code": PKG_LINE_CODE}
            )
        )
        self.assertEqual(line_count, 1, "Expected exactly one Package Line with this code")

    # ── Test 3: missing PE ────────────────────────────────────────────────────
    def test_003_missing_pe_returns_error(self):
        """SEED-TEST-R2-007-003: Missing Procuring Entity returns MISSING_PROCURING_ENTITY."""
        from kentender_procurement.procurement_planning.seeds import (
            works_master_planning_seed as mod,
        )
        original = mod.resolve_procuring_entity_moh
        mod.resolve_procuring_entity_moh = lambda: None
        try:
            out = upsert_works_master_planning()
            self.assertFalse(out.get("ok"))
            self.assertEqual(out["error_code"], "MISSING_PROCURING_ENTITY")
        finally:
            mod.resolve_procuring_entity_moh = original

    # ── Test 4: missing demand ────────────────────────────────────────────────
    def test_004_missing_demand_returns_error(self):
        """SEED-TEST-R2-007-004: Missing Demand returns MISSING_DEMAND."""
        from kentender_procurement.procurement_planning.seeds import (
            works_master_planning_seed as mod,
        )
        original = mod._resolve_demand
        mod._resolve_demand = lambda: None
        try:
            out = upsert_works_master_planning()
            self.assertFalse(out.get("ok"))
            self.assertEqual(out["error_code"], "MISSING_DEMAND")
        finally:
            mod._resolve_demand = original

    # ── Test 5: missing budget line ───────────────────────────────────────────
    def test_005_missing_budget_line_returns_error(self):
        """SEED-TEST-R2-007-005: Missing Budget Line returns MISSING_BUDGET_LINE."""
        from kentender_procurement.procurement_planning.seeds import (
            works_master_planning_seed as mod,
        )
        original = mod._resolve_budget_line
        mod._resolve_budget_line = lambda: None
        try:
            out = upsert_works_master_planning()
            self.assertFalse(out.get("ok"))
            self.assertEqual(out["error_code"], "MISSING_BUDGET_LINE")
        finally:
            mod._resolve_budget_line = original

    # ── Test 6: VAL-SEED-007 / 008 / 009 ─────────────────────────────────────
    def test_006_val_seed_007_008_009_plan_package_released_to_tender(self):
        """VAL-SEED-007/008/009: Plan exists; package line links demand+budget line; package Released."""
        out = upsert_works_master_planning()
        self.assertTrue(out.get("ok"), f"Seed error: {out}")

        # VAL-SEED-007: Procurement Plan PLAN-MOH-2026 exists
        self.assertTrue(
            frappe.db.exists("Procurement Plan", {"plan_code": PLAN_CODE}),
            "VAL-SEED-007: Procurement Plan PLAN-MOH-2026 must exist",
        )

        # VAL-SEED-008: Package line links DEM-MOH-2026-001 and BUD-MOH-INFRA-2026-001
        pkg_name = frappe.db.get_value(
            "Procurement Package", {"package_code": PKG_CODE}, "name"
        )
        self.assertIsNotNone(pkg_name, "Package PKG-MOH-2026-001 must exist")

        lines = frappe.get_all(
            "Procurement Package Line",
            filters={"package_id": pkg_name},
            fields=["demand_id", "budget_line_id"],
        )
        matched = any(
            ln.get("demand_id") == self.demand_name
            and ln.get("budget_line_id") == self.budget_line_name
            for ln in lines
        )
        self.assertTrue(
            matched,
            f"VAL-SEED-008: Package line must link demand {self.demand_name} "
            f"and budget line {self.budget_line_name}. Lines found: {lines}",
        )

        # VAL-SEED-009: Package status is Released to Tender
        pkg_status = frappe.db.get_value("Procurement Package", pkg_name, "status")
        self.assertEqual(
            pkg_status,
            "Released to Tender",
            f"VAL-SEED-009: Package status must be 'Released to Tender', got {pkg_status!r}",
        )
