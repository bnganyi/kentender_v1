# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R3-005 — ``create_planning_release_package`` service tests.

## Tests

1. **PKG-TEST-R3-005-001** — Happy path: valid ``(package_code, journey_code)`` creates
   ``PKGREL-MOH-2026-001`` with correct source fields, status ``Consumed``, and
   ``locked_summary`` containing ``package_code``, ``package_title``,
   ``procurement_method``, ``budget_line``, ``estimated_value``, and ``currency``.

2. **PKG-TEST-R3-005-002** — Idempotency: re-running returns ``action="updated"`` and
   only one card exists for ``PKGREL-MOH-2026-001``.

3. **PKG-TEST-R3-005-003** — TM2 consume linkage (LV-R3-005-01): when a TM2 Tender
   references the package, the card has ``target_object_code = "TND-MOH-2026-001"``,
   two evidence links (Package + TM2 Tender), and ``technical_refs.tm2_tender_code``.

4. **PKG-TEST-R3-005-004** — ``passed_forward_summary`` contains ``required_std_category``
   and ``tender_title``; ``technical_refs`` contains ``procurement_plan_code`` and
   ``package_line_code``.

5. **PKG-TEST-R3-005-005** — Unknown ``package_code`` raises ``ValueError`` with
   ``PACKAGE_NOT_FOUND``; blank inputs raise the appropriate error codes.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r3_005_planning_release_handoff
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
from kentender_procurement.procurement_lifecycle.legacy_demand_seed_shim import (
    upsert_works_master_demand,
)
from kentender_procurement.procurement_planning.seeds.works_master_planning_seed import (
    upsert_works_master_planning,
)
from kentender_procurement.tender_management.seeds.works_master_tender_seed import (
    upsert_works_master_tender,
)
from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
    load_procurement_lifecycle_works_master,
)
from kentender_procurement.procurement_lifecycle.planning_release_handoff import (
    create_planning_release_package,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    JOURNEY_CODE,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"

# WORKS master codes (spec §4.2 / §16.6)
_PACKAGE_CODE = "PKG-MOH-2026-001"
_EXPECTED_HANDOFF_CODE = "PKGREL-MOH-2026-001"
_EXPECTED_TM2_CODE = "TND-MOH-2026-001"
_EXPECTED_BUDGET_LINE = "BUD-MOH-INFRA-2026-001"
_EXPECTED_PLAN_CODE = "PLAN-MOH-2026"
_EXPECTED_PKG_LINE_CODE = "PKGLINE-MOH-2026-001-001"


class TestR3005PlanningReleaseHandoff(IntegrationTestCase):
    """R3-005 — Planning release package handoff service tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        cls.pe_name = ensure_procuring_entity(_PE_CODE, _PE_DISPLAY)

        # Seed the full prerequisite chain up to and including the TM2 Tender
        for label, fn in (
            ("Strategy", upsert_works_master_strategy_hierarchy),
            ("Budget", upsert_works_master_budget),
            ("Demand", upsert_works_master_demand),
            ("Planning", upsert_works_master_planning),
            ("Tender", upsert_works_master_tender),
        ):
            result = fn()
            assert result.get("ok"), f"{label} seed failed: {result}"

        plc_result = load_procurement_lifecycle_works_master(checkpoint="TENDER_PUBLISHED")
        assert plc_result.get("ok"), f"PLC base seed failed: {plc_result}"
        frappe.db.commit()

    # ------------------------------------------------------------------
    # PKG-TEST-R3-005-001 — Happy path
    # ------------------------------------------------------------------
    def test_001_creates_pkgrel_card_with_correct_fields(self):
        """Service creates PKGREL card with expected code and required locked_summary fields."""
        result = create_planning_release_package(_PACKAGE_CODE, JOURNEY_CODE)
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
        self.assertIsNotNone(card, "PKGREL card must exist in DB")
        self.assertEqual(card["handoff_title"], "Planning Release Package")
        self.assertEqual(card["source_module"], "Procurement Planning")
        self.assertEqual(card["target_module"], "Tender Management")
        self.assertEqual(card["source_object_type"], "Procurement Package")
        self.assertEqual(card["source_object_code"], _PACKAGE_CODE)
        self.assertEqual(card["status"], "Consumed")
        self.assertEqual(card["journey_code"], JOURNEY_CODE)

        locked = json.loads(card["locked_summary"])
        self.assertEqual(locked.get("package_code"), _PACKAGE_CODE)
        self.assertTrue(locked.get("package_title"), "package_title must be non-empty")
        self.assertTrue(locked.get("procurement_method"), "procurement_method must be non-empty")
        self.assertEqual(locked.get("budget_line"), _EXPECTED_BUDGET_LINE)
        self.assertGreater(locked.get("estimated_value", 0), 0, "estimated_value must be > 0")
        self.assertTrue(locked.get("currency"), "currency must be non-empty")

    # ------------------------------------------------------------------
    # PKG-TEST-R3-005-002 — Idempotency
    # ------------------------------------------------------------------
    def test_002_idempotent_no_duplicate(self):
        """Re-running creates only one PKGREL card; action=updated on second call."""
        create_planning_release_package(_PACKAGE_CODE, JOURNEY_CODE)
        frappe.db.commit()
        result2 = create_planning_release_package(_PACKAGE_CODE, JOURNEY_CODE)
        frappe.db.commit()

        self.assertTrue(result2.get("ok"))
        self.assertEqual(result2["action"], "updated")

        count = frappe.db.count(
            "Procurement Handoff Card",
            filters={"handoff_code": _EXPECTED_HANDOFF_CODE},
        )
        self.assertEqual(count, 1, "Must not create duplicate PKGREL cards")

    # ------------------------------------------------------------------
    # PKG-TEST-R3-005-003 — TM2 consume linkage (LV-R3-005-01)
    # ------------------------------------------------------------------
    def test_003_tm2_consume_linkage(self):
        """When TM2 Tender references package: target_object_code set; two evidence links; tm2_tender_code in technical_refs."""
        create_planning_release_package(_PACKAGE_CODE, JOURNEY_CODE)
        frappe.db.commit()

        card = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
            [
                "target_object_type", "target_object_code",
                "evidence_links_json", "technical_refs_json",
            ],
            as_dict=True,
        )

        # target_object_code must be set to the TM2 Tender
        self.assertEqual(card["target_object_type"], "TM2 Tender")
        self.assertEqual(
            card["target_object_code"], _EXPECTED_TM2_CODE,
            f"target_object_code must be {_EXPECTED_TM2_CODE!r}",
        )

        ev = json.loads(card["evidence_links_json"])
        links = ev.get("links", [])
        self.assertEqual(len(links), 2, f"Must have 2 evidence links (package + TM2); got {len(links)}")

        pkg_link = next((lk for lk in links if lk.get("object_type") == "Procurement Package"), None)
        self.assertIsNotNone(pkg_link, "Must have a Procurement Package evidence link")
        self.assertEqual(pkg_link["object_code"], _PACKAGE_CODE)

        tm2_link = next((lk for lk in links if lk.get("object_type") == "TM2 Tender"), None)
        self.assertIsNotNone(tm2_link, "Must have a TM2 Tender evidence link")
        self.assertEqual(tm2_link["object_code"], _EXPECTED_TM2_CODE)
        self.assertTrue(tm2_link.get("route", "").strip(), "TM2 Tender link route must be non-empty")

        tech = json.loads(card["technical_refs_json"])
        self.assertIn("tm2_tender_code", tech, "technical_refs must contain tm2_tender_code")
        self.assertEqual(tech["tm2_tender_code"], _EXPECTED_TM2_CODE)

    # ------------------------------------------------------------------
    # PKG-TEST-R3-005-004 — passed_forward_summary + technical_refs
    # ------------------------------------------------------------------
    def test_004_passed_forward_summary_and_technical_refs(self):
        """passed_forward_summary and technical_refs contain required fields."""
        create_planning_release_package(_PACKAGE_CODE, JOURNEY_CODE)
        frappe.db.commit()

        card = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
            ["passed_forward_summary", "technical_refs_json"],
            as_dict=True,
        )

        passed = json.loads(card["passed_forward_summary"])
        self.assertIn("tender_title", passed, "passed_forward_summary must contain tender_title")
        self.assertTrue(passed["tender_title"], "tender_title must be non-empty")
        self.assertIn(
            "required_std_category", passed,
            "passed_forward_summary must contain required_std_category",
        )
        self.assertTrue(passed["required_std_category"])

        tech = json.loads(card["technical_refs_json"])
        self.assertIn("procurement_plan_code", tech, "technical_refs must contain procurement_plan_code")
        self.assertEqual(tech["procurement_plan_code"], _EXPECTED_PLAN_CODE)
        self.assertIn("package_line_code", tech, "technical_refs must contain package_line_code")
        self.assertEqual(tech["package_line_code"], _EXPECTED_PKG_LINE_CODE)

    # ------------------------------------------------------------------
    # PKG-TEST-R3-005-005 — Error handling
    # ------------------------------------------------------------------
    def test_005_unknown_package_raises_value_error(self):
        """Non-existent package_code raises ValueError with PACKAGE_NOT_FOUND."""
        with self.assertRaises(ValueError) as ctx:
            create_planning_release_package("PKG-DOES-NOT-EXIST-R3005", JOURNEY_CODE)
        self.assertIn("PACKAGE_NOT_FOUND", str(ctx.exception))

    def test_005b_blank_inputs_raise_value_error(self):
        """Blank package_code or journey_code raises ValueError with the expected code."""
        for bad_pkg, bad_jrn, expected_code in [
            ("", JOURNEY_CODE, "INVALID_PACKAGE_CODE"),
            ("  ", JOURNEY_CODE, "INVALID_PACKAGE_CODE"),
            (_PACKAGE_CODE, "", "INVALID_JOURNEY_CODE"),
            (_PACKAGE_CODE, "  ", "INVALID_JOURNEY_CODE"),
        ]:
            with self.subTest(pkg=repr(bad_pkg), jrn=repr(bad_jrn)):
                with self.assertRaises(ValueError) as ctx:
                    create_planning_release_package(bad_pkg, bad_jrn)
                self.assertIn(expected_code, str(ctx.exception))
