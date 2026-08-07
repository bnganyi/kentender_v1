# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R2-012 — WORKS master full seed §20 summary output tests.

Tests:
  1. SEED-TEST-R2-012-001 — Base seed returns spec §20 shape with all required top-level keys.
  2. SEED-TEST-R2-012-002 — ``created_or_updated`` counts match spec §20 expected values for base.
  3. SEED-TEST-R2-012-003 — ``warnings`` is empty when all prerequisites exist.
  4. SEED-TEST-R2-012-004 — Opening checkpoint returns ``handoff_cards=9`` and ``evidence_events=10``.
  5. SEED-TEST-R2-012-005 — Unsupported checkpoint returns ``ok=False`` with ``UNSUPPORTED_CHECKPOINT``.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r2_012_works_master_full_seed_summary
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_strategy.seeds.works_master_strategy_hierarchy import (
    upsert_works_master_strategy_hierarchy,
)
from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_procurement.procurement_lifecycle.legacy_demand_seed_shim import (
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
from kentender_procurement.procurement_lifecycle.seeds.works_master_full_seed import (
    run_works_master_full_seed,
    _SPEC_COUNTS_BASE,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    JOURNEY_CODE,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"

# Required top-level keys per spec §20
_REQUIRED_SUMMARY_KEYS = {
    "ok", "checkpoint", "journey_code", "master_scenario",
    "created_or_updated", "current_stage", "next_action",
    "warnings", "status",
}

# Required created_or_updated sub-keys per spec §20
_REQUIRED_COUNT_KEYS = {
    "procuring_entities", "strategy_records", "budget_records",
    "demand_records", "planning_records", "std_reference_records",
    "tm2_reference_records", "journey_records", "journey_steps",
    "handoff_cards", "evidence_events",
}


def _reset_plc_to_base() -> None:
    """Restore PLC to base TENDER_PUBLISHED state for tearDown."""
    from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
        load_procurement_lifecycle_works_master,
    )
    load_procurement_lifecycle_works_master(reset=True, checkpoint="TENDER_PUBLISHED")


class TestR2012WorksMasterFullSeedSummary(IntegrationTestCase):
    """R2-012 — Full seed §20 summary output."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        cls.pe_name = ensure_procuring_entity(_PE_CODE, _PE_DISPLAY)

        # Ensure prerequisites exist so summary tests can pass with all counts
        for label, fn in (
            ("Strategy", upsert_works_master_strategy_hierarchy),
            ("Budget", upsert_works_master_budget),
            ("Demand", upsert_works_master_demand),
            ("Planning", upsert_works_master_planning),
            ("STD", upsert_works_master_std),
            ("Tender", upsert_works_master_tender),
        ):
            result = fn()
            assert result.get("ok"), f"{label} prerequisite failed: {result}"

    def tearDown(self):
        _reset_plc_to_base()

    # ── Test 1: spec §20 shape ────────────────────────────────────────────────
    def test_001_base_seed_returns_spec_20_shape(self):
        """SEED-TEST-R2-012-001: Base seed returns all required spec §20 top-level keys."""
        out = run_works_master_full_seed(checkpoint="TENDER_PUBLISHED")

        self.assertTrue(out.get("ok"), f"Full seed returned error: {out}")
        for key in _REQUIRED_SUMMARY_KEYS:
            self.assertIn(key, out, f"Summary must contain key {key!r}")

        self.assertEqual(out["checkpoint"], "TENDER_PUBLISHED")
        self.assertEqual(out["journey_code"], JOURNEY_CODE)
        self.assertEqual(out["master_scenario"], "District Hospital Renovation Works")
        self.assertEqual(out["current_stage"], "Tender Published")
        self.assertEqual(out["status"], "loaded")

        counts = out["created_or_updated"]
        self.assertIsInstance(counts, dict, "created_or_updated must be a dict")
        for key in _REQUIRED_COUNT_KEYS:
            self.assertIn(key, counts, f"created_or_updated must contain key {key!r}")

    # ── Test 2: count values match spec §20 ──────────────────────────────────
    def test_002_created_or_updated_counts_match_spec_20(self):
        """SEED-TEST-R2-012-002: created_or_updated counts match spec §20 expected values (base)."""
        out = run_works_master_full_seed(checkpoint="TENDER_PUBLISHED")
        self.assertTrue(out.get("ok"), f"Full seed error: {out}")

        counts = out["created_or_updated"]
        for key, expected in _SPEC_COUNTS_BASE.items():
            self.assertEqual(
                counts[key],
                expected,
                f"created_or_updated[{key!r}] must equal spec §20 value {expected} (got {counts.get(key)})",
            )

    # ── Test 3: no warnings with all prerequisites ────────────────────────────
    def test_003_no_warnings_when_all_prerequisites_exist(self):
        """SEED-TEST-R2-012-003: warnings list is empty when all upstream records exist."""
        out = run_works_master_full_seed(checkpoint="TENDER_PUBLISHED")
        self.assertTrue(out.get("ok"), f"Full seed error: {out}")

        warnings = out.get("warnings", [])
        self.assertIsInstance(warnings, list, "warnings must be a list")
        self.assertEqual(warnings, [], f"Unexpected warnings: {warnings}")

    # ── Test 4: opening checkpoint counts ────────────────────────────────────
    def test_004_opening_checkpoint_returns_nine_cards_and_ten_events(self):
        """SEED-TEST-R2-012-004: OPENING_READY checkpoint returns handoff_cards=9, evidence_events=10."""
        out = run_works_master_full_seed(checkpoint="OPENING_READY")
        self.assertTrue(out.get("ok"), f"Full seed error: {out}")

        self.assertEqual(out["checkpoint"], "OPENING_READY")
        self.assertEqual(out["current_stage"], "Opening Ready")

        counts = out["created_or_updated"]
        self.assertEqual(counts["handoff_cards"], 9, "OPENING_READY must have 9 handoff cards")
        self.assertEqual(counts["evidence_events"], 10, "OPENING_READY must have 10 evidence events")

    # ── Test 5: unsupported checkpoint ───────────────────────────────────────
    def test_005_unsupported_checkpoint_returns_error(self):
        """SEED-TEST-R2-012-005: Unsupported checkpoint returns ok=False with UNSUPPORTED_CHECKPOINT."""
        out = run_works_master_full_seed(checkpoint="INVALID_CP")
        self.assertFalse(out.get("ok"), "Unsupported checkpoint must return ok=False")
        self.assertEqual(
            out.get("error_code"), "UNSUPPORTED_CHECKPOINT",
            "error_code must be UNSUPPORTED_CHECKPOINT",
        )
