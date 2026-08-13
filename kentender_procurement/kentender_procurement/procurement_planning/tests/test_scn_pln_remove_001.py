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
