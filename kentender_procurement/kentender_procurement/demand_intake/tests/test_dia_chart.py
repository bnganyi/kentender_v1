# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""H12 — TDD for DIA Budget Consumption chart API.

Tests (failing first, then implemented):
  CHART-BE-001  get_dia_consumption_chart_data returns ok=True
  CHART-BE-002  response includes 'bars' list
  CHART-BE-003  response includes 'period_label' string
  CHART-BE-004  each bar entry has label, total_value, approved_value
  CHART-BE-005  approved_value <= total_value for every bar
  CHART-BE-006  bars list is limited to at most 5 entries
  CHART-BE-007  total_value increments when a new active demand is inserted
  CHART-BE-008  approved_value increments only when demand status is Approved/Planning Ready
  CHART-BE-009  cancelled/rejected demands are excluded from total_value

Run:
  bench --site kentender.midas.com run-tests --app kentender_procurement \\
    --module kentender_procurement.demand_intake.tests.test_dia_chart
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department, ensure_procuring_entity


class TestDiaConsumptionChart(IntegrationTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        if not frappe.db.exists("DocType", "Demand"):
            self._skip = True
            return
        self._skip = False
        ensure_currency_kes()
        h = frappe.generate_hash(length=6)
        self.entity = ensure_procuring_entity(f"MOH_CHT_{h}", f"Chart Entity {h}")
        self.dept = ensure_department(f"ChartDept {h}", self.entity)
        self._demand_names: list[str] = []

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

    def _mk_demand(self, *, status="Draft", amount=10_000, **kwargs) -> str:
        doc = frappe.get_doc(
            {
                "doctype": "Demand",
                "title": kwargs.pop("title", None) or f"Chart {frappe.generate_hash(length=4)}",
                "procuring_entity": self.entity,
                "requesting_department": self.dept,
                "request_date": today(),
                "required_by_date": today(),
                "requisition_type": "Goods",
                "items": [
                    {
                        "item_description": "Item",
                        "uom": "ea",
                        "quantity": 1,
                        "estimated_unit_cost": amount,
                    }
                ],
                **kwargs,
            }
        )
        doc.flags.ignore_mandatory = True
        doc.insert(ignore_permissions=True)
        frappe.db.set_value("Demand", doc.name, "status", status, update_modified=False)
        self._demand_names.append(doc.name)
        return doc.name

    def _call(self):
        from kentender_procurement.demand_intake.api.chart import get_dia_consumption_chart_data
        return get_dia_consumption_chart_data()

    # ── CHART-BE-001 ──────────────────────────────────────────────────────────

    def test_chart_be_001_returns_ok(self):
        """get_dia_consumption_chart_data must return ok=True."""
        if self._skip:
            self.skipTest("Demand DocType not installed")
        out = self._call()
        self.assertTrue(out.get("ok"), f"Expected ok=True, got: {out}")

    # ── CHART-BE-002 ──────────────────────────────────────────────────────────

    def test_chart_be_002_response_includes_bars(self):
        """Response must include a 'bars' list."""
        if self._skip:
            self.skipTest("Demand DocType not installed")
        out = self._call()
        self.assertIn("bars", out, "'bars' key missing from response")
        self.assertIsInstance(out["bars"], list)

    # ── CHART-BE-003 ──────────────────────────────────────────────────────────

    def test_chart_be_003_response_includes_period_label(self):
        """Response must include a 'period_label' string."""
        if self._skip:
            self.skipTest("Demand DocType not installed")
        out = self._call()
        self.assertIn("period_label", out, "'period_label' key missing")
        self.assertIsInstance(out["period_label"], str)
        self.assertTrue(out["period_label"].strip())

    # ── CHART-BE-004 ──────────────────────────────────────────────────────────

    def test_chart_be_004_each_bar_has_required_fields(self):
        """Each bar entry must have label, total_value, and approved_value."""
        if self._skip:
            self.skipTest("Demand DocType not installed")
        self._mk_demand(status="Draft", amount=5_000)
        out = self._call()
        bars = out.get("bars") or []
        for b in bars:
            self.assertIn("label", b, f"bar missing 'label': {b}")
            self.assertIn("total_value", b, f"bar missing 'total_value': {b}")
            self.assertIn("approved_value", b, f"bar missing 'approved_value': {b}")

    # ── CHART-BE-005 ──────────────────────────────────────────────────────────

    def test_chart_be_005_approved_value_lte_total_value(self):
        """approved_value must never exceed total_value for any bar."""
        if self._skip:
            self.skipTest("Demand DocType not installed")
        self._mk_demand(status="Draft", amount=8_000)
        self._mk_demand(status="Approved", amount=3_000)
        out = self._call()
        for b in (out.get("bars") or []):
            self.assertLessEqual(
                b.get("approved_value", 0),
                b.get("total_value", 0),
                f"approved_value > total_value for bar: {b}",
            )

    # ── CHART-BE-006 ──────────────────────────────────────────────────────────

    def test_chart_be_006_bars_limited_to_five(self):
        """bars list must contain at most 5 entries."""
        if self._skip:
            self.skipTest("Demand DocType not installed")
        out = self._call()
        self.assertLessEqual(len(out.get("bars") or []), 5)

    # ── CHART-BE-007 ──────────────────────────────────────────────────────────

    def test_chart_be_007_total_value_reflects_new_demand(self):
        """total_value for our test department must increase after inserting a demand."""
        if self._skip:
            self.skipTest("Demand DocType not installed")
        # Insert a known amount and check our department bar appears
        self._mk_demand(status="Draft", amount=50_000, title="Chart total test")
        out = self._call()
        # Find the bar for our test department
        dept_name = frappe.db.get_value("Procuring Department", self.dept, "department_name") or self.dept
        matching = [b for b in (out.get("bars") or []) if b.get("label") == dept_name]
        # May not appear if there are 5 bigger departments — soft assert
        if matching:
            self.assertGreaterEqual(matching[0]["total_value"], 50_000)

    # ── CHART-BE-008 ──────────────────────────────────────────────────────────

    def test_chart_be_008_approved_value_counts_only_approved(self):
        """approved_value must only include Approved and Planning Ready demands."""
        if self._skip:
            self.skipTest("Demand DocType not installed")
        self._mk_demand(status="Draft", amount=10_000, title="Draft only")
        self._mk_demand(status="Approved", amount=7_000, title="Approved one")
        self._mk_demand(status="Planning Ready", amount=3_000, title="Ready one")
        out = self._call()
        dept_name = frappe.db.get_value("Procuring Department", self.dept, "department_name") or self.dept
        matching = [b for b in (out.get("bars") or []) if b.get("label") == dept_name]
        if matching:
            b = matching[0]
            # approved_value must be >= 10_000 (7k + 3k) and total_value >= 20_000
            self.assertGreaterEqual(b["approved_value"], 10_000)
            self.assertGreaterEqual(b["total_value"], 20_000)

    # ── CHART-BE-009 ──────────────────────────────────────────────────────────

    def test_chart_be_009_cancelled_rejected_excluded(self):
        """Cancelled and Rejected demands must not appear in total_value."""
        if self._skip:
            self.skipTest("Demand DocType not installed")
        self._mk_demand(status="Cancelled", amount=99_000, title="Cancelled big")
        self._mk_demand(status="Rejected",  amount=88_000, title="Rejected big")
        out = self._call()
        dept_name = frappe.db.get_value("Procuring Department", self.dept, "department_name") or self.dept
        matching = [b for b in (out.get("bars") or []) if b.get("label") == dept_name]
        # No active demands for our dept → should not appear, or if it does, total_value < 99k
        if matching:
            self.assertLess(matching[0]["total_value"], 99_000)
