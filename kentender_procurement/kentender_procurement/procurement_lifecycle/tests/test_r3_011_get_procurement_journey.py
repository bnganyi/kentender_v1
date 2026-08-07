# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R3-011 / LV-R3-011-01 — ``get_procurement_journey`` service tests.

## Tests

1. **AGG-001** — Response shape: WORKS master journey returns a dict with all
   required top-level keys from pack §9.1.

2. **AGG-002** — Header fields: ``journey_code``, ``title``, ``procuring_entity_code``,
   ``category``, ``method``, ``current_stage``, ``current_status``, ``next_action``
   match the WORKS seed specification values.

3. **AGG-003** — Steps: ``steps`` list contains 12 entries in correct order (delegates
   to R3-013; validates integration).

4. **AGG-004** — Handoff cards: ``handoff_cards`` contains the 7 base checkpoint
   handoff cards (STRATREF, BUDCONF, DEMAPP, PLANINCL, PKGREL, STDREADY, PUBCERT).

5. **AGG-005** — Evidence summary: ``evidence_summary`` has one entry per handoff
   card; each entry has required event shape fields (``occurred_at``, ``module``,
   ``event_type``, ``handoff_code``).

6. **AGG-006** — Blocker counts: ``blocker_count`` and ``critical_blocker_count``
   are derived from live steps; for the WORKS master seed (no blockers) both are 0.

7. **AGG-007** — Refs sub-dict: ``refs`` contains all spine reference fields;
   ``tm2_tender_ref`` == the seeded TM2 Tender Frappe name.

8. **ERR-001** — Blank input raises ``INVALID_JOURNEY_CODE``.

