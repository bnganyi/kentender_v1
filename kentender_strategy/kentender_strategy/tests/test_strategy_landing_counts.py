# Copyright (c) 2026, KenTender and contributors

import frappe
from frappe.tests import IntegrationTestCase

from kentender_strategy.api.landing import get_strategy_landing_data
from kentender_strategy.services import strategy_builder as svc


class TestStrategyLandingCounts(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": "Landing Counts Test Plan",
				"procuring_entity": self._ensure_entity(),
				"start_year": 2026,
				"end_year": 2030,
				"status": "Draft",
				"version_no": 1,
				"is_current_version": 1,
			}
		).insert(ignore_permissions=True).name
		prog = svc.create_node(self.plan, None, "Program", {"node_title": "P1"})
		sub = svc.create_node(self.plan, prog, "SubProgram", {"node_title": "SP1"})
		svc.create_node(self.plan, sub, "Indicator", {"node_title": "I1"})

	def tearDown(self):
		frappe.db.delete("Strategy Target", {"strategic_plan": self.plan})
		frappe.db.delete("Strategy Objective", {"strategic_plan": self.plan})
		frappe.db.delete("Sub Program", {"strategic_plan": self.plan})
		frappe.db.delete("Strategy Program", {"strategic_plan": self.plan})
		if frappe.db.exists("Strategic Plan", self.plan):
			frappe.delete_doc("Strategic Plan", self.plan, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _ensure_entity(self) -> str:
		name = frappe.db.get_value("Procuring Entity", {"entity_code": "PE-MOH"}, "name")
		if name:
			return name
		return frappe.get_doc(
			{
				"doctype": "Procuring Entity",
				"entity_name": "MOH Test Entity",
				"entity_code": "PE-MOH",
			}
		).insert(ignore_permissions=True).name

	def test_landing_includes_four_level_counts(self):
		data = get_strategy_landing_data()
		row = next((p for p in data["plans"] if p["name"] == self.plan), None)
		self.assertIsNotNone(row)
		self.assertEqual(row["program_count"], 1)
		self.assertEqual(row["sub_program_count"], 1)
		self.assertEqual(row["indicator_count"], 1)
		self.assertEqual(row["objective_count"], 1)
