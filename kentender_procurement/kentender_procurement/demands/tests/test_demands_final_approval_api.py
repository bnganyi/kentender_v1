# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-UI-08 Final Approval API — projection, approve/reserve, return, reject."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_procurement.demands.api import (
	approve_and_reserve_form,
	get_demand_review,
	prepare_final_approval_ui08,
	record_final_decision_form,
)
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_BUDGET,
	ROLE_PAA,
	ROLE_REQUESTER,
	ensure_demand_roles,
)
from kentender_procurement.demands.tests.test_demands_budget_api import _ensure_user


class TestDemandsFinalApprovalUi08(IntegrationTestCase):
	def test_prepare_factory_and_projection_ready(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_final_approval_ui08(
			requester=_ensure_user("dem-fa-req@example.com", [ROLE_REQUESTER])
		)
		self.assertTrue(payload["ok"])
		self.assertEqual(payload["current_stage"], "Final Approval")
		fa = payload["final_approval"]
		self.assertTrue(fa["approve_ready"])
		self.assertEqual(fa["readiness"]["blocking_issues_display"], "None")
		self.assertIn("KES", fa["demand_summary"]["confirmed_estimate_display"])
		self.assertIn(",", fa["demand_summary"]["confirmed_estimate_display"])
		self.assertIsNotNone(fa["funding"])
		self.assertNotEqual(
			fa["funding"]["budget_line_display"], fa["funding"]["budget_line"]
		)

		paa = payload["procurement_approver"]
		frappe.set_user(paa)
		loaded = get_demand_review(demand=payload["demand"])
		self.assertTrue(loaded["can_final_approve"])
		self.assertIsNotNone(loaded["final_approval"])
		self.assertTrue(loaded["final_approval"]["approve_ready"])

	def test_approve_reserves_and_sets_planning_ready(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_final_approval_ui08(
			requester=_ensure_user("dem-fa-approve-req@example.com", [ROLE_REQUESTER])
		)
		name = payload["demand"]
		paa = payload["procurement_approver"]
		frappe.set_user(paa)
		result = approve_and_reserve_form(demand=name)
		self.assertTrue(result["ok"])
		self.assertEqual(result["status"], "Approved")
		self.assertEqual(result["stage"], "Complete")
		self.assertEqual(result["planning_ready"], 1)
		self.assertTrue(result["reservations"])
		fresh = frappe.get_doc("Demand", name)
		self.assertEqual(fresh.status, "Approved")
		self.assertEqual(cint_planning_ready(fresh), 1)
		with self.assertRaises(Exception):
			approve_and_reserve_form(demand=name)

	def test_return_invalidates_bo_signoff(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_final_approval_ui08(
			requester=_ensure_user("dem-fa-ret-req@example.com", [ROLE_REQUESTER])
		)
		name = payload["demand"]
		paa = payload["procurement_approver"]
		frappe.set_user(paa)
		with self.assertRaises(Exception):
			record_final_decision_form(demand=name, decision="Return", reason="")
		result = record_final_decision_form(
			demand=name,
			decision="Return",
			reason="Funding line needs BO reconfirmation after scope check",
		)
		self.assertTrue(result["ok"])
		self.assertEqual(result["status"], "Returned")
		self.assertEqual(result["stage"], "Budget Confirmation")
		confirmed = frappe.get_all(
			"Demand Funding Allocation",
			filters={"demand": name, "bo_confirmation_status": "Confirmed"},
			pluck="name",
		)
		self.assertEqual(confirmed, [])
		pending = frappe.get_all(
			"Demand Funding Allocation",
			filters={"demand": name, "bo_confirmation_status": "Pending"},
			pluck="name",
		)
		self.assertGreaterEqual(len(pending), 1)

	def test_reject_is_terminal(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_final_approval_ui08(
			requester=_ensure_user("dem-fa-rej-req@example.com", [ROLE_REQUESTER])
		)
		name = payload["demand"]
		paa = payload["procurement_approver"]
		frappe.set_user(paa)
		result = record_final_decision_form(
			demand=name,
			decision="Reject",
			reason="No longer aligned with entity priorities",
		)
		self.assertTrue(result["ok"])
		self.assertEqual(result["status"], "Rejected")
		self.assertEqual(result["stage"], "Complete")

	def test_non_paa_cannot_approve(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_final_approval_ui08(
			requester=_ensure_user("dem-fa-deny-req@example.com", [ROLE_REQUESTER])
		)
		name = payload["demand"]
		bo = payload["budget_officer"]
		frappe.set_user(bo)
		with self.assertRaises(Exception):
			approve_and_reserve_form(demand=name)
		ensure_demand_roles()
		_ensure_user(bo, [ROLE_BUDGET])
		loaded = get_demand_review(demand=name)
		self.assertFalse(loaded.get("can_final_approve"))


def cint_planning_ready(doc) -> int:
	return int(flt(doc.planning_ready) or 0)
