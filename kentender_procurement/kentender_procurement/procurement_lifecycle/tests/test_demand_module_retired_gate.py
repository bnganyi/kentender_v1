# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-INT-011 — Demand consumers live when DocType is present."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase


class TestDemandModuleRetiredGate(IntegrationTestCase):
	def test_consumers_live_when_doctype_available(self) -> None:
		frappe.set_user("Administrator")
		from kentender_procurement.demands import CONSUMERS_LIVE
		from kentender_procurement.procurement_lifecycle.demand_module_gate import (
			assert_demand_module_available,
			demand_consumers_live,
			demand_doctype_available,
			retired_payload,
		)

		self.assertTrue(demand_doctype_available())
		self.assertTrue(CONSUMERS_LIVE)
		self.assertTrue(demand_consumers_live())
		assert_demand_module_available()  # must not throw
		payload = retired_payload()
		self.assertFalse(payload["ok"])
		self.assertEqual(payload["error_code"], "DEMAND_MODULE_RETIRED")

	def test_approved_demand_queue_live_when_demand_doctype_available(self) -> None:
		frappe.set_user("Administrator")
		from kentender_procurement.procurement_lifecycle.demand_module_gate import (
			demand_doctype_available,
		)
		from kentender_procurement.procurement_planning.services.approved_demand_queue import (
			get_approved_demands_for_queue,
		)

		self.assertTrue(demand_doctype_available())
		out = get_approved_demands_for_queue(filters={}, actor="Administrator")
		self.assertTrue(out.get("ok"))
		self.assertNotEqual(out.get("error_code"), "DEMAND_MODULE_RETIRED")
		self.assertFalse(out.get("skipped"))
		self.assertIn("rows", out)
