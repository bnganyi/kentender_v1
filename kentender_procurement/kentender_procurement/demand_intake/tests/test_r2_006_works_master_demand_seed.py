# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R2-006 — WORKS master demand seed tests (spec §10 / VAL-SEED-005, VAL-SEED-006).

Tests:
  1. SEED-TEST-R2-006-001 — Fresh seed creates Demand with exact spec values.
  2. SEED-TEST-R2-006-002 — Idempotent: second run does not duplicate records.
  3. SEED-TEST-R2-006-003 — Missing PE returns MISSING_PROCURING_ENTITY error code.
  4. SEED-TEST-R2-006-004 — Missing budget line returns MISSING_BUDGET_LINE error code.
  5. SEED-TEST-R2-006-005 — VAL-SEED-005/006: Demand links to master budget line and
     status is Approved.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.demand_intake.tests.test_r2_006_works_master_demand_seed
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
    BUDGET_LINE_CODE,
    DEMAND_ID,
    DEMAND_TITLE,
    DEPT_INFRA,
    ESTIMATED_UNIT_COST,
    upsert_works_master_demand,
)

_PE_CODE = "PE-MOH"
_PE_NAME_DISPLAY = "Ministry of Health"


def _clean_demand() -> None:
    """Remove the WORKS master demand for teardown."""
    name = frappe.db.get_value("Demand", {"demand_id": DEMAND_ID}, "name")
    if name:
        # Release any budget reservation if present.
        res_ref = frappe.db.get_value("Demand", name, "reservation_reference") or ""
        if res_ref:
            try:
                from kentender_budget.api.dia_budget_control import release_reservation
                release_reservation(res_ref, reason="Test teardown", actor="Administrator")
            except Exception:
                pass
        frappe.delete_doc("Demand", name, force=True, ignore_permissions=True)


class TestR2006WorksMasterDemandSeed(IntegrationTestCase):
    """R2-006 — Demand seed alignment (spec §10)."""

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
        cls.budget_line_name = frappe.db.get_value(
            "Budget Line", {"generated_reference": BUDGET_LINE_CODE}, "name"
        )
        # Entity lives on parent Budget (Budget Line no longer stores procuring_entity).
        budget_name = frappe.db.get_value("Budget Line", cls.budget_line_name, "budget")
        cls.budget_line_entity = frappe.db.get_value("Budget", budget_name, "procuring_entity")

    def setUp(self):
        super().setUp()
        frappe.set_user("Administrator")
        _clean_demand()

    def tearDown(self):
        _clean_demand()

    # ── Test 1: fresh seed shape and values ───────────────────────────────────
    def test_001_fresh_seed_creates_demand_with_spec_values(self):
        """SEED-TEST-R2-006-001: First run creates Demand with correct spec values."""
        out = upsert_works_master_demand()

        self.assertTrue(out.get("ok"), f"Seed returned error: {out}")
        self.assertEqual(out["demand_id"], DEMAND_ID)
        self.assertTrue(out["demand_created"])
        self.assertFalse(out["idempotent"])
        self.assertEqual(out["status"], "Approved")

        doc = frappe.get_doc("Demand", out["demand"])
        self.assertEqual(doc.demand_id, DEMAND_ID)
        self.assertEqual(doc.title, DEMAND_TITLE)
        self.assertEqual(doc.status, "Approved")
        self.assertEqual(doc.demand_type, "Planned")
        self.assertEqual(doc.requisition_type, "Works")
        self.assertEqual(doc.priority_level, "High")
        self.assertEqual(doc.procuring_entity, self.budget_line_entity)
        self.assertIsNotNone(doc.requesting_department)
        self.assertAlmostEqual(flt(doc.total_amount), ESTIMATED_UNIT_COST, places=2)

        # Items check — exactly one item matching the spec
        self.assertEqual(len(doc.items), 1)
        item = doc.items[0]
        self.assertEqual(item.uom, "Lot")
        self.assertAlmostEqual(flt(item.quantity), 1.0, places=4)
        self.assertAlmostEqual(flt(item.estimated_unit_cost), ESTIMATED_UNIT_COST, places=2)

        # Audit timestamps must be set to spec dates
        self.assertIsNotNone(doc.finance_approved_by)
        self.assertIsNotNone(doc.finance_approved_at)

    # ── Test 2: idempotency ───────────────────────────────────────────────────
    def test_002_idempotent_second_run_does_not_duplicate(self):
        """SEED-TEST-R2-006-002: Running twice must not create duplicate records."""
        first = upsert_works_master_demand()
        self.assertTrue(first.get("ok"))
        first_name = first["demand"]

        second = upsert_works_master_demand()
        self.assertTrue(second.get("ok"))
        self.assertFalse(second["demand_created"], "Demand should not be re-created on second run")
        self.assertTrue(second["idempotent"])
        self.assertEqual(second["demand"], first_name)
        self.assertEqual(second["demand_id"], DEMAND_ID)

        # Confirm no duplicate in DB
        count = len(
            frappe.get_all("Demand", filters={"demand_id": DEMAND_ID})
        )
        self.assertEqual(count, 1, "Expected exactly one Demand with this ID")

    # ── Test 3: missing PE ────────────────────────────────────────────────────
    def test_003_missing_pe_returns_error(self):
        """SEED-TEST-R2-006-003: Missing Procuring Entity returns MISSING_PROCURING_ENTITY."""
        from kentender_procurement.demand_intake.seeds import works_master_demand_seed as mod
        original = mod.resolve_procuring_entity_moh
        mod.resolve_procuring_entity_moh = lambda: None
        try:
            out = upsert_works_master_demand()
            self.assertFalse(out.get("ok"))
            self.assertEqual(out["error_code"], "MISSING_PROCURING_ENTITY")
        finally:
            mod.resolve_procuring_entity_moh = original

    # ── Test 4: missing budget line ───────────────────────────────────────────
    def test_004_missing_budget_line_returns_error(self):
        """SEED-TEST-R2-006-004: Missing Budget Line returns MISSING_BUDGET_LINE."""
        from kentender_procurement.demand_intake.seeds import works_master_demand_seed as mod
        original = mod._resolve_budget_line
        mod._resolve_budget_line = lambda: None
        try:
            out = upsert_works_master_demand()
            self.assertFalse(out.get("ok"))
            self.assertEqual(out["error_code"], "MISSING_BUDGET_LINE")
        finally:
            mod._resolve_budget_line = original

    # ── Test 5: VAL-SEED-005 + VAL-SEED-006 ──────────────────────────────────
    def test_005_val_seed_005_006_demand_links_budget_line_and_is_approved(self):
        """VAL-SEED-005: Demand links to master budget line. VAL-SEED-006: status is Approved."""
        out = upsert_works_master_demand()
        self.assertTrue(out.get("ok"))

        doc = frappe.get_doc("Demand", out["demand"])

        # VAL-SEED-005: demand.budget_line must be the master budget line
        self.assertEqual(doc.budget_line, self.budget_line_name,
                         "VAL-SEED-005: Demand must link to BUD-MOH-INFRA-2026-001")

        # VAL-SEED-006: status must be Approved
        self.assertEqual(doc.status, "Approved",
                         "VAL-SEED-006: Demand status must be Approved")

        # XMOD-STR-002 — primary Strategy Reference (not legacy strategic_plan derive)
        self.assertTrue(
            (getattr(doc, "strategy_target", None) or "").strip(),
            "Demand seed should carry primary strategy_target",
        )
        self.assertTrue(
            (getattr(doc, "strategy_plan_version", None) or "").strip(),
            "Demand seed should carry strategy_plan_version",
        )
