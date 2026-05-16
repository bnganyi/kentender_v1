# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R3-012 / LV-R3-012-01 — ``get_procurement_journey_by_object`` full-aggregate service tests.

## Tests

1. **OBJ-001** — Demand lookup: resolving ``DEM-MOH-2026-001`` returns the full journey
   aggregate with ``journey_code == "JRN-MOH-2026-001"`` and all pack §9.1 keys.

2. **OBJ-002** — Procurement Package lookup: resolving ``PKG-MOH-2026-001`` returns the
   same journey with identical header fields.

3. **OBJ-003** — TM2 Tender lookup: resolving ``TND-MOH-2026-001`` returns the same
   journey (same ``journey_code``).

4. **OBJ-004** — Full aggregate shape: the response contains ``steps``, ``handoff_cards``,
   ``evidence_summary``, ``blocker_count``, ``refs`` — confirming it is the full R3-011
   aggregate, not the minimal R1-009 dict.

5. **OBJ-005** — Budget Line lookup: resolving via ``Budget Line`` type resolves the
   same journey (proves additional ref field mapping).

6. **MISS-001** — Unknown code returns None (no journey linked to that object code).

7. **MISS-002** — Unsupported object type returns None (not an error, just no mapping).

8. **ERR-001** — Blank object_type raises ``INVALID_OBJECT_TYPE``; blank object_code
   raises ``INVALID_OBJECT_CODE``.

9. **SUPPORT-001** — ``is_object_type_supported`` correctly identifies supported and
   unsupported types.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r3_012_journey_by_object
