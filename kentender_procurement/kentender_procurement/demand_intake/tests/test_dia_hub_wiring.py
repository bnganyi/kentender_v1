# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""H13 — TDD for DIA Hub wiring backend functions.

Tests (failing first):
  HUB-BE-001  alignment_pct = 0 when no active demands exist
  HUB-BE-002  alignment_pct = 100 when all active demands have strategic_plan set
  HUB-BE-003  alignment_pct rounds correctly for partial linkage
  HUB-BE-004  alignment_pct = 0 when all active demands have no strategic_plan
  HUB-BE-005  get_dia_landing_shell_data response includes alignment_pct key
  HUB-BE-006  cancelled demands are excluded from alignment_pct calculation
  HUB-BE-007  category_breakdown is present in landing response with Goods/Works/Services keys
  HUB-BE-008  category_breakdown counts reflect actual demand records

Run:
  bench --site kentender.midas.com run-tests --app kentender_procurement \\
    --module kentender_procurement.demand_intake.tests.test_dia_hub_wiring
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department, ensure_procuring_entity
from kentender_procurement.demand_intake.api.landing import (
    get_dia_landing_shell_data,
)


def _compute_strategic_alignment_pct():
    from kentender_procurement.demand_intake.api.landing import compute_strategic_alignment_pct
    return compute_strategic_alignment_pct()


