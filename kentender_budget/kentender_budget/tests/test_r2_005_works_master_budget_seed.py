# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R2-005 — WORKS master budget seed tests (spec §9 / VAL-SEED-004).

Tests:
  1. SEED-TEST-R2-005-001 — Fresh seed creates Budget + Budget Line with exact spec values.
  2. SEED-TEST-R2-005-002 — Idempotent: second run does not duplicate records.
  3. SEED-TEST-R2-005-003 — Missing PE returns MISSING_PROCURING_ENTITY error code.
  4. SEED-TEST-R2-005-004 — Missing strategy chain returns MISSING_STRATEGIC_PLAN or
     MISSING_STRATEGY_PROGRAM error.
  5. SEED-TEST-R2-005-005 — VAL-SEED-004: Budget Line links to strategy objective and programme.

Run::

    bench --site kentender.midas.com run-tests --app kentender_budget \\
      --module kentender_budget.tests.test_r2_005_works_master_budget_seed
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_strategy.seeds.works_master_strategy_hierarchy import (
    upsert_works_master_strategy_hierarchy,
)

from kentender_budget.seeds.works_master_budget_seed import (
    AMOUNT_ALLOCATED,
    AMOUNT_RESERVED,
    BUDGET_LINE_CODE,
    BUDGET_NAME,
    FISCAL_YEAR,
    OBJECTIVE_CODE,
    PROGRAM_CODE,
    upsert_works_master_budget,
)

_PE_CODE = "PE-MOH"
_PE_NAME_DISPLAY = "Ministry of Health"


def _clean_budget(pe_name: str) -> None:
    """Remove seeded Budget + Budget Line for teardown. Uses force-delete flag."""
    if frappe.db.exists("Budget Line", BUDGET_LINE_CODE):
        try:
            frappe.flags.budget_line_force_delete = True
            frappe.delete_doc("Budget Line", BUDGET_LINE_CODE, force=True, ignore_permissions=True)
        finally:
            frappe.flags.budget_line_force_delete = False
    for bname in frappe.get_all(
        "Budget",
        filters={"budget_name": BUDGET_NAME, "procuring_entity": pe_name, "fiscal_year": FISCAL_YEAR},
        pluck="name",
    ):
        # Budget on_trash requires Draft status.
        frappe.db.set_value("Budget", bname, "status", "Draft")
        frappe.delete_doc("Budget", bname, force=True, ignore_permissions=True)


