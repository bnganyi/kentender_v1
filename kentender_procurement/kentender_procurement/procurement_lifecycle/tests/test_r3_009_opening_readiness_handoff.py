# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R3-009 — ``create_opening_readiness_handoff`` service tests.

## Tests

1. **ORR-TEST-R3-009-001** — Happy path: when a real ``TM2 Opening Readiness Record``
   exists, creates ``OPENREADY-TND-MOH-2026-001`` with correct source fields,
   ``status="Handed Off"``, ``source_object_type="Opening Readiness Record"``,
   ``target_object_type="Bid Opening Session"``, and ``locked_summary`` containing
   ``opening_model``, ``publication_snapshot``, ``opening_scheduled_at``, and
   ``arithmetic_correction_at_opening=False``.

2. **ORR-TEST-R3-009-002** — Idempotency: re-running returns ``action="updated"``
   and exactly one card exists.

3. **ORR-TEST-R3-009-003** — passed_forward_summary: ``sealed_submission_refs`` is
   populated from the JSON field; ``opening_register_rules_ready=True`` when
   ``readiness_status="Ready"``; ``display_submitted_total_only=True`` always.

4. **ORR-TEST-R3-009-004** — technical_refs: contains ``dom_output_code`` and
   ``publication_snapshot_code`` from the Journey.

5. **ORR-TEST-R3-009-005** — evidence_link: points to ``Opening Readiness Record``
   with the correct ``object_code``.

6. **ORR-TEST-R3-009-006** — No-fabrication guard (LV-R3-009-01): calling with a
   non-existent ``opening_readiness_code`` raises ``ValueError`` with
   ``OPENING_READINESS_NOT_FOUND``; no card is created. Blank inputs raise appropriate
   error codes.

