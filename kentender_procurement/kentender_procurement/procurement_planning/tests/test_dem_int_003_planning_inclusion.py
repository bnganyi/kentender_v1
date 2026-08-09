# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-INT-003 — Planning inclusion and wizard cards read MVP Demand."""

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
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE, PLAN_DRAFT
from kentender_procurement.procurement_planning.services.package_wizard_service import (
	_demand_card_fields,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	_demand_budget_ok,
	_load_demand_for_inclusion,
	_resolve_demand_row,
	can_include_demand_in_plan,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import DemandInclusion


class TestDemInt003PlanningInclusion(IntegrationTestCase):
	def test_approved_planning_ready_resolves_by_code_with_funding_allocation(self) -> None:
		frappe.set_user("Administrator")
		self.assertTrue(demand_consumers_live())
		payload = prepare_final_approval_ui08(
			requester=_ensure_user("dem-int003-req@example.com", [ROLE_REQUESTER])
		)
		demand_name = payload["demand"]
		paa = payload["procurement_approver"]

		frappe.set_user(paa)
		result = approve_and_reserve_form(demand=demand_name)
		self.assertTrue(result["ok"])
		self.assertEqual(result["status"], "Approved")
		self.assertEqual(cint(result["planning_ready"]), 1)

		frappe.set_user("Administrator")
		demand = frappe.db.get_value(
			"Demand",
			demand_name,
			("demand_code", "title", "confirmed_estimate", "procuring_entity"),
			as_dict=True,
		)
		allocation = frappe.db.get_value(
			"Demand Funding Allocation",
			{"demand": demand_name},
			("budget_line", "allocation_amount"),
			as_dict=True,
		)
		self.assertTrue(allocation and allocation.get("budget_line"))

		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"DEM-INT-003 plan {frappe.generate_hash(length=6)}",
				"plan_code": f"PP-DEMINT003-{frappe.generate_hash(length=6)}",
				"fiscal_year": 2029,
				"procuring_entity": demand["procuring_entity"],
				"currency": "KES",
				"status": PLAN_DRAFT,
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value("Procurement Plan", plan.name, "status", PLAN_ACTIVE, update_modified=False)

		resolved = _resolve_demand_row(demand["demand_code"])
		self.assertEqual(resolved["name"], demand_name)
		self.assertEqual(resolved["demand_code"], demand["demand_code"])
		self.assertEqual(resolved["budget_line"], allocation["budget_line"])
		self.assertTrue(_demand_budget_ok(resolved))

		inclusion = _load_demand_for_inclusion(demand["demand_code"])
		self.assertEqual(inclusion["name"], demand_name)
		self.assertEqual(inclusion["title"], demand["title"])
		self.assertEqual(float(inclusion["confirmed_estimate"]), float(demand["confirmed_estimate"]))

		guard = can_include_demand_in_plan(
			demand["demand_code"],
			[],
			plan.name,
			"Administrator",
		)
		self.assertTrue(guard["allowed"], guard["blockers"])

		card = _demand_card_fields(demand["demand_code"])
		self.assertEqual(card["demand_code"], demand["demand_code"])
		self.assertEqual(card["name"], demand["title"])
		self.assertEqual(float(card["estimated_value"]), float(demand["confirmed_estimate"]))
		self.assertEqual(card["budget_line"], allocation["budget_line"])

		frappe.db.set_value("Demand", demand_name, "planning_usage", "Fully planned", update_modified=False)
		fully_planned_guard = can_include_demand_in_plan(
			demand["demand_code"],
			[],
			plan.name,
			"Administrator",
		)
		self.assertFalse(fully_planned_guard["allowed"])
		self.assertIn(
			DemandInclusion.DEMAND_NOT_APPROVED,
			[blocker["code"] for blocker in fully_planned_guard["blockers"]],
		)
