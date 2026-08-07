# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R2-013 — WORKS master seed conflict report tests.

Tests:
  1. SEED-TEST-R2-013-001 — Clean state returns ok=True, safe_to_proceed=True, no critical conflicts.
  2. SEED-TEST-R2-013-002 — Report has the required top-level keys per the conflict report template.
  3. SEED-TEST-R2-013-003 — Non-master seed registry lists all 6 known non-master seeds from G0-003.
  4. SEED-TEST-R2-013-004 — Simulated non-master journey ownership triggers CRITICAL conflict.
  5. SEED-TEST-R2-013-005 — Legacy sibling check structure is correct (SIB-001 through SIB-005).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r2_013_works_master_conflict_report
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
from kentender_procurement.procurement_lifecycle.seeds.works_master_conflict_report import (
    generate_works_master_conflict_report,
    NON_MASTER_SEED_REGISTRY,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    JOURNEY_CODE,
    BASE_HANDOFF_CODES,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"

# Required top-level keys per R2-013 conflict report template
_REQUIRED_REPORT_KEYS = {
    "ok", "safe_to_proceed", "critical_conflicts", "record_warnings",
    "clean_records", "no_go_violations", "legacy_siblings",
    "non_master_seed_registry", "summary",
}


def _restore_journey_master_flag() -> None:
    """Restore is_master_seed=1 on journey after simulated conflict test."""
    if frappe.db.exists("Procurement Journey", JOURNEY_CODE):
        frappe.db.set_value("Procurement Journey", JOURNEY_CODE, "is_master_seed", 1)
        frappe.db.commit()


class TestR2013WorksMasterConflictReport(IntegrationTestCase):
    """R2-013 — Conflict report template and detection tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        cls.pe_name = ensure_procuring_entity(_PE_CODE, _PE_DISPLAY)

        # Full seed prerequisites
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

        # Ensure PLC base seed is present
        from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
            load_procurement_lifecycle_works_master,
        )
        plc = load_procurement_lifecycle_works_master(reset=False, checkpoint="TENDER_PUBLISHED")
        assert plc.get("ok"), f"PLC prerequisite failed: {plc}"

    def tearDown(self):
        _restore_journey_master_flag()

    # ── Test 1: clean state ───────────────────────────────────────────────────
    def test_001_clean_state_returns_ok_true_no_critical_conflicts(self):
        """SEED-TEST-R2-013-001: With all master seeds correctly set up, report returns ok=True."""
        report = generate_works_master_conflict_report()

        self.assertTrue(report.get("ok"), f"Clean state must return ok=True: {report.get('critical_conflicts')}")
        self.assertTrue(report.get("safe_to_proceed"), "Clean state must be safe_to_proceed=True")
        self.assertEqual(
            report.get("critical_conflicts"), [],
            f"Clean state must have no critical conflicts: {report.get('critical_conflicts')}",
        )
        self.assertEqual(report.get("no_go_violations"), [], "Clean state must have no No-Go violations")

    # ── Test 2: report template shape ────────────────────────────────────────
    def test_002_report_has_required_template_keys(self):
        """SEED-TEST-R2-013-002: Report contains all required template top-level keys."""
        report = generate_works_master_conflict_report()

        for key in _REQUIRED_REPORT_KEYS:
            self.assertIn(key, report, f"Report must contain key {key!r}")

        # Type checks
        self.assertIsInstance(report["critical_conflicts"], list)
        self.assertIsInstance(report["record_warnings"], list)
        self.assertIsInstance(report["clean_records"], list)
        self.assertIsInstance(report["no_go_violations"], list)
        self.assertIsInstance(report["legacy_siblings"], list)
        self.assertIsInstance(report["non_master_seed_registry"], list)
        self.assertIsInstance(report["summary"], str)
        self.assertTrue(report["summary"].strip(), "Summary must be non-empty")

    # ── Test 3: non-master seed registry ─────────────────────────────────────
    def test_003_non_master_seed_registry_lists_all_known_seeds(self):
        """SEED-TEST-R2-013-003: Non-master seed registry contains all 6 G0-003 documented seeds."""
        registry = NON_MASTER_SEED_REGISTRY
        self.assertGreaterEqual(
            len(registry), 6,
            f"Non-master seed registry must have at least 6 entries (got {len(registry)})",
        )

        seed_ids = [r["seed_id"] for r in registry]
        for expected_id in ("NMS-001", "NMS-002", "NMS-003", "NMS-004", "NMS-005", "NMS-006"):
            self.assertIn(expected_id, seed_ids, f"Registry must contain {expected_id!r}")

        # Every entry must have required fields
        for entry in registry:
            self.assertIn("seed_id", entry, "Registry entry must have seed_id")
            self.assertIn("module", entry, "Registry entry must have module")
            self.assertIn("uses_master_codes", entry, "Registry entry must have uses_master_codes")
            self.assertIn("disposition", entry, "Registry entry must have disposition")
            self.assertIn("g0_reference", entry, "Registry entry must have g0_reference")

        # Verify NMS-001 references PKG-MOH-2026-001 and TND-MOH-2026-001
        nms001 = next(r for r in registry if r["seed_id"] == "NMS-001")
        self.assertIn("PKG-MOH-2026-001", nms001["uses_master_codes"])
        self.assertIn("TND-MOH-2026-001", nms001["uses_master_codes"])

    # ── Test 4: simulated conflict detection ──────────────────────────────────
    def test_004_non_master_journey_ownership_triggers_critical_conflict(self):
        """SEED-TEST-R2-013-004: Setting is_master_seed=0 on journey triggers CRITICAL conflict."""
        # Temporarily simulate a non-master record owning the journey code
        frappe.db.set_value("Procurement Journey", JOURNEY_CODE, "is_master_seed", 0)
        frappe.db.commit()

        try:
            report = generate_works_master_conflict_report()

            self.assertFalse(report.get("ok"), "Simulated conflict must return ok=False")
            self.assertFalse(report.get("safe_to_proceed"), "Conflict must not be safe_to_proceed")
            self.assertGreater(
                len(report.get("critical_conflicts", [])), 0,
                "Simulated conflict must produce at least one critical conflict entry",
            )

            # Find the journey conflict entry
            journey_conflict = next(
                (c for c in report["critical_conflicts"] if c.get("doctype") == "Procurement Journey"),
                None,
            )
            self.assertIsNotNone(journey_conflict, "Must find journey conflict entry")
            self.assertEqual(journey_conflict.get("severity"), "CRITICAL")
            self.assertFalse(journey_conflict.get("safe_reset"), "Non-master conflict must have safe_reset=False")
        finally:
            _restore_journey_master_flag()

    # ── Test 5: sibling check structure ──────────────────────────────────────
    def test_005_legacy_sibling_checks_have_correct_structure(self):
        """SEED-TEST-R2-013-005: Legacy sibling check results have SIB-001 through SIB-005."""
        report = generate_works_master_conflict_report()
        siblings = report.get("legacy_siblings", [])

        self.assertGreaterEqual(len(siblings), 5, "Must have at least 5 sibling check results")

        sibling_ids = [s["sibling_id"] for s in siblings]
        for expected_id in ("SIB-001", "SIB-002", "SIB-003", "SIB-004", "SIB-005"):
            self.assertIn(expected_id, sibling_ids, f"Sibling checks must include {expected_id!r}")

        # Every entry must have required fields
        for entry in siblings:
            self.assertIn("sibling_id", entry)
            self.assertIn("description", entry)
            self.assertIn("count", entry)
            self.assertIn("severity", entry)
            self.assertIn("message", entry)
            self.assertIn("safe_to_coexist", entry)
            # All legacy siblings are safe to coexist (per G0-003 policy)
            self.assertTrue(entry["safe_to_coexist"], f"{entry['sibling_id']} must be safe_to_coexist=True")
