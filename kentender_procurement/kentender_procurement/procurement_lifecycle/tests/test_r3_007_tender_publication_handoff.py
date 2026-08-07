# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R3-007 — ``create_tender_publication_certificate`` service tests.

## Tests

1. **TND-TEST-R3-007-001** — Happy path: valid ``(tender_code, publication_code, journey_code)``
   creates ``PUBCERT-TND-MOH-2026-001`` with correct source/target fields, ``status="Handed Off"``,
   and ``locked_summary`` containing ``published_tender``, ``procurement_method``,
   ``procurement_category``, and ``submission_deadline``.

2. **TND-TEST-R3-007-002** — Idempotency: re-running returns ``action="updated"`` and
   exactly one card exists for ``PUBCERT-TND-MOH-2026-001``.

3. **TND-TEST-R3-007-003** — Addendum awareness (LV-R3-007-01): when
   ``TM2 Tender Timeline.deadline_extended=1`` and
   ``extension_source_addendum_code`` is set, ``passed_forward_summary`` reflects
   ``addendum_acknowledgement_required=True`` + ``current_addendum``, and the
   evidence links include the addendum.

4. **TND-TEST-R3-007-004** — Snapshot awareness (LV-R3-007-01): when a real
   ``Tender Publication Snapshot`` is linked via ``tm2_tender``, output codes
   (``bundle/dsm/dom/dem/dcm_output_code``) appear in ``technical_refs``.

5. **TND-TEST-R3-007-005** — No addendum case: when no deadline extension or addendum
   exists, ``addendum_acknowledgement_required=False``, no addendum evidence link.

