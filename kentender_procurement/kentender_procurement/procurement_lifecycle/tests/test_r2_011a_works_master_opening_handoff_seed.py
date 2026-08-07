# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R2-011A — WORKS master optional opening handoff card seed tests (spec §16.9–16.10).

Tests:
  1. SEED-TEST-R2-011A-001 — CLOSECERT and OPENREADY exist with correct §16.9–16.10 core fields.
  2. SEED-TEST-R2-011A-002 — locked_summary, passed_forward_summary, evidence_links_json and
                              technical_refs_json are valid non-empty JSON for both opening cards.
  3. SEED-TEST-R2-011A-003 — Journey step mutations applied: tender_closing → Completed,
                              opening_readiness → Ready for Handoff; header updated.
  4. SEED-TEST-R2-011A-004 — Idempotent: second run returns ok=True, exactly 9 cards, no duplicates.
  5. SEED-TEST-R2-011A-005 — All 7 base cards remain intact after opening checkpoint seed.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r2_011a_works_master_opening_handoff_seed
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
from kentender_procurement.procurement_lifecycle.seeds.works_master_opening_handoff_seed import (
    upsert_works_master_opening_handoff_cards,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    BASE_HANDOFF_CODES,
    JOURNEY_CODE,
    OPENING_HANDOFF_CODES,
)

_PE_CODE = "PE-MOH"
_PE_NAME_DISPLAY = "Ministry of Health"

# Spec §16.9–16.10 expected core field values
_OPENING_CARD_SPEC = {
    "CLOSECERT-TND-MOH-2026-001": {
        "handoff_title": "Tender Closing Certificate",
        "status": "Consumed",
        "source_module": "Tender Management",
        "target_module": "Bid Opening",
        "source_object_type": "Tender Closing Record",
        "source_object_code": "CLS-TND-MOH-2026-001",
        "target_object_type": "Opening Readiness Record",
        "target_object_code": "ORR-TND-MOH-2026-001",
        "generated_by": "SYSTEM",
        "consumed_by": "SYSTEM",
    },
    "OPENREADY-TND-MOH-2026-001": {
        "handoff_title": "Opening Readiness Record",
        "status": "Handed Off",
        "source_module": "Tender Management",
        "target_module": "Bid Opening",
        "source_object_type": "Opening Readiness Record",
        "source_object_code": "ORR-TND-MOH-2026-001",
        "target_object_type": "Bid Opening Session",
        "target_object_code": "",
        "generated_by": "SYSTEM",
        "consumed_by": "",
    },
}

# Expected locked_summary key samples per card (spot-checks)
_LOCKED_SUMMARY_REQUIRED_KEYS = {
    "CLOSECERT-TND-MOH-2026-001": {"submission_deadline", "closed_at", "submission_window_closed"},
    "OPENREADY-TND-MOH-2026-001": {"opening_model", "publication_snapshot", "opening_scheduled_at"},
}

# Expected passed_forward_summary key samples per card (spot-checks)
_PASSED_FORWARD_REQUIRED_KEYS = {
    "CLOSECERT-TND-MOH-2026-001": {"valid_submission_count", "sealed_submission_refs_available"},
    "OPENREADY-TND-MOH-2026-001": {"sealed_submission_refs", "opening_register_rules_ready"},
}


def _clean_plc_to_base() -> None:
    """Reset PLC to TENDER_PUBLISHED (removes opening cards) — safe tearDown."""
    from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
        load_procurement_lifecycle_works_master,
    )
    load_procurement_lifecycle_works_master(reset=True, checkpoint="TENDER_PUBLISHED")