9. **ERR-002** — Non-existent journey code raises ``JOURNEY_NOT_FOUND`` via
   ``frappe.DoesNotExistError``.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r3_011_get_procurement_journey
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
from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
    load_procurement_lifecycle_works_master,
)
from kentender_procurement.procurement_lifecycle.journey_aggregate import (
    get_procurement_journey,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    JOURNEY_CODE,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"

# Expected WORKS master base checkpoint values (spec §4.2 / §9.1 + §9.4)
_EXPECTED_JOURNEY_CODE = "JRN-MOH-2026-001"
_EXPECTED_TITLE = "District Hospital Renovation Works"
_EXPECTED_PE_CODE = "PE-MOH"
_EXPECTED_CATEGORY = "Works"
_EXPECTED_METHOD = "Open Tender"
_EXPECTED_CURRENT_STAGE = "Tender Published"
_EXPECTED_CURRENT_STATUS = "Completed"
_EXPECTED_STEP_COUNT = 12

# Base checkpoint handoff codes (7 required; CLOSECERT and OPENREADY are optional)
_BASE_HANDOFF_CODES = {
    "STRATREF-MOH-2026-001",
    "BUDCONF-MOH-2026-001",
    "DEMAPP-MOH-2026-001",
    "PLANINCL-MOH-2026-001",
    "PKGREL-MOH-2026-001",
    "STDREADY-TND-MOH-2026-001",
    "PUBCERT-TND-MOH-2026-001",
}


class TestR3011GetProcurementJourney(IntegrationTestCase):
    """R3-011 — get_procurement_journey integration tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        cls.pe_name = ensure_procuring_entity(_PE_CODE, _PE_DISPLAY)

        for label, fn in (
            ("Strategy", upsert_works_master_strategy_hierarchy),
            ("Budget", upsert_works_master_budget),
            ("Demand", upsert_works_master_demand),
            ("Planning", upsert_works_master_planning),
            ("STD", upsert_works_master_std),
            ("Tender", upsert_works_master_tender),
        ):
            result = fn()
            assert result.get("ok"), f"{label} seed failed: {result}"

        plc_result = load_procurement_lifecycle_works_master(checkpoint="TENDER_PUBLISHED")
        assert plc_result.get("ok"), f"PLC base seed failed: {plc_result}"
        frappe.db.commit()

    # ------------------------------------------------------------------
    # Test 1 — AGG-001: required response shape
    # ------------------------------------------------------------------

    def test_01_response_has_required_top_level_keys(self):
        """Response dict contains all keys required by pack §9.1."""
        result = get_procurement_journey(JOURNEY_CODE)

        required_keys = {
            "journey_code",
            "title",
            "procuring_entity_code",
            "category",
            "method",
            "current_stage",
            "current_status",
            "next_action",
            "blocker_count",
            "critical_blocker_count",
            "steps",
            "handoff_cards",
            "evidence_summary",
        }
        missing = required_keys - set(result.keys())
        self.assertFalse(
            missing,
            f"Response is missing required keys: {missing}",
        )
        self.assertIsInstance(result["steps"], list)
        self.assertIsInstance(result["handoff_cards"], list)
        self.assertIsInstance(result["evidence_summary"], list)

    # ------------------------------------------------------------------
    # Test 2 — AGG-002: header field values from WORKS seed
    # ------------------------------------------------------------------

    def test_02_header_fields_match_works_seed_spec(self):
        """Header fields match WORKS master specification values."""
        result = get_procurement_journey(JOURNEY_CODE)

        self.assertEqual(result["journey_code"], _EXPECTED_JOURNEY_CODE)
        self.assertEqual(result["title"], _EXPECTED_TITLE)
        self.assertEqual(result["procuring_entity_code"], _EXPECTED_PE_CODE)
        self.assertEqual(result["category"], _EXPECTED_CATEGORY)
        self.assertEqual(result["method"], _EXPECTED_METHOD)
        self.assertEqual(result["current_stage"], _EXPECTED_CURRENT_STAGE)
        self.assertEqual(result["current_status"], _EXPECTED_CURRENT_STATUS)
        # next_action must be non-empty (Await tender closing / prepare bid opening readiness)
        self.assertTrue(result["next_action"], "next_action must be non-empty")

    # ------------------------------------------------------------------
    # Test 3 — AGG-003: step list from R3-013 integration
    # ------------------------------------------------------------------

    def test_03_steps_list_has_twelve_entries_in_order(self):
        """steps list has 12 entries (delegates to R3-013) in step_order order."""
        result = get_procurement_journey(JOURNEY_CODE)
        steps = result["steps"]

        self.assertEqual(len(steps), _EXPECTED_STEP_COUNT)
        # Verify step_order ascending
        orders = [s["step_order"] for s in steps]
        self.assertEqual(orders, sorted(orders))
        # Verify first and last step keys
        self.assertEqual(steps[0]["step_key"], "strategy")
        self.assertEqual(steps[-1]["step_key"], "contract")

    # ------------------------------------------------------------------
    # Test 4 — AGG-004: handoff cards
    # ------------------------------------------------------------------

    def test_04_handoff_cards_contains_base_checkpoint_cards(self):
        """handoff_cards includes all 7 base checkpoint handoff codes."""
        result = get_procurement_journey(JOURNEY_CODE)
        cards = result["handoff_cards"]

        card_codes = {c["handoff_code"] for c in cards}
        missing = _BASE_HANDOFF_CODES - card_codes
        self.assertFalse(
            missing,
            f"Expected handoff codes missing from result: {missing}",
        )

        # Each card has required shape fields
        for card in cards:
            self.assertIn("handoff_code", card)
            self.assertIn("status", card)
            self.assertIn("source_module", card)
            self.assertIn("target_module", card)
            self.assertIsInstance(card.get("locked_summary"), dict)
            self.assertIsInstance(card.get("passed_forward_summary"), dict)
            self.assertIsInstance(card.get("evidence_links"), list)
            self.assertIsInstance(card.get("technical_refs"), dict)

    # ------------------------------------------------------------------
    # Test 5 — AGG-005: evidence summary shape
    # ------------------------------------------------------------------

    def test_05_evidence_summary_shape(self):
        """Each evidence_summary entry has required event shape fields."""
        result = get_procurement_journey(JOURNEY_CODE)
        evidence = result["evidence_summary"]

        self.assertGreaterEqual(len(evidence), 7, "Expected at least 7 evidence rows")

        handoff_linked = [e for e in evidence if e.get("handoff_code")]
        self.assertGreaterEqual(len(handoff_linked), 7, "Seven base handoffs must emit events")

        required_evt_keys = {
            "occurred_at",
            "module",
            "event_type",
            "business_label",
            "object_type",
            "object_code",
            "handoff_code",
            "evidence_refs",
            "handoff_status",
            "stale_reason",
            "stale_warning",
            "audit_event_code",
        }
        for evt in evidence:
            missing = required_evt_keys - set(evt.keys())
            self.assertFalse(
                missing,
                f"Evidence event missing keys {missing}: {evt}",
            )
            self.assertIsNotNone(evt["module"], "module must be non-null")
            if evt.get("handoff_code") is not None:
                hc = str(evt["handoff_code"]).strip()
                self.assertTrue(hc, msg="when handoff_code is set it must be non-empty")

        pubcert = next(
            (x for x in evidence if x.get("handoff_code") == "PUBCERT-TND-MOH-2026-001"),
            None,
        )
        self.assertIsNotNone(pubcert, msg="WORKS timeline must contain PUBCERT")
        assert pubcert is not None
        self.assertIn(
            "PUBSNAP-TND-MOH-2026-001-V2",
            pubcert["evidence_refs"],
            msg="Publication snapshot surfaces in lifecycle evidence_refs (**R7-004**)",
        )

    # ------------------------------------------------------------------
    # Test 6 — AGG-006: blocker counts
    # ------------------------------------------------------------------

    def test_06_blocker_counts_derived_from_steps(self):
        """blocker_count and critical_blocker_count are 0 for WORKS master (no blockers)."""
        result = get_procurement_journey(JOURNEY_CODE)

        self.assertIsInstance(result["blocker_count"], int)
        self.assertIsInstance(result["critical_blocker_count"], int)
        self.assertEqual(result["blocker_count"], 0)
        self.assertEqual(result["critical_blocker_count"], 0)

    # ------------------------------------------------------------------
    # Test 7 — AGG-007: refs sub-dict
    # ------------------------------------------------------------------

    def test_07_refs_sub_dict_contains_tm2_tender_ref(self):
        """refs sub-dict is present and tm2_tender_ref is non-null for the WORKS master."""
        result = get_procurement_journey(JOURNEY_CODE)

        self.assertIn("refs", result)
        refs = result["refs"]
        self.assertIsNotNone(
            refs.get("tm2_tender_ref"),
            "tm2_tender_ref must be non-null for the WORKS master journey",
        )
        # strategy_ref, demand_ref, procurement_package_ref should also be present
        self.assertIsNotNone(refs.get("strategy_ref"))
        self.assertIsNotNone(refs.get("demand_ref"))
        self.assertIsNotNone(refs.get("procurement_package_ref"))

    # ------------------------------------------------------------------
    # Test 8 — ERR-001: blank input
    # ------------------------------------------------------------------

    def test_08_blank_input_raises_invalid_journey_code(self):
        """Blank journey_code raises INVALID_JOURNEY_CODE ValueError."""
        with self.assertRaises(ValueError) as ctx:
            get_procurement_journey("")
        self.assertIn("INVALID_JOURNEY_CODE", str(ctx.exception))

    # ------------------------------------------------------------------
    # Test 9 — ERR-002: non-existent journey
    # ------------------------------------------------------------------

    def test_09_nonexistent_journey_raises_does_not_exist(self):
        """Non-existent journey_code raises frappe.DoesNotExistError (JOURNEY_NOT_FOUND)."""
        with self.assertRaises(frappe.DoesNotExistError):
            get_procurement_journey("JRN-NONEXISTENT-9999")
