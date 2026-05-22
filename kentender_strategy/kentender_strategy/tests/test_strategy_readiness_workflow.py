# Copyright (c) 2026, KenTender and contributors

import frappe
from frappe.tests import IntegrationTestCase

from kentender_strategy.api.strategy_workflow import activate_plan, approve_plan, submit_plan
from kentender_strategy.services import strategy_builder as svc
from kentender_strategy.services.strategy_readiness import evaluate_plan_readiness


class TestStrategyReadinessWorkflow(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": "Workflow Test Plan",
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

	def _seed_chain(self):
		prog = svc.create_node(self.plan, None, "Program", {"node_title": "P"})
		sub = svc.create_node(self.plan, prog, "SubProgram", {"node_title": "SP"})
		ind = svc.create_node(self.plan, sub, "Indicator", {"node_title": "I"})
		svc.create_node(self.plan, ind, "Target", {"node_title": "T", "target_value": 1})

	def test_incomplete_plan_not_ready(self):
		result = evaluate_plan_readiness(self.plan)
		self.assertFalse(result["ready"])

	def test_workflow_transitions(self):
		self._seed_chain()
		submit_plan(self.plan)
		self.assertEqual(frappe.db.get_value("Strategic Plan", self.plan, "status"), "Submitted")
		approve_plan(self.plan)
		self.assertEqual(frappe.db.get_value("Strategic Plan", self.plan, "status"), "Approved")
		activate_plan(self.plan)
		self.assertEqual(frappe.db.get_value("Strategic Plan", self.plan, "status"), "Active")
