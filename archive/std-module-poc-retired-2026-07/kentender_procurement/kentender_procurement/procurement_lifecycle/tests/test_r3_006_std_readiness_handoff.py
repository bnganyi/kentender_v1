# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R3-006 — ``create_std_readiness_certificate`` service tests.

## Tests

1. **TND-TEST-R3-006-001** — Happy path: valid ``(tender_code, journey_code)`` creates
   ``STDREADY-TND-MOH-2026-001`` with correct source fields (``source_module``,
   ``source_object_type``, ``target_object_type``), ``status = "Consumed"``, and
   ``locked_summary`` containing ``tender_std_instance``, ``readiness_status``,
   and ``std_template_version``.

2. **TND-TEST-R3-006-002** — Idempotency: re-running returns ``action="updated"``
   and only one card exists for ``STDREADY-TND-MOH-2026-001``.

3. **TND-TEST-R3-006-003** — Real STD instance data (LV-R3-006-01): when a
   ``Tender STD Instance`` is linked to the TM2 Tender via ``tm2_tender``, the
   service reads its live ``readiness_status`` and output codes; when
   ``readiness_status == "Ready"`` all ``passed_forward_summary`` flags are ``True``
   and ``technical_refs`` contains the five output codes.

4. **TND-TEST-R3-006-004** — ``passed_forward_summary`` flag derivation: all five
   boolean flags are ``False`` when ``readiness_status != "Ready"``.

