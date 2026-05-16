# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R3-010 / LV-R3-010-01 — ``validate_handoff_card_freshness`` service tests.

## Tests

1. **FRESH-001** — Fresh card (no drift): a freshly created handoff card returns
   ``{"fresh": True, "stale_reason": null}`` when the source object has not changed.

2. **STALE-001** — Fingerprint drift: a card with a stored ``source_state_hash`` that
   differs from the live fingerprint → card transitions to ``Stale`` and response
   includes ``"fresh": False, "status": "Stale", "stale_reason"``, ``"required_action"``.

3. **STALE-002** — Source-not-found: calling on a card whose ``source_object_code``
   refers to a deleted/non-existent object → card transitions to ``Stale`` with
   ``stale_reason="source_object_not_found..."``.

4. **STALE-003** — Already-stale: a card that is already ``Stale`` returns the
   existing stale info without re-marking.

5. **TERMINAL-001** — Terminal status: a card with status ``Cancelled`` (or
   ``Superseded`` / ``Audit Only``) returns ``fresh=True`` (staleness N/A).

6. **NOFP-001** — No source_state_hash but modified-timestamp fallback: when a card
   has no stored hash and the source was recently modified (simulated), the service
   marks the card Stale.

7. **ERR-001** — Input validation: blank/invalid ``handoff_code`` raises
   ``INVALID_HANDOFF_CODE``; non-existent code raises ``HANDOFF_NOT_FOUND``.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r3_010_handoff_freshness
"""

from __future__ import annotations

import hashlib
import json
import time

import frappe
from frappe.tests import IntegrationTestCase

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
from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
    load_procurement_lifecycle_works_master,
)
from kentender_procurement.procurement_lifecycle.handoff_freshness import (
    validate_handoff_card_freshness,
    _fingerprint,
    _live_fingerprint,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    JOURNEY_CODE,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"

# WORKS master codes used as test anchors
_PKGREL_CODE = "PKGREL-MOH-2026-001"  # Procurement Package → Planning Release Package
_DEMAPP_CODE = "DEMAPP-MOH-2026-001"  # Demand → Demand Approval Certificate
_PUBCERT_CODE = "PUBCERT-TND-MOH-2026-001"  # TM2 Tender → Publication Certificate

# Test-only synthetic handoff code for fabricated cards
_TEST_HANDOFF_CODE = "TEST-FRESH-HANDOFF-R3010"


def _make_fingerprint(data: dict) -> str:
    """Compute a SHA-1 fingerprint matching the service's internal logic."""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha1(canonical.encode("utf-8"), usedforsecurity=False).hexdigest()


def _create_test_handoff(
    handoff_code: str = _TEST_HANDOFF_CODE,
    status: str = "Handed Off",
    source_object_type: str = "Procurement Package",
    source_object_code: str = "PKG-MOH-2026-001",
    source_state_hash: str | None = None,
) -> str:
    """Insert a minimal Procurement Handoff Card and return its Frappe name."""
    doc = frappe.get_doc(
        {
            "doctype": "Procurement Handoff Card",
            "handoff_code": handoff_code,
            "handoff_title": "Test Fresh Handoff",
            "journey_code": JOURNEY_CODE,
            "source_module": "Procurement Planning",
            "target_module": "Tender Management",
            "source_object_type": source_object_type,
            "source_object_code": source_object_code,
            "status": status,
            "generated_by": "SYSTEM",
            "next_action": "Test next action.",
            "locked_summary": "{}",
            "passed_forward_summary": "{}",
            "evidence_links_json": '{"links":[]}',
            "source_state_hash": source_state_hash,
        }
    )
    doc.flags.ignore_permissions = True
    doc.flags.ignore_mandatory = True
    doc.insert()
    frappe.db.commit()
    return doc.name


def _delete_test_handoff(handoff_code: str = _TEST_HANDOFF_CODE) -> None:
    for name in frappe.db.get_all(
        "Procurement Handoff Card", filters={"handoff_code": handoff_code}, pluck="name"
    ):
        frappe.delete_doc("Procurement Handoff Card", name, force=True)
    frappe.db.commit()


