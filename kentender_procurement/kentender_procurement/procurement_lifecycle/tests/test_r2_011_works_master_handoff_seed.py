# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R2-011 — WORKS master base handoff card seed tests (spec §16.2–16.8).

Tests:
  1. SEED-TEST-R2-011-001 — All 7 base handoff cards exist with correct spec §16 core fields.
  2. SEED-TEST-R2-011-002 — Idempotent: second run returns ok=True, exactly 7 cards, no duplicates.
  3. SEED-TEST-R2-011-003 — locked_summary and passed_forward_summary JSON populated for all 7 cards.
  4. SEED-TEST-R2-011-004 — evidence_links_json and technical_refs_json populated for all 7 cards.
  5. SEED-TEST-R2-011-005 — CLOSECERT and OPENREADY are NOT created by the base checkpoint.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r2_011_works_master_handoff_seed
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cint

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
from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import (
    upsert_works_master_journey,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_seed import (
    upsert_works_master_handoff_cards,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    BASE_HANDOFF_CODES,
    JOURNEY_CODE,
    OPENING_HANDOFF_CODES,
)

_PE_CODE = "PE-MOH"
_PE_NAME_DISPLAY = "Ministry of Health"

# Spec §16 per-card expected values (core fields only — JSON bodies tested separately)
_CARD_SPEC = {
    "STRATREF-MOH-2026-001": {
        "handoff_title": "Strategy Alignment Reference",
        "status": "Consumed",
        "source_object_code": "OBJ-MOH-HOSP-RENOV",
        "target_object_code": "BUD-MOH-INFRA-2026-001",
        "source_module": "Strategy",
        "target_module": "Budget",
    },
    "BUDCONF-MOH-2026-001": {
        "handoff_title": "Budget Funding Confirmation",
        "status": "Consumed",
        "source_object_code": "BUD-MOH-INFRA-2026-001",
        "target_object_code": "DEM-MOH-2026-001",
        "source_module": "Budget",
        "target_module": "Demand Intake and Approval",
    },
    "DEMAPP-MOH-2026-001": {
        "handoff_title": "Demand Approval Certificate",
        "status": "Consumed",
        "source_object_code": "DEM-MOH-2026-001",
        "target_object_code": "PLAN-MOH-2026",
        "source_module": "Demand Intake and Approval",
        "target_module": "Procurement Planning",
    },
    "PLANINCL-MOH-2026-001": {
        "handoff_title": "Planning Inclusion Record",
        "status": "Consumed",
        "source_object_code": "DEM-MOH-2026-001",
        "target_object_code": "PLAN-MOH-2026",
        "source_module": "Procurement Planning",
        "target_module": "Procurement Planning",
    },
    "PKGREL-MOH-2026-001": {
        "handoff_title": "Planning Release Package",
        "status": "Consumed",
        "source_object_code": "PKG-MOH-2026-001",
        "target_object_code": "TND-MOH-2026-001",
        "source_module": "Procurement Planning",
        "target_module": "Tender Management",
    },
    "STDREADY-TND-MOH-2026-001": {
        "handoff_title": "Tender Document Readiness Certificate",
        "status": "Consumed",
        "source_object_code": "STDINST-TND-MOH-2026-001",
        "target_object_code": "TND-MOH-2026-001",
        "source_module": "STD Engine / Tender Management",
        "target_module": "Tender Publication",
    },
    "PUBCERT-TND-MOH-2026-001": {
        "handoff_title": "Tender Publication Certificate",
        "status": "Handed Off",
        "source_object_code": "TND-MOH-2026-001",
        "target_object_code": "TND-MOH-2026-001",
        "source_module": "Tender Management",
        "target_module": "Suppliers / Tender Closing",
    },
}


def _clean_plc() -> None:
    """Reset PLC to base TENDER_PUBLISHED state only — do NOT create opening cards."""
    from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
        load_procurement_lifecycle_works_master,
    )
    # Use TENDER_PUBLISHED (not OPENING_READY) so CLOSECERT/OPENREADY are absent
    # after tearDown — required for test_005 which asserts their absence.
    load_procurement_lifecycle_works_master(reset=True, checkpoint="TENDER_PUBLISHED")


