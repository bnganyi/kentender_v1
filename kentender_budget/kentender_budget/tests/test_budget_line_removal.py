# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""Budget Line soft remove and hard delete governance (System Direction).

Run:
  bench --site <site> run-tests --app kentender_budget --module kentender_budget.tests.test_budget_line_removal
"""

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase
from frappe.utils import flt, today

from kentender_budget.api.builder import delete_budget_line_permanent, remove_budget_line
from kentender_budget.api.dia_budget_control import create_reservation, release_reservation
from kentender_core.seeds._common import ensure_currency_kes, ensure_department, ensure_procuring_entity


class TestBudgetLineRemoval(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_currency_kes()
		h = frappe.generate_hash(length=6)
		self.entity = ensure_procuring_entity(f"MOH_BLRM_{h}", f"Entity BLRM {h}")
		self.dept = ensure_department(f"Dept BLRM {h}", self.entity)
		self.plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": f"Plan BLRM {h}",
				"procuring_entity": self.entity,
				"start_year": 2026,
				"end_year": 2030,
				"status": "Draft",
				"version_no": 1,
				"is_current_version": 1,
			}
		)
		self.plan.insert(ignore_permissions=True)
		self.program = frappe.get_doc(
			{
				"doctype": "Strategy Program",
				"strategic_plan": self.plan.name,
				"program_title": f"P-BLRM-{h}",
				"order_index": 1,
			}
		)
		self.program.insert(ignore_permissions=True)
		self.objective = frappe.get_doc(
			{
				"doctype": "Strategy Objective",
				"strategic_plan": self.plan.name,
				"program": self.program.name,
				"objective_title": f"O-BLRM-{h}",
				"order_index": 1,
			}
		)
		self.objective.insert(ignore_permissions=True)
		self.target = frappe.get_doc(
			{
				"doctype": "Strategy Target",
				"strategic_plan": self.plan.name,
				"program": self.program.name,
				"objective": self.objective.name,
				"target_title": f"T-BLRM-{h}",
				"order_index": 1,
				"measurement_type": "Numeric",
				"target_period_type": "Annual",
				"target_year": 2026,
				"target_value_numeric": 1,
				"target_unit": "Units",
			}
		)
		self.target.insert(ignore_permissions=True)
		self.sub = frappe.get_doc(
			{
				"doctype": "Sub Program",
				"program": self.program.name,
				"title": f"Sub-BLRM-{h}",
			}
		)
		self.sub.insert(ignore_permissions=True)
		self.budget = frappe.get_doc(
			{
				"doctype": "Budget",
				"budget_name": f"BUD-BLRM-{h}",
				"procuring_entity": self.entity,
				"fiscal_year": 2026,
				"strategic_plan": self.plan.name,
				"currency": "KES",
				"total_budget_amount": 500_000,
				"version_no": 1,
				"is_current_version": 1,
				"order_index": 0,
				"status": "Draft",
			}
		)
		self.budget.insert(ignore_permissions=True)
		self._demand_name = None

	def _bl_name(self, attr: str) -> str | None:
		v = getattr(self, attr, None)
		if not v:
			return None
		if isinstance(v, str):
			return v
		return v.name

	def tearDown(self):
		frappe.set_user("Administrator")
		if self._demand_name and frappe.db.exists("Demand", self._demand_name):
			frappe.delete_doc("Demand", self._demand_name, force=True, ignore_permissions=True)
		for attr in ("bl_zero", "bl_funded", "bl_delete_alloc"):
			n = self._bl_name(attr)
			if not n or not frappe.db.exists("Budget Line", n):
				continue
			for res in frappe.get_all("Budget Reservation", filters={"budget_line": n}, pluck="name"):
				frappe.delete_doc("Budget Reservation", res, force=True, ignore_permissions=True)
			try:
				frappe.flags.budget_line_force_delete = True
				frappe.delete_doc("Budget Line", n, force=True, ignore_permissions=True)
			finally:
				frappe.flags.budget_line_force_delete = False
		if getattr(self, "budget", None) and frappe.db.exists("Budget", self.budget.name):
			frappe.delete_doc("Budget", self.budget.name, force=True, ignore_permissions=True)
		for dt, name in [
			("Sub Program", self.sub.name if getattr(self, "sub", None) else None),
			("Strategy Target", self.target.name if getattr(self, "target", None) else None),
			("Strategy Objective", self.objective.name if getattr(self, "objective", None) else None),
			("Strategy Program", self.program.name if getattr(self, "program", None) else None),
			("Strategic Plan", self.plan.name if getattr(self, "plan", None) else None),
		]:
			if name and frappe.db.exists(dt, name):
				frappe.delete_doc(dt, name, force=True, ignore_permissions=True)

	def _make_line(self, code_suffix: str, allocated: float, reserved: float = 0):
		h = frappe.generate_hash(length=4)
		bl = frappe.get_doc(
			{
				"doctype": "Budget Line",
				"budget_line_code": f"BL-BLRM-{code_suffix}-{h}",
				"budget_line_name": f"Line {code_suffix}",
				"budget": self.budget.name,
				"procuring_entity": self.entity,
				"fiscal_year": 2026,
				"amount_allocated": allocated,
				"amount_reserved": reserved,
				"amount_consumed": 0,
				"currency": "KES",
				"strategic_plan": self.plan.name,
				"program": self.program.name,
				"sub_program": self.sub.name,
				"output_indicator": self.objective.name,
				"performance_target": self.target.name,
				"is_active": 1,
			}
		)
		bl.insert(ignore_permissions=True)
		return bl

	def test_soft_remove_zero_balance_ok(self):
		self.bl_zero = self._make_line("Z", 0, 0)
		remove_budget_line(self.budget.name, self.bl_zero.name, lines_filter="all")
		bl = frappe.get_doc("Budget Line", self.bl_zero.name)
		self.assertEqual(int(bl.is_active or 0), 0)
		self.assertTrue(bl.removed_at)
		self.assertEqual(bl.removed_by, "Administrator")

	def test_soft_remove_idempotent_when_already_inactive(self):
		self.bl_zero = self._make_line("I", 0, 0)
		remove_budget_line(self.budget.name, self.bl_zero.name, lines_filter="all")
		remove_budget_line(self.budget.name, self.bl_zero.name, lines_filter="all")
		bl = frappe.get_doc("Budget Line", self.bl_zero.name)
		self.assertEqual(int(bl.is_active or 0), 0)

	def test_soft_remove_blocked_when_active_reservation(self):
		self.bl_funded = self._make_line("R", 1000, 0)
		res_id = None
		try:
			out = create_reservation(
				self.bl_funded.name,
				"Demand",
				"DIA-BLRM-RES-1",
				50,
				actor="Administrator",
			)
			self.assertTrue(out.get("ok"))
			res_id = out["data"]["reservation_id"]
			with self.assertRaises(ValidationError):
				remove_budget_line(self.budget.name, self.bl_funded.name, lines_filter="all")
		finally:
			if res_id:
				release_reservation(res_id, reason="Test cleanup", actor="Administrator")

	def test_soft_remove_blocked_when_submitted_budget(self):
		self.bl_zero = self._make_line("S", 0, 0)
		frappe.db.set_value("Budget", self.budget.name, "status", "Submitted")
		try:
			with self.assertRaises(ValidationError):
				remove_budget_line(self.budget.name, self.bl_zero.name, lines_filter="all")
		finally:
			frappe.db.set_value("Budget", self.budget.name, "status", "Draft")

	def test_soft_remove_blocked_when_demand_linked(self):
		if not frappe.db.has_table("Demand"):
			return
		self.bl_zero = self._make_line("D", 0, 0)
		d = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": "Demand BLRM link",
				"procuring_entity": self.entity,
				"requesting_department": self.dept,
				"requested_by": "Administrator",
				"request_date": today(),
				"required_by_date": today(),
				"priority_level": "Normal",
				"demand_type": "Planned",
				"requisition_type": "Goods",
				"budget": self.budget.name,
				"budget_line": self.bl_zero.name,
				"strategic_plan": self.plan.name,
				"program": self.program.name,
				"sub_program": self.sub.name,
				"output_indicator": self.objective.name,
				"performance_target": self.target.name,
				"total_amount": 0,
				"status": "Draft",
				"planning_status": "Not Planned",
				"reservation_status": "None",
				"is_exception": 0,
				"specification_summary": "Test spec",
				"delivery_location": "HQ",
				"created_by": "Administrator",
			}
		)
		d.insert(ignore_permissions=True)
		self._demand_name = d.name
		with self.assertRaises(ValidationError):
			remove_budget_line(self.budget.name, self.bl_zero.name, lines_filter="all")

	def test_hard_delete_active_zero_ok(self):
		self.bl_zero = self._make_line("H0", 0, 0)
		delete_budget_line_permanent(self.budget.name, self.bl_zero.name, lines_filter="all")
		self.assertFalse(frappe.db.exists("Budget Line", self.bl_zero.name))
		self.bl_zero = None

	def test_hard_delete_active_with_allocation_blocked(self):
		self.bl_delete_alloc = self._make_line("H1", 500, 0)
		with self.assertRaises(ValidationError):
			delete_budget_line_permanent(self.budget.name, self.bl_delete_alloc.name, lines_filter="all")

	def test_hard_delete_blocked_after_released_reservation_row_exists(self):
		self.bl_funded = self._make_line("HR", 1000, 0)
		out = create_reservation(
			self.bl_funded.name,
			"Demand",
			"DIA-BLRM-REL-1",
			10,
			actor="Administrator",
		)
		self.assertTrue(out.get("ok"))
		release_reservation(out["data"]["reservation_id"], reason="Test", actor="Administrator")
		bl = frappe.get_doc("Budget Line", self.bl_funded.name)
		self.assertLessEqual(flt(bl.amount_reserved), 1e-6)
		with self.assertRaises(ValidationError):
			delete_budget_line_permanent(self.budget.name, self.bl_funded.name, lines_filter="all")

	def test_soft_remove_then_hard_delete_inactive_ok(self):
		self.bl_zero = self._make_line("SD", 0, 0)
		remove_budget_line(self.budget.name, self.bl_zero.name, lines_filter="all")
		delete_budget_line_permanent(self.budget.name, self.bl_zero.name, lines_filter="all")
		self.assertFalse(frappe.db.exists("Budget Line", self.bl_zero.name))
		self.bl_zero = None

	def test_desk_delete_blocked_without_force_flag(self):
		self.bl_zero = self._make_line("TR", 0, 0)
		with self.assertRaises(ValidationError):
			frappe.delete_doc("Budget Line", self.bl_zero.name, ignore_permissions=True)
