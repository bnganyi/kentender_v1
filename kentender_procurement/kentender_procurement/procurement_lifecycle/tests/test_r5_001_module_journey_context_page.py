# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R5-001 — Desk ``Page`` ``plc-module-journey-context`` exists after patch.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r5_001_module_journey_context_page
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

PAGE = "plc-module-journey-context"


class TestR5001ModuleJourneyContextPage(IntegrationTestCase):
    """R5-001 — smoke Page registered for module journey context host."""

    def test_plc_module_journey_context_page_exists(self):
        self.assertTrue(
            frappe.db.exists("Page", PAGE),
            msg="Run migrate so ensure_plc_module_journey_context_page patch applies.",
        )
        title = frappe.db.get_value("Page", PAGE, "title")
        self.assertTrue(title)
