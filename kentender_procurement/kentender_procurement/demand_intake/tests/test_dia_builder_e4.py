# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""E4 — Budget-line-first strategy derivation on Demand (server validate).

Run:
  bench --site <site> run-tests --app kentender_procurement \\
    --module kentender_procurement.demand_intake.tests.test_dia_builder_e4
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds._common import ensure_currency_kes, ensure_department


class TestDiaBuilderE4(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		for name in getattr(self, "_demand_names", []):
			if frappe.db.exists("Demand", name):
				frappe.delete_doc("Demand", name, force=True, ignore_permissions=True)
		dept = getattr(self, "_dept", None)
		if dept and frappe.db.exists("Procuring Department", dept):
			frappe.delete_doc("Procuring Department", dept, force=True, ignore_permissions=True)

	def test_budget_line_derives_strategy_on_insert(self):
		if not frappe.db.exists("DocType", "Demand"):
			self.skipTest("Demand DocType not installed")
		bl_name = frappe.db.get_value("Budget Line", {"budget_line_code": "BL-MOH-2026-001"}, "name")
		if not bl_name:
			self.skipTest("Seed budget line BL-MOH-2026-001 not present on site")

		bl = frappe.db.get_value(
			"Budget Line",
			bl_name,
			[
				"procuring_entity",
				"budget",
				"funding_source",
				"strategic_plan",
				"program",
				"sub_program",
				"output_indicator",
				"performance_target",
			],
			as_dict=True,
		)
		self._demand_names = []
		frappe.set_user("Administrator")
		ensure_currency_kes()
		self._dept = ensure_department(f"Dept E4 {frappe.generate_hash(length=4)}", bl.procuring_entity)

		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": "E4 budget-line-first",
				"procuring_entity": bl.procuring_entity,
				"requesting_department": self._dept,
				"request_date": today(),
				"required_by_date": today(),
				"specification_summary": "Equipment per seed line",
				"delivery_location": "HQ",
				"requested_delivery_period_days": 30,
				"budget_line": bl_name,
				"items": [
					{
						"item_description": "Test line",
						"category": "c",
						"uom": "ea",
						"quantity": 1,
						"estimated_unit_cost": 50,
					}
				],
			}
		)
		doc.insert(ignore_permissions=True)
		self._demand_names.append(doc.name)

		ctx = get_budget_line_context(bl_name)
		self.assertTrue(ctx.get("ok"), msg=ctx.get("message"))
		data = ctx.get("data") or {}

		self.assertEqual(doc.budget_line, bl_name)
		self.assertEqual(doc.budget, data.get("budget"))
		self.assertEqual(doc.funding_source, data.get("funding_source"))
		self.assertEqual(doc.strategic_plan, data.get("strategic_plan"))
		self.assertEqual(doc.program, data.get("program"))
		self.assertEqual(doc.sub_program, data.get("sub_program"))
		self.assertEqual(doc.output_indicator, data.get("output_indicator"))
		self.assertEqual(doc.performance_target, data.get("performance_target"))
