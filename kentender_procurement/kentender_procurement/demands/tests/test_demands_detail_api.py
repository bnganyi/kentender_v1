# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-UI-09 Approved Demand detail API — projection, factory, cancel gate."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.demands.api import (
	cancel_remaining_demand_form,
	get_demand_detail,
	prepare_approved_detail_ui09,
	prepare_final_approval_ui08,
)
from kentender_procurement.demands.services.demand_lifecycle import (
	approve_and_reserve_demand,
)
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_BUDGET,
	ROLE_PAA,
	ROLE_REQUESTER,
	ensure_demand_roles,
)
from kentender_procurement.demands.tests.test_demands_budget_api import _ensure_user


class TestDemandsDetailUi09(IntegrationTestCase):
	def test_prepare_factory_fully_planned_projection(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_approved_detail_ui09(
			requester=_ensure_user("dem-ui09-req@example.com", [ROLE_REQUESTER])
		)
		self.assertTrue(payload["ok"])
		self.assertEqual(payload["status"], "Approved")
		self.assertEqual(payload["planning_usage"], "Fully planned")
		self.assertEqual(payload["planning_ready"], 1)
		ov = payload["detail"]["overview"]
		self.assertIn("KES", ov["approved_amount_display"])
		self.assertIn(",", ov["approved_amount_display"])
		self.assertIn("Plan Item", ov["downstream_summary"])
		lc = payload["detail"]["lifecycle"]
		self.assertTrue(lc["downstream"])
		self.assertTrue(lc["decisions"])
		fu = payload["detail"]["funding"]
		self.assertIsNotNone(fu.get("allocation"))
		self.assertIsNotNone(fu.get("reservation"))
		self.assertNotEqual(
			fu["allocation"]["budget_line_display"],
			fu["allocation"]["budget_line"],
		)

		paa = payload["procurement_approver"]
		frappe.set_user(paa)
		loaded = get_demand_detail(demand=payload["demand"])
		self.assertTrue(loaded["ok"])
		self.assertFalse(loaded["can_cancel"])
		self.assertIn("locked", (loaded.get("lock_message") or "").lower())
		self.assertEqual(loaded["demand"]["status"], "Approved")
		self.assertTrue(loaded["scope"]["items"])
		self.assertIn("KES", loaded["scope"]["total_display"])
		self.assertTrue(loaded["strategy"].get("confirmed_label"))
		self.assertTrue(loaded["lifecycle"]["audit"])

	def test_not_taken_up_can_cancel_for_paa(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_final_approval_ui08(
			requester=_ensure_user("dem-ui09-cancel-req@example.com", [ROLE_REQUESTER])
		)
		name = payload["demand"]
		paa = payload["procurement_approver"]
		approve_and_reserve_demand(demand=name, user=paa)
		frappe.db.commit()

		frappe.set_user(paa)
		loaded = get_demand_detail(demand=name)
		self.assertTrue(loaded["can_cancel"])
		self.assertEqual(loaded["demand"]["planning_usage"], "Not taken up")

		with self.assertRaises(Exception):
			cancel_remaining_demand_form(demand=name, reason="")
		result = cancel_remaining_demand_form(
			demand=name,
			reason="No longer required — cancel remaining reserved funding",
		)
		self.assertTrue(result["ok"])
		self.assertEqual(result["status"], "Cancelled")

	def test_non_reader_denied(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_approved_detail_ui09(
			requester=_ensure_user("dem-ui09-deny-req@example.com", [ROLE_REQUESTER])
		)
		name = payload["demand"]
		# Guest cannot read.
		frappe.set_user("Guest")
		with self.assertRaises(Exception):
			get_demand_detail(demand=name)

	def test_bo_cannot_cancel_remaining(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_final_approval_ui08(
			requester=_ensure_user("dem-ui09-bo-req@example.com", [ROLE_REQUESTER])
		)
		name = payload["demand"]
		paa = payload["procurement_approver"]
		bo = payload["budget_officer"]
		approve_and_reserve_demand(demand=name, user=paa)
		frappe.db.commit()
		ensure_demand_roles()
		_ensure_user(bo, [ROLE_BUDGET])
		frappe.set_user(bo)
		loaded = get_demand_detail(demand=name)
		self.assertFalse(loaded["can_cancel"])
		with self.assertRaises(Exception):
			cancel_remaining_demand_form(
				demand=name, reason="BO must not cancel remaining"
			)
