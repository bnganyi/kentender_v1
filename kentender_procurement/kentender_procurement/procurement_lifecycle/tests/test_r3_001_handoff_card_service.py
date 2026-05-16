# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R3-001 — ``create_or_update_handoff_card`` generic upsert service tests.

## Tests

1. **SVC-TEST-R3-001-001** — Happy path: valid payload creates a new card with all
   required fields persisted correctly.

2. **SVC-TEST-R3-001-002** — Idempotency / update: calling twice with the same
   ``handoff_code`` updates the existing card (``action="updated"``), does not
   duplicate records, and returns ``ok=True``.

3. **SVC-TEST-R3-001-003** — Missing required field raises ``ValueError`` with code
   ``MISSING_REQUIRED_FIELD``.

4. **SVC-TEST-R3-001-004** — Invalid status raises ``ValueError`` with code
   ``INVALID_STATUS``.

5. **SVC-TEST-R3-001-005** — Non-existent ``journey_code`` raises
   ``frappe.DoesNotExistError`` with title ``JOURNEY_NOT_FOUND``.

6. **SVC-TEST-R3-001-006** — Source module ownership is preserved: ``source_module``
   set on create is not overwritten by an update that passes a different value.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r3_001_handoff_card_service
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_strategy.seeds.works_master_strategy_hierarchy import (
    upsert_works_master_strategy_hierarchy,
)
from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
    load_procurement_lifecycle_works_master,
)
from kentender_procurement.procurement_lifecycle.handoff_card_service import (
    create_or_update_handoff_card,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    JOURNEY_CODE,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"

# A test-specific handoff code that will not clash with WORKS master seed cards
_TEST_CODE = "TEST-HANDOFF-R3001-001"


def _base_payload(**overrides: object) -> dict:
    """Minimal valid payload for a test handoff card."""
    base = {
        "handoff_code": _TEST_CODE,
        "handoff_title": "R3-001 Test Handoff",
        "journey_code": JOURNEY_CODE,
        "source_module": "Strategy",
        "target_module": "Budget",
        "status": "Ready",
        "locked_summary": {"test_key": "test_value"},
        "passed_forward_summary": {"info": "passed"},
        "next_action": "Do the next thing.",
        "evidence_links": [
            {
                "label": "Test Object",
                "object_type": "Strategy Objective",
                "object_code": "OBJ-TEST-001",
                "module": "Strategy",
                "route": "/app/strategy-objective/OBJ-TEST-001",
                "visibility": "Internal",
            }
        ],
        "technical_refs": {"ref_key": "ref_value"},
    }
    base.update(overrides)
    return base


class TestR3001HandoffCardService(IntegrationTestCase):
    """R3-001 — Generic handoff upsert service tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        cls.pe_name = ensure_procuring_entity(_PE_CODE, _PE_DISPLAY)

        # Ensure journey exists (only needs base strategy + PLC)
        upsert_works_master_strategy_hierarchy()
        plc_result = load_procurement_lifecycle_works_master(checkpoint="TENDER_PUBLISHED")
        assert plc_result.get("ok"), f"PLC base seed failed: {plc_result}"
        frappe.db.commit()

    def setUp(self):
        # Remove the test card before each test for isolation
        if frappe.db.exists("Procurement Handoff Card", {"handoff_code": _TEST_CODE}):
            frappe.db.delete("Procurement Handoff Card", {"handoff_code": _TEST_CODE})
            frappe.db.commit()

    def tearDown(self):
        if frappe.db.exists("Procurement Handoff Card", {"handoff_code": _TEST_CODE}):
            frappe.db.delete("Procurement Handoff Card", {"handoff_code": _TEST_CODE})
            frappe.db.commit()

    # ------------------------------------------------------------------
    # SVC-TEST-R3-001-001 — Happy path
    # ------------------------------------------------------------------
    def test_001_happy_path_creates_card_with_persisted_fields(self):
        """Valid payload creates a card and persists all required fields."""
        result = create_or_update_handoff_card(_base_payload())
        frappe.db.commit()

        self.assertTrue(result.get("ok"), f"Expected ok=True; got {result}")
        self.assertEqual(result["action"], "created")
        self.assertEqual(result["handoff_code"], _TEST_CODE)
        self.assertEqual(result["warnings"], [])

        # Verify persisted
        card = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _TEST_CODE},
            ["handoff_title", "journey_code", "source_module", "target_module",
             "status", "locked_summary", "evidence_links_json", "technical_refs_json"],
            as_dict=True,
        )
        self.assertIsNotNone(card, "Card must exist in DB after creation")
        self.assertEqual(card["handoff_title"], "R3-001 Test Handoff")
        self.assertEqual(card["journey_code"], JOURNEY_CODE)
        self.assertEqual(card["source_module"], "Strategy")
        self.assertEqual(card["status"], "Ready")

        locked = json.loads(card["locked_summary"])
        self.assertEqual(locked.get("test_key"), "test_value")

        ev = json.loads(card["evidence_links_json"])
        self.assertIn("links", ev)
        self.assertEqual(len(ev["links"]), 1)
        self.assertEqual(ev["links"][0]["object_code"], "OBJ-TEST-001")

        tech = json.loads(card["technical_refs_json"])
        self.assertEqual(tech.get("ref_key"), "ref_value")

    # ------------------------------------------------------------------
    # SVC-TEST-R3-001-002 — Idempotency / update
    # ------------------------------------------------------------------
    def test_002_idempotent_update_does_not_duplicate(self):
        """Calling twice updates in place; count stays 1; action=updated second time."""
        create_or_update_handoff_card(_base_payload())
        frappe.db.commit()

        result2 = create_or_update_handoff_card(
            _base_payload(handoff_title="R3-001 Updated Title", status="Consumed")
        )
        frappe.db.commit()

        self.assertTrue(result2.get("ok"))
        self.assertEqual(result2["action"], "updated")

        count = frappe.db.count(
            "Procurement Handoff Card", filters={"handoff_code": _TEST_CODE}
        )
        self.assertEqual(count, 1, "Must not duplicate records on re-run")

        title = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _TEST_CODE},
            "handoff_title",
        )
        self.assertEqual(title, "R3-001 Updated Title")

    # ------------------------------------------------------------------
    # SVC-TEST-R3-001-003 — Missing required field
    # ------------------------------------------------------------------
    def test_003_missing_required_field_raises_value_error(self):
        """Missing required keys raise ValueError with MISSING_REQUIRED_FIELD."""
        for missing_key in ("handoff_code", "handoff_title", "journey_code",
                            "source_module", "target_module", "status"):
            with self.subTest(missing=missing_key):
                p = _base_payload()
                del p[missing_key]
                with self.assertRaises(ValueError) as ctx:
                    create_or_update_handoff_card(p)
                self.assertIn("MISSING_REQUIRED_FIELD", str(ctx.exception))

    # ------------------------------------------------------------------
    # SVC-TEST-R3-001-004 — Invalid status
    # ------------------------------------------------------------------
    def test_004_invalid_status_raises_value_error(self):
        """Bad status value raises ValueError with INVALID_STATUS."""
        with self.assertRaises(ValueError) as ctx:
            create_or_update_handoff_card(_base_payload(status="NOT_A_REAL_STATUS"))
        self.assertIn("INVALID_STATUS", str(ctx.exception))

    # ------------------------------------------------------------------
    # SVC-TEST-R3-001-005 — Journey not found
    # ------------------------------------------------------------------
    def test_005_missing_journey_raises_does_not_exist(self):
        """Non-existent journey_code raises DoesNotExistError (JOURNEY_NOT_FOUND)."""
        with self.assertRaises(frappe.DoesNotExistError):
            create_or_update_handoff_card(
                _base_payload(journey_code="JRN-DOES-NOT-EXIST-R3001")
            )

    # ------------------------------------------------------------------
    # SVC-TEST-R3-001-006 — Source module ownership
    # ------------------------------------------------------------------
    def test_006_source_module_ownership_preserved_on_update(self):
        """source_module set on create is preserved even when update passes a different value."""
        create_or_update_handoff_card(_base_payload(source_module="Strategy"))
        frappe.db.commit()

        # Update with a different source_module — should be ignored
        create_or_update_handoff_card(
            _base_payload(source_module="INJECTED_MODULE", status="Consumed")
        )
        frappe.db.commit()

        stored = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _TEST_CODE},
            "source_module",
        )
        self.assertEqual(
            stored, "Strategy",
            "source_module must be preserved from the initial create call",
        )
