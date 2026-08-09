# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-INT-011 — retire fail-closed Demand consumer gate."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.demands import CONSUMERS_LIVE
from kentender_procurement.procurement_lifecycle.demand_module_gate import (
	assert_demand_module_available,
	demand_consumers_live,
	demand_doctype_available,
)
from kentender_procurement.procurement_planning.services.planning_home_summary import (
	get_planning_home_summary,
)


class TestDemInt011ConsumersLive(IntegrationTestCase):
	def test_package_flag_and_gate_are_live(self) -> None:
		frappe.set_user("Administrator")
		self.assertTrue(CONSUMERS_LIVE)
		self.assertTrue(demand_doctype_available())
		self.assertTrue(demand_consumers_live())
		assert_demand_module_available()

	def test_planning_home_summary_does_not_fail_closed(self) -> None:
		frappe.set_user("Administrator")
		# Must not raise on MVP Demand fields (no DIA demand_id/planning_status).
		out = get_planning_home_summary(actor="Administrator")
		self.assertTrue(out.get("ok"))
		summary = out.get("summary") or {}
		for key in (
			"needs_planning",
			"needs_review",
			"ready_to_release",
			"released_recently",
			"blocked",
		):
			self.assertIn(key, summary)
			self.assertGreaterEqual(int(summary[key]), 0)