class TestR2011WorksMasterHandoffSeed(IntegrationTestCase):
    """R2-011 — Base handoff card seed alignment (spec §16.2–16.8)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        cls.pe_name = ensure_procuring_entity(_PE_CODE, _PE_NAME_DISPLAY)

        # Prerequisites R2-004 through R2-009
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

        # Ensure R2-010 journey exists
        j = upsert_works_master_journey()
        assert j.get("ok"), f"Journey prerequisite failed: {j}"

    def tearDown(self):
        _clean_plc()

    # ── Test 1: all 7 cards have correct spec §16 core fields ─────────────────
    def test_001_all_seven_cards_have_correct_spec16_core_fields(self):
        """SEED-TEST-R2-011-001: All 7 base handoff cards exist with spec §16 core fields."""
        out = upsert_works_master_handoff_cards()
        self.assertTrue(out.get("ok"), f"Seed returned error: {out}")
        self.assertEqual(len(out["handoff_codes"]), len(BASE_HANDOFF_CODES))

        for code, expected in _CARD_SPEC.items():
            self.assertTrue(
                frappe.db.exists("Procurement Handoff Card", code),
                f"Handoff card {code!r} must exist",
            )
            card = frappe.get_doc("Procurement Handoff Card", code)
            self.assertEqual(card.handoff_title, expected["handoff_title"], f"{code} title §16")
            self.assertEqual(card.status, expected["status"], f"{code} status §16")
            self.assertEqual(
                card.source_object_code,
                expected["source_object_code"],
                f"{code} source_object_code §16",
            )
            self.assertEqual(
                card.target_object_code,
                expected["target_object_code"],
                f"{code} target_object_code §16",
            )
            self.assertEqual(card.source_module, expected["source_module"], f"{code} source_module §16")
            self.assertEqual(card.target_module, expected["target_module"], f"{code} target_module §16")
            self.assertEqual(card.journey_code, JOURNEY_CODE, f"{code} must be linked to journey")
            self.assertEqual(cint(card.is_master_seed), 1, f"{code} is_master_seed must be 1")

    # ── Test 2: idempotency ───────────────────────────────────────────────────
    def test_002_idempotent_second_run_no_duplicates(self):
        """SEED-TEST-R2-011-002: Running twice returns ok=True with exactly 7 cards each."""
        first = upsert_works_master_handoff_cards()
        self.assertTrue(first.get("ok"), f"First run error: {first}")

        second = upsert_works_master_handoff_cards()
        self.assertTrue(second.get("ok"), f"Second run error: {second}")

        # No duplicate cards
        for code in BASE_HANDOFF_CODES:
            count = frappe.db.sql(
                "SELECT COUNT(*) FROM `tabProcurement Handoff Card` WHERE handoff_code=%s",
                (code,),
            )[0][0]
            self.assertEqual(count, 1, f"Expected exactly 1 card for {code!r}")

    # ── Test 3: locked_summary and passed_forward_summary JSON ────────────────
    def test_003_locked_and_passed_forward_summaries_populated(self):
        """SEED-TEST-R2-011-003: locked_summary and passed_forward_summary are non-empty JSON."""
        upsert_works_master_handoff_cards()

        for code in BASE_HANDOFF_CODES:
            card = frappe.get_doc("Procurement Handoff Card", code)

            locked = card.locked_summary or ""
            self.assertTrue(
                locked.strip(),
                f"{code}: locked_summary must be non-empty",
            )
            try:
                locked_obj = json.loads(locked)
            except Exception as exc:
                self.fail(f"{code}: locked_summary is not valid JSON: {exc}")
            self.assertIsInstance(locked_obj, dict, f"{code}: locked_summary must be a JSON object")
            self.assertTrue(locked_obj, f"{code}: locked_summary must not be empty dict")

            passed = card.passed_forward_summary or ""
            self.assertTrue(
                passed.strip(),
                f"{code}: passed_forward_summary must be non-empty",
            )
            try:
                passed_obj = json.loads(passed)
            except Exception as exc:
                self.fail(f"{code}: passed_forward_summary is not valid JSON: {exc}")
            self.assertIsInstance(passed_obj, dict, f"{code}: passed_forward_summary must be a JSON object")
            self.assertTrue(passed_obj, f"{code}: passed_forward_summary must not be empty dict")

    # ── Test 4: evidence_links_json and technical_refs_json ───────────────────
    def test_004_evidence_links_and_technical_refs_populated(self):
        """SEED-TEST-R2-011-004: evidence_links_json and technical_refs_json are valid JSON."""
        upsert_works_master_handoff_cards()

        for code in BASE_HANDOFF_CODES:
            card = frappe.get_doc("Procurement Handoff Card", code)

            ev = card.evidence_links_json or ""
            self.assertTrue(ev.strip(), f"{code}: evidence_links_json must be non-empty")
            try:
                ev_obj = json.loads(ev)
            except Exception as exc:
                self.fail(f"{code}: evidence_links_json is not valid JSON: {exc}")
            # Evidence links are stored as {"links": [...]} by the normaliser
            links = ev_obj.get("links") if isinstance(ev_obj, dict) else ev_obj
            self.assertIsInstance(links, list, f"{code}: evidence links must be a list")
            self.assertGreater(len(links), 0, f"{code}: evidence_links_json must have at least one link")
            # Each link must have object_code
            for lnk in links:
                self.assertIn(
                    "object_code", lnk,
                    f"{code}: every evidence link must have an object_code",
                )

            tr = card.technical_refs_json or ""
            self.assertTrue(tr.strip(), f"{code}: technical_refs_json must be non-empty")
            try:
                tr_obj = json.loads(tr)
            except Exception as exc:
                self.fail(f"{code}: technical_refs_json is not valid JSON: {exc}")
            self.assertIsInstance(tr_obj, dict, f"{code}: technical_refs_json must be a JSON object")

    # ── Test 5: CLOSECERT and OPENREADY absent from base checkpoint ───────────
    def test_005_opening_cards_not_created_at_base_checkpoint(self):
        """SEED-TEST-R2-011-005: CLOSECERT and OPENREADY must NOT exist after base seed."""
        upsert_works_master_handoff_cards()

        for code in OPENING_HANDOFF_CODES:
            self.assertFalse(
                frappe.db.exists("Procurement Handoff Card", code),
                f"Opening card {code!r} must NOT be created by the base checkpoint seed",
            )