"""

from __future__ import annotations

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
from kentender_procurement.procurement_lifecycle.journey_by_object import (
    get_procurement_journey_by_object,
    is_object_type_supported,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
    JOURNEY_CODE,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"

# WORKS master business codes (spec §4.2)
_DEMAND_CODE = "DEM-MOH-2026-001"
_PACKAGE_CODE = "PKG-MOH-2026-001"
_TENDER_CODE = "TND-MOH-2026-001"
_BUDGET_LINE_CODE = "BUD-MOH-INFRA-2026-001"

_EXPECTED_JOURNEY_CODE = "JRN-MOH-2026-001"
_EXPECTED_TITLE = "District Hospital Renovation Works"

# All required top-level keys from pack §9.1
_REQUIRED_KEYS = {
    "journey_code",
    "title",
    "procuring_entity_code",
    "category",
    "method",
    "current_stage",
    "current_status",
    "next_action",
    "blocker_count",
    "critical_blocker_count",
    "steps",
    "handoff_cards",
    "evidence_summary",
}


class TestR3012JourneyByObject(IntegrationTestCase):
    """R3-012 — get_procurement_journey_by_object full-aggregate tests."""

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

    # ------------------------------------------------------------------
    # Test 1 — OBJ-001: Demand lookup
    # ------------------------------------------------------------------

    def test_01_demand_code_resolves_to_full_journey(self):
        """Demand code DEM-MOH-2026-001 → full journey aggregate."""
        result = get_procurement_journey_by_object("Demand", _DEMAND_CODE)

        self.assertIsNotNone(result, f"Expected journey for Demand {_DEMAND_CODE!r}")
        self.assertEqual(result["journey_code"], _EXPECTED_JOURNEY_CODE)
        self.assertEqual(result["title"], _EXPECTED_TITLE)
        # Check all required keys present
        missing = _REQUIRED_KEYS - set(result.keys())
        self.assertFalse(missing, f"Missing required keys: {missing}")

    # ------------------------------------------------------------------
    # Test 2 — OBJ-002: Procurement Package lookup
    # ------------------------------------------------------------------

    def test_02_procurement_package_resolves_to_same_journey(self):
        """Procurement Package code PKG-MOH-2026-001 → same journey."""
        result = get_procurement_journey_by_object("Procurement Package", _PACKAGE_CODE)

        self.assertIsNotNone(result)
        self.assertEqual(result["journey_code"], _EXPECTED_JOURNEY_CODE)

    # ------------------------------------------------------------------
    # Test 3 — OBJ-003: TM2 Tender lookup
    # ------------------------------------------------------------------

    def test_03_tm2_tender_resolves_to_same_journey(self):
        """TM2 Tender code TND-MOH-2026-001 → same journey."""
        result = get_procurement_journey_by_object("TM2 Tender", _TENDER_CODE)

        self.assertIsNotNone(result)
        self.assertEqual(result["journey_code"], _EXPECTED_JOURNEY_CODE)

    # ------------------------------------------------------------------
    # Test 4 — OBJ-004: Full aggregate shape (not minimal dict)
    # ------------------------------------------------------------------

    def test_04_response_is_full_aggregate_not_minimal(self):
        """Response includes steps, handoff_cards, evidence_summary, refs — confirming full aggregate."""
        result = get_procurement_journey_by_object("TM2 Tender", _TENDER_CODE)

        self.assertIsNotNone(result)
        # Full aggregate fields
        self.assertIsInstance(result.get("steps"), list)
        self.assertIsInstance(result.get("handoff_cards"), list)
        self.assertIsInstance(result.get("evidence_summary"), list)
        self.assertIn("refs", result)
        self.assertIsInstance(result.get("blocker_count"), int)
        # These fields only exist in full aggregate, NOT in the R1-009 minimal dict
        self.assertGreater(len(result["steps"]), 0, "steps must be non-empty for WORKS master")
        self.assertGreater(
            len(result["handoff_cards"]), 0, "handoff_cards must be non-empty for WORKS master"
        )

    # ------------------------------------------------------------------
    # Test 5 — OBJ-005: Budget Line lookup (additional ref field)
    # ------------------------------------------------------------------

    def test_05_budget_line_resolves_to_journey(self):
        """Budget Line code resolves to the same WORKS master journey."""
        result = get_procurement_journey_by_object("Budget Line", _BUDGET_LINE_CODE)

        self.assertIsNotNone(result, f"Expected journey for Budget Line {_BUDGET_LINE_CODE!r}")
        self.assertEqual(result["journey_code"], _EXPECTED_JOURNEY_CODE)

    # ------------------------------------------------------------------
    # Test 6 — MISS-001: unknown code returns None
    # ------------------------------------------------------------------

    def test_06_unknown_code_returns_none(self):
        """object_code that has no linked journey returns None."""
        result = get_procurement_journey_by_object("Demand", "DEM-DOES-NOT-EXIST-9999")
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # Test 7 — MISS-002: unsupported object type returns None
    # ------------------------------------------------------------------

    def test_07_unsupported_object_type_returns_none(self):
        """Unknown object_type returns None (graceful — not an error)."""
        result = get_procurement_journey_by_object("Widget Machine", "WM-001")
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # Test 8 — ERR-001: input validation
    # ------------------------------------------------------------------

    def test_08_blank_object_type_raises_invalid_object_type(self):
        """Blank object_type raises INVALID_OBJECT_TYPE."""
        with self.assertRaises(ValueError) as ctx:
            get_procurement_journey_by_object("", _DEMAND_CODE)
        self.assertIn("INVALID_OBJECT_TYPE", str(ctx.exception))

    def test_08b_blank_object_code_raises_invalid_object_code(self):
        """Blank object_code raises INVALID_OBJECT_CODE."""
        with self.assertRaises(ValueError) as ctx:
            get_procurement_journey_by_object("Demand", "")
        self.assertIn("INVALID_OBJECT_CODE", str(ctx.exception))

    # ------------------------------------------------------------------
    # Test 9 — SUPPORT-001: is_object_type_supported
    # ------------------------------------------------------------------

    def test_09_is_object_type_supported(self):
        """is_object_type_supported returns True for known types, False for unknown."""
        self.assertTrue(is_object_type_supported("Demand"))
        self.assertTrue(is_object_type_supported("TM2 Tender"))
        self.assertTrue(is_object_type_supported("Procurement Package"))
        self.assertTrue(is_object_type_supported("Budget Line"))
        self.assertFalse(is_object_type_supported("Widget Machine"))
        self.assertFalse(is_object_type_supported(""))
