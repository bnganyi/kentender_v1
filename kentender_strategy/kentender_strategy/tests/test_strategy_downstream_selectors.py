# Copyright (c) 2026, KenTender and contributors

import frappe
from frappe.tests import IntegrationTestCase

from kentender_strategy.api.selectors import (
	get_active_strategy_indicators,
	get_active_strategy_programs,
	get_active_strategy_sub_programs,
	get_active_strategy_targets,
)
from kentender_strategy.services import strategy_builder as svc


class TestStrategyDownstreamSelectors(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.entity = self._ensure_entity()
		self.draft_plan = self._insert_plan("Draft Selector Plan", "Draft")
		self.active_plan = self._insert_plan("Active Selector Plan", "Draft")
		self._seed_hierarchy(self.draft_plan)
		self._seed_hierarchy(self.active_plan)
		frappe.db.set_value("Strategic Plan", self.active_plan, "status", "Active")
		frappe.db.commit()

	def tearDown(self):
		for plan in (self.draft_plan, self.active_plan):
			frappe.db.delete("Strategy Target", {"strategic_plan": plan})
			frappe.db.delete("Strategy Objective", {"strategic_plan": plan})
			frappe.db.delete("Sub Program", {"strategic_plan": plan})
			frappe.db.delete("Strategy Program", {"strategic_plan": plan})
			if frappe.db.exists("Strategic Plan", plan):
				frappe.delete_doc("Strategic Plan", plan, force=True, ignore_permissions=True)
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

	def _insert_plan(self, title: str, status: str) -> str:
		return frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": title,
				"procuring_entity": self.entity,
				"start_year": 2026,
				"end_year": 2030,
				"status": status,
				"version_no": 1,
				"is_current_version": 1,
			}
		).insert(ignore_permissions=True).name

	def _seed_hierarchy(self, plan: str) -> None:
		prog = svc.create_node(plan, None, "Program", {"node_title": f"P-{plan[:6]}"})
		sub = svc.create_node(plan, prog, "SubProgram", {"node_title": f"SP-{plan[:6]}"})
		ind = svc.create_node(plan, sub, "Indicator", {"node_title": f"I-{plan[:6]}"})
		svc.create_node(plan, ind, "Target", {"node_title": f"T-{plan[:6]}", "target_value": 1})

	def test_active_selectors_exclude_non_active_plans(self):
		programs = get_active_strategy_programs()
		program_ids = {row["id"] for row in programs}
		draft_programs = frappe.get_all(
			"Strategy Program", filters={"strategic_plan": self.draft_plan}, pluck="name"
		)
		active_programs = frappe.get_all(
			"Strategy Program", filters={"strategic_plan": self.active_plan}, pluck="name"
		)
		self.assertTrue(active_programs)
		for pid in draft_programs:
			self.assertNotIn(pid, program_ids)
		for pid in active_programs:
			self.assertIn(pid, program_ids)

		sub_programs = get_active_strategy_sub_programs()
		sub_ids = {row["id"] for row in sub_programs}
		for sid in frappe.get_all("Sub Program", filters={"strategic_plan": self.draft_plan}, pluck="name"):
			self.assertNotIn(sid, sub_ids)

		indicators = get_active_strategy_indicators()
		ind_ids = {row["id"] for row in indicators}
		for iid in frappe.get_all("Strategy Objective", filters={"strategic_plan": self.draft_plan}, pluck="name"):
			self.assertNotIn(iid, ind_ids)

		targets = get_active_strategy_targets()
		tgt_ids = {row["id"] for row in targets}
		for tid in frappe.get_all("Strategy Target", filters={"strategic_plan": self.draft_plan}, pluck="name"):
			self.assertNotIn(tid, tgt_ids)

	def test_selector_rows_expose_id_code_name(self):
		rows = get_active_strategy_programs()
		self.assertTrue(rows)
		row = rows[0]
		self.assertIn("id", row)
		self.assertIn("code", row)
		self.assertIn("name", row)
