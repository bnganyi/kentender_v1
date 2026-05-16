# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R3-002 — ``create_strategy_alignment_reference`` service tests.

## Tests

1. **STRAT-TEST-R3-002-001** — Happy path: valid ``(strategy_ref, journey_code)``
   creates a handoff card with the correct code (``STRATREF-MOH-2026-001``),
   source fields, and non-empty ``locked_summary`` / ``passed_forward_summary``.

2. **STRAT-TEST-R3-002-002** — Idempotency: re-running returns ``action="updated"``;
   only one card exists for ``STRATREF-MOH-2026-001``.

3. **STRAT-TEST-R3-002-003** — Card contains a ``Strategy Objective`` evidence link
   and non-empty ``technical_refs`` with ``programme_code`` and ``target_code``.

4. **STRAT-TEST-R3-002-004** — Unknown ``strategy_ref`` raises ``ValueError`` with
   code ``OBJECTIVE_NOT_FOUND``.

5. **STRAT-TEST-R3-002-005** — Blank inputs raise ``ValueError`` with codes
   ``INVALID_STRATEGY_REF`` / ``INVALID_JOURNEY_CODE``.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r3_002_strategy_alignment_handoff
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
from kentender_procurement.procurement_lifecycle.strategy_alignment_handoff import (
    create_strategy_alignment_reference,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    JOURNEY_CODE,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"

# WORKS master codes (spec §4.2 / §16.2)
_OBJECTIVE_CODE = "OBJ-MOH-HOSP-RENOV"
_EXPECTED_HANDOFF_CODE = "STRATREF-MOH-2026-001"


class TestR3002StrategyAlignmentHandoff(IntegrationTestCase):
    """R3-002 — Strategy alignment handoff service tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        cls.pe_name = ensure_procuring_entity(_PE_CODE, _PE_DISPLAY)

        # Seed strategy hierarchy and journey
        result = upsert_works_master_strategy_hierarchy()
        assert result.get("ok"), f"Strategy seed failed: {result}"

        plc_result = load_procurement_lifecycle_works_master(checkpoint="TENDER_PUBLISHED")
        assert plc_result.get("ok"), f"PLC base seed failed: {plc_result}"
        frappe.db.commit()

    # ------------------------------------------------------------------
    # STRAT-TEST-R3-002-001 — Happy path
    # ------------------------------------------------------------------
    def test_001_creates_stratref_card_with_correct_fields(self):
        """Service creates STRATREF card with expected code and required field values."""
        result = create_strategy_alignment_reference(_OBJECTIVE_CODE, JOURNEY_CODE)
        frappe.db.commit()

        self.assertTrue(result.get("ok"), f"Expected ok=True; got {result}")
        self.assertIn(result["action"], {"created", "updated"})
        self.assertEqual(result["handoff_code"], _EXPECTED_HANDOFF_CODE)

        card = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
            ["handoff_title", "source_module", "target_module",
             "source_object_type", "source_object_code",
             "status", "journey_code", "locked_summary", "passed_forward_summary"],
            as_dict=True,
        )
        self.assertIsNotNone(card, "STRATREF card must exist in DB")
        self.assertEqual(card["handoff_title"], "Strategy Alignment Reference")
        self.assertEqual(card["source_module"], "Strategy")
        self.assertEqual(card["target_module"], "Budget")
        self.assertEqual(card["source_object_type"], "Strategy Objective")
        self.assertEqual(card["source_object_code"], _OBJECTIVE_CODE)
        self.assertEqual(card["status"], "Consumed")
        self.assertEqual(card["journey_code"], JOURNEY_CODE)

        locked = json.loads(card["locked_summary"])
        self.assertIn("objective", locked)
        self.assertEqual(locked["objective"], _OBJECTIVE_CODE)

        passed = json.loads(card["passed_forward_summary"])
        self.assertIn("strategic_priority", passed)
        self.assertTrue(passed["strategic_priority"])

    # ------------------------------------------------------------------
    # STRAT-TEST-R3-002-002 — Idempotency
    # ------------------------------------------------------------------
    def test_002_idempotent_no_duplicate(self):
        """Re-running creates only one STRATREF card; action=updated on second call."""
        create_strategy_alignment_reference(_OBJECTIVE_CODE, JOURNEY_CODE)
        frappe.db.commit()
        result2 = create_strategy_alignment_reference(_OBJECTIVE_CODE, JOURNEY_CODE)
        frappe.db.commit()

        self.assertTrue(result2.get("ok"))
        self.assertEqual(result2["action"], "updated")

        count = frappe.db.count(
            "Procurement Handoff Card",
            filters={"handoff_code": _EXPECTED_HANDOFF_CODE},
        )
        self.assertEqual(count, 1, "Must not create duplicate STRATREF cards")

    # ------------------------------------------------------------------
    # STRAT-TEST-R3-002-003 — Evidence links + technical refs
    # ------------------------------------------------------------------
    def test_003_evidence_links_and_technical_refs(self):
        """Card has a Strategy Objective evidence link and programme/target in technical_refs."""
        create_strategy_alignment_reference(_OBJECTIVE_CODE, JOURNEY_CODE)
        frappe.db.commit()

        card = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
            ["evidence_links_json", "technical_refs_json"],
            as_dict=True,
        )

        ev = json.loads(card["evidence_links_json"])
        links = ev.get("links", [])
        self.assertTrue(links, "evidence_links must be non-empty")

        obj_link = next(
            (lk for lk in links if lk.get("object_type") == "Strategy Objective"), None
        )
        self.assertIsNotNone(obj_link, "Must have a Strategy Objective link")
        self.assertEqual(obj_link["object_code"], _OBJECTIVE_CODE)
        self.assertIn("route", obj_link)
        self.assertTrue(obj_link["route"].strip())

        tech = json.loads(card["technical_refs_json"])
        self.assertIn("programme_code", tech, "technical_refs must contain programme_code")
        self.assertEqual(tech["programme_code"], "PROG-MOH-INFRA")
        self.assertIn("target_code", tech, "technical_refs must contain target_code")
        self.assertEqual(tech["target_code"], "TGT-MOH-HOSP-RENOV-2026")

    # ------------------------------------------------------------------
    # STRAT-TEST-R3-002-004 — Unknown strategy_ref
    # ------------------------------------------------------------------
    def test_004_unknown_strategy_ref_raises_value_error(self):
        """Non-existent objective_code raises ValueError with OBJECTIVE_NOT_FOUND."""
        with self.assertRaises(ValueError) as ctx:
            create_strategy_alignment_reference("OBJ-DOES-NOT-EXIST-R3002", JOURNEY_CODE)
        self.assertIn("OBJECTIVE_NOT_FOUND", str(ctx.exception))

    # ------------------------------------------------------------------
    # STRAT-TEST-R3-002-005 — Blank inputs
    # ------------------------------------------------------------------
    def test_005_blank_inputs_raise_value_error(self):
        """Blank strategy_ref or journey_code raises ValueError with the expected error code."""
        for bad_ref, bad_jrn, expected_code in [
            ("", JOURNEY_CODE, "INVALID_STRATEGY_REF"),
            ("  ", JOURNEY_CODE, "INVALID_STRATEGY_REF"),
            (_OBJECTIVE_CODE, "", "INVALID_JOURNEY_CODE"),
            (_OBJECTIVE_CODE, "  ", "INVALID_JOURNEY_CODE"),
        ]:
            with self.subTest(ref=repr(bad_ref), jrn=repr(bad_jrn)):
                with self.assertRaises(ValueError) as ctx:
                    create_strategy_alignment_reference(bad_ref, bad_jrn)
                self.assertIn(expected_code, str(ctx.exception))