class TestR2011aWorksMasterOpeningHandoffSeed(IntegrationTestCase):
    """R2-011A — Optional opening handoff cards seed (spec §16.9–16.10)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        cls.pe_name = ensure_procuring_entity(_PE_CODE, _PE_NAME_DISPLAY)

        # Prerequisites R2-004 through R2-010
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

        j = upsert_works_master_journey()
        assert j.get("ok"), f"Journey prerequisite failed: {j}"

    def tearDown(self):
        _clean_plc_to_base()

    # ── Test 1: CLOSECERT and OPENREADY core fields ───────────────────────────
    def test_001_opening_cards_have_correct_spec_core_fields(self):
        """SEED-TEST-R2-011A-001: CLOSECERT and OPENREADY exist with spec §16.9–16.10 core fields."""
        out = upsert_works_master_opening_handoff_cards()
        self.assertTrue(out.get("ok"), f"Seed returned error: {out}")
        self.assertEqual(len(out["handoff_codes"]), len(OPENING_HANDOFF_CODES))

        for code, expected in _OPENING_CARD_SPEC.items():
            self.assertTrue(
                frappe.db.exists("Procurement Handoff Card", code),
                f"Opening card {code!r} must exist after OPENING_READY seed",
            )
            card = frappe.get_doc("Procurement Handoff Card", code)

            self.assertEqual(card.handoff_title, expected["handoff_title"], f"{code} handoff_title §16")
            self.assertEqual(card.status, expected["status"], f"{code} status §16")
            self.assertEqual(card.source_module, expected["source_module"], f"{code} source_module §16")
            self.assertEqual(card.target_module, expected["target_module"], f"{code} target_module §16")
            self.assertEqual(
                card.source_object_type, expected["source_object_type"], f"{code} source_object_type §16"
            )
            self.assertEqual(
                card.source_object_code, expected["source_object_code"], f"{code} source_object_code §16"
            )
            self.assertEqual(
                card.target_object_type, expected["target_object_type"], f"{code} target_object_type §16"
            )
            self.assertEqual(
                (card.target_object_code or "").strip(),
                expected["target_object_code"],
                f"{code} target_object_code §16",
            )
            self.assertEqual(card.generated_by, expected["generated_by"], f"{code} generated_by §16")
            self.assertEqual(
                (card.consumed_by or "").strip(), expected["consumed_by"], f"{code} consumed_by §16"
            )
            # Journey linkage
            self.assertEqual(card.journey_code, JOURNEY_CODE, f"{code} must be linked to master journey")
            self.assertEqual(cint(card.is_master_seed), 1, f"{code} is_master_seed must be 1")

    # ── Test 2: JSON payloads ─────────────────────────────────────────────────
    def test_002_opening_cards_json_payloads_valid(self):
        """SEED-TEST-R2-011A-002: locked_summary, passed_forward_summary, evidence_links and technical_refs are valid JSON."""
        upsert_works_master_opening_handoff_cards()

        for code in OPENING_HANDOFF_CODES:
            card = frappe.get_doc("Procurement Handoff Card", code)

            # locked_summary
            locked_raw = card.locked_summary or ""
            self.assertTrue(locked_raw.strip(), f"{code}: locked_summary must be non-empty")
            try:
                locked = json.loads(locked_raw)
            except Exception as exc:
                self.fail(f"{code}: locked_summary is not valid JSON: {exc}")
            self.assertIsInstance(locked, dict, f"{code}: locked_summary must be a JSON object")
            for key in _LOCKED_SUMMARY_REQUIRED_KEYS[code]:
                self.assertIn(key, locked, f"{code}: locked_summary must contain key {key!r}")

            # passed_forward_summary
            passed_raw = card.passed_forward_summary or ""
            self.assertTrue(passed_raw.strip(), f"{code}: passed_forward_summary must be non-empty")
            try:
                passed = json.loads(passed_raw)
            except Exception as exc:
                self.fail(f"{code}: passed_forward_summary is not valid JSON: {exc}")
            self.assertIsInstance(passed, dict, f"{code}: passed_forward_summary must be a JSON object")
            for key in _PASSED_FORWARD_REQUIRED_KEYS[code]:
                self.assertIn(key, passed, f"{code}: passed_forward_summary must contain key {key!r}")

            # evidence_links_json
            ev_raw = card.evidence_links_json or ""
            self.assertTrue(ev_raw.strip(), f"{code}: evidence_links_json must be non-empty")
            try:
                ev = json.loads(ev_raw)
            except Exception as exc:
                self.fail(f"{code}: evidence_links_json is not valid JSON: {exc}")
            links = ev.get("links") if isinstance(ev, dict) else ev
            self.assertIsInstance(links, list, f"{code}: evidence links must be a list")
            self.assertGreater(len(links), 0, f"{code}: evidence_links_json must have at least one link")

            # technical_refs_json
            tr_raw = card.technical_refs_json or ""
            self.assertTrue(tr_raw.strip(), f"{code}: technical_refs_json must be non-empty")
            try:
                tr = json.loads(tr_raw)
            except Exception as exc:
                self.fail(f"{code}: technical_refs_json is not valid JSON: {exc}")
            self.assertIsInstance(tr, dict, f"{code}: technical_refs_json must be a JSON object")
            self.assertTrue(tr, f"{code}: technical_refs_json must not be empty dict")

    # ── Test 3: journey step mutations ────────────────────────────────────────
    def test_003_journey_step_mutations_applied_at_opening_checkpoint(self):
        """SEED-TEST-R2-011A-003: Journey updated — tender_closing → Completed, opening_readiness → Ready for Handoff."""
        upsert_works_master_opening_handoff_cards()

        journey = frappe.get_doc("Procurement Journey", JOURNEY_CODE)

        # Header mutations
        self.assertEqual(journey.current_stage_key, "opening_ready", "Journey current_stage_key must be opening_ready")
        self.assertEqual(
            journey.opening_readiness_ref, "ORR-TND-MOH-2026-001", "Journey opening_readiness_ref must be set"
        )

        # Step-level mutations
        steps_by_key = {s.step_key: s for s in journey.steps}

        closing_step = steps_by_key.get("tender_closing")
        self.assertIsNotNone(closing_step, "Step tender_closing must exist")
        self.assertEqual(closing_step.status_category, "Completed", "tender_closing status_category §15")
        self.assertEqual(closing_step.source_object_code, "CLS-TND-MOH-2026-001", "tender_closing source_object_code §15")
        self.assertEqual(closing_step.handoff_code, "CLOSECERT-TND-MOH-2026-001", "tender_closing handoff_code §15")

        opening_step = steps_by_key.get("opening_readiness")
        self.assertIsNotNone(opening_step, "Step opening_readiness must exist")
        self.assertEqual(opening_step.status_category, "Ready for Handoff", "opening_readiness status_category §15")
        self.assertEqual(
            opening_step.source_object_code, "ORR-TND-MOH-2026-001", "opening_readiness source_object_code §15"
        )
        self.assertEqual(
            opening_step.handoff_code, "OPENREADY-TND-MOH-2026-001", "opening_readiness handoff_code §15"
        )

    # ── Test 4: idempotency ───────────────────────────────────────────────────
    def test_004_idempotent_second_run_no_duplicates(self):
        """SEED-TEST-R2-011A-004: Running twice returns ok=True with exactly 9 cards (7 base + 2 opening)."""
        first = upsert_works_master_opening_handoff_cards()
        self.assertTrue(first.get("ok"), f"First run error: {first}")

        second = upsert_works_master_opening_handoff_cards()
        self.assertTrue(second.get("ok"), f"Second run error: {second}")

        all_codes = list(BASE_HANDOFF_CODES) + list(OPENING_HANDOFF_CODES)
        for code in all_codes:
            count = frappe.db.sql(
                "SELECT COUNT(*) FROM `tabProcurement Handoff Card` WHERE handoff_code=%s",
                (code,),
            )[0][0]
            self.assertEqual(count, 1, f"Expected exactly 1 card for {code!r} after two runs")

    # ── Test 5: all 7 base cards remain intact ────────────────────────────────
    def test_005_base_cards_intact_after_opening_checkpoint(self):
        """SEED-TEST-R2-011A-005: All 7 base cards remain present and linked after opening seed."""
        upsert_works_master_opening_handoff_cards()

        for code in BASE_HANDOFF_CODES:
            self.assertTrue(
                frappe.db.exists("Procurement Handoff Card", code),
                f"Base card {code!r} must still exist after OPENING_READY checkpoint",
            )
            card_journey = frappe.db.get_value("Procurement Handoff Card", code, "journey_code")
            self.assertEqual(
                card_journey,
                JOURNEY_CODE,
                f"Base card {code!r} must still be linked to {JOURNEY_CODE}",
            )
