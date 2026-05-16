# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R3-008 — ``create_tender_closing_certificate`` service tests.

## Tests

1. **CLS-TEST-R3-008-001** — Happy path: when a real ``TM2 Tender Closing Record``
   exists, creates ``CLOSECERT-TND-MOH-2026-001`` with correct source fields, ``status="Consumed"``,
   ``locked_summary`` containing ``submission_window_closed``, ``closed_at``,
   ``submission_deadline``, and ``official_time_source="Server Time"``.

2. **CLS-TEST-R3-008-002** — Idempotency: re-running returns ``action="updated"`` and
   exactly one card exists.

3. **CLS-TEST-R3-008-003** — passed_forward_summary: ``valid_submission_count``,
   ``late_attempt_count``, and ``sealed_submission_refs_available`` are read from the
   real closing record; ``sealed_submission_refs_available=True`` when count > 0.

4. **CLS-TEST-R3-008-004** — Opening readiness linkage: when a ``TM2 Opening Readiness
   Record`` is linked to the closing record, ``target_object_code`` is set to its
   ``opening_readiness_code``.

5. **CLS-TEST-R3-008-005** — technical_refs: contains ``tender_code`` and
   ``publication_snapshot_code`` from the Journey.

6. **CLS-TEST-R3-008-006** — No-fabrication guard (LV-R3-008-01): calling with a
   non-existent ``closing_code`` raises ``ValueError`` with ``CLOSING_RECORD_NOT_FOUND``;
   blank inputs raise appropriate error codes.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r3_008_tender_closing_handoff
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
from kentender_procurement.procurement_lifecycle.tender_closing_handoff import (
    create_tender_closing_certificate,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    JOURNEY_CODE,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"

# WORKS master codes (spec §4.2 / §16.9)
_TENDER_CODE = "TND-MOH-2026-001"
_CLOSING_CODE = "CLS-TND-MOH-2026-001"
_EXPECTED_HANDOFF_CODE = "CLOSECERT-TND-MOH-2026-001"
_EXPECTED_SNAPSHOT_CODE = "PUBSNAP-TND-MOH-2026-001-V2"


def _get_tm2_tender_frappe_name() -> str:
    """Return the Frappe record name for TND-MOH-2026-001."""
    return frappe.db.get_value("TM2 Tender", {"tender_code": _TENDER_CODE}, "name") or ""


def _create_test_closing_record(
    tm2_tender_name: str,
    closing_code: str = _CLOSING_CODE,
    valid_count: int = 2,
    late_count: int = 1,
) -> str:
    """Create a minimal TM2 Tender Closing Record for testing. Returns Frappe name."""
    doc = frappe.get_doc(
        {
            "doctype": "TM2 Tender Closing Record",
            "tm2_tender": tm2_tender_name,
            "tender_code": _TENDER_CODE,
            "closing_code": closing_code,
            "submission_deadline_at": "2026-06-05 11:00:00",
            "closed_at": "2026-06-05 11:00:05",
            "closed_by": "SYSTEM",
            "closing_status": "Closed On Time",
            "valid_submission_count": valid_count,
            "late_attempt_count": late_count,
        }
    )
    doc.flags.ignore_permissions = True
    doc.flags.ignore_mandatory = True
    doc.insert()
    frappe.db.commit()
    return doc.name


class TestR3008TenderClosingHandoff(IntegrationTestCase):
    """R3-008 — Tender closing certificate handoff service tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        cls.pe_name = ensure_procuring_entity(_PE_CODE, _PE_DISPLAY)

        # Seed the full prerequisite chain
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

        # Store TM2 Tender Frappe name for test fixture creation
        cls.tm2_frappe_name = _get_tm2_tender_frappe_name()
        assert cls.tm2_frappe_name, "TM2 Tender TND-MOH-2026-001 must exist"

    @classmethod
    def tearDownClass(cls):
        frappe.set_user("Administrator")
        # Clean up closing records and handoff card created in tests
        for rec_name in frappe.db.get_all(
            "TM2 Tender Closing Record",
            filters={"closing_code": ["like", "CLS-TND-MOH-2026-001%"]},
            pluck="name",
        ):
            frappe.delete_doc("TM2 Tender Closing Record", rec_name, force=True)
        for card_name in frappe.db.get_all(
            "Procurement Handoff Card",
            filters={"handoff_code": _EXPECTED_HANDOFF_CODE},
            pluck="name",
        ):
            frappe.delete_doc("Procurement Handoff Card", card_name, force=True)
        frappe.db.commit()
        super().tearDownClass()

    # ------------------------------------------------------------------
    # Test 1 — Happy path (creates card from real closing record)
    # ------------------------------------------------------------------

    def test_01_creates_card_with_correct_source_fields(self):
        """Creates CLOSECERT card with correct source fields and locked_summary."""
        cls_frappe_name = _create_test_closing_record(self.tm2_frappe_name)
        try:
            result = create_tender_closing_certificate(_TENDER_CODE, _CLOSING_CODE, JOURNEY_CODE)

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
                    "status",
                    "next_action",
                    "locked_summary",
                ],
                as_dict=True,
            )
            self.assertIsNotNone(card, f"Card {_EXPECTED_HANDOFF_CODE!r} not found")

            self.assertEqual(card["handoff_title"], "Tender Closing Certificate")
            self.assertEqual(card["source_module"], "Tender Management")
            self.assertEqual(card["target_module"], "Bid Opening")
            self.assertEqual(card["source_object_type"], "Tender Closing Record")
            self.assertEqual(card["source_object_code"], _CLOSING_CODE)
            self.assertEqual(card["status"], "Consumed")

            locked = json.loads(card["locked_summary"])
            self.assertTrue(locked.get("submission_window_closed"))
            self.assertEqual(locked.get("official_time_source"), "Server Time")
            self.assertIn("closed_at", locked)
            self.assertIn("submission_deadline", locked)
            self.assertTrue(
                locked["closed_at"].startswith("2026-06-05"),
                f"Expected closed_at starting with 2026-06-05; got {locked['closed_at']}",
            )
        finally:
            frappe.db.delete("TM2 Tender Closing Record", {"name": cls_frappe_name})
            frappe.db.commit()

    # ------------------------------------------------------------------
    # Test 2 — Idempotency
    # ------------------------------------------------------------------

    def test_02_idempotency_returns_updated(self):
        """Re-running returns action='updated' with one card."""
        cls_frappe_name = _create_test_closing_record(self.tm2_frappe_name)
        try:
            create_tender_closing_certificate(_TENDER_CODE, _CLOSING_CODE, JOURNEY_CODE)
            result2 = create_tender_closing_certificate(_TENDER_CODE, _CLOSING_CODE, JOURNEY_CODE)

            self.assertTrue(result2.get("ok"))
            self.assertEqual(result2["action"], "updated")
            count = frappe.db.count(
                "Procurement Handoff Card", {"handoff_code": _EXPECTED_HANDOFF_CODE}
            )
            self.assertEqual(count, 1)
        finally:
            frappe.db.delete("TM2 Tender Closing Record", {"name": cls_frappe_name})
            frappe.db.delete(
                "Procurement Handoff Card", {"handoff_code": _EXPECTED_HANDOFF_CODE}
            )
            frappe.db.commit()

    # ------------------------------------------------------------------
    # Test 3 — passed_forward_summary from closing record
    # ------------------------------------------------------------------

    def test_03_passed_forward_summary_from_closing_record(self):
        """passed_forward_summary reflects real counts from TM2 Tender Closing Record."""
        cls_frappe_name = _create_test_closing_record(
            self.tm2_frappe_name, valid_count=2, late_count=1
        )
        try:
            result = create_tender_closing_certificate(_TENDER_CODE, _CLOSING_CODE, JOURNEY_CODE)
            self.assertTrue(result.get("ok"))

            passed_raw = frappe.db.get_value(
                "Procurement Handoff Card",
                {"handoff_code": _EXPECTED_HANDOFF_CODE},
                "passed_forward_summary",
            )
            passed = json.loads(passed_raw)
            self.assertEqual(passed.get("valid_submission_count"), 2)
            self.assertEqual(passed.get("late_attempt_count"), 1)
            self.assertTrue(
                passed.get("sealed_submission_refs_available"),
                "sealed_submission_refs_available must be True when valid_submission_count > 0",
            )
        finally:
            frappe.db.delete("TM2 Tender Closing Record", {"name": cls_frappe_name})
            frappe.db.delete(
                "Procurement Handoff Card", {"handoff_code": _EXPECTED_HANDOFF_CODE}
            )
            frappe.db.commit()

    # ------------------------------------------------------------------
    # Test 4 — Opening readiness linkage
    # ------------------------------------------------------------------

    def test_04_target_object_code_from_opening_readiness_record(self):
        """When TM2 Opening Readiness Record is linked, target_object_code is set."""
        cls_frappe_name = _create_test_closing_record(self.tm2_frappe_name)
        orr_frappe_name = None
        try:
            # Create a linked TM2 Opening Readiness Record
            orr_doc = frappe.get_doc(
                {
                    "doctype": "TM2 Opening Readiness Record",
                    "tm2_tender": self.tm2_frappe_name,
                    "tender_code": _TENDER_CODE,
                    "tm2_tender_closing_record": cls_frappe_name,
                    "opening_readiness_code": "ORR-TND-MOH-2026-001",
                    "dom_output_code": "DOM-TND-MOH-2026-001-V2",
                    "tender_std_instance_code": "STDINST-TND-MOH-2026-001",
                    "valid_submission_count": 2,
                    "readiness_status": "Ready",
                }
            )
            orr_doc.flags.ignore_permissions = True
            orr_doc.flags.ignore_mandatory = True
            orr_doc.insert()
            orr_frappe_name = orr_doc.name
            frappe.db.commit()

            result = create_tender_closing_certificate(_TENDER_CODE, _CLOSING_CODE, JOURNEY_CODE)
            self.assertTrue(result.get("ok"))

            card = frappe.db.get_value(
                "Procurement Handoff Card",
                {"handoff_code": _EXPECTED_HANDOFF_CODE},
                ["target_object_type", "target_object_code"],
                as_dict=True,
            )
            self.assertEqual(card["target_object_type"], "Opening Readiness Record")
            self.assertEqual(card["target_object_code"], "ORR-TND-MOH-2026-001")

        finally:
            if orr_frappe_name:
                frappe.db.delete("TM2 Opening Readiness Record", {"name": orr_frappe_name})
            frappe.db.delete("TM2 Tender Closing Record", {"name": cls_frappe_name})
            frappe.db.delete(
                "Procurement Handoff Card", {"handoff_code": _EXPECTED_HANDOFF_CODE}
            )
            frappe.db.commit()

    # ------------------------------------------------------------------
    # Test 5 — technical_refs
    # ------------------------------------------------------------------

    def test_05_technical_refs_contains_tender_code_and_snapshot(self):
        """technical_refs has tender_code and publication_snapshot_code from Journey."""
        cls_frappe_name = _create_test_closing_record(self.tm2_frappe_name)
        try:
            result = create_tender_closing_certificate(_TENDER_CODE, _CLOSING_CODE, JOURNEY_CODE)
            self.assertTrue(result.get("ok"))

            tech_raw = frappe.db.get_value(
                "Procurement Handoff Card",
                {"handoff_code": _EXPECTED_HANDOFF_CODE},
                "technical_refs_json",
            )
            tech = json.loads(tech_raw or "{}")
            self.assertEqual(tech.get("tender_code"), _TENDER_CODE)
            self.assertEqual(tech.get("publication_snapshot_code"), _EXPECTED_SNAPSHOT_CODE)
        finally:
            frappe.db.delete("TM2 Tender Closing Record", {"name": cls_frappe_name})
            frappe.db.delete(
                "Procurement Handoff Card", {"handoff_code": _EXPECTED_HANDOFF_CODE}
            )
            frappe.db.commit()

    # ------------------------------------------------------------------
    # Test 6 — No-fabrication guard (LV-R3-008-01)
    # ------------------------------------------------------------------

    def test_06_no_fabrication_raises_closing_record_not_found(self):
        """Calling with non-existent closing_code raises CLOSING_RECORD_NOT_FOUND."""
        with self.assertRaises(ValueError) as ctx:
            create_tender_closing_certificate(
                _TENDER_CODE, "CLS-DOES-NOT-EXIST-9999", JOURNEY_CODE
            )
        self.assertIn("CLOSING_RECORD_NOT_FOUND", str(ctx.exception))
        # Confirm no card was created
        count = frappe.db.count(
            "Procurement Handoff Card",
            {"handoff_code": "CLOSECERT-TND-MOH-2026-001"},
        )
        self.assertEqual(count, 0, "No card must be created when closing record is absent")

    def test_06b_unknown_tender_raises_tender_not_found(self):
        """Unknown tender_code raises TENDER_NOT_FOUND."""
        with self.assertRaises(ValueError) as ctx:
            create_tender_closing_certificate(
                "TND-NONEXISTENT-9999", _CLOSING_CODE, JOURNEY_CODE
            )
        self.assertIn("TENDER_NOT_FOUND", str(ctx.exception))

    def test_06c_blank_inputs_raise_appropriate_codes(self):
        """Blank inputs raise the correct error codes."""
        with self.assertRaises(ValueError) as ctx:
            create_tender_closing_certificate("", _CLOSING_CODE, JOURNEY_CODE)
        self.assertIn("INVALID_TENDER_CODE", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            create_tender_closing_certificate(_TENDER_CODE, "", JOURNEY_CODE)
        self.assertIn("INVALID_CLOSING_CODE", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            create_tender_closing_certificate(_TENDER_CODE, _CLOSING_CODE, "")
        self.assertIn("INVALID_JOURNEY_CODE", str(ctx.exception))
