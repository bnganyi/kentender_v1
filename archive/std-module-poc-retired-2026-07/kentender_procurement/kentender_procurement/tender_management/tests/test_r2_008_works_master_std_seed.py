# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""R2-008 — WORKS master STD seed tests (spec §12).

Tests:
  1. SEED-TEST-R2-008-001 — Seed creates/updates STD Template with lifecycle_status=Active.
  2. SEED-TEST-R2-008-002 — Idempotent: second run does not error and returns ok=True.
  3. SEED-TEST-R2-008-003 — §16 postconditions pass (hash, category, status, atc, version).
  4. SEED-TEST-R2-008-004 — Procurement Template PTPL-WORKS-OPEN-R2007 is linked to STD Template.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.tender_management.tests.test_r2_008_works_master_std_seed
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cint

from kentender_core.seeds._common import ensure_currency_kes
from kentender_procurement.tender_management.seeds.works_master_std_seed import (
    STD_TEMPLATE_CODE,
    STD_TEMPLATE_VERSION_REF,
    _PLANNING_TEMPLATE_CODE,
    upsert_works_master_std,
)
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE
from kentender_procurement.procurement_planning.seeds.works_std_seed_requirements import (
    verify_std_template_doc3_section_16,
)


class TestR2008WorksMasterStdSeed(IntegrationTestCase):
    """R2-008 — STD seed alignment (spec §12)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()

    def tearDown(self):
        # Reset planning template default_std_template to keep tests isolated.
        planning_tpl = frappe.db.get_value(
            "Procurement Template", {"template_code": _PLANNING_TEMPLATE_CODE}, "name"
        )
        if planning_tpl:
            frappe.db.set_value(
                "Procurement Template",
                planning_tpl,
                "default_std_template",
                None,
                update_modified=False,
            )

    # ── Test 1: STD Template created / updated and Active ────────────────────
    def test_001_seed_ensures_active_std_template(self):
        """SEED-TEST-R2-008-001: Seed produces an Active, tender-eligible STD Template."""
        out = upsert_works_master_std()

        self.assertTrue(out.get("ok"), f"Seed returned error: {out}")
        self.assertIn(out.get("action"), ("created", "updated"))

        std_name = out["std_template"]
        self.assertIsNotNone(std_name)
        self.assertEqual(out["std_template_code"], STD_TEMPLATE_CODE)
        self.assertEqual(out["std_version_ref"], STD_TEMPLATE_VERSION_REF)

        # Lifecycle status must be Active (manifest declares allowed_for_tender_creation)
        lc = frappe.db.get_value("STD Template", std_name, "lifecycle_status")
        self.assertEqual(lc, "Active", f"lifecycle_status must be Active, got {lc!r}")

        # allowed_for_tender_creation must be 1
        atc = cint(
            frappe.db.get_value("STD Template", std_name, "allowed_for_tender_creation")
        )
        self.assertEqual(atc, 1, "allowed_for_tender_creation must be 1")

        # template_version must be non-empty
        tv = frappe.db.get_value("STD Template", std_name, "template_version") or ""
        self.assertTrue(tv.strip(), "template_version must be populated")

        # procurement_category must be WORKS
        cat = (
            frappe.db.get_value("STD Template", std_name, "procurement_category") or ""
        ).upper()
        self.assertEqual(cat, "WORKS")

    # ── Test 2: idempotency ───────────────────────────────────────────────────
    def test_002_idempotent_second_run(self):
        """SEED-TEST-R2-008-002: Running twice must not error and must return ok=True."""
        first = upsert_works_master_std()
        self.assertTrue(first.get("ok"), f"First run error: {first}")
        first_name = first["std_template"]

        second = upsert_works_master_std()
        self.assertTrue(second.get("ok"), f"Second run error: {second}")
        self.assertEqual(second["std_template"], first_name)

        # Exactly one STD Template with this code
        count = len(frappe.get_all("STD Template", filters={"template_code": STD_TEMPLATE_CODE}))
        self.assertEqual(count, 1, "Expected exactly one STD Template with this code")

    # ── Test 3: §16 postconditions ────────────────────────────────────────────
    def test_003_sec16_postconditions_pass(self):
        """SEED-TEST-R2-008-003: verify_std_template_doc3_section_16() passes after seed."""
        upsert_works_master_std()

        # Must not raise
        std_name = verify_std_template_doc3_section_16(STD_TEMPLATE_CODE)
        self.assertIsNotNone(std_name, "§16 verification must return a non-None template name")

        # package_hash must be populated
        ph = frappe.db.get_value("STD Template", std_name, "package_hash") or ""
        self.assertTrue(ph.strip(), "package_hash must be populated (§16)")

        # package_version must be populated
        pv = frappe.db.get_value("STD Template", std_name, "package_version") or ""
        self.assertTrue(pv.strip(), "package_version must be populated (§16)")

    # ── Test 4: Procurement Template linked ───────────────────────────────────
    def test_004_procurement_template_linked_to_std(self):
        """SEED-TEST-R2-008-004: PTPL-WORKS-OPEN-R2007 default_std_template is set."""
        planning_tpl = frappe.db.get_value(
            "Procurement Template", {"template_code": _PLANNING_TEMPLATE_CODE}, "name"
        )
        if not planning_tpl:
            self.skipTest(
                f"Procurement Template {_PLANNING_TEMPLATE_CODE} not found "
                "(R2-007 prerequisite not run); skipping link assertion."
            )

        out = upsert_works_master_std()
        self.assertTrue(out.get("ok"))

        linked_std = (
            frappe.db.get_value(
                "Procurement Template", planning_tpl, "default_std_template"
            )
            or ""
        )
        self.assertEqual(
            linked_std,
            out["std_template"],
            f"PTPL-WORKS-OPEN-R2007.default_std_template must point to "
            f"{out['std_template']!r}, got {linked_std!r}",
        )
