"""Focused PLN-CHG-015 authoritative workspace-state contract."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api import prepare_planning_workspace_ui
from kentender_procurement.procurement_planning.services.get_planning_workspace import (
	WORKSPACE_APPROVED_ACTIONABLE,
	WORKSPACE_APPROVED_NO_WORK,
	WORKSPACE_DRAFT_ACTION,
	WORKSPACE_DRAFT_FINANCE,
	WORKSPACE_INITIAL_DRAFT_EMPTY,
	WORKSPACE_NO_PLAN,
	WORKSPACE_REVIEW,
	get_planning_workspace,
)
from kentender_procurement.procurement_planning.tests._gate02_helpers import (
	PE_MOH,
	ensure_org,
)


class TestPlanningWorkspaceStates(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_org()
		cls.planner = "moh.planning.officer@example.test"

	def _prepare(self, state: str) -> dict:
		previous = frappe.session.user
		frappe.set_user("Administrator")
		try:
			return prepare_planning_workspace_ui(state)
		finally:
			frappe.set_user(previous or "Administrator")

	def _workspace(self, fy: str) -> dict:
		return get_planning_workspace(procuring_entity=PE_MOH, financial_year=fy, user=self.planner)

	def test_no_plan_and_initial_draft_exact_boundaries(self) -> None:
		self._prepare("A")
		before = {
			"plans": frappe.db.count("Procurement Plan", {"procuring_entity": PE_MOH, "financial_year": "2028/29"}),
			"versions": frappe.db.count("Procurement Plan Version"),
			"decisions": frappe.db.count("Plan Decision"),
		}
		no_plan = self._workspace("2028/29")
		self.assertEqual(no_plan["workspace_state"], WORKSPACE_NO_PLAN)
		self.assertEqual(no_plan["eligible_demand_count"], 2)
		self.assertEqual(no_plan["primary_action"]["label"], "Create annual plan")
		self.assertEqual(no_plan["work_requiring_action"], [])
		self.assertEqual(no_plan["empty_states"]["work_requiring_action"], "Create the annual Plan to begin Planning approved requirements.")
		self.assertEqual(before["plans"], frappe.db.count("Procurement Plan", {"procuring_entity": PE_MOH, "financial_year": "2028/29"}))
		self.assertEqual(before["versions"], frappe.db.count("Procurement Plan Version"))
		self.assertEqual(before["decisions"], frappe.db.count("Plan Decision"))

		self._prepare("B")
		draft = self._workspace("2028/29")
		self.assertEqual(draft["workspace_state"], WORKSPACE_INITIAL_DRAFT_EMPTY)
		self.assertEqual(draft["primary_action"]["label"], "Continue planning")
		self.assertEqual(draft["current_plan"]["draft"]["item_count"], 0)
		self.assertEqual(draft["current_plan"]["draft"]["planned_total"], 0)
		self.assertEqual([row["reference"] for row in draft["work_requiring_action"]], ["DMD-MOH-2028-001", "DMD-MOH-2028-002"])
		self.assertTrue(all(row["action"]["label"] == "Add to plan" for row in draft["work_requiring_action"]))

	def test_base_and_draft_action_states(self) -> None:
		self._prepare("BASE")
		base = self._workspace("2027/28")
		self.assertEqual(base["workspace_state"], WORKSPACE_APPROVED_ACTIONABLE)
		self.assertEqual(base["primary_action"]["label"], "View approved plan")
		self.assertEqual([row["reference"] for row in base["work_requiring_action"]], ["DMD-MOH-2027-019"])

		self._prepare("C")
		draft = self._workspace("2027/28")
		self.assertEqual(draft["workspace_state"], WORKSPACE_DRAFT_ACTION)
		self.assertEqual(draft["primary_action"]["label"], "Continue plan update")
		row = next(row for row in draft["work_requiring_action"] if row["reference"] == "PPI-MOH-2027-022")
		self.assertEqual(row["status"], "Planning incomplete")
		self.assertEqual(row["action"]["label"], "Complete item")
		self.assertEqual([metric["label"] for metric in draft["current_plan"]["summary_metrics"]], ["Approved value", "Draft value", "Net change", "Planning complete", "Finance confirmed", "Validation"])

	def test_finance_and_review_waiting_are_informational(self) -> None:
		self._prepare("D")
		finance = self._workspace("2027/28")
		self.assertEqual(finance["workspace_state"], WORKSPACE_DRAFT_FINANCE)
		self.assertEqual(finance["primary_action"]["label"], "View plan update")
		self.assertEqual(finance["work_requiring_action"], [])
		self.assertEqual(len(finance["waiting_on_others"]), 1)
		self.assertEqual(finance["waiting_on_others"][0]["stage"], "Finance confirmation")
		self.assertNotIn("action", finance["waiting_on_others"][0])
		self.assertNotIn("task", finance["waiting_on_others"][0])

		self._prepare("E")
		review = self._workspace("2027/28")
		self.assertEqual(review["workspace_state"], WORKSPACE_REVIEW)
		self.assertEqual(review["primary_action"]["label"], "View approved plan")
		self.assertEqual(review["waiting_on_others"][0]["stage"], "Professional review")
		self.assertEqual(review["waiting_on_others"][0]["with_role"], "Head of Procurement")
		self.assertNotIn("action", review["waiting_on_others"][0])
		self.assertNotIn("task", review["waiting_on_others"][0])

	def test_approved_no_work_has_no_add_path(self) -> None:
		self._prepare("F")
		approved = self._workspace("2027/28")
		self.assertEqual(approved["workspace_state"], WORKSPACE_APPROVED_NO_WORK)
		self.assertEqual(approved["primary_action"]["label"], "View approved plan")
		self.assertEqual(approved["work_requiring_action"], [])
		self.assertEqual(approved["waiting_on_others"], [])
		self.assertEqual(approved["current_plan"]["approved"]["item_count"], 2)
		self.assertEqual(approved["current_plan"]["approved"]["planned_total"], 535_000_000)
		self.assertEqual(approved["current_plan"]["approved"]["finance_confirmed_label"], "2 of 2")
		self.assertFalse(any(row.get("action", {}).get("code") == "add_to_plan" for row in approved["work_requiring_action"]))
		self.assertNotIn("add_demand", approved["primary_action"]["route"])

	def test_filtering_does_not_change_state(self) -> None:
		self._prepare("BASE")
		unfiltered = self._workspace("2027/28")
		filtered = get_planning_workspace(
			procuring_entity=PE_MOH,
			financial_year="2027/28",
			work_filter="returned_work",
			search="not present",
			user=self.planner,
		)
		self.assertEqual(filtered["workspace_state"], unfiltered["workspace_state"])
		self.assertEqual(filtered["work_requiring_action"], [])
		self.assertEqual(filtered["counts"], unfiltered["counts"])
