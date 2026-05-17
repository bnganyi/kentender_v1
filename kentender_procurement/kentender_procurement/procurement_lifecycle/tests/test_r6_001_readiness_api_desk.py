# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R6-001 / R6-002 / R6-003 — Desk API tests (R3-016 parity + R6-003 authorization flag)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.api.readiness_api import (
    read_business_readiness_summary,
)
from kentender_procurement.procurement_lifecycle.business_readiness_summary import (
    get_business_readiness_summary,
)

_WORKS_TENDER_CODE = "TND-MOH-2026-001"


class TestR6001ReadinessApiDesk(IntegrationTestCase):
    """R6-001 / R6-002 — API parity for Desk (`frappe.call` integration)."""

    def test_read_api_matches_service_for_works_tender(self):
        frappe.set_user("Administrator")
        api = read_business_readiness_summary("TM2 Tender", _WORKS_TENDER_CODE)
        svc = get_business_readiness_summary("TM2 Tender", _WORKS_TENDER_CODE)
        can_view = api.pop("can_view_technical_output_codes", None)
        self.assertIsInstance(can_view, bool)
        self.assertEqual(api, svc)

    def test_r6_003_administrator_may_view_technical_output_codes(self):
        frappe.set_user("Administrator")
        api = read_business_readiness_summary("TM2 Tender", _WORKS_TENDER_CODE)
        self.assertIs(api.get("can_view_technical_output_codes"), True)

    def test_rejects_non_tm2_object_type(self):
        frappe.set_user("Administrator")
        with self.assertRaises(frappe.ValidationError):
            read_business_readiness_summary("Demand", _WORKS_TENDER_CODE)

    def test_guest_session_denied(self):
        """R6-002 — loading path must not succeed for Guest (mount shows plc-br-error)."""
        frappe.set_user("Guest")
        with self.assertRaises(frappe.PermissionError):
            read_business_readiness_summary("TM2 Tender", _WORKS_TENDER_CODE)
        frappe.set_user("Administrator")
