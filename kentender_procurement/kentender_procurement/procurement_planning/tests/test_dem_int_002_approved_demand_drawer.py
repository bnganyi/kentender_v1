# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-INT-002 — Planning approved-demand drawer reads MVP Demand baseline."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cint

from kentender_procurement.demands.api import (
	approve_and_reserve_form,
	prepare_final_approval_ui08,
)
from kentender_procurement.demands.services.demand_permissions import ROLE_REQUESTER
from kentender_procurement.demands.tests.test_demands_budget_api import _ensure_user
from kentender_procurement.procurement_planning.services.approved_demand_drawer import (
	get_approved_demand_planning_drawer,
)


class TestDemInt002ApprovedDemandDrawer(IntegrationTestCase):
	def test_drawer_shows_baseline_code_estimate_strategy(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_final_approval_ui08(
			requester=_ensure_user("dem-int002-req@example.com", [ROLE_REQUESTER])
		)
		name = payload["demand"]
		paa = payload["procurement_approver"]
		frappe.set_user(paa)
		result = approve_and_reserve_form(demand=name)
		self.assertTrue(result["ok"])
		self.assertEqual(cint(result["planning_ready"]), 1)

		code = frappe.db.get_value("Demand", name, "demand_code")
		frappe.set_user("Administrator")
		drawer = get_approved_demand_planning_drawer(code, actor="Administrator")
		self.assertTrue(drawer.get("ok"))
		self.assertNotEqual(drawer.get("error_code"), "DEMAND_MODULE_RETIRED")
		demand = drawer.get("demand") or {}
		self.assertEqual(demand.get("id"), name)
		self.assertEqual(demand.get("code"), code)
		self.assertNotEqual(demand.get("code"), demand.get("id"))
		self.assertEqual(demand.get("status"), "Approved")
		self.assertGreater(float(demand.get("estimated_value") or 0), 0)
		self.assertTrue(demand.get("name"))

		budget = (drawer.get("budget_context") or {}).get("budget_line") or {}
		self.assertTrue(budget.get("code") or budget.get("name"))
		if budget.get("id") and budget.get("code"):
			self.assertNotEqual(budget.get("code"), budget.get("id"))

		strategy = (drawer.get("budget_context") or {}).get("strategy_objective") or {}
		self.assertTrue(strategy.get("code") or strategy.get("name"))
		self.assertTrue(drawer.get("demand_items"))
