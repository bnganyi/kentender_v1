# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-INT-004 — Package readiness reads MVP Demand references and state."""

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
from kentender_procurement.procurement_planning.services.package_readiness_service import (
	evaluate_pp2_readiness_checks,
)


def _check(result: dict, check_id: str) -> dict:
	return next(row for row in result["checks"] if row["check_id"] == check_id)


class TestDemInt004PackageReadiness(IntegrationTestCase):
	def test_readiness_uses_mvp_demand_code_state_and_funding_allocation(self) -> None:
		frappe.set_user("Administrator")
		self.assertTrue(demand_consumers_live())
		payload = prepare_final_approval_ui08(
			requester=_ensure_user("dem-int004-req@example.com", [ROLE_REQUESTER])
		)
		demand_name = payload["demand"]

		frappe.set_user(payload["procurement_approver"])
		approved = approve_and_reserve_form(demand=demand_name)
		self.assertTrue(approved["ok"])
		self.assertEqual(approved["status"], "Approved")
		self.assertEqual(cint(approved["planning_ready"]), 1)

		frappe.set_user("Administrator")
		demand = frappe.db.get_value(
			"Demand",
			demand_name,
			("demand_code", "status", "planning_ready", "planning_usage", "confirmed_estimate"),
			as_dict=True,
		)
		allocation = frappe.db.get_value(
			"Demand Funding Allocation",
			{"demand": demand_name, "bo_confirmation_status": "Confirmed"},
			("name", "budget_line", "allocation_amount"),
			as_dict=True,
		)
		item_code = frappe.db.get_value("Demand Item", {"demand": demand_name}, "item_code")
		self.assertTrue(demand["demand_code"])
		self.assertEqual(demand["status"], "Approved")
		self.assertEqual(cint(demand["planning_ready"]), 1)
		self.assertNotEqual(demand["planning_usage"], "Fully planned")
		self.assertTrue(allocation and allocation["budget_line"])
		self.assertTrue(item_code)

		package_code = f"PKG-DEMINT004-{frappe.generate_hash(length=6)}"
		frappe.get_doc(
			{
				"doctype": "Procurement Package",
				"name": package_code,
				"package_code": package_code,
				"package_name": "DEM-INT-004 readiness package",
				"plan_id": "DEM-INT-004-PLAN",
				"template_id": "DEM-INT-004-TEMPLATE",
				"procurement_method": "Open Tender",
				"contract_type": "Fixed Price",
				"currency": "KES",
				"estimated_value": demand["confirmed_estimate"],
				"status": "Draft",
				"readiness_status": "Not Run",
				"demand_id": demand_name,
				"budget_line_id": allocation["budget_line"],
				"procurement_category": "Goods",
				"required_std_category": "Goods",
				"is_active": 1,
			}
		).db_insert()
		frappe.get_doc(
			{
				"doctype": "Procurement Package Line",
				"name": frappe.generate_hash(length=10),
				"package_id": package_code,
				"package_line_code": f"PKGLINE-{package_code}-001",
				"demand_id": demand_name,
				"demand_item_code": item_code,
				"budget_line_id": allocation["budget_line"],
				"amount": demand["confirmed_estimate"],
				"currency": "KES",
				"line_status": "Draft",
				"is_active": 1,
			}
		).db_insert()

		result = evaluate_pp2_readiness_checks(package_code)
		self.assertEqual(result["source_snapshot_json"]["demand_code"], demand["demand_code"])
		self.assertNotEqual(result["source_snapshot_json"]["demand_code"], demand_name)
		self.assertEqual(_check(result, "PP2-READY-001")["result"], "PASS")
		self.assertEqual(_check(result, "PP2-READY-007")["result"], "PASS")

		frappe.db.set_value(
			"Demand",
			demand_name,
			"planning_usage",
			"Fully planned",
			update_modified=False,
		)
		fully_planned = evaluate_pp2_readiness_checks(package_code)
		self.assertEqual(_check(fully_planned, "PP2-READY-001")["result"], "FAIL")

		frappe.db.set_value(
			"Demand",
			demand_name,
			{"planning_usage": "Not taken up", "planning_ready": 0},
			update_modified=False,
		)
		not_ready = evaluate_pp2_readiness_checks(package_code)
		self.assertEqual(_check(not_ready, "PP2-READY-001")["result"], "FAIL")

		frappe.db.set_value(
			"Demand",
			demand_name,
			"planning_ready",
			1,
			update_modified=False,
		)
		frappe.db.set_value(
			"Demand Funding Allocation",
			allocation["name"],
			"bo_confirmation_status",
			"Pending",
			update_modified=False,
		)
		unconfirmed_funding = evaluate_pp2_readiness_checks(package_code)
		self.assertEqual(_check(unconfirmed_funding, "PP2-READY-007")["result"], "FAIL")
