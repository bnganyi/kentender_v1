# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""BX5 — Budget control smoke tests for DIA (mini-PRD §15).

Run:
  bench --site <site> run-tests --app kentender_budget --module kentender_budget.tests.test_dia_budget_control_bx5
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_budget.api.dia_budget_control import (
	check_available_budget,
	create_reservation,
	get_active_reservation_for_source,
	get_available_budget,
	get_budget_line_context,
	list_reservations_for_budget_line,
	release_reservation,
)
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity


class TestDiaBudgetControlBX5(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_currency_kes()
		self.entity = ensure_procuring_entity("MOH_BX5", "Ministry BX5 Test")
		h = frappe.generate_hash(length=6)
		self.plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": f"Plan BX5 {h}",
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
				"program_title": f"P-BX5-{h}",
				"order_index": 1,
			}
		)
		self.program.insert(ignore_permissions=True)
		self.objective = frappe.get_doc(
			{
				"doctype": "Strategy Objective",
				"strategic_plan": self.plan.name,
				"program": self.program.name,
				"objective_title": f"O-BX5-{h}",
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
				"target_title": f"T-BX5-{h}",
				"order_index": 1,
				"measurement_type": "Numeric",
				"target_period_type": "Annual",
				"target_year": 2026,
				"target_value_numeric": 10,
				"target_unit": "Units",
			}
		)
		self.target.insert(ignore_permissions=True)
		self.sub = frappe.get_doc(
			{
				"doctype": "Sub Program",
				"program": self.program.name,
				"title": f"Sub-BX5-{h}",
			}
		)
		self.sub.insert(ignore_permissions=True)
		self.budget = frappe.get_doc(
			{
				"doctype": "Budget",
				"budget_name": f"BUD-BX5-{h}",
				"procuring_entity": self.entity,
				"fiscal_year": 2026,
				"strategic_plan": self.plan.name,
				"currency": "KES",
				"version_no": 1,
				"is_current_version": 1,
				"order_index": 0,
			}
		)
		self.budget.insert(ignore_permissions=True)
		self.bl = frappe.get_doc(
			{
				"doctype": "Budget Line",
				"budget_line_code": f"BL-BX5-{h}",
				"budget_line_name": "BX5 Test Line",
				"budget": self.budget.name,
				"procuring_entity": self.entity,
				"fiscal_year": 2026,
				"amount_allocated": 1000,
				"amount_reserved": 0,
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
		self.bl.insert(ignore_permissions=True)

	def test_get_budget_line_context_linkage(self):
		ctx = get_budget_line_context(self.bl.name)
		self.assertTrue(ctx.get("ok"))
		data = ctx["data"]
		self.assertEqual(data["budget"], self.budget.name)
		self.assertEqual(data["procuring_entity"], self.entity)
		self.assertEqual(data["strategic_plan"], self.plan.name)
		self.assertEqual(data["program"], self.program.name)
		self.assertEqual(flt(data["amount_available"]), 1000.0)

	def test_check_available_budget(self):
		ok = check_available_budget(self.bl.name, 500)
		self.assertTrue(ok["ok"])
		self.assertEqual(flt(ok["data"]["amount_available"]), 1000.0)
		bad = check_available_budget(self.bl.name, 2000)
		self.assertTrue(bad["ok"])
		self.assertFalse(bad["data"]["is_sufficient"])
		self.assertGreater(flt(bad["data"]["shortfall"]), 0)

	def test_create_and_release_restores_available(self):
		before = get_available_budget(self.bl.name)["data"]["amount_available"]
		out = create_reservation(
			self.bl.name,
			"Demand",
			"DIA-TEST-001",
			400,
			actor="Administrator",
		)
		self.assertTrue(out.get("ok"))
		self.assertTrue(out["data"].get("reservation_id"))
		after = get_available_budget(self.bl.name)["data"]["amount_available"]
		self.assertAlmostEqual(flt(after), before - 400, places=2)
		release = release_reservation(
			out["data"]["reservation_id"], reason="Test release", actor="Administrator"
		)
		self.assertTrue(release.get("ok"))
		final = get_available_budget(self.bl.name)["data"]["amount_available"]
		self.assertAlmostEqual(flt(final), before, places=2)

	def test_cannot_reserve_beyond_allocated(self):
		out = create_reservation(
			self.bl.name,
			"Demand",
			"DIA-TEST-002",
			2000,
			actor="Administrator",
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "INSUFFICIENT_BUDGET")

	def test_get_available_budget_inactive_line(self):
		frappe.db.set_value("Budget Line", self.bl.name, "is_active", 0)
		try:
			out = get_available_budget(self.bl.name)
			self.assertFalse(out.get("ok"))
			self.assertEqual(out.get("error_code"), "BUDGET_LINE_INACTIVE")
		finally:
			frappe.db.set_value("Budget Line", self.bl.name, "is_active", 1)

	def test_get_budget_line_context_inactive_line(self):
		frappe.db.set_value("Budget Line", self.bl.name, "is_active", 0)
		try:
			out = get_budget_line_context(self.bl.name)
			self.assertFalse(out.get("ok"))
			self.assertEqual(out.get("error_code"), "BUDGET_LINE_INACTIVE")
		finally:
			frappe.db.set_value("Budget Line", self.bl.name, "is_active", 1)

	def test_get_active_reservation_for_source_and_list(self):
		src = f"DIA-BX5-SRC-{frappe.generate_hash(length=6)}"
		out = create_reservation(self.bl.name, "Demand", src, 100, actor="Administrator")
		self.assertTrue(out.get("ok"))
		res_id = out["data"]["reservation_id"]
		lu = get_active_reservation_for_source("Demand", src)
		self.assertTrue(lu.get("ok"))
		self.assertEqual(lu["data"]["reservation_id"], res_id)
		self.assertEqual(flt(lu["data"]["amount"]), 100.0)
		lst = list_reservations_for_budget_line(self.bl.name)
		self.assertTrue(lst.get("ok"))
		ids = {r["reservation_id"] for r in lst["data"]["reservations"]}
		self.assertIn(res_id, ids)
		release_reservation(res_id, reason="BX5 cleanup", actor="Administrator")

	def test_create_reservation_persists_source_business_id(self):
		"""Mirrors finance-approve behaviour: business id stored on Budget Reservation."""
		src = f"DIA-BX5-BIZ-{frappe.generate_hash(length=6)}"
		out = create_reservation(
			self.bl.name,
			"Demand",
			src,
			75,
			actor="Administrator",
			source_business_id="DIA-MOH-2026-9999",
		)
		self.assertTrue(out.get("ok"))
		res_id = out["data"]["reservation_id"]
		row = frappe.db.get_value(
			"Budget Reservation",
			{"reservation_id": res_id},
			["name", "source_business_id"],
			as_dict=True,
		)
		self.assertEqual(row.source_business_id, "DIA-MOH-2026-9999")
		release_reservation(res_id, reason="BX5 cleanup", actor="Administrator")

	def test_release_already_released_is_not_active(self):
		out = create_reservation(
			self.bl.name,
			"Demand",
			f"DIA-BX5-REL-{frappe.generate_hash(length=6)}",
			50,
			actor="Administrator",
		)
		self.assertTrue(out.get("ok"))
		res_id = out["data"]["reservation_id"]
		first = release_reservation(res_id, reason="First", actor="Administrator")
		self.assertTrue(first.get("ok"))
		again = release_reservation(res_id, reason="Second", actor="Administrator")
		self.assertFalse(again.get("ok"))
		self.assertEqual(again.get("error_code"), "RESERVATION_NOT_ACTIVE")
