# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""PRD §32.3 / UX-AC-003 — BOQ panel exposes PE vs supplier ownership semantics."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.services.instance_boq_workbench_service import (
	build_std_instance_boq_workbench_panel,
)
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDPRDBoqUxLabels(_Phase7Fixture):
	def test_boq_workbench_panel_labels_pe_quantity_supplier_rate(self):
		frappe.set_user("Administrator")
		res = build_std_instance_boq_workbench_panel(self.instance_code, actor="Administrator")
		self.assertTrue(res.get("ok"))
		if not res.get("boq"):
			self.skipTest("Fixture has no BOQ instance row on this site.")
		self.assertIn("Procuring Entity", str(res.get("quantity_owner_label") or ""))
		self.assertIn("Supplier", str(res.get("rate_owner_note") or ""))
