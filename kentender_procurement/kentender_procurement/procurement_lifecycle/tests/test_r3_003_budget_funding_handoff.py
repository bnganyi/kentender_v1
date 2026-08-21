# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R3-003 — ``create_budget_funding_confirmation`` service tests.

## Tests

1. **BUD-TEST-R3-003-001** — Happy path: valid ``(budget_line_code, journey_code)``
   creates ``BUDCONF-MOH-2026-001`` with correct source fields, status ``Consumed``,
   and non-empty ``locked_summary`` containing ``budget_line``, ``approved_amount``,
   ``currency``, and ``fiscal_year``.

2. **BUD-TEST-R3-003-002** — Idempotency: re-running returns ``action="updated"``
   and only one card exists for ``BUDCONF-MOH-2026-001``.

3. **BUD-TEST-R3-003-003** — Evidence link is a ``Budget Line`` link with non-empty
   ``route``; ``technical_refs`` contains ``budget_code`` and
   ``strategy_objective_code``.

4. **BUD-TEST-R3-003-004** — ``passed_forward_summary`` contains
   ``available_for_procurement_request`` (bool), ``reserved_for_master_demand``
   (positive number), and ``strategic_objective`` (the WORKS objective code).

5. **BUD-TEST-R3-003-005** — Unknown ``budget_line_code`` raises ``ValueError`` with
   ``BUDGET_LINE_NOT_FOUND``; blank inputs raise ``ValueError`` with the appropriate
   error code.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r3_003_budget_funding_handoff
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_strategy.seeds.works_master_strategy_hierarchy import (
    upsert_works_master_strategy_hierarchy,
)
from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
    load_procurement_lifecycle_works_master,
)
from kentender_procurement.procurement_lifecycle.budget_funding_handoff import (
    create_budget_funding_confirmation,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    JOURNEY_CODE,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"

# WORKS master codes (spec §4.2 / §16.3)
_BUDGET_LINE_CODE = "BUD-MOH-INFRA-2026-001"
_EXPECTED_HANDOFF_CODE = "BUDCONF-MOH-2026-001"
_EXPECTED_OBJECTIVE_CODE = "OBJ-MOH-HOSP-RENOV"


class TestR3003BudgetFundingHandoff(IntegrationTestCase):
    """R3-003 — Budget funding confirmation handoff service tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        cls.pe_name = ensure_procuring_entity(_PE_CODE, _PE_DISPLAY)

        # Seed strategy hierarchy + budget + PLC journey
        result_strat = upsert_works_master_strategy_hierarchy()
        assert result_strat.get("ok"), f"Strategy seed failed: {result_strat}"

        result_bud = upsert_works_master_budget()
        assert result_bud.get("ok"), f"Budget seed failed: {result_bud}"

        plc_result = load_procurement_lifecycle_works_master(checkpoint="TENDER_PUBLISHED")
        assert plc_result.get("ok"), f"PLC base seed failed: {plc_result}"
        frappe.db.commit()

    # ------------------------------------------------------------------
    # BUD-TEST-R3-003-001 — Happy path
    # ------------------------------------------------------------------
    def test_001_creates_budconf_card_with_correct_fields(self):
        """Service creates BUDCONF card with expected code and required field values."""
        result = create_budget_funding_confirmation(_BUDGET_LINE_CODE, JOURNEY_CODE)
        frappe.db.commit()

        self.assertTrue(result.get("ok"), f"Expected ok=True; got {result}")
        self.assertIn(result["action"], {"created", "updated"})
        self.assertEqual(result["handoff_code"], _EXPECTED_HANDOFF_CODE)

        card = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
            [
                "handoff_title", "source_module", "target_module",
                "source_object_type", "source_object_code",
                "status", "journey_code", "locked_summary",
            ],
            as_dict=True,
        )
        self.assertIsNotNone(card, "BUDCONF card must exist in DB")
        self.assertEqual(card["handoff_title"], "Budget Funding Confirmation")
        self.assertEqual(card["source_module"], "Budget")
        self.assertEqual(card["target_module"], "Demands")
        self.assertEqual(card["source_object_type"], "Budget Line")
        self.assertEqual(card["source_object_code"], _BUDGET_LINE_CODE)
        self.assertEqual(card["status"], "Consumed")
        self.assertEqual(card["journey_code"], JOURNEY_CODE)

        locked = json.loads(card["locked_summary"])
        self.assertEqual(locked.get("budget_line"), _BUDGET_LINE_CODE)
        self.assertGreater(locked.get("approved_amount", 0), 0, "approved_amount must be > 0")
        self.assertTrue(locked.get("currency"), "currency must be non-empty")
        self.assertIn("fiscal_year", locked, "locked_summary must contain fiscal_year")
        # Fiscal year must be formatted as "YYYY/YYYY+1"
        fy = locked["fiscal_year"]
        self.assertRegex(str(fy), r"^\d{4}/\d{4}$", f"fiscal_year must match YYYY/YYYY+1, got {fy!r}")

    # ------------------------------------------------------------------
    # BUD-TEST-R3-003-002 — Idempotency
    # ------------------------------------------------------------------
    def test_002_idempotent_no_duplicate(self):
        """Re-running creates only one BUDCONF card; action=updated on second call."""
        create_budget_funding_confirmation(_BUDGET_LINE_CODE, JOURNEY_CODE)
        frappe.db.commit()
        result2 = create_budget_funding_confirmation(_BUDGET_LINE_CODE, JOURNEY_CODE)
        frappe.db.commit()

        self.assertTrue(result2.get("ok"))
        self.assertEqual(result2["action"], "updated")

        count = frappe.db.count(
            "Procurement Handoff Card",
            filters={"handoff_code": _EXPECTED_HANDOFF_CODE},
        )
        self.assertEqual(count, 1, "Must not create duplicate BUDCONF cards")

    # ------------------------------------------------------------------
    # BUD-TEST-R3-003-003 — Evidence links + technical refs
    # ------------------------------------------------------------------
    def test_003_evidence_links_and_technical_refs(self):
        """Card has a Budget Line evidence link and budget_code/strategy_objective_code in technical_refs."""
        create_budget_funding_confirmation(_BUDGET_LINE_CODE, JOURNEY_CODE)
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

        bl_link = next(
            (lk for lk in links if lk.get("object_type") == "Budget Line"), None
        )
        self.assertIsNotNone(bl_link, "Must have a Budget Line evidence link")
        self.assertEqual(bl_link["object_code"], _BUDGET_LINE_CODE)
        self.assertEqual(bl_link["module"], "Budget")
        self.assertIn("route", bl_link)
        self.assertTrue(bl_link["route"].strip(), "route must be non-empty")

        tech = json.loads(card["technical_refs_json"])
        self.assertIn("budget_code", tech, "technical_refs must contain budget_code")
        self.assertTrue(tech["budget_code"], "budget_code must be non-empty")
        self.assertIn("strategy_objective_code", tech, "technical_refs must contain strategy_objective_code")
        self.assertEqual(tech["strategy_objective_code"], _EXPECTED_OBJECTIVE_CODE)

    # ------------------------------------------------------------------
    # BUD-TEST-R3-003-004 — passed_forward_summary
    # ------------------------------------------------------------------
    def test_004_passed_forward_summary_shape(self):
        """passed_forward_summary has available flag, reserved amount, and strategic_objective."""
        create_budget_funding_confirmation(_BUDGET_LINE_CODE, JOURNEY_CODE)
        frappe.db.commit()

        card = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
            "passed_forward_summary",
        )
        passed = json.loads(card)

        self.assertIn("available_for_procurement_request", passed)
        self.assertIs(passed["available_for_procurement_request"], True)

        self.assertIn("reserved_for_master_demand", passed, "reserved_for_master_demand must be present")
        self.assertGreater(
            passed["reserved_for_master_demand"], 0,
            "reserved_for_master_demand must be > 0",
        )

        self.assertIn("strategic_objective", passed, "passed_forward_summary must contain strategic_objective")
        self.assertEqual(passed["strategic_objective"], _EXPECTED_OBJECTIVE_CODE)

    # ------------------------------------------------------------------
    # BUD-TEST-R3-003-005 — Error handling
    # ------------------------------------------------------------------
    def test_005_unknown_budget_line_raises_value_error(self):
        """Non-existent budget_line_code raises ValueError with BUDGET_LINE_NOT_FOUND."""
        with self.assertRaises(ValueError) as ctx:
            create_budget_funding_confirmation("BUD-DOES-NOT-EXIST-R3003", JOURNEY_CODE)
        self.assertIn("BUDGET_LINE_NOT_FOUND", str(ctx.exception))

    def test_005b_blank_inputs_raise_value_error(self):
        """Blank budget_line_code or journey_code raises ValueError with the expected code."""
        for bad_bl, bad_jrn, expected_code in [
            ("", JOURNEY_CODE, "INVALID_BUDGET_LINE_CODE"),
            ("  ", JOURNEY_CODE, "INVALID_BUDGET_LINE_CODE"),
            (_BUDGET_LINE_CODE, "", "INVALID_JOURNEY_CODE"),
            (_BUDGET_LINE_CODE, "  ", "INVALID_JOURNEY_CODE"),
        ]:
            with self.subTest(bl=repr(bad_bl), jrn=repr(bad_jrn)):
                with self.assertRaises(ValueError) as ctx:
                    create_budget_funding_confirmation(bad_bl, bad_jrn)
                self.assertIn(expected_code, str(ctx.exception))