5. **TND-TEST-R3-006-005** — Error handling: unknown ``tender_code`` raises
   ``ValueError`` with ``TENDER_NOT_FOUND``; blank inputs raise the appropriate
   error codes.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r3_006_std_readiness_handoff
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
from kentender_procurement.procurement_lifecycle.std_readiness_handoff import (
    create_std_readiness_certificate,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    JOURNEY_CODE,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"

# WORKS master codes (spec §4.2 / §16.7)
_TENDER_CODE = "TND-MOH-2026-001"
_EXPECTED_HANDOFF_CODE = "STDREADY-TND-MOH-2026-001"
_EXPECTED_STDINST_CODE = "STDINST-TND-MOH-2026-001"
_EXPECTED_TEMPLATE_VERSION = "STDTV-WORKS-BUILDING-CIVIL-APR2022"


class TestR3006StdReadinessHandoff(IntegrationTestCase):
    """R3-006 — STD readiness certificate handoff service tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        cls.pe_name = ensure_procuring_entity(_PE_CODE, _PE_DISPLAY)

        # Seed prerequisite chain: Strategy → Budget → Demand → Planning → STD → Tender
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
        # Clean up the handoff card created during tests
        frappe.set_user("Administrator")
        for card_name in frappe.db.get_all(
            "Procurement Handoff Card",
            filters={"handoff_code": ["like", "STDREADY-TND-R3006-TEST%"]},
            pluck="name",
        ):
            frappe.delete_doc("Procurement Handoff Card", card_name, force=True)
        frappe.db.commit()
        super().tearDownClass()

    # ------------------------------------------------------------------
    # Test 1 — Happy path
    # ------------------------------------------------------------------

    def test_01_creates_card_with_correct_source_fields(self):
        """Creates STDREADY card with source/target fields matching spec §16.7."""
        result = create_std_readiness_certificate(_TENDER_CODE, JOURNEY_CODE)

        self.assertTrue(result.get("ok"), f"Expected ok=True; got: {result}")
        self.assertEqual(result["handoff_code"], _EXPECTED_HANDOFF_CODE)
        self.assertIn(result["action"], ("created", "updated"))

        card = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
            [
                "handoff_title",
                "source_module",
                "target_module",
                "source_object_type",
                "source_object_code",
                "target_object_type",
                "target_object_code",
                "status",
                "next_action",
                "locked_summary",
            ],
            as_dict=True,
        )
        self.assertIsNotNone(card, f"Card {_EXPECTED_HANDOFF_CODE!r} not found in DB")

        self.assertEqual(card["handoff_title"], "Tender Document Readiness Certificate")
        self.assertEqual(card["source_module"], "STD Engine / Tender Management")
        self.assertEqual(card["target_module"], "Tender Publication")
        self.assertEqual(card["source_object_type"], "Tender STD Instance")
        # source_object_code should be the canonical STDINST code from the Journey ref
        self.assertEqual(card["source_object_code"], _EXPECTED_STDINST_CODE)
        self.assertEqual(card["target_object_type"], "TM2 Tender")
        self.assertEqual(card["target_object_code"], _TENDER_CODE)
        self.assertEqual(card["status"], "Consumed")
        self.assertEqual(card["next_action"], "Submit tender for publication review.")

        # locked_summary shape (spec §16.7)
        locked = json.loads(card["locked_summary"])
        self.assertIn("tender_std_instance", locked)
        self.assertIn("readiness_status", locked)
        self.assertIn("std_template_version", locked)
        self.assertEqual(locked["tender_std_instance"], _EXPECTED_STDINST_CODE)
        self.assertEqual(locked["std_template_version"], _EXPECTED_TEMPLATE_VERSION)

    # ------------------------------------------------------------------
    # Test 2 — Idempotency
    # ------------------------------------------------------------------

    def test_02_idempotency_returns_updated(self):
        """Re-running returns action='updated' and exactly one card exists."""
        create_std_readiness_certificate(_TENDER_CODE, JOURNEY_CODE)
        result2 = create_std_readiness_certificate(_TENDER_CODE, JOURNEY_CODE)

        self.assertTrue(result2.get("ok"))
        self.assertEqual(result2["action"], "updated")

        count = frappe.db.count(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
        )
        self.assertEqual(count, 1, "Must have exactly one STDREADY card")

    # ------------------------------------------------------------------
    # Test 3 — Real STD instance data (LV-R3-006-01)
    # ------------------------------------------------------------------

    def test_03_real_std_instance_outputs_read_from_live_record(self):
        """When a real Tender STD Instance is linked, output codes come from it.

        LV-R3-006-01: driven from real TM2/STD outputs.
        When readiness_status == 'Ready', all passed_forward_summary flags are True
        and technical_refs contains the five output codes.
        """
        # Create a test Tender STD Instance linked to TND-MOH-2026-001
        tm2_frappe_name = frappe.db.get_value("TM2 Tender", {"tender_code": _TENDER_CODE}, "name")
        self.assertIsNotNone(tm2_frappe_name, "TM2 Tender TND-MOH-2026-001 must exist for this test")

        test_inst = frappe.get_doc(
            {
                "doctype": "Tender STD Instance",
                "tm2_tender": tm2_frappe_name,
                "template_version_code": _EXPECTED_TEMPLATE_VERSION,
                "readiness_status": "Ready",
                "instance_status": "Locked for Approval",
                # Required to pass the controller's orphan-creation guard
                "created_from_tender_context": 1,
                "current_bundle_output_code": "GB-TND-MOH-2026-001-V2",
                "current_dsm_output_code": "DSM-TND-MOH-2026-001-V2",
                "current_dom_output_code": "DOM-TND-MOH-2026-001-V2",
                "current_dem_output_code": "DEM-TND-MOH-2026-001-V2",
                "current_dcm_output_code": "DCM-TND-MOH-2026-001-V2",
            }
        )
        test_inst.flags.ignore_permissions = True
        test_inst.flags.ignore_mandatory = True
        test_inst.insert()
        test_inst_name = test_inst.name

        try:
            result = create_std_readiness_certificate(_TENDER_CODE, JOURNEY_CODE)
            self.assertTrue(result.get("ok"))

            card = frappe.db.get_value(
                "Procurement Handoff Card",
                {"handoff_code": _EXPECTED_HANDOFF_CODE},
                ["locked_summary", "passed_forward_summary", "technical_refs_json"],
                as_dict=True,
            )
            self.assertIsNotNone(card)

            locked = json.loads(card["locked_summary"])
            # The name from the real instance (auto-named) is used as stdinst_code
            self.assertEqual(locked["readiness_status"], "Ready")
            self.assertEqual(locked["std_template_version"], _EXPECTED_TEMPLATE_VERSION)

            # passed_forward_summary — all True when Ready
            passed = json.loads(card["passed_forward_summary"])
            self.assertTrue(passed.get("tender_document_package_ready"), "tender_document_package_ready must be True when Ready")
            self.assertTrue(passed.get("supplier_submission_checklist_ready"))
            self.assertTrue(passed.get("opening_register_rules_ready"))
            self.assertTrue(passed.get("evaluation_rules_ready"))
            self.assertTrue(passed.get("contract_carry_forward_terms_ready"))

            # technical_refs — output codes from real instance
            tech = json.loads(card["technical_refs_json"] or "{}")
            self.assertEqual(tech.get("bundle_output_code"), "GB-TND-MOH-2026-001-V2")
            self.assertEqual(tech.get("dsm_output_code"), "DSM-TND-MOH-2026-001-V2")
            self.assertEqual(tech.get("dom_output_code"), "DOM-TND-MOH-2026-001-V2")
            self.assertEqual(tech.get("dem_output_code"), "DEM-TND-MOH-2026-001-V2")
            self.assertEqual(tech.get("dcm_output_code"), "DCM-TND-MOH-2026-001-V2")

        finally:
            # Clean up test STD instance
            frappe.delete_doc("Tender STD Instance", test_inst_name, force=True)
            frappe.db.commit()

    # ------------------------------------------------------------------
    # Test 4 — passed_forward_summary flags are False when not Ready
    # ------------------------------------------------------------------

    def test_04_passed_forward_flags_false_when_not_ready(self):
        """All passed_forward flags are False when readiness_status is not 'Ready'."""
        # The WORKS master seed sets TM2 std_readiness_status = "Not Assessed"
        # and no real STD instance is linked → service falls back to TM2 status.
        # Ensure no lingering real instance from test 3 interferes.
        result = create_std_readiness_certificate(_TENDER_CODE, JOURNEY_CODE)
        self.assertTrue(result.get("ok"))

        card = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
            "passed_forward_summary",
        )
        passed = json.loads(card)
        # readiness_status is "Not Assessed" (or "Not Ready") — all flags must be False
        self.assertFalse(passed.get("tender_document_package_ready"), f"expected False; got {passed}")
        self.assertFalse(passed.get("supplier_submission_checklist_ready"))
        self.assertFalse(passed.get("opening_register_rules_ready"))
        self.assertFalse(passed.get("evaluation_rules_ready"))
        self.assertFalse(passed.get("contract_carry_forward_terms_ready"))

    # ------------------------------------------------------------------
    # Test 5 — Evidence link
    # ------------------------------------------------------------------

    def test_05_evidence_link_points_to_std_instance(self):
        """evidence_links_json contains one Tender STD Instance link."""
        result = create_std_readiness_certificate(_TENDER_CODE, JOURNEY_CODE)
        self.assertTrue(result.get("ok"))

        raw = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
            "evidence_links_json",
        )
        links_envelope = json.loads(raw)
        links = links_envelope.get("links", links_envelope) if isinstance(links_envelope, dict) else links_envelope
        self.assertTrue(len(links) >= 1, "Expected at least one evidence link")
        first = links[0]
        self.assertEqual(first.get("object_type"), "Tender STD Instance")
        self.assertEqual(first.get("object_code"), _EXPECTED_STDINST_CODE)
        self.assertEqual(first.get("module"), "STD Engine")

    # ------------------------------------------------------------------
    # Test 6 — Error handling
    # ------------------------------------------------------------------

    def test_06_unknown_tender_raises_tender_not_found(self):
        """Unknown tender_code raises ValueError with TENDER_NOT_FOUND."""
        with self.assertRaises(ValueError) as ctx:
            create_std_readiness_certificate("TND-NONEXISTENT-9999", JOURNEY_CODE)
        self.assertIn("TENDER_NOT_FOUND", str(ctx.exception))

    def test_06b_blank_inputs_raise_appropriate_error_codes(self):
        """Blank tender_code → INVALID_TENDER_CODE; blank journey_code → INVALID_JOURNEY_CODE."""
        with self.assertRaises(ValueError) as ctx:
            create_std_readiness_certificate("", JOURNEY_CODE)
        self.assertIn("INVALID_TENDER_CODE", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            create_std_readiness_certificate(_TENDER_CODE, "")
        self.assertIn("INVALID_JOURNEY_CODE", str(ctx.exception))
