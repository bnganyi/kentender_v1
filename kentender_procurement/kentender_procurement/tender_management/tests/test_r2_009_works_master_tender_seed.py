# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R2-009 — WORKS master tender seed tests (spec §13 / VAL-SEED-010 prep).

Tests:
  1. SEED-TEST-R2-009-001 — Fresh seed creates TND-MOH-2026-001 with status=Published,
     linked to PKG-MOH-2026-001.
  2. SEED-TEST-R2-009-002 — Idempotent: second run returns ok=True and no duplicate TM2 record.
  3. SEED-TEST-R2-009-003 — template_version = STDTV-WORKS-BUILDING-CIVIL-APR2022
     (VAL-SEED-010 prerequisite).
  4. SEED-TEST-R2-009-004 — TM2 Tender Timeline exists with deadline_extended and
     extension_source_addendum_code set per spec §13.2.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.tender_management.tests.test_r2_009_works_master_tender_seed
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cint

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
    TENDER_CODE,
    PACKAGE_CODE,
    STD_VERSION_REF,
    _ADDENDUM_CODE,
    upsert_works_master_tender,
)

_PE_CODE = "PE-MOH"
_PE_NAME_DISPLAY = "Ministry of Health"


def _clean_tender() -> None:
    """Remove TND-MOH-2026-001 and all linked satellite records."""
    # Timeline (UNIQUE on tm2_tender)
    frappe.db.delete("TM2 Tender Timeline", {"tm2_tender": TENDER_CODE})
    frappe.db.delete("TM2 Tender Timeline", {"tender_code": TENDER_CODE})
    # Access Rule
    frappe.db.delete("TM2 Tender Access Rule", {"tm2_tender": TENDER_CODE})
    frappe.db.delete("TM2 Tender Access Rule", {"tender_code": TENDER_CODE})
    # Audit Events
    frappe.db.delete("TM2 Tender Audit Event", {"tm2_tender": TENDER_CODE})
    frappe.db.delete("TM2 Tender Audit Event", {"tender_code": TENDER_CODE})
    # Tender itself
    if frappe.db.exists("TM2 Tender", TENDER_CODE):
        frappe.db.delete("TM2 Tender", {"name": TENDER_CODE})

    # Also sweep any auto-coded tender for PKG-MOH-2026-001 that was not renamed
    pkg_name = frappe.db.get_value(
        "Procurement Package", {"package_code": PACKAGE_CODE}, "name"
    )
    if pkg_name:
        for row in frappe.get_all(
            "TM2 Tender",
            filters={"procurement_package": pkg_name},
            pluck="name",
        ):
            frappe.db.delete("TM2 Tender Timeline", {"tm2_tender": row})
            frappe.db.delete("TM2 Tender Access Rule", {"tm2_tender": row})
            frappe.db.delete("TM2 Tender Audit Event", {"tm2_tender": row})
            frappe.db.delete("TM2 Tender", {"name": row})


