# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Demands MVP-1 — consumers stay fail-closed until CONSUMERS_LIVE."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase


class TestDemandModuleRetiredGate(IntegrationTestCase):
	def test_consumers_gated_while_schema_exists(self) -> None:
		frappe.set_user("Administrator")
		from kentender_procurement.demands import CONSUMERS_LIVE
		from kentender_procurement.procurement_lifecycle.demand_module_gate import (
			RETIRED_MESSAGE,
			demand_consumers_live,
			demand_doctype_available,
			retired_payload,
		)

		self.assertTrue(demand_doctype_available())
		self.assertFalse(CONSUMERS_LIVE)
		self.assertFalse(demand_consumers_live())
		payload = retired_payload()
		self.assertFalse(payload["ok"])
		self.assertEqual(payload["error_code"], "DEMAND_MODULE_RETIRED")
		self.assertIn("retired", RETIRED_MESSAGE.lower())

	def test_approved_demand_queue_returns_empty_when_consumers_not_live(self) -> None:
		frappe.set_user("Administrator")
		from kentender_procurement.procurement_planning.services.approved_demand_queue import (
			get_approved_demands_for_queue,
		)

		out = get_approved_demands_for_queue(filters={}, actor="Administrator")
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("error_code"), "DEMAND_MODULE_RETIRED")
		self.assertEqual(out.get("total"), 0)
		self.assertEqual(out.get("rows"), [])
		self.assertTrue(out.get("skipped"))