Note on fixtures: ``TM2 Tender Closing Record`` and ``TM2 Opening Readiness Record``
each enforce at-most-one-per-tender uniqueness. Therefore the ORR fixture is created
once in ``setUpClass`` (reusing the existing seed closing record ``CLS-TND-MOH-2026-001``)
and torn down in ``tearDownClass``.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r3_009_opening_readiness_handoff
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
from kentender_procurement.procurement_lifecycle.opening_readiness_handoff import (
    create_opening_readiness_handoff,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    JOURNEY_CODE,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"

# WORKS master codes (spec §4.2 / §16.10)
_TENDER_CODE = "TND-MOH-2026-001"
_CLOSING_CODE = "CLS-TND-MOH-2026-001"
_ORR_CODE = "ORR-TND-MOH-2026-001"
_EXPECTED_HANDOFF_CODE = "OPENREADY-TND-MOH-2026-001"
_EXPECTED_SNAPSHOT_CODE = "PUBSNAP-TND-MOH-2026-001-V2"
_EXPECTED_DOM_CODE = "DOM-TND-MOH-2026-001-V2"
_EXPECTED_OPENING_SCHEDULED_PREFIX = "2026-06-05"

_SEALED_REFS = [
    "BID-TND-MOH-2026-001-SUP-ALPHA-01",
    "BID-TND-MOH-2026-001-SUP-BETA-01",
]


def _get_or_create_orr(tm2_tender_name: str, closing_frappe_name: str) -> str:
    """Return existing or create a new TM2 Opening Readiness Record; returns Frappe name.

    Only one ORR is allowed per tender, so we reuse it if it already exists.
    """
    existing = frappe.db.get_value(
        "TM2 Opening Readiness Record", {"tm2_tender": tm2_tender_name}, "name"
    )
    if existing:
        return existing

    # sealed_submission_refs must be a JSON object with a "refs" key (TM2-ORR-004)
    refs_json = json.dumps({"refs": _SEALED_REFS})
    doc = frappe.get_doc(
        {
            "doctype": "TM2 Opening Readiness Record",
            "tm2_tender": tm2_tender_name,
            "tender_code": _TENDER_CODE,
            "tm2_tender_closing_record": closing_frappe_name,
            "opening_readiness_code": _ORR_CODE,
            "dom_output_code": _EXPECTED_DOM_CODE,
            "tender_std_instance_code": "STDINST-TND-MOH-2026-001",
            "sealed_submission_refs": refs_json,
            "valid_submission_count": 2,
            "readiness_status": "Ready",
            "prepared_by": "SYSTEM",
        }
    )
    doc.flags.ignore_permissions = True
    doc.flags.ignore_mandatory = True
    doc.insert()
    frappe.db.commit()
    return doc.name


class TestR3009OpeningReadinessHandoff(IntegrationTestCase):
    """R3-009 — Opening readiness handoff service tests.

    Fixtures are shared within the class:
    - The seed closing record ``CLS-TND-MOH-2026-001`` is reused (created by seed).
    - The ORR ``ORR-TND-MOH-2026-001`` is created once and deleted in tearDownClass.
    - The handoff card is deleted after each test.
    """

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

        # Locate TM2 Tender (required for fixture creation)
        cls.tm2_frappe_name = (
            frappe.db.get_value("TM2 Tender", {"tender_code": _TENDER_CODE}, "name") or ""
        )
        assert cls.tm2_frappe_name, "TM2 Tender TND-MOH-2026-001 must exist"

        # Reuse the seed closing record (uniqueness constraint: one per tender)
        cls.closing_frappe_name = (
            frappe.db.get_value(
                "TM2 Tender Closing Record", {"tender_code": _TENDER_CODE}, "name"
            )
            or ""
        )
        assert cls.closing_frappe_name, (
            f"Closing record for {_TENDER_CODE} must exist (seeded by works_master_tender_seed)"
        )

        # Create shared ORR fixture (uniqueness constraint: one per tender)
        cls.orr_frappe_name = _get_or_create_orr(cls.tm2_frappe_name, cls.closing_frappe_name)
        assert cls.orr_frappe_name, "TM2 Opening Readiness Record must be created"
        frappe.db.commit()

    @classmethod
    def tearDownClass(cls):
        frappe.set_user("Administrator")
        # Remove any handoff cards created during tests
        for card_name in frappe.db.get_all(
            "Procurement Handoff Card",
            filters={"handoff_code": _EXPECTED_HANDOFF_CODE},
            pluck="name",
        ):
            frappe.delete_doc("Procurement Handoff Card", card_name, force=True)
        # Remove the ORR fixture (closing record was seeded — leave it)
        for rec_name in frappe.db.get_all(
            "TM2 Opening Readiness Record",
            filters={"opening_readiness_code": _ORR_CODE},
            pluck="name",
        ):
            frappe.delete_doc("TM2 Opening Readiness Record", rec_name, force=True)
        frappe.db.commit()
        super().tearDownClass()

    def _cleanup_card(self):
        """Delete the OPENREADY handoff card (so tests start clean)."""
        for card_name in frappe.db.get_all(
            "Procurement Handoff Card",
            filters={"handoff_code": _EXPECTED_HANDOFF_CODE},
            pluck="name",
        ):
            frappe.delete_doc("Procurement Handoff Card", card_name, force=True)
        frappe.db.commit()

    # ------------------------------------------------------------------
    # Test 1 — Happy path
    # ------------------------------------------------------------------

    def test_01_creates_card_with_correct_source_fields(self):
        """Creates OPENREADY card with correct source/target fields and locked_summary."""
        self._cleanup_card()
        result = create_opening_readiness_handoff(_TENDER_CODE, _ORR_CODE, JOURNEY_CODE)

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
                "status",
                "next_action",
                "locked_summary",
            ],
            as_dict=True,
        )
        self.assertIsNotNone(card, f"Card {_EXPECTED_HANDOFF_CODE!r} not found")

        self.assertEqual(card["handoff_title"], "Opening Readiness Record")
        self.assertEqual(card["source_module"], "Tender Management")
        self.assertEqual(card["target_module"], "Bid Opening")
        self.assertEqual(card["source_object_type"], "Opening Readiness Record")
        self.assertEqual(card["source_object_code"], _ORR_CODE)
        self.assertEqual(card["target_object_type"], "Bid Opening Session")
        self.assertEqual(card["status"], "Handed Off")

        # locked_summary shape (spec §16.10)
        locked = json.loads(card["locked_summary"])
        self.assertEqual(locked.get("opening_model"), _EXPECTED_DOM_CODE)
        self.assertEqual(locked.get("publication_snapshot"), _EXPECTED_SNAPSHOT_CODE)
        self.assertFalse(locked.get("arithmetic_correction_at_opening"))
        opening_sched = locked.get("opening_scheduled_at", "")
        self.assertTrue(
            opening_sched.startswith(_EXPECTED_OPENING_SCHEDULED_PREFIX),
            f"opening_scheduled_at should start with {_EXPECTED_OPENING_SCHEDULED_PREFIX}; got {opening_sched!r}",
        )

    # ------------------------------------------------------------------
    # Test 2 — Idempotency
    # ------------------------------------------------------------------

    def test_02_idempotency_returns_updated(self):
        """Re-running returns action='updated' with one card."""
        self._cleanup_card()
        create_opening_readiness_handoff(_TENDER_CODE, _ORR_CODE, JOURNEY_CODE)
        result2 = create_opening_readiness_handoff(_TENDER_CODE, _ORR_CODE, JOURNEY_CODE)

        self.assertTrue(result2.get("ok"))
        self.assertEqual(result2["action"], "updated")
        count = frappe.db.count(
            "Procurement Handoff Card", {"handoff_code": _EXPECTED_HANDOFF_CODE}
        )
        self.assertEqual(count, 1)

    # ------------------------------------------------------------------
    # Test 3 — passed_forward_summary
    # ------------------------------------------------------------------

    def test_03_passed_forward_summary_shape(self):
        """passed_forward_summary has correct sealed_submission_refs, readiness flag, and display flag."""
        self._cleanup_card()
        result = create_opening_readiness_handoff(_TENDER_CODE, _ORR_CODE, JOURNEY_CODE)
        self.assertTrue(result.get("ok"))

        passed_raw = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
            "passed_forward_summary",
        )
        passed = json.loads(passed_raw)

        # opening_register_rules_ready=True when readiness_status="Ready"
        self.assertTrue(passed.get("opening_register_rules_ready"))
        # display_submitted_total_only always True
        self.assertTrue(passed.get("display_submitted_total_only"))
        # sealed_submission_refs from the JSON field
        refs = passed.get("sealed_submission_refs", [])
        self.assertIsInstance(refs, list)
        self.assertEqual(len(refs), 2)
        self.assertIn("BID-TND-MOH-2026-001-SUP-ALPHA-01", refs)
        self.assertIn("BID-TND-MOH-2026-001-SUP-BETA-01", refs)

    # ------------------------------------------------------------------
    # Test 4 — technical_refs
    # ------------------------------------------------------------------

    def test_04_technical_refs_contains_dom_and_snapshot(self):
        """technical_refs has dom_output_code and publication_snapshot_code."""
        self._cleanup_card()
        result = create_opening_readiness_handoff(_TENDER_CODE, _ORR_CODE, JOURNEY_CODE)
        self.assertTrue(result.get("ok"))

        tech_raw = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
            "technical_refs_json",
        )
        tech = json.loads(tech_raw or "{}")
        self.assertEqual(tech.get("dom_output_code"), _EXPECTED_DOM_CODE)
        self.assertEqual(tech.get("publication_snapshot_code"), _EXPECTED_SNAPSHOT_CODE)

    # ------------------------------------------------------------------
    # Test 5 — evidence link
    # ------------------------------------------------------------------

    def test_05_evidence_link_points_to_orr(self):
        """evidence_links_json contains one link to the Opening Readiness Record."""
        self._cleanup_card()
        result = create_opening_readiness_handoff(_TENDER_CODE, _ORR_CODE, JOURNEY_CODE)
        self.assertTrue(result.get("ok"))

        raw = frappe.db.get_value(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
            "evidence_links_json",
        )
        links_envelope = json.loads(raw)
        links = (
            links_envelope.get("links", links_envelope)
            if isinstance(links_envelope, dict)
            else links_envelope
        )
        self.assertTrue(len(links) >= 1, "Expected at least one evidence link")
        first = links[0]
        self.assertEqual(first.get("object_type"), "Opening Readiness Record")
        self.assertEqual(first.get("object_code"), _ORR_CODE)
        self.assertEqual(first.get("module"), "Tender Management")

    # ------------------------------------------------------------------
    # Test 6 — No-fabrication guard (LV-R3-009-01)
    # ------------------------------------------------------------------

    def test_06_no_fabrication_raises_opening_readiness_not_found(self):
        """Non-existent opening_readiness_code raises OPENING_READINESS_NOT_FOUND; no card created."""
        self._cleanup_card()
        with self.assertRaises(ValueError) as ctx:
            create_opening_readiness_handoff(
                _TENDER_CODE, "ORR-DOES-NOT-EXIST-9999", JOURNEY_CODE
            )
        self.assertIn("OPENING_READINESS_NOT_FOUND", str(ctx.exception))
        count = frappe.db.count(
            "Procurement Handoff Card",
            {"handoff_code": _EXPECTED_HANDOFF_CODE},
        )
        self.assertEqual(count, 0, "No card must be created when ORR is absent")

    def test_06b_unknown_tender_raises_tender_not_found(self):
        """Unknown tender_code raises TENDER_NOT_FOUND."""
        with self.assertRaises(ValueError) as ctx:
            create_opening_readiness_handoff(
                "TND-NONEXISTENT-9999", _ORR_CODE, JOURNEY_CODE
            )
        self.assertIn("TENDER_NOT_FOUND", str(ctx.exception))

    def test_06c_blank_inputs_raise_appropriate_codes(self):
        """Blank inputs raise the correct error codes."""
        with self.assertRaises(ValueError) as ctx:
            create_opening_readiness_handoff("", _ORR_CODE, JOURNEY_CODE)
        self.assertIn("INVALID_TENDER_CODE", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            create_opening_readiness_handoff(_TENDER_CODE, "", JOURNEY_CODE)
        self.assertIn("INVALID_OPENING_READINESS_CODE", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            create_opening_readiness_handoff(_TENDER_CODE, _ORR_CODE, "")
        self.assertIn("INVALID_JOURNEY_CODE", str(ctx.exception))