class TestR3010HandoffFreshness(IntegrationTestCase):
    """R3-010 — validate_handoff_card_freshness integration tests."""

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

    @classmethod
    def tearDownClass(cls):
        frappe.set_user("Administrator")
        _delete_test_handoff()
        super().tearDownClass()

    def setUp(self):
        frappe.set_user("Administrator")
        _delete_test_handoff()

    # ------------------------------------------------------------------
    # Test 1 — FRESH-001: fresh card (no drift)
    # ------------------------------------------------------------------

    def test_01_fresh_card_with_matching_hash(self):
        """Card with matching source_state_hash returns fresh=True, stale_reason=null."""
        # Compute the live fingerprint of PKG-MOH-2026-001 (Procurement Package)
        live_fp = _live_fingerprint("Procurement Package", "PKG-MOH-2026-001")
        self.assertIsNotNone(live_fp, "Live fingerprint must be computable for WORKS master package")

        _create_test_handoff(
            handoff_code=_TEST_HANDOFF_CODE,
            status="Handed Off",
            source_object_type="Procurement Package",
            source_object_code="PKG-MOH-2026-001",
            source_state_hash=live_fp,
        )
        result = validate_handoff_card_freshness(_TEST_HANDOFF_CODE)

        self.assertTrue(result.get("fresh"), f"Expected fresh=True; got: {result}")
        self.assertIsNone(result.get("stale_reason"))
        self.assertEqual(result["status"], "Handed Off")
        self.assertEqual(result["handoff_code"], _TEST_HANDOFF_CODE)

    # ------------------------------------------------------------------
    # Test 2 — STALE-001: fingerprint drift marks card Stale
    # ------------------------------------------------------------------

    def test_02_stale_on_fingerprint_drift(self):
        """Card with stale source_state_hash → marked Stale; response includes required_action."""
        _create_test_handoff(
            handoff_code=_TEST_HANDOFF_CODE,
            status="Handed Off",
            source_object_type="Procurement Package",
            source_object_code="PKG-MOH-2026-001",
            source_state_hash="0000000000000000000000000000000000000000",  # deliberately wrong
        )
        result = validate_handoff_card_freshness(_TEST_HANDOFF_CODE)

        self.assertFalse(result.get("fresh"), f"Expected fresh=False; got: {result}")
        self.assertEqual(result["status"], "Stale")
        self.assertIsNotNone(result.get("stale_reason"))
        self.assertIn("Procurement Package", result.get("stale_reason", ""))
        self.assertIsNotNone(result.get("required_action"))

        # Verify the card was actually updated in DB
        db_status = frappe.db.get_value(
            "Procurement Handoff Card", {"handoff_code": _TEST_HANDOFF_CODE}, "status"
        )
        self.assertEqual(db_status, "Stale")

    # ------------------------------------------------------------------
    # Test 3 — STALE-002: source-not-found marks card Stale
    # ------------------------------------------------------------------

    def test_03_stale_on_source_not_found(self):
        """Card whose source_object_code refers to a non-existent record → Stale."""
        _create_test_handoff(
            handoff_code=_TEST_HANDOFF_CODE,
            status="Handed Off",
            source_object_type="Demand",
            source_object_code="DEM-NONEXISTENT-9999",
            source_state_hash=None,
        )
        result = validate_handoff_card_freshness(_TEST_HANDOFF_CODE)

        self.assertFalse(result.get("fresh"))
        self.assertEqual(result["status"], "Stale")
        self.assertIn("no longer exists", str(result.get("stale_reason", "")))

        db_status = frappe.db.get_value(
            "Procurement Handoff Card", {"handoff_code": _TEST_HANDOFF_CODE}, "status"
        )
        self.assertEqual(db_status, "Stale")

    # ------------------------------------------------------------------
    # Test 4 — STALE-003: already-Stale card returns existing info without re-marking
    # ------------------------------------------------------------------

    def test_04_already_stale_card_returns_stale_info(self):
        """Already-Stale card returns existing stale information without mutation."""
        _create_test_handoff(
            handoff_code=_TEST_HANDOFF_CODE,
            status="Stale",
            source_object_type="Procurement Package",
            source_object_code="PKG-MOH-2026-001",
            source_state_hash=None,
        )
        # Plant a stale_reason directly
        frappe.db.set_value(
            "Procurement Handoff Card",
            {"handoff_code": _TEST_HANDOFF_CODE},
            "stale_reason",
            "pre-existing stale reason",
            update_modified=False,
        )
        frappe.db.commit()

        result = validate_handoff_card_freshness(_TEST_HANDOFF_CODE)

        self.assertFalse(result.get("fresh"))
        self.assertEqual(result["status"], "Stale")
        # Should preserve the pre-existing stale_reason
        self.assertIn("pre-existing", str(result.get("stale_reason", "")))

    # ------------------------------------------------------------------
    # Test 5 — TERMINAL-001: terminal status returns fresh=True (N/A)
    # ------------------------------------------------------------------

    def test_05_terminal_status_returns_fresh_not_applicable(self):
        """Cancelled, Superseded, and Audit Only cards return fresh=True (N/A)."""
        for terminal_status in ("Cancelled", "Superseded", "Audit Only"):
            _delete_test_handoff()
            _create_test_handoff(
                handoff_code=_TEST_HANDOFF_CODE,
                status=terminal_status,
                source_object_type="Procurement Package",
                source_object_code="PKG-MOH-2026-001",
            )
            result = validate_handoff_card_freshness(_TEST_HANDOFF_CODE)
            self.assertTrue(
                result.get("fresh"),
                f"Expected fresh=True for terminal status {terminal_status!r}; got: {result}",
            )
            self.assertIsNone(result.get("stale_reason"))
            self.assertEqual(result["status"], terminal_status)

    # ------------------------------------------------------------------
    # Test 6 — NOFP-001: modified-timestamp fallback
    # ------------------------------------------------------------------

    def test_06_timestamp_fallback_when_no_stored_hash(self):
        """No stored hash + source modified after card → card marked Stale via timestamp fallback."""
        # Create card first
        card_name = _create_test_handoff(
            handoff_code=_TEST_HANDOFF_CODE,
            status="Handed Off",
            source_object_type="Procurement Package",
            source_object_code="PKG-MOH-2026-001",
            source_state_hash=None,
        )
        # Back-date the card's modified to before epoch + 10 years so source is "newer"
        frappe.db.set_value(
            "Procurement Handoff Card",
            card_name,
            "modified",
            "2020-01-01 00:00:00",
            update_modified=False,
        )
        frappe.db.commit()

        result = validate_handoff_card_freshness(_TEST_HANDOFF_CODE)

        # Source (Procurement Package PKG-MOH-2026-001) was definitely modified after
        # 2020-01-01 (the seed ran in 2026) → service should mark Stale
        self.assertFalse(
            result.get("fresh"),
            f"Expected fresh=False (timestamp fallback); got: {result}",
        )
        self.assertEqual(result["status"], "Stale")
        db_status = frappe.db.get_value(
            "Procurement Handoff Card", {"handoff_code": _TEST_HANDOFF_CODE}, "status"
        )
        self.assertEqual(db_status, "Stale")

    # ------------------------------------------------------------------
    # Test 7 — ERR-001: input validation
    # ------------------------------------------------------------------

    def test_07_blank_input_raises_invalid_handoff_code(self):
        """Blank handoff_code raises INVALID_HANDOFF_CODE."""
        with self.assertRaises(ValueError) as ctx:
            validate_handoff_card_freshness("")
        self.assertIn("INVALID_HANDOFF_CODE", str(ctx.exception))

    def test_07b_nonexistent_code_raises_handoff_not_found(self):
        """Non-existent handoff_code raises HANDOFF_NOT_FOUND."""
        with self.assertRaises(ValueError) as ctx:
            validate_handoff_card_freshness("NONEXISTENT-HANDOFF-9999")
        self.assertIn("HANDOFF_NOT_FOUND", str(ctx.exception))

    # ------------------------------------------------------------------
    # Test 8 — SEED-001: WORKS master seed card freshness check (smoke)
    # ------------------------------------------------------------------

    def test_08_works_master_pkgrel_card_freshness_smoke(self):
        """Smoke: PKGREL WORKS master card (no stored hash) returns a valid freshness dict."""
        # The PKGREL card was created without a stored source_state_hash.
        # Since the seed was just applied, the source Procurement Package was also
        # recently created. Depending on timing, it may or may not be flagged stale.
        # The key requirement is that the function returns a valid dict without errors.
        result = validate_handoff_card_freshness(_PKGREL_CODE)

        self.assertIn("handoff_code", result)
        self.assertIn("fresh", result)
        self.assertIn("status", result)
        self.assertIsInstance(result["fresh"], bool)
        # handoff_code must match
        self.assertEqual(result["handoff_code"], _PKGREL_CODE)
