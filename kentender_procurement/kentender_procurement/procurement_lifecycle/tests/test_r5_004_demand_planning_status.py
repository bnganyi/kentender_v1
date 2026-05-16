# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R5-004 / LV-R5-004-02 — ``get_demand_planning_status`` integration tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.api.journey_api import (
    get_demand_planning_status,
)

_WORKS_DEMAND_ID = "DEM-MOH-2026-001"
_WORKS_JOURNEY = "JRN-MOH-2026-001"
_DEMAPP_CODE = "DEMAPP-MOH-2026-001"
_PLANINCL_CODE = "PLANINCL-MOH-2026-001"
_APPROVAL_REF = "DEMAPPROVAL-MOH-2026-001"


class TestR5004DemandPlanningStatus(IntegrationTestCase):
    """R5-004 — Demand planning handoff read model."""

    def _works_demand_name(self) -> str | None:
        return frappe.db.get_value("Demand", {"demand_id": _WORKS_DEMAND_ID}, "name")

    def test_blank_name_raises_validation_error(self):
        with self.assertRaises(frappe.ValidationError):
            get_demand_planning_status("")

    def test_whitespace_name_raises_validation_error(self):
        with self.assertRaises(frappe.ValidationError):
            get_demand_planning_status("   ")

    def test_unknown_demand_returns_not_found_payload(self):
        out = get_demand_planning_status("zzzz-nonexistent-demand-name")
        self.assertFalse(out.get("ok"))
        self.assertEqual(out.get("error"), "NOT_FOUND")

    def test_guest_denied(self):
        nm = self._works_demand_name()
        if not nm:
            self.skipTest("WORKS Demand not present on site.")

        frappe.set_user("Guest")
        try:
            with self.assertRaises(frappe.PermissionError):
                get_demand_planning_status(nm)
        finally:
            frappe.set_user("Administrator")

    def test_works_approved_returns_journey_and_handoffs(self):
        nm = self._works_demand_name()
        if not nm:
            self.skipTest("WORKS Demand not present on site.")

        out = get_demand_planning_status(nm)
        self.assertTrue(out.get("ok"), msg=out)
        self.assertTrue(out.get("eligible_for_certificate"))
        self.assertEqual(out.get("demand_id"), _WORKS_DEMAND_ID)

        j = out.get("journey")
        self.assertIsNotNone(j, msg=out)
        self.assertEqual(j.get("journey_code"), _WORKS_JOURNEY)
        self.assertIn("/desk/plc-procurement-journey", j.get("open_route", ""))

        cert = out.get("demand_approval_certificate")
        self.assertIsNotNone(cert)
        self.assertEqual(cert.get("handoff_code"), _DEMAPP_CODE)
        self.assertEqual(cert.get("handoff_title"), "Demand Approval Certificate")
        self.assertEqual(cert.get("demand_approval_record_code"), _APPROVAL_REF)
        self.assertTrue(cert.get("demand_approval_record_route"))

        pf = cert.get("passed_forward_summary") or {}
        self.assertIn("planning_action", pf)

        incl = out.get("planning_inclusion")
        self.assertIsNotNone(incl)
        self.assertEqual(incl.get("handoff_code"), _PLANINCL_CODE)
        self.assertTrue(incl.get("target_object_code") or incl.get("plan_code_hint"))

    def test_locked_summary_contains_demand_artefacts(self):
        nm = self._works_demand_name()
        if not nm:
            self.skipTest("WORKS Demand not present on site.")

        out = get_demand_planning_status(nm)
        cert = out.get("demand_approval_certificate") or {}
        locked = cert.get("locked_summary") or {}
        self.assertEqual(locked.get("demand_code"), _WORKS_DEMAND_ID)

    def test_not_approved_has_no_journey_block(self):
        rows = frappe.get_all(
            "Demand",
            filters={"status": ["!=", "Approved"]},
            fields=["name"],
            limit=1,
        )
        if not rows:
            self.skipTest("No non-Approved Demand on site for negative path.")

        out = get_demand_planning_status(rows[0].name)
        self.assertTrue(out.get("ok"), msg=out)
        self.assertFalse(out.get("eligible_for_certificate"))
        self.assertIsNone(out.get("journey"))
        self.assertIsNone(out.get("demand_approval_certificate"))