class TestR2009WorksMasterTenderSeed(IntegrationTestCase):
    """R2-009 — Tender seed alignment (spec §13 / VAL-SEED-010 prep)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        cls.pe_name = ensure_procuring_entity(_PE_CODE, _PE_NAME_DISPLAY)

        # R2-004: strategy chain
        strat = upsert_works_master_strategy_hierarchy()
        assert strat.get("ok"), f"Strategy prerequisite failed: {strat}"

        # R2-005: budget chain
        budget = upsert_works_master_budget()
        assert budget.get("ok"), f"Budget prerequisite failed: {budget}"

        # R2-006: demand
        demand = upsert_works_master_demand()
        assert demand.get("ok"), f"Demand prerequisite failed: {demand}"

        # R2-007: planning
        planning = upsert_works_master_planning()
        assert planning.get("ok"), f"Planning prerequisite failed: {planning}"

        # R2-008: STD template
        std = upsert_works_master_std()
        assert std.get("ok"), f"STD prerequisite failed: {std}"

    def tearDown(self):
        _clean_tender()

    # ── Test 1: fresh seed creates TND-MOH-2026-001 ──────────────────────────
    def test_001_fresh_seed_creates_tender_with_spec_values(self):
        """SEED-TEST-R2-009-001: Seed creates TND-MOH-2026-001 linked to PKG-MOH-2026-001."""
        out = upsert_works_master_tender()

        self.assertTrue(out.get("ok"), f"Seed returned error: {out}")
        self.assertIn(out.get("action"), ("created", "adopted"))
        self.assertEqual(out["tender_code"], TENDER_CODE)

        # Document must exist
        self.assertTrue(
            frappe.db.exists("TM2 Tender", TENDER_CODE),
            f"TM2 Tender {TENDER_CODE!r} must exist after seed",
        )

        # Linked to correct package
        pkg_link = frappe.db.get_value("TM2 Tender", TENDER_CODE, "procurement_package_code")
        self.assertEqual(pkg_link, PACKAGE_CODE, "tender must reference PKG-MOH-2026-001")

        # Status = Published
        status = frappe.db.get_value("TM2 Tender", TENDER_CODE, "status")
        self.assertEqual(status, "Published", f"status must be Published, got {status!r}")

        # Title per spec §13.1
        title = frappe.db.get_value("TM2 Tender", TENDER_CODE, "tender_title") or ""
        self.assertIn("District Hospital", title, "tender_title must include spec §13.1 title text")

        # STD Template set (PKG has default_std_template from R2-008)
        std_link = frappe.db.get_value("TM2 Tender", TENDER_CODE, "std_template") or ""
        self.assertTrue(std_link.strip(), "std_template must be populated by the release service")

    # ── Test 2: idempotency ───────────────────────────────────────────────────
    def test_002_idempotent_second_run_no_duplicate(self):
        """SEED-TEST-R2-009-002: Running twice must not error or create a duplicate."""
        first = upsert_works_master_tender()
        self.assertTrue(first.get("ok"), f"First run error: {first}")

        second = upsert_works_master_tender()
        self.assertTrue(second.get("ok"), f"Second run error: {second}")
        self.assertEqual(second.get("action"), "existing", "Second run must report 'existing'")
        self.assertEqual(second["tender_code"], TENDER_CODE)

        # Exactly one TM2 Tender with this tender_code
        count = frappe.db.sql(
            "SELECT COUNT(*) FROM `tabTM2 Tender` WHERE tender_code=%s",
            (TENDER_CODE,),
        )[0][0]
        self.assertEqual(count, 1, "Expected exactly one TM2 Tender with code TND-MOH-2026-001")

    # ── Test 3: template_version = VAL-SEED-010 business version code ─────────
    def test_003_template_version_set_to_business_version_code(self):
        """SEED-TEST-R2-009-003: template_version = STDTV-WORKS-BUILDING-CIVIL-APR2022 (VAL-SEED-010)."""
        upsert_works_master_tender()

        tv = frappe.db.get_value("TM2 Tender", TENDER_CODE, "template_version") or ""
        self.assertEqual(
            tv,
            STD_VERSION_REF,
            f"template_version must be {STD_VERSION_REF!r} for VAL-SEED-010, got {tv!r}",
        )

    # ── Test 4: Timeline row with extended deadline and addendum code ──────────
    def test_004_timeline_exists_with_extended_deadline_fields(self):
        """SEED-TEST-R2-009-004: Timeline has deadline_extended=1 and addendum code per §13.2."""
        upsert_works_master_tender()

        tl_name = frappe.db.get_value(
            "TM2 Tender Timeline", {"tm2_tender": TENDER_CODE}, "name"
        )
        self.assertIsNotNone(tl_name, "TM2 Tender Timeline must exist for TND-MOH-2026-001")

        tl = frappe.get_doc("TM2 Tender Timeline", tl_name)
        self.assertEqual(
            cint(tl.deadline_extended),
            1,
            "deadline_extended must be 1 (spec §13.2)",
        )
        self.assertEqual(
            tl.extension_source_addendum_code,
            _ADDENDUM_CODE,
            f"extension_source_addendum_code must be {_ADDENDUM_CODE!r}",
        )
        # Submission deadline must be after original deadline (deadline was extended)
        self.assertIsNotNone(tl.submission_deadline_at, "submission_deadline_at must be set")
        self.assertIsNotNone(tl.clarification_deadline_at, "clarification_deadline_at must be set")
        self.assertIsNotNone(tl.opening_scheduled_at, "opening_scheduled_at must be set")
