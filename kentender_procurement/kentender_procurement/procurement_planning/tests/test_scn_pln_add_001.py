# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SEED-002 — SCN-PLN-ADD-001 setup / run / reset + idempotency."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.procurement_planning.seeds import scn_pln_add_001 as scn


class TestScnPlnAdd001(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.setup_result = scn.setup(force=True)

	def test_00_setup_base_planning(self) -> None:
		self.assertTrue(self.setup_result.get("ok"))
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Version",
				{"version_code": C.PROCUREMENT_PLAN_VERSION_CODE},
				"status",
			),
			"Approved",
		)
		self.assertFalse(
			frappe.db.exists(
				"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE_SCN}
			)
		)

	def test_run_adds_022_and_535m(self) -> None:
		result = scn.run(reset_first=False, force=True)
		self.assertTrue(result.get("ok"))
		self.assertFalse(result.get("idempotent"))
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Item",
				{"plan_item_code": C.PLAN_ITEM_CODE_SCN},
				"baseline_state",
			),
			"Active",
		)
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Version",
				{"version_code": C.PROCUREMENT_PLAN_VERSION_V2},
				"status",
			),
			"Approved",
		)
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Version",
				{"version_code": C.PROCUREMENT_PLAN_VERSION_CODE},
				"status",
			),
			"Superseded",
		)
		self.assertAlmostEqual(flt(result.get("total")), C.PLAN_AMOUNT_V2, places=2)

	def test_second_run_idempotent(self) -> None:
		first_count = frappe.db.count(
			"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE_SCN}
		)
		second = scn.run(reset_first=False, force=True)
		self.assertTrue(second.get("ok"))
		self.assertTrue(second.get("idempotent"))
		self.assertEqual(
			frappe.db.count(
				"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE_SCN}
			),
			first_count,
		)
		self.assertEqual(first_count, 1)

	def test_reset_restores_base(self) -> None:
		scn.run(reset_first=False, force=True)
		reset = scn.reset(force=True)
		self.assertTrue(reset.get("ok"))
		self.assertFalse(
			frappe.db.exists(
				"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE_SCN}
			)
		)
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Version",
				{"version_code": C.PROCUREMENT_PLAN_VERSION_CODE},
				"status",
			),
			"Approved",
		)
		item = frappe.db.get_value(
			"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE}, "name"
		)
		total = sum(
			flt(r.allocated_amount)
			for r in frappe.get_all(
				"Plan Demand Allocation",
				filters={"plan_item": item, "status": "Effective"},
				fields=["allocated_amount"],
			)
		)
		self.assertAlmostEqual(total, C.PLAN_AMOUNT_V1, places=2)
