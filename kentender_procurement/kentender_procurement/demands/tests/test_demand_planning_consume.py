# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-AC-008 — partial then full consume; approval status unchanged."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_procurement.demands.services.demand_lifecycle import (
	consume_demand_in_planning,
)
from kentender_procurement.demands.services.demand_permissions import ensure_demand_roles
from kentender_procurement.demands.tests._ac_helpers import (
	actor_bundle,
	advance_to_approved,
)


class TestDemandPlanningConsume(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_ac008_partial_then_full_consume_keeps_approved(self) -> None:
		"""DIA-AC-008 — partial then full consume; status remains Approved."""
		actors = actor_bundle("dem-ac008")
		name = advance_to_approved(
			req=actors["req"],
			ba=actors["ba"],
			paa=actors["paa"],
			bo=actors["bo"],
			estimate=1000,
			title="AC008 consume demand",
		)
		item = frappe.db.get_value("Demand Item", {"demand": name}, "name")
		self.assertTrue(item)

		partial = consume_demand_in_planning(
			demand=name,
			demand_item=item,
			consumed_amount=400,
			user=actors["planner"],
		)
		self.assertEqual(partial["demand"]["status"], "Approved")
		self.assertEqual(partial["demand"]["planning_usage"], "Partially planned")

		full = consume_demand_in_planning(
			demand=name,
			demand_item=item,
			consumed_amount=600,
			user=actors["planner"],
		)
		self.assertEqual(full["demand"]["status"], "Approved")
		self.assertEqual(full["demand"]["current_stage"], "Complete")
		self.assertEqual(full["demand"]["planning_usage"], "Fully planned")
		self.assertAlmostEqual(flt(full["demand"]["items"][0]["remaining_amount"]), 0.0)
