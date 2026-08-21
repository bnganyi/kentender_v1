# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SEED / Demo v2.7 §7.8 — SCN-PLN-REMOVE-001."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.procurement_planning.seeds import scn_pln_remove_001 as scn
from kentender_procurement.procurement_planning.seeds.scn_pln_remove_001 import REMOVE_REASON
from kentender_procurement.procurement_planning.services.get_planning_workspace import (
	get_planning_workspace,
)


class TestScnPlnRemove001(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.setup_result = scn.setup(force=True)

	def test_00_prepared_proposed_022(self) -> None:
		self.assertTrue(self.setup_result.get("ok"))
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Item",
				{"plan_item_code": C.PLAN_ITEM_CODE_SCN},
				"baseline_state",
			),
			"Proposed",
		)
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Version",
				{"version_code": C.PROCUREMENT_PLAN_VERSION_CODE},
				"status",
			),
			"Approved",
		)

	def test_run_restores_455m_and_eligibility(self) -> None:
		result = scn.run(reset_first=False, force=True)
		self.assertTrue(result.get("ok"))
		self.assertFalse(result.get("idempotent"))
		self.assertEqual(result.get("baseline_state"), "Removed")
		self.assertAlmostEqual(flt(result.get("planned_total")), C.PLAN_AMOUNT_V1, places=2)
		self.assertTrue(result.get("demand_eligible"))
		self.assertEqual(result.get("approved_v1_status"), "Approved")
		item = result["plan_item"]
		self.assertTrue(frappe.db.exists("Procurement Plan Item", item))
		iv = frappe.db.get_value(
			"Procurement Plan Item Version",
			{"plan_item": item},
			"name",
		)
		self.assertTrue(iv)
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item Version", iv, "removal_reason"),
			REMOVE_REASON,
		)
		self.assertTrue(
			frappe.db.exists("Plan Demand Allocation", {"plan_item": item}),
		)

	def test_second_run_idempotent(self) -> None:
		v2 = frappe.db.get_value(
			"Procurement Plan Version",
			{"version_code": C.PROCUREMENT_PLAN_VERSION_V2},
			"name",
		)
		first = frappe.db.count(
			"Plan Decision",
			{"plan_version": v2, "decision_type": "Removal"},
		)
		second = scn.run(reset_first=False, force=True)
		self.assertTrue(second.get("ok"))
		self.assertTrue(second.get("idempotent"))
		self.assertEqual(
			frappe.db.count(
				"Plan Decision",
				{"plan_version": v2, "decision_type": "Removal"},
			),
			first,
		)

	def test_workspace_projects_no_effective_changes_state(self) -> None:
		"""A no-change Draft remains planner-action work, never a workspace mutation."""
		scn.run(reset_first=False, force=True)
		payload = get_planning_workspace(
			procuring_entity=C.PE_MOH,
			financial_year="2027/28",
			user=C.USER_PLANNING_OFFICER,
		)

		self.assertEqual(payload.get("workspace_state"), "DRAFT_WITH_PLANNER_ACTION")
		self.assertEqual(payload["current_plan"]["approved"]["planned_total"], C.PLAN_AMOUNT_V1)
		self.assertEqual(payload["current_plan"]["draft"]["planned_total"], C.PLAN_AMOUNT_V1)
		self.assertEqual(payload["primary_action"]["label"], "Continue plan update")
		self.assertEqual(payload.get("waiting_on_others"), [])
		cancel_rows = [
			row
			for row in payload["work_requiring_action"]
			if row["action"]["code"] == "cancel_update"
		]
		self.assertEqual(len(cancel_rows), 1)
		action = cancel_rows[0]["action"]
		self.assertEqual(action["label"], "Cancel update")
		self.assertEqual(action["route"], payload["current_plan"]["update_route"])

	def test_validate_include_scn_remove(self) -> None:
		scn.run(reset_first=False, force=True)
		from kentender_core.seeds.kentender_mvp_v1.orchestrator import (
			validate_kentender_mvp_v1,
		)

		report = validate_kentender_mvp_v1(include_scn_remove=True)
		self.assertTrue(report.get("ok"), report.get("summary"))
