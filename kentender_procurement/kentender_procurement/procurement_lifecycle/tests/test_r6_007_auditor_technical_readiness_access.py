# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R6-007 / LV-R6-007-01 — Auditor (and equivalent internal roles) may receive technical output codes."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.api.readiness_api import (
    read_business_readiness_summary,
)

_WORKS_TENDER_CODE = "TND-MOH-2026-001"
_AUDITOR = "auditor@moh.test"


class TestR6007AuditorTechnicalReadinessAccess(IntegrationTestCase):
    def test_auditor_may_view_technical_output_codes(self):
        """Auditor is in `internal_clearing` (readiness_api) — API must expose the technical flag."""
        if not frappe.db.exists("User", _AUDITOR):
            self.skipTest("Auditor user not on site (seed or create auditor@moh.test)")
        if not frappe.db.exists("TM2 Tender", _WORKS_TENDER_CODE):
            self.skipTest("WORKS tender not seeded")

        frappe.set_user(_AUDITOR)
        if not frappe.has_permission("TM2 Tender", "read", doc=_WORKS_TENDER_CODE):
            self.skipTest("Auditor lacks TM2 Tender read for seeded tender on this site")

        api = read_business_readiness_summary("TM2 Tender", _WORKS_TENDER_CODE)
        self.assertIs(
            api.get("can_view_technical_output_codes"),
            True,
            msg="Auditor must be able to open the technical drawer (pack §12.6 / R6-003)",
        )

    def test_administrator_still_may_view_technical_output_codes(self):
        """Regression anchor for “admin” in R6-007 (LV pairs Auditor with privileged desk users)."""
        if not frappe.db.exists("TM2 Tender", _WORKS_TENDER_CODE):
            self.skipTest("WORKS tender not seeded")
        frappe.set_user("Administrator")
        api = read_business_readiness_summary("TM2 Tender", _WORKS_TENDER_CODE)
        self.assertIs(api.get("can_view_technical_output_codes"), True)
