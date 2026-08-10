# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SEED-001/003 — KENTENDER_MVP_V1 Planning seed + validate idempotency."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds.kentender_mvp_v1 import constants as C


class TestPlanningMvpSeedContract(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		from kentender_core.seeds.kentender_mvp_v1.orchestrator import run_kentender_mvp_v1

		cls.seed = run_kentender_mvp_v1(
			reset=True, force=True, validate=True
		)

	def test_seed_ok(self) -> None:
		self.assertTrue(self.seed.get("ok"), msg=str(self.seed.get("validate")))

	def test_plan_identities(self) -> None:
		self.assertTrue(
			frappe.db.exists("Procurement Plan", {"plan_code": C.PROCUREMENT_PLAN_CODE})
		)
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Version",
				{"version_code": C.PROCUREMENT_PLAN_VERSION_CODE},
				"status",
			),
			"Approved",
		)
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Item",
				{"plan_item_code": C.PLAN_ITEM_CODE},
				"baseline_state",
			),
			"Active",
		)

	def test_allocations_455m(self) -> None:
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

	def test_idempotent_second_run(self) -> None:
		from kentender_core.seeds.kentender_mvp_v1.orchestrator import run_kentender_mvp_v1

		before_plans = frappe.db.count(
			"Procurement Plan", {"plan_code": C.PROCUREMENT_PLAN_CODE}
		)
		before_items = frappe.db.count(
			"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE}
		)
		second = run_kentender_mvp_v1(
			reset=False, force=True, validate=True
		)
		self.assertTrue(second.get("ok"), msg=str(second.get("validate")))
		self.assertEqual(
			frappe.db.count("Procurement Plan", {"plan_code": C.PROCUREMENT_PLAN_CODE}),
			before_plans,
		)
		self.assertEqual(
			frappe.db.count(
				"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE}
			),
			before_items,
		)
		self.assertEqual(before_plans, 1)
		self.assertEqual(before_items, 1)