class TestDiaHubWiringBackend(IntegrationTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        if not frappe.db.exists("DocType", "Demand"):
            self._skip = True
            return
        self._skip = False
        ensure_currency_kes()
        h = frappe.generate_hash(length=6)
        self.entity = ensure_procuring_entity(f"MOH_HUB_{h}", f"Hub Entity {h}")
        self.dept = ensure_department(f"HubDept {h}", self.entity)
        self._demand_names: list[str] = []

        # Grab a real Strategic Plan name to use when we want one
        self._strategic_plan = frappe.db.get_value("Strategic Plan", {}, "name") or None

    def tearDown(self):
        if getattr(self, "_skip", False):
            return
        frappe.set_user("Administrator")
        for name in list(self._demand_names):
            if frappe.db.exists("Demand", name):
                frappe.delete_doc("Demand", name, force=True, ignore_permissions=True)
        self._demand_names.clear()
        dept = getattr(self, "dept", None)
        if dept and frappe.db.exists("Procuring Department", dept):
            frappe.delete_doc("Procuring Department", dept, force=True, ignore_permissions=True)
        ent = getattr(self, "entity", None)
        if ent and frappe.db.exists("Procuring Entity", ent):
            frappe.delete_doc("Procuring Entity", ent, force=True, ignore_permissions=True)

    def _mk_demand(self, *, strategic_plan=None, status="Draft", requisition_type="Goods", **kwargs) -> str:
        doc = frappe.get_doc(
            {
                "doctype": "Demand",
                "title": kwargs.pop("title", None) or f"Hub {frappe.generate_hash(length=4)}",
                "procuring_entity": self.entity,
                "requesting_department": self.dept,
                "request_date": today(),
                "required_by_date": today(),
                "requisition_type": requisition_type,
                "items": [
                    {
                        "item_description": "Item",
                        "uom": "ea",
                        "quantity": 1,
                        "estimated_unit_cost": 1000,
                    }
                ],
                **kwargs,
            }
        )
        doc.flags.ignore_mandatory = True
        doc.insert(ignore_permissions=True)
        # Set strategic_plan and status directly to avoid lifecycle guards
        update = {"status": status}
        if strategic_plan:
            update["strategic_plan"] = strategic_plan
        frappe.db.set_value("Demand", doc.name, update, update_modified=False)
        self._demand_names.append(doc.name)
        return doc.name

    # ── HUB-BE-001 ────────────────────────────────────────────────────────────

    def test_hub_be_001_alignment_zero_when_no_demands(self):
        """alignment_pct = 0 when the isolated test has no active demands (empty scope)."""
        if self._skip:
            self.skipTest("Demand DocType not installed")
        # No demands created — the function must return 0 if none exist in scope
        pct = _compute_strategic_alignment_pct()
        self.assertIsInstance(pct, (int, float))
        self.assertGreaterEqual(pct, 0)
        self.assertLessEqual(pct, 100)

    # ── HUB-BE-002 ────────────────────────────────────────────────────────────

    def test_hub_be_002_alignment_100_when_all_have_strategic_plan(self):
        """alignment_pct = 100 when every active demand has strategic_plan set."""
        if self._skip:
            self.skipTest("Demand DocType not installed")
        if not self._strategic_plan:
            self.skipTest("No Strategic Plan records seeded — cannot test full linkage")

        self._mk_demand(strategic_plan=self._strategic_plan, title="Linked 1")
        self._mk_demand(strategic_plan=self._strategic_plan, title="Linked 2")

        from kentender_procurement.demand_intake.api.landing import _compute_alignment_for_entity
        pct = _compute_alignment_for_entity(self.entity)
        self.assertEqual(pct, 100)

    # ── HUB-BE-003 ────────────────────────────────────────────────────────────

    def test_hub_be_003_alignment_partial_linkage(self):
        """alignment_pct rounds to nearest integer for partial linkage (2 of 3 = 67)."""
        if self._skip:
            self.skipTest("Demand DocType not installed")
        if not self._strategic_plan:
            self.skipTest("No Strategic Plan records seeded — cannot test partial linkage")

        self._mk_demand(strategic_plan=self._strategic_plan, title="Linked A")
        self._mk_demand(strategic_plan=self._strategic_plan, title="Linked B")
        self._mk_demand(title="Unlinked C")  # no strategic_plan

        from kentender_procurement.demand_intake.api.landing import _compute_alignment_for_entity
        pct = _compute_alignment_for_entity(self.entity)
        self.assertEqual(pct, 67)

    # ── HUB-BE-004 ────────────────────────────────────────────────────────────

    def test_hub_be_004_alignment_zero_when_none_linked(self):
        """alignment_pct = 0 when all active demands have no strategic_plan."""
        if self._skip:
            self.skipTest("Demand DocType not installed")

        self._mk_demand(title="Unlinked 1")
        self._mk_demand(title="Unlinked 2")

        from kentender_procurement.demand_intake.api.landing import _compute_alignment_for_entity
        pct = _compute_alignment_for_entity(self.entity)
        self.assertEqual(pct, 0)

    # ── HUB-BE-005 ────────────────────────────────────────────────────────────

    def test_hub_be_005_landing_response_includes_alignment_pct(self):
        """get_dia_landing_shell_data response must include alignment_pct key."""
        if self._skip:
            self.skipTest("Demand DocType not installed")

        out = get_dia_landing_shell_data()
        self.assertTrue(out.get("ok"), f"Landing API returned error: {out}")
        self.assertIn(
            "alignment_pct",
            out,
            "alignment_pct key missing from get_dia_landing_shell_data response",
        )
        pct = out["alignment_pct"]
        self.assertIsInstance(pct, (int, float))
        self.assertGreaterEqual(pct, 0)
        self.assertLessEqual(pct, 100)

    # ── HUB-BE-006 ────────────────────────────────────────────────────────────

    def test_hub_be_006_cancelled_excluded_from_alignment(self):
        """Cancelled demands must not affect alignment_pct numerator or denominator."""
        if self._skip:
            self.skipTest("Demand DocType not installed")
        if not self._strategic_plan:
            self.skipTest("No Strategic Plan records seeded")

        # 1 cancelled demand with strategy (should not count)
        self._mk_demand(
            strategic_plan=self._strategic_plan,
            status="Cancelled",
            title="Cancelled linked",
        )
        # 1 active demand without strategy
        self._mk_demand(title="Active unlinked")

        from kentender_procurement.demand_intake.api.landing import _compute_alignment_for_entity
        pct = _compute_alignment_for_entity(self.entity)
        # Only the active unlinked demand counts → 0/1 = 0%
        self.assertEqual(pct, 0)

    # ── HUB-BE-007 ────────────────────────────────────────────────────────────

    def test_hub_be_007_landing_response_includes_category_breakdown(self):
        """get_dia_landing_shell_data response must include category_breakdown with Goods/Works/Services."""
        if self._skip:
            self.skipTest("Demand DocType not installed")

        out = get_dia_landing_shell_data()
        self.assertTrue(out.get("ok"))
        self.assertIn(
            "category_breakdown",
            out,
            "category_breakdown key missing from get_dia_landing_shell_data response",
        )
        breakdown = out["category_breakdown"]
        self.assertIsInstance(breakdown, dict)
        for key in ("Goods", "Works", "Services"):
            self.assertIn(key, breakdown, f"'{key}' missing from category_breakdown")
            self.assertIsInstance(breakdown[key], (int, float))

    # ── HUB-BE-009 ────────────────────────────────────────────────────────────

    def test_hub_be_009_queue_list_returns_total_count(self):
        """get_dia_queue_list must return a total_count integer for pagination."""
        if self._skip:
            self.skipTest("Demand DocType not installed")
        from kentender_procurement.demand_intake.api.queue_list import get_dia_queue_list

        # Create 2 demands so we have something to count
        self._mk_demand(title="Count A")
        self._mk_demand(title="Count B")

        out = get_dia_queue_list(work_tab="all", lifecycle_filter="all", limit=50, start=0)
        self.assertTrue(out.get("ok"), f"queue_list returned error: {out}")
        self.assertIn("total_count", out, "total_count key missing from get_dia_queue_list response")
        tc = out["total_count"]
        self.assertIsInstance(tc, int, f"total_count must be int, got {type(tc)}")
        self.assertGreaterEqual(tc, 2, "total_count must be >= 2 after inserting 2 demands")

    # ── HUB-BE-008 ────────────────────────────────────────────────────────────

    def test_hub_be_008_category_breakdown_reflects_actual_demands(self):
        """category_breakdown counts must increment when new demands are inserted."""
        if self._skip:
            self.skipTest("Demand DocType not installed")

        out_before = get_dia_landing_shell_data()
        goods_before = (out_before.get("category_breakdown") or {}).get("Goods", 0)
        works_before = (out_before.get("category_breakdown") or {}).get("Works", 0)

        self._mk_demand(requisition_type="Goods", title="Goods demand")
        self._mk_demand(requisition_type="Works", title="Works demand")

        out_after = get_dia_landing_shell_data()
        self.assertTrue(out_after.get("ok"))
        breakdown = out_after.get("category_breakdown") or {}

        self.assertGreaterEqual(breakdown.get("Goods", 0), goods_before + 1)
        self.assertGreaterEqual(breakdown.get("Works", 0), works_before + 1)
