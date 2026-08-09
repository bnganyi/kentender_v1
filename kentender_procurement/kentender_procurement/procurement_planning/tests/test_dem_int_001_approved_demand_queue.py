# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-INT-001 — Planning approved-demand queue reads MVP Demand DocType."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cint

from kentender_procurement.demands.api import (
	approve_and_reserve_form,
	prepare_final_approval_ui08,
)
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_REQUESTER,
)
from kentender_procurement.demands.tests.test_demands_budget_api import _ensure_user
from kentender_procurement.procurement_planning.services.approved_demand_queue import (
	get_approved_demands_awaiting_planning,
	get_approved_demands_for_queue,
)


def _find_row(rows: list[dict], demand_name: str = "", demand_code: str = "") -> dict | None:
	for row in rows or []:
		demand = row.get("demand") or {}
		if demand_name and demand.get("id") == demand_name:
			return row
		if demand_code and demand.get("code") == demand_code:
			return row
	return None


class TestDemInt001ApprovedDemandQueue(IntegrationTestCase):
	def test_approved_planning_ready_appears_in_ready_queue(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_final_approval_ui08(
			requester=_ensure_user("dem-int001-req@example.com", [ROLE_REQUESTER])
		)
		name = payload["demand"]
		paa = payload["procurement_approver"]
		frappe.set_user(paa)
		result = approve_and_reserve_form(demand=name)
		self.assertTrue(result["ok"])
		self.assertEqual(result["status"], "Approved")
		self.assertEqual(cint(result["planning_ready"]), 1)

		frappe.set_user("Administrator")
		out = get_approved_demands_awaiting_planning(filters={}, actor="Administrator")
		self.assertTrue(out.get("ok"))
		self.assertFalse(out.get("skipped"))
		self.assertNotEqual(out.get("error_code"), "DEMAND_MODULE_RETIRED")
		row = _find_row(out.get("rows") or [], demand_name=name)
		self.assertIsNotNone(row, "Approved planning_ready Demand missing from ready-to-plan queue")
		demand = row["demand"]
		self.assertEqual(demand["id"], name)
		self.assertTrue(demand.get("code"))
		self.assertNotEqual(demand.get("code"), demand.get("id"))
		self.assertGreater(float(row.get("estimated_value") or 0), 0)
		self.assertTrue(row.get("budget_line", {}).get("code") or row.get("budget_line", {}).get("name"))
		self.assertTrue(row.get("demand_items"))
		# No raw internal id as the only display for budget line.
		bl = row.get("budget_line") or {}
		if bl.get("id") and bl.get("code"):
			self.assertNotEqual(bl.get("code"), bl.get("id"))

	def test_draft_and_not_planning_ready_excluded(self) -> None:
		frappe.set_user("Administrator")
		# Factory leaves Demand at Final Approval — not Approved / not planning_ready.
		payload = prepare_final_approval_ui08(
			requester=_ensure_user("dem-int001-excl@example.com", [ROLE_REQUESTER])
		)
		name = payload["demand"]
		out = get_approved_demands_for_queue(
			filters={"queue": "ready-to-plan"},
			actor="Administrator",
		)
		self.assertTrue(out.get("ok"))
		self.assertIsNone(_find_row(out.get("rows") or [], demand_name=name))
