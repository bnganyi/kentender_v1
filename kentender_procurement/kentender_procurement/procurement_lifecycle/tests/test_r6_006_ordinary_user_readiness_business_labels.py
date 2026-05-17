# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R6-006 — Ordinary internal user (Procurement Officer) receives business-first payload."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.api.readiness_api import (
    read_business_readiness_summary,
)

_WORKS_TENDER_CODE = "TND-MOH-2026-001"
_OFFICER = "procurement.officer@moh.test"


class TestR6006OrdinaryUserReadinessBusinessLabels(IntegrationTestCase):
    def test_procurement_officer_api_returns_business_labels_and_technical_flag(self):
        if not frappe.db.exists("User", _OFFICER):
            self.skipTest("Seed user procurement.officer@moh.test not on site")
        if not frappe.db.exists("TM2 Tender", _WORKS_TENDER_CODE):
            self.skipTest("WORKS tender not seeded")

        frappe.set_user(_OFFICER)
        if not frappe.has_permission("TM2 Tender", "read", doc=_WORKS_TENDER_CODE):
            self.skipTest("Procurement Officer lacks TM2 Tender read on this site")

        api = read_business_readiness_summary("TM2 Tender", _WORKS_TENDER_CODE)
        self.assertIs(api.get("can_view_technical_output_codes"), True)

        label = (api.get("summary_label") or "").strip()
        self.assertRegex(
            label,
            r"(?i)tender\s+document\s+readiness",
            msg="summary_label should stay business-readable for ordinary procurement users",
        )

        checks = api.get("checks") or []
        self.assertTrue(checks, msg="expected non-empty readiness checks")
        bl0 = (checks[0].get("business_label") or "").strip()
        self.assertTrue(bl0, msg="first check must expose a business_label")
