# Copyright (c) 2026, KenTender and contributors

import frappe
from frappe.tests import IntegrationTestCase

from kentender_strategy.services import strategy_builder as svc


class TestStrategyBuilderFourLevel(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": "Four-Level Test Plan",
				"procuring_entity": self._ensure_entity(),
				"start_year": 2026,
				"end_year": 2030,
				"status": "Draft",
				"version_no": 1,
				"is_current_version": 1,
			}
		).insert(ignore_permissions=True).name

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

	def test_create_full_four_level_chain(self):
		prog = svc.create_node(self.plan, None, "Program", {"node_title": "Health Program"})
		sub = svc.create_node(self.plan, prog, "SubProgram", {"node_title": "District Works"})
		ind = svc.create_node(self.plan, sub, "Indicator", {"node_title": "Hospital readiness"})
		tgt = svc.create_node(
			self.plan,
			ind,
			"Target",
			{"node_title": "Renovate hospitals", "target_value": 1, "target_unit": "projects"},
		)

		tree = svc.build_tree(self.plan)
		self.assertEqual(tree["counts"]["programs"], 1)
		self.assertEqual(tree["counts"]["sub_programs"], 1)
		self.assertEqual(tree["counts"]["indicators"], 1)
		self.assertEqual(tree["counts"]["targets"], 1)

		types = {n["name"]: n["node_type"] for n in tree["nodes"]}
		self.assertEqual(types[prog], "Program")
		self.assertEqual(types[sub], "SubProgram")
		self.assertEqual(types[ind], "Indicator")
		self.assertEqual(types[tgt], "Target")

	def test_indicator_under_program_rejected(self):
		prog = svc.create_node(self.plan, None, "Program", {"node_title": "Health Program"})
		with self.assertRaises(frappe.ValidationError):
			svc.create_node(self.plan, prog, "Indicator", {"node_title": "Orphan indicator"})

	def test_objective_alias_maps_to_indicator(self):
		prog = svc.create_node(self.plan, None, "Program", {"node_title": "Health Program"})
		sub = svc.create_node(self.plan, prog, "SubProgram", {"node_title": "District Works"})
		name = svc.create_node(self.plan, sub, "Objective", {"node_title": "Legacy alias"})
		self.assertTrue(frappe.db.exists("Strategy Objective", name))

	def test_draft_guard_blocks_mutation_on_active_plan(self):
		prog = svc.create_node(self.plan, None, "Program", {"node_title": "Health Program"})
		frappe.db.set_value("Strategic Plan", self.plan, "status", "Active")
		with self.assertRaises(frappe.ValidationError):
			svc.create_node(self.plan, prog, "SubProgram", {"node_title": "Blocked sub"})
