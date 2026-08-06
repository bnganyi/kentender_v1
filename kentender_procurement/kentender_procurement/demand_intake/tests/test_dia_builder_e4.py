# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""E4 — Demand primary Strategy Reference via apply_strategy_reference_to_doc (XMOD-STR-002).

Legacy budget-line strategy derivation was removed; Active target selection is authoritative.

Run:
  bench --site <site> run-tests --app kentender_procurement \\
    --module kentender_procurement.demand_intake.tests.test_dia_builder_e4
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy


class TestDiaBuilderE4(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.seed = upsert_works_master_strategy_hierarchy()

	def tearDown(self):
		frappe.set_user("Administrator")
		for name in getattr(self, "_demand_names", []):
			if frappe.db.exists("Demand", name):
				frappe.delete_doc("Demand", name, force=True, ignore_permissions=True)
		dept = getattr(self, "_dept", None)
		if dept and frappe.db.exists("Procuring Department", dept):
			frappe.delete_doc("Procuring Department", dept, force=True, ignore_permissions=True)

	def test_strategy_target_applies_plan_and_snapshot_on_insert(self):
		if not frappe.db.exists("DocType", "Demand"):
			self.skipTest("Demand DocType not installed")
		target = self.seed.get("target")
		plan = self.seed.get("plan")
		if not target or not plan:
			self.skipTest("MOH strategy seed missing target/plan")

		self._demand_names = []
		frappe.set_user("Administrator")
		ensure_currency_kes()
		self._dept = ensure_department(
			f"Dept E4 {frappe.generate_hash(length=4)}", self.seed["procuring_entity"]
		)

		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": "E4 strategy reference",
				"procuring_entity": self.seed["procuring_entity"],
				"requesting_department": self._dept,
				"request_date": today(),
				"required_by_date": today(),
				"specification_summary": "Equipment per strategy target",
				"delivery_location": "HQ",
				"requested_delivery_period_days": 30,
				"strategy_target": target,
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

		self.assertEqual(doc.strategy_target, target)
		self.assertEqual(doc.strategy_plan_version, plan)
		self.assertTrue((doc.strategy_snapshot_label or "").strip())
