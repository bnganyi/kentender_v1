# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R5-003 / LV-R5-003-02 — ``get_procurement_use_for_budget_line`` integration tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.api.journey_api import (
    get_procurement_use_for_budget_line,
)

_WORKS_BL = "BUD-MOH-INFRA-2026-001"
_WORKS_JOURNEY = "JRN-MOH-2026-001"
_WORKS_BUDGET_NAME = "BUDGET-MOH-2026"
_WORKS_PKG = "PKG-MOH-2026-001"
_WORKS_DEMAND_ID = "DEM-MOH-2026-001"


class TestR5003ProcurementUseForBudgetLine(IntegrationTestCase):
    """R5-003 — budget line → procurement use aggregation."""

    def _works_bl_name(self) -> str | None:
        """Return the Frappe name of the WORKS Budget Line, or None if missing."""
        return frappe.db.exists("Procurement Budget Line", _WORKS_BL)

    # ------------------------------------------------------------------
    # Guard tests
    # ------------------------------------------------------------------

    def test_missing_param_raises_validation_error(self):
        with self.assertRaises(frappe.ValidationError):
            get_procurement_use_for_budget_line("")

    def test_blank_whitespace_param_raises_validation_error(self):
        with self.assertRaises(frappe.ValidationError):
            get_procurement_use_for_budget_line("   ")

    def test_unknown_budget_line_returns_not_found(self):
        out = get_procurement_use_for_budget_line("ZZZZ-DOES-NOT-EXIST")
        self.assertFalse(out.get("ok"), msg=out)
        self.assertEqual(out.get("error"), "NOT_FOUND")

    def test_guest_denied(self):
        bl_name = self._works_bl_name()
        if not bl_name:
            self.skipTest("WORKS Budget Line not present on site.")

        frappe.set_user("Guest")
        try:
            with self.assertRaises(frappe.PermissionError):
                get_procurement_use_for_budget_line(bl_name)
        finally:
            frappe.set_user("Administrator")

    # ------------------------------------------------------------------
    # Happy path: WORKS budget line
    # ------------------------------------------------------------------

    def test_works_budget_line_returns_ok(self):
        bl_name = self._works_bl_name()
        if not bl_name:
            self.skipTest("WORKS Budget Line not present on site.")

        out = get_procurement_use_for_budget_line(bl_name)
        self.assertTrue(out.get("ok"), msg=out)

    def test_works_returns_correct_budget_line_code(self):
        bl_name = self._works_bl_name()
        if not bl_name:
            self.skipTest("WORKS Budget Line not present on site.")

        out = get_procurement_use_for_budget_line(bl_name)
        self.assertEqual(out.get("budget_line_code"), _WORKS_BL)

    def test_works_returns_funding_confirmation(self):
        bl_name = self._works_bl_name()
        if not bl_name:
            self.skipTest("WORKS Budget Line not present on site.")

        out = get_procurement_use_for_budget_line(bl_name)
        self.assertTrue(out.get("ok"), msg=out)
        self.assertEqual(out.get("budget_name"), _WORKS_BUDGET_NAME)
        self.assertEqual(out.get("budget_status"), "Approved")
        self.assertEqual(out.get("fiscal_year"), 2026)
        self.assertGreater(out.get("amount_allocated", 0), 0,
                           "amount_allocated should be positive")
        self.assertIsNotNone(out.get("currency"))
        self.assertNotEqual(out.get("currency"), "")

    def test_works_amounts_structure(self):
        bl_name = self._works_bl_name()
        if not bl_name:
            self.skipTest("WORKS Budget Line not present on site.")

        out = get_procurement_use_for_budget_line(bl_name)
        for key in ("amount_allocated", "amount_reserved", "amount_available"):
            self.assertIn(key, out, f"missing key: {key}")
            self.assertIsNotNone(out[key])

    def test_works_returns_linked_journey(self):
        bl_name = self._works_bl_name()
        if not bl_name:
            self.skipTest("WORKS Budget Line not present on site.")

        out = get_procurement_use_for_budget_line(bl_name)
        self.assertTrue(out.get("ok"), msg=out)
        codes = [j.get("journey_code") for j in out.get("journeys", [])]
        self.assertIn(
            _WORKS_JOURNEY, codes,
            f"WORKS journey not in journeys; got: {codes}",
        )

    def test_works_journey_has_required_keys(self):
        bl_name = self._works_bl_name()
        if not bl_name:
            self.skipTest("WORKS Budget Line not present on site.")

        out = get_procurement_use_for_budget_line(bl_name)
        journeys = out.get("journeys", [])
        if not journeys:
            self.skipTest("No journeys returned — seed data may be incomplete.")

        for key in ("journey_code", "journey_title", "current_stage_label", "open_route"):
            self.assertIn(key, journeys[0], f"journey missing key: {key}")

    def test_works_returns_linked_demand(self):
        bl_name = self._works_bl_name()
        if not bl_name:
            self.skipTest("WORKS Budget Line not present on site.")

        out = get_procurement_use_for_budget_line(bl_name)
        self.assertTrue(out.get("ok"), msg=out)
        dem_ids = [d.get("demand_id") for d in out.get("demands", [])]
        self.assertIn(
            _WORKS_DEMAND_ID, dem_ids,
            f"WORKS demand not found; got demand_ids: {dem_ids}",
        )

    def test_works_returns_linked_package(self):
        bl_name = self._works_bl_name()
        if not bl_name:
            self.skipTest("WORKS Budget Line not present on site.")

        out = get_procurement_use_for_budget_line(bl_name)
        self.assertTrue(out.get("ok"), msg=out)
        pkg_names = [p.get("id") for p in out.get("packages", [])]
        self.assertIn(
            _WORKS_PKG, pkg_names,
            f"WORKS package not found; got: {pkg_names}",
        )

    def test_works_package_has_required_keys(self):
        bl_name = self._works_bl_name()
        if not bl_name:
            self.skipTest("WORKS Budget Line not present on site.")

        out = get_procurement_use_for_budget_line(bl_name)
        packages = out.get("packages", [])
        if not packages:
            self.skipTest("No packages returned — seed data may be incomplete.")

        for key in ("id", "code", "name", "status", "list_route"):
            self.assertIn(key, packages[0], f"package missing key: {key}")

    def test_journey_open_route_contains_code(self):
        bl_name = self._works_bl_name()
        if not bl_name:
            self.skipTest("WORKS Budget Line not present on site.")

        out = get_procurement_use_for_budget_line(bl_name)
        journeys = out.get("journeys", [])
        if not journeys:
            self.skipTest("No journeys returned.")

        for j in journeys:
            self.assertIn("/desk/plc-procurement-journey", j.get("open_route", ""),
                          f"open_route malformed: {j}")
