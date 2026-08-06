# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""Planning readiness — finance-approved demands before planning handoff."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.demand_intake.services.readiness import (
	assert_planning_ready,
	evaluate_planning_panel_checks,
	evaluate_planning_readiness,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy


class TestDemandPlanningReadiness(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.seed = upsert_works_master_strategy_hierarchy()

	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Demand"):
			self._skipped_no_demand = True
			return
		self._skipped_no_demand = False
		ensure_currency_kes()
		self._demand_names: list[str] = []

	def tearDown(self):
		if getattr(self, "_skipped_no_demand", False):
			return
		frappe.set_user("Administrator")
		for name in getattr(self, "_demand_names", []):
			if frappe.db.exists("Demand", name):
				frappe.delete_doc("Demand", name, force=True, ignore_permissions=True)

	def _seed_budget_line(self):
		bl_name = frappe.db.get_value(
			"Budget Line", {"generated_reference": "MOH-BL-0001"}, "name"
		) or (self.seed.get("downstream") or {}).get("linked", {}).get("budget_line")
		if not bl_name:
			return None, None, None
		ctx = get_budget_line_context(bl_name)
		if not ctx.get("ok"):
			# Fallback: organisational owner on Budget Line / Budget
			ent = self.seed.get("procuring_entity")
			if not ent:
				return None, None, None
			dept = ensure_department(f"Dept Plan {frappe.generate_hash(length=4)}", ent)
			return bl_name, ent, dept
		ent = (ctx.get("data") or {}).get("procuring_entity") or self.seed.get("procuring_entity")
		dept = ensure_department(f"Dept Plan {frappe.generate_hash(length=4)}", ent)
		return bl_name, ent, dept

	def _mk_demand(self, bl_name, entity, dept, **kwargs):
		if "strategy_target" not in kwargs:
			kwargs["strategy_target"] = self.seed["target"]
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": kwargs.pop("title", None) or f"Plan {frappe.generate_hash(length=4)}",
				"procuring_entity": entity,
				"requesting_department": dept,
				"request_date": today(),
				"required_by_date": today(),
				"requisition_type": "Goods",
				"priority_level": "Normal",
				"demand_type": "Planned",
				"specification_summary": "Scope",
				"budget_line": bl_name,
				"items": [
					{
						"item_description": "Line",
						"category": "c",
						"uom": "ea",
						"quantity": 1,
						"estimated_unit_cost": 100,
					}
				],
				**kwargs,
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		self._demand_names.append(doc.name)
		return doc

	def test_approved_without_reservation_not_planning_ready(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("Seed budget line BL-MOH-2026-001 not present")
		doc = self._mk_demand(bl_name, entity, dept)
		frappe.db.set_value(
			"Demand",
			doc.name,
			{"status": "Approved", "reservation_status": "None"},
			update_modified=False,
		)
		doc.reload()
		out = evaluate_planning_readiness(doc)
		self.assertFalse(out["ready"])
		with self.assertRaises(frappe.ValidationError):
			assert_planning_ready(doc)

	def test_planning_panel_checks_maps_owners(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("Seed budget line BL-MOH-2026-001 not present")
		doc = self._mk_demand(
			bl_name,
			entity,
			dept,
			hod_approved_by="Administrator",
			hod_approved_at=today(),
			finance_approved_by="Administrator",
			finance_approved_at=today(),
		)
		frappe.db.set_value(
			"Demand",
			doc.name,
			{
				"status": "Approved",
				"reservation_status": "Reserved",
				"reservation_reference": "RES-PANEL",
			},
			update_modified=False,
		)
		doc.reload()
		out = evaluate_planning_panel_checks(doc)
		self.assertIn("checks", out)
		ids = {row["id"] for row in out["checks"]}
		self.assertIn("budget_reservation", ids)
		self.assertIn("planning_handoff", ids)

	def test_approved_with_reservation_can_be_planning_ready(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		bl_name, entity, dept = self._seed_budget_line()
		if not bl_name:
			self.skipTest("Seed budget line BL-MOH-2026-001 not present")
		doc = self._mk_demand(
			bl_name,
			entity,
			dept,
			hod_approved_by="Administrator",
			hod_approved_at=today(),
			finance_approved_by="Administrator",
			finance_approved_at=today(),
		)
		frappe.db.set_value(
			"Demand",
			doc.name,
			{
				"status": "Approved",
				"reservation_status": "Reserved",
				"reservation_reference": "RES-TEST",
			},
			update_modified=False,
		)
		doc.reload()
		out = evaluate_planning_readiness(doc)
		self.assertTrue(out["ready"])
		assert_planning_ready(doc)