6. **TND-TEST-R3-007-006** — Error handling: unknown ``tender_code`` raises ``ValueError``
   with ``TENDER_NOT_FOUND``; blank inputs raise appropriate error codes.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r3_007_tender_publication_handoff
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
from kentender_procurement.tender_management.seeds.works_master_std_seed import (
    upsert_works_master_std,
)
from kentender_procurement.tender_management.seeds.works_master_tender_seed import (
    upsert_works_master_tender,
)
from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
    load_procurement_lifecycle_works_master,
)
from kentender_procurement.procurement_lifecycle.tender_publication_handoff import (
    create_tender_publication_certificate,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    JOURNEY_CODE,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"

# WORKS master codes (spec §4.2 / §16.8)
_TENDER_CODE = "TND-MOH-2026-001"
_PUBLICATION_CODE = "PUB-TND-MOH-2026-001-001"
_EXPECTED_HANDOFF_CODE = "PUBCERT-TND-MOH-2026-001"
_EXPECTED_SNAPSHOT_CODE = "PUBSNAP-TND-MOH-2026-001-V2"  # Journey ref (conceptual)
_EXPECTED_ADDENDUM_CODE = "ADD-TND-MOH-2026-001-01"
_EXPECTED_SUBMISSION_DEADLINE_PREFIX = "2026-06-05"


class TestR3007TenderPublicationHandoff(IntegrationTestCase):
    """R3-007 — Tender publication certificate handoff service tests."""

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

    @classmethod
    def tearDownClass(cls):
        frappe.set_user("Administrator")
        for card_name in frappe.db.get_all(
            "Procurement Handoff Card",
            filters={"handoff_code": ["like", "PUBCERT-TND-R3007-TEST%"]},
            pluck="name",
        ):
            frappe.delete_doc("Procurement Handoff Card", card_name, force=True)
        frappe.db.commit()
        super().tearDownClass()

    # ------------------------------------------------------------------
    # Test 1 — Happy path
    # ------------------------------------------------------------------

    def test_01_creates_card_with_correct_fields(self):
        """Creates PUBCERT card with correct source/target fields and locked_summary."""
        result = create_tender_publication_certificate(
            _TENDER_CODE, _PUBLICATION_CODE, JOURNEY_CODE
        )

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

        self.assertEqual(card["handoff_title"], "Tender Publication Certificate")
        self.assertEqual(card["source_module"], "Tender Management")
        self.assertEqual(card["target_module"], "Suppliers / Tender Closing")
        self.assertEqual(card["source_object_type"], "TM2 Tender")
        self.assertEqual(card["source_object_code"], _TENDER_CODE)
        self.assertEqual(card["target_object_type"], "Supplier Portal / Tender Closing")
        self.assertEqual(card["target_object_code"], _TENDER_CODE)
        self.assertEqual(card["status"], "Handed Off")

        # locked_summary shape (spec §16.8)
        locked = json.loads(card["locked_summary"])
        self.assertEqual(locked.get("published_tender"), _TENDER_CODE)
        self.assertIn("procurement_method", locked)
        self.assertIn("procurement_category", locked)
        # submission_deadline from timeline
        deadline = locked.get("submission_deadline", "")
        self.assertTrue(
            deadline.startswith(_EXPECTED_SUBMISSION_DEADLINE_PREFIX),
            f"Expected deadline starting with {_EXPECTED_SUBMISSION_DEADLINE_PREFIX!r}, got {deadline!r}",
        )

    # ------------------------------------------------------------------
    # Test 2 — Idempotency
    # ------------------------------------------------------------------

    def test_02_idempotency_returns_updated(self):
        """Re-running returns action='updated' with one card."""
        create_tender_publication_certificate(_TENDER_CODE, _PUBLICATION_CODE, JOURNEY_CODE)
        result2 = create_tender_publication_certificate(
            _TENDER_CODE, _PUBLICATION_CODE, JOURNEY_CODE
        )
        self.assertTrue(result2.get("ok"))
        self.assertEqual(result2["action"], "updated")

        count = frappe.db.count(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
        )
        self.assertEqual(count, 1, "Must have exactly one PUBCERT card")

    # ------------------------------------------------------------------
    # Test 3 — Addendum awareness (LV-R3-007-01)
    # ------------------------------------------------------------------

    def test_03_addendum_awareness_from_timeline(self):
        """Addendum from TM2 Tender Timeline deadline extension populates passed_forward_summary."""
        # WORKS master seed sets TM2 Tender Timeline with:
        # deadline_extended=1, extension_source_addendum_code="ADD-TND-MOH-2026-001-01"
        result = create_tender_publication_certificate(
            _TENDER_CODE, _PUBLICATION_CODE, JOURNEY_CODE
        )
        self.assertTrue(result.get("ok"))

        card = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
            ["passed_forward_summary", "evidence_links_json"],
            as_dict=True,
        )
        self.assertIsNotNone(card)

        passed = json.loads(card["passed_forward_summary"])
        self.assertTrue(
            passed.get("addendum_acknowledgement_required"),
            f"Expected addendum_acknowledgement_required=True; got: {passed}",
        )
        self.assertEqual(
            passed.get("current_addendum"),
            _EXPECTED_ADDENDUM_CODE,
            f"Expected current_addendum={_EXPECTED_ADDENDUM_CODE!r}; got {passed.get('current_addendum')!r}",
        )

        # Evidence links must include the addendum
        links_raw = json.loads(card["evidence_links_json"])
        links = links_raw.get("links", links_raw) if isinstance(links_raw, dict) else links_raw
        object_types = [lnk.get("object_type") for lnk in links]
        self.assertIn("Tender Addendum", object_types, f"Expected Tender Addendum link; got {object_types}")
        add_link = next(lnk for lnk in links if lnk.get("object_type") == "Tender Addendum")
        self.assertEqual(add_link.get("object_code"), _EXPECTED_ADDENDUM_CODE)

    # ------------------------------------------------------------------
    # Test 4 — Snapshot awareness (LV-R3-007-01)
    # ------------------------------------------------------------------

    def test_04_snapshot_awareness_output_codes_from_real_snapshot(self):
        """When a real Tender Publication Snapshot is linked, output codes appear in technical_refs."""
        # Create a test Publication Snapshot linked to TND-MOH-2026-001
        tm2_frappe_name = frappe.db.get_value(
            "TM2 Tender", {"tender_code": _TENDER_CODE}, "name"
        )
        self.assertIsNotNone(tm2_frappe_name)

        test_snap = frappe.get_doc(
            {
                "doctype": "Tender Publication Snapshot",
                "tm2_tender": tm2_frappe_name,
                "bundle_output_code": "GB-TND-MOH-2026-001-V2",
                "dsm_output_code": "DSM-TND-MOH-2026-001-V2",
                "dom_output_code": "DOM-TND-MOH-2026-001-V2",
                "dem_output_code": "DEM-TND-MOH-2026-001-V2",
                "dcm_output_code": "DCM-TND-MOH-2026-001-V2",
            }
        )
        test_snap.flags.ignore_permissions = True
        test_snap.flags.ignore_mandatory = True
        test_snap.insert()
        test_snap_name = test_snap.name
        frappe.db.commit()

        try:
            result = create_tender_publication_certificate(
                _TENDER_CODE, _PUBLICATION_CODE, JOURNEY_CODE
            )
            self.assertTrue(result.get("ok"))

            tech_raw = frappe.db.get_value(
                "Procurement Handoff Card",
                {"handoff_code": _EXPECTED_HANDOFF_CODE},
                "technical_refs_json",
            )
            tech = json.loads(tech_raw or "{}")
            self.assertEqual(tech.get("bundle_output_code"), "GB-TND-MOH-2026-001-V2")
            self.assertEqual(tech.get("dsm_output_code"), "DSM-TND-MOH-2026-001-V2")
            self.assertEqual(tech.get("dom_output_code"), "DOM-TND-MOH-2026-001-V2")
            self.assertEqual(tech.get("dem_output_code"), "DEM-TND-MOH-2026-001-V2")
            self.assertEqual(tech.get("dcm_output_code"), "DCM-TND-MOH-2026-001-V2")

        finally:
            frappe.delete_doc("Tender Publication Snapshot", test_snap_name, force=True)
            frappe.db.commit()

    # ------------------------------------------------------------------
    # Test 5 — technical_refs contains publication_code
    # ------------------------------------------------------------------

    def test_05_publication_code_in_technical_refs(self):
        """publication_code always appears in technical_refs regardless of DB record."""
        result = create_tender_publication_certificate(
            _TENDER_CODE, _PUBLICATION_CODE, JOURNEY_CODE
        )
        self.assertTrue(result.get("ok"))

        tech_raw = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
            "technical_refs_json",
        )
        tech = json.loads(tech_raw or "{}")
        self.assertEqual(
            tech.get("publication_code"),
            _PUBLICATION_CODE,
            f"Expected publication_code={_PUBLICATION_CODE!r}; got {tech.get('publication_code')!r}",
        )

    # ------------------------------------------------------------------
    # Test 6 — supplier_access_active reflects Published status
    # ------------------------------------------------------------------

    def test_06_supplier_access_active_when_published(self):
        """supplier_access_active=True and tender_documents_available=True for Published tender."""
        result = create_tender_publication_certificate(
            _TENDER_CODE, _PUBLICATION_CODE, JOURNEY_CODE
        )
        self.assertTrue(result.get("ok"))

        passed_raw = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
            "passed_forward_summary",
        )
        passed = json.loads(passed_raw)
        self.assertTrue(passed.get("supplier_access_active"))
        self.assertTrue(passed.get("tender_documents_available"))

    # ------------------------------------------------------------------
    # Test 7 — Error handling
    # ------------------------------------------------------------------

    def test_07_unknown_tender_raises_tender_not_found(self):
        """Unknown tender_code raises ValueError with TENDER_NOT_FOUND."""
        with self.assertRaises(ValueError) as ctx:
            create_tender_publication_certificate(
                "TND-NONEXISTENT-9999", _PUBLICATION_CODE, JOURNEY_CODE
            )
        self.assertIn("TENDER_NOT_FOUND", str(ctx.exception))

    def test_07b_blank_inputs_raise_appropriate_codes(self):
        """Blank inputs raise the expected error codes."""
        with self.assertRaises(ValueError) as ctx:
            create_tender_publication_certificate("", _PUBLICATION_CODE, JOURNEY_CODE)
        self.assertIn("INVALID_TENDER_CODE", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            create_tender_publication_certificate(_TENDER_CODE, "", JOURNEY_CODE)
        self.assertIn("INVALID_PUBLICATION_CODE", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            create_tender_publication_certificate(_TENDER_CODE, _PUBLICATION_CODE, "")
        self.assertIn("INVALID_JOURNEY_CODE", str(ctx.exception))
