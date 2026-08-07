# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R3-004 — ``create_demand_approval_certificate`` service tests.

## Tests

1. **DEM-TEST-R3-004-001** — Happy path: valid ``(demand_code, journey_code)`` creates
   ``DEMAPP-MOH-2026-001`` with correct source fields, status ``Consumed``, and
   ``locked_summary`` containing ``demand_code``, ``demand_title``,
   ``approved_estimated_value``, ``budget_line``, and ``procurement_category``.

2. **DEM-TEST-R3-004-002** — Idempotency: re-running returns ``action="updated"`` and
   only one card exists for ``DEMAPP-MOH-2026-001``.

3. **DEM-TEST-R3-004-003** — Two evidence links are present: ``Demand`` (Approved
   Demand) with non-empty route, and ``Demand Approval`` (Demand Approval Record) with
   the derived ``DEMAPPROVAL-MOH-2026-001`` code.

4. **DEM-TEST-R3-004-004** — ``passed_forward_summary`` contains ``approved_need``
   (from first Demand Item), ``requesting_department``, and ``planning_action``.
   ``technical_refs`` contains ``budget_line_code``.

5. **DEM-TEST-R3-004-005** — Unknown ``demand_code`` raises ``ValueError`` with
   ``DEMAND_NOT_FOUND``; non-Approved demand raises ``ValueError`` with
   ``DEMAND_NOT_APPROVED``; blank inputs raise appropriate error codes.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r3_004_demand_approval_handoff
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
from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
    load_procurement_lifecycle_works_master,
)
from kentender_procurement.procurement_lifecycle.demand_approval_handoff import (
    create_demand_approval_certificate,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    JOURNEY_CODE,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"

# WORKS master codes (spec §4.2 / §16.4)
_DEMAND_CODE = "DEM-MOH-2026-001"
_EXPECTED_HANDOFF_CODE = "DEMAPP-MOH-2026-001"
_EXPECTED_APPROVAL_CODE = "DEMAPPROVAL-MOH-2026-001"
_EXPECTED_BUDGET_LINE = "BUD-MOH-INFRA-2026-001"


class TestR3004DemandApprovalHandoff(IntegrationTestCase):
    """R3-004 — Demand approval certificate handoff service tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        cls.pe_name = ensure_procuring_entity(_PE_CODE, _PE_DISPLAY)

        # Seed prerequisites: strategy → budget → demand → PLC journey
        for label, fn in (
            ("Strategy", upsert_works_master_strategy_hierarchy),
            ("Budget", upsert_works_master_budget),
            ("Demand", upsert_works_master_demand),
        ):
            result = fn()
            assert result.get("ok"), f"{label} seed failed: {result}"

        plc_result = load_procurement_lifecycle_works_master(checkpoint="TENDER_PUBLISHED")
        assert plc_result.get("ok"), f"PLC base seed failed: {plc_result}"
        frappe.db.commit()

    # ------------------------------------------------------------------
    # DEM-TEST-R3-004-001 — Happy path
    # ------------------------------------------------------------------
    def test_001_creates_demapp_card_with_correct_fields(self):
        """Service creates DEMAPP card with expected code and required field values."""
        result = create_demand_approval_certificate(_DEMAND_CODE, JOURNEY_CODE)
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
        self.assertIsNotNone(card, "DEMAPP card must exist in DB")
        self.assertEqual(card["handoff_title"], "Demand Approval Certificate")
        self.assertEqual(card["source_module"], "Demand Intake and Approval")
        self.assertEqual(card["target_module"], "Procurement Planning")
        self.assertEqual(card["source_object_type"], "Demand")
        self.assertEqual(card["source_object_code"], _DEMAND_CODE)
        self.assertEqual(card["status"], "Consumed")
        self.assertEqual(card["journey_code"], JOURNEY_CODE)

        locked = json.loads(card["locked_summary"])
        self.assertEqual(locked.get("demand_code"), _DEMAND_CODE)
        self.assertTrue(locked.get("demand_title"), "demand_title must be non-empty")
        self.assertGreater(
            locked.get("approved_estimated_value", 0), 0,
            "approved_estimated_value must be > 0",
        )
        self.assertEqual(locked.get("budget_line"), _EXPECTED_BUDGET_LINE)
        self.assertTrue(locked.get("procurement_category"), "procurement_category must be non-empty")

    # ------------------------------------------------------------------
    # DEM-TEST-R3-004-002 — Idempotency
    # ------------------------------------------------------------------
    def test_002_idempotent_no_duplicate(self):
        """Re-running creates only one DEMAPP card; action=updated on second call."""
        create_demand_approval_certificate(_DEMAND_CODE, JOURNEY_CODE)
        frappe.db.commit()
        result2 = create_demand_approval_certificate(_DEMAND_CODE, JOURNEY_CODE)
        frappe.db.commit()

        self.assertTrue(result2.get("ok"))
        self.assertEqual(result2["action"], "updated")

        count = frappe.db.count(
            "Procurement Handoff Card",
            filters={"handoff_code": _EXPECTED_HANDOFF_CODE},
        )
        self.assertEqual(count, 1, "Must not create duplicate DEMAPP cards")

    # ------------------------------------------------------------------
    # DEM-TEST-R3-004-003 — Two evidence links
    # ------------------------------------------------------------------
    def test_003_two_evidence_links_with_correct_codes(self):
        """Card has Demand link and Demand Approval link with correct codes and routes."""
        create_demand_approval_certificate(_DEMAND_CODE, JOURNEY_CODE)
        frappe.db.commit()

        card = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
            "evidence_links_json",
        )
        ev = json.loads(card)
        links = ev.get("links", [])
        self.assertEqual(len(links), 2, f"Must have exactly 2 evidence links; got {len(links)}")

        demand_link = next(
            (lk for lk in links if lk.get("object_type") == "Demand"), None
        )
        self.assertIsNotNone(demand_link, "Must have a Demand evidence link")
        self.assertEqual(demand_link["object_code"], _DEMAND_CODE)
        self.assertEqual(demand_link["module"], "Demand Intake and Approval")
        self.assertTrue(demand_link.get("route", "").strip(), "Demand link route must be non-empty")

        approval_link = next(
            (lk for lk in links if lk.get("object_type") == "Demand Approval"), None
        )
        self.assertIsNotNone(approval_link, "Must have a Demand Approval evidence link")
        self.assertEqual(
            approval_link["object_code"], _EXPECTED_APPROVAL_CODE,
            f"Approval code must be {_EXPECTED_APPROVAL_CODE!r}; got {approval_link['object_code']!r}",
        )

    # ------------------------------------------------------------------
    # DEM-TEST-R3-004-004 — passed_forward_summary + technical_refs
    # ------------------------------------------------------------------
    def test_004_passed_forward_summary_and_technical_refs(self):
        """passed_forward_summary and technical_refs contain the required fields."""
        create_demand_approval_certificate(_DEMAND_CODE, JOURNEY_CODE)
        frappe.db.commit()

        card = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
            ["passed_forward_summary", "technical_refs_json"],
            as_dict=True,
        )

        passed = json.loads(card["passed_forward_summary"])
        self.assertIn("planning_action", passed)
        self.assertTrue(passed["planning_action"])
        self.assertIn("approved_need", passed, "approved_need must be present (from demand item)")
        self.assertTrue(passed["approved_need"], "approved_need must be non-empty")
        self.assertIn("requesting_department", passed, "requesting_department must be present")
        self.assertTrue(passed["requesting_department"], "requesting_department must be non-empty")

        tech = json.loads(card["technical_refs_json"])
        self.assertIn("budget_line_code", tech, "technical_refs must contain budget_line_code")
        self.assertEqual(tech["budget_line_code"], _EXPECTED_BUDGET_LINE)

    # ------------------------------------------------------------------
    # DEM-TEST-R3-004-005 — Error handling
    # ------------------------------------------------------------------
    def test_005_unknown_demand_raises_value_error(self):
        """Non-existent demand_code raises ValueError with DEMAND_NOT_FOUND."""
        with self.assertRaises(ValueError) as ctx:
            create_demand_approval_certificate("DEM-DOES-NOT-EXIST-R3004", JOURNEY_CODE)
        self.assertIn("DEMAND_NOT_FOUND", str(ctx.exception))

    def test_005b_non_approved_demand_raises_value_error(self):
        """Non-Approved demand raises ValueError with DEMAND_NOT_APPROVED."""
        # Create a temporary Draft demand for this test
        temp_id = "DEM-TEST-R3004-DRAFT"
        if not frappe.db.exists("Demand", {"demand_id": temp_id}):
            pe = frappe.db.get_value("Procuring Entity", {"entity_code": _PE_CODE}, "name") or _PE_CODE
            doc = frappe.get_doc({
                "doctype": "Demand",
                "demand_id": temp_id,
                "title": "R3-004 test draft demand",
                "procuring_entity": pe,
                "status": "Draft",
                "requisition_type": "Works",
                "total_amount": 0,
            })
            doc.flags.ignore_permissions = True
            doc.flags.ignore_mandatory = True
            doc.insert()
            frappe.db.commit()

        try:
            with self.assertRaises(ValueError) as ctx:
                create_demand_approval_certificate(temp_id, JOURNEY_CODE)
            self.assertIn("DEMAND_NOT_APPROVED", str(ctx.exception))
        finally:
            if frappe.db.exists("Demand", {"demand_id": temp_id}):
                frappe.db.delete("Demand", {"demand_id": temp_id})
                frappe.db.commit()

    def test_005c_blank_inputs_raise_value_error(self):
        """Blank demand_code or journey_code raises ValueError with the expected code."""
        for bad_dem, bad_jrn, expected_code in [
            ("", JOURNEY_CODE, "INVALID_DEMAND_CODE"),
            ("  ", JOURNEY_CODE, "INVALID_DEMAND_CODE"),
            (_DEMAND_CODE, "", "INVALID_JOURNEY_CODE"),
            (_DEMAND_CODE, "  ", "INVALID_JOURNEY_CODE"),
        ]:
            with self.subTest(dem=repr(bad_dem), jrn=repr(bad_jrn)):
                with self.assertRaises(ValueError) as ctx:
                    create_demand_approval_certificate(bad_dem, bad_jrn)
                self.assertIn(expected_code, str(ctx.exception))