class TestR2005WorksMasterBudgetSeed(IntegrationTestCase):
    """R2-005 — Budget seed alignment (spec §9)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        # Ensure PE-MOH exists (prerequisite for strategy + budget seeds).
        cls.pe_name = ensure_procuring_entity(_PE_CODE, _PE_NAME_DISPLAY)
        # Ensure §8 strategy chain (R2-004 prerequisite).
        strat = upsert_works_master_strategy_hierarchy()
        assert strat.get("ok"), f"Strategy seed prerequisite failed: {strat}"
        cls.plan_name = strat["strategic_plan"]
        cls.program_name = strat["strategy_program"]
        cls.objective_name = strat["strategy_objective"]

    def tearDown(self):
        _clean_budget(self.pe_name)

    # ── Test 1: fresh seed shape and values ───────────────────────────────────
    def test_001_fresh_seed_creates_budget_and_line_with_spec_values(self):
        """SEED-TEST-R2-005-001: First run materialises correct codes and amounts."""
        _clean_budget(self.pe_name)
        out = upsert_works_master_budget()

        self.assertTrue(out.get("ok"), f"Seed returned error: {out}")
        self.assertEqual(out["codes"]["budget_name"], BUDGET_NAME)
        self.assertEqual(out["codes"]["budget_line_code"], BUDGET_LINE_CODE)
        self.assertTrue(out["budget_created"])
        self.assertTrue(out["budget_line_created"])
        self.assertEqual(out["amounts"]["allocated"], AMOUNT_ALLOCATED)
        self.assertEqual(out["amounts"]["reserved"], AMOUNT_RESERVED)
        # amount_available = allocated − reserved − consumed = 120M − 98M = 22M
        self.assertAlmostEqual(out["amounts"]["available"], 22_000_000.0, places=2)

        # Verify DB state: Budget
        budget_doc = frappe.get_doc("Budget", out["budget"])
        self.assertEqual(budget_doc.budget_name, BUDGET_NAME)
        self.assertEqual(budget_doc.fiscal_year, FISCAL_YEAR)
        self.assertEqual(budget_doc.procuring_entity, self.pe_name)
        self.assertEqual(budget_doc.status, "Approved")
        self.assertAlmostEqual(flt(budget_doc.total_budget_amount), AMOUNT_ALLOCATED, places=2)

        # Verify DB state: Budget Line
        bl_doc = frappe.get_doc("Budget Line", BUDGET_LINE_CODE)
        self.assertEqual(bl_doc.name, BUDGET_LINE_CODE)
        self.assertEqual(bl_doc.budget, out["budget"])
        self.assertEqual(bl_doc.procuring_entity, self.pe_name)
        self.assertEqual(bl_doc.fiscal_year, FISCAL_YEAR)
        self.assertAlmostEqual(flt(bl_doc.amount_allocated), AMOUNT_ALLOCATED, places=2)
        self.assertAlmostEqual(flt(bl_doc.amount_reserved), AMOUNT_RESERVED, places=2)
        self.assertAlmostEqual(flt(bl_doc.amount_available), 22_000_000.0, places=2)
        self.assertEqual(bl_doc.currency, "KES")
        self.assertEqual(int(bl_doc.is_active), 1)
        self.assertTrue(bl_doc.sub_program)
        self.assertTrue(frappe.db.exists("Sub Program", bl_doc.sub_program))

    # ── Test 2: idempotency ───────────────────────────────────────────────────
    def test_002_idempotent_second_run_does_not_duplicate(self):
        """SEED-TEST-R2-005-002: Running twice must not create duplicate records."""
        first = upsert_works_master_budget()
        self.assertTrue(first.get("ok"))
        first_budget_name = first["budget"]

        second = upsert_works_master_budget()
        self.assertTrue(second.get("ok"))
        self.assertFalse(second["budget_created"], "Budget should not be re-created on second run")
        self.assertFalse(second["budget_line_created"], "Budget Line should not be re-created on second run")
        self.assertTrue(second["idempotent"])
        self.assertEqual(second["budget"], first_budget_name)
        self.assertEqual(second["codes"]["budget_line_code"], BUDGET_LINE_CODE)

        # Confirm no duplicates in DB
        budget_count = len(frappe.get_all(
            "Budget",
            filters={"budget_name": BUDGET_NAME, "procuring_entity": self.pe_name, "fiscal_year": FISCAL_YEAR},
        ))
        self.assertEqual(budget_count, 1, "Expected exactly one Budget with this code")
        self.assertTrue(frappe.db.exists("Budget Line", BUDGET_LINE_CODE))

    # ── Test 3: missing PE ────────────────────────────────────────────────────
    def test_003_missing_pe_returns_error(self):
        """SEED-TEST-R2-005-003: Missing Procuring Entity returns MISSING_PROCURING_ENTITY."""
        # Temporarily patch the resolver to simulate missing PE.
        from kentender_budget.seeds import works_master_budget_seed as mod
        original = mod.resolve_procuring_entity_moh
        mod.resolve_procuring_entity_moh = lambda: None
        try:
            out = upsert_works_master_budget()
            self.assertFalse(out.get("ok"))
            self.assertEqual(out["error_code"], "MISSING_PROCURING_ENTITY")
        finally:
            mod.resolve_procuring_entity_moh = original

    # ── Test 4: missing strategy prerequisites ────────────────────────────────
    def test_004_missing_strategic_plan_returns_error(self):
        """SEED-TEST-R2-005-004: Missing Strategic Plan returns MISSING_STRATEGIC_PLAN."""
        from kentender_budget.seeds import works_master_budget_seed as mod
        original = mod._resolve_strategic_plan
        mod._resolve_strategic_plan = lambda pe: None
        try:
            out = upsert_works_master_budget()
            self.assertFalse(out.get("ok"))
            self.assertIn(out["error_code"], ("MISSING_STRATEGIC_PLAN", "MISSING_STRATEGY_PROGRAM"))
        finally:
            mod._resolve_strategic_plan = original

    # ── Test 5: VAL-SEED-004 — budget line links to strategy objective/programme
    def test_005_val_seed_004_budget_line_links_strategy_refs(self):
        """VAL-SEED-004: Budget Line exists and links to strategy objective and programme."""
        out = upsert_works_master_budget()
        self.assertTrue(out.get("ok"))

        bl_doc = frappe.get_doc("Budget Line", BUDGET_LINE_CODE)

        # Strategic Plan alignment
        self.assertEqual(bl_doc.strategic_plan, self.plan_name)

        # Programme link (output_indicator = Strategy Objective)
        self.assertEqual(bl_doc.program, self.program_name)
        prog_doc = frappe.get_doc("Strategy Program", self.program_name)
        self.assertEqual(prog_doc.program_code, PROGRAM_CODE)

        # Output Indicator = Strategy Objective (spec §9.2 objective_code)
        self.assertIsNotNone(bl_doc.output_indicator)
        obj_doc = frappe.get_doc("Strategy Objective", bl_doc.output_indicator)
        self.assertEqual(obj_doc.objective_code, OBJECTIVE_CODE)

        # Budget itself links to same PE and plan as budget line
        budget_doc = frappe.get_doc("Budget", bl_doc.budget)
        self.assertEqual(budget_doc.procuring_entity, bl_doc.procuring_entity)
        self.assertEqual(budget_doc.strategic_plan, bl_doc.strategic_plan)
