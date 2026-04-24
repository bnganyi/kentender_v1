# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""Demand lifecycle ↔ Budget Line reservation (finance approve / cancel).

Lives under ``kentender_budget`` tests so it runs with the budget suite. If the
site has no ``Demand`` DocType (procurement app not migrated), tests **skip**
with a clear message. When Demand exists, they exercise
``kentender_procurement.demand_intake.api.lifecycle`` end-to-end.

Run:
  bench --site <site> run-tests --app kentender_budget \\
    --module kentender_budget.tests.test_demand_lifecycle_budget
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt, today

from kentender_core.seeds._common import (
	ensure_currency_kes,
	ensure_department,
	ensure_procuring_entity,
	upsert_seed_user,
)
from kentender_procurement.demand_intake.api.lifecycle import (
	approve_finance,
	approve_hod,
	cancel_demand,
	submit_demand,
)


class TestDemandLifecycleBudget(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Demand"):
			self._skipped_no_demand_doctype = True
			return
		self._skipped_no_demand_doctype = False
		ensure_currency_kes()
		h = frappe.generate_hash(length=6)
		self.entity = ensure_procuring_entity(f"MOH_DLCB_{h}", f"Entity DLCB {h}")
		self.dept = ensure_department(f"Dept DLCB {h}", self.entity)
		self.plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": f"Plan DLCB {h}",
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
				"program_title": f"P-DLCB-{h}",
				"order_index": 1,
			}
		)
		self.program.insert(ignore_permissions=True)
		self.objective = frappe.get_doc(
			{
				"doctype": "Strategy Objective",
				"strategic_plan": self.plan.name,
				"program": self.program.name,
				"objective_title": f"O-DLCB-{h}",
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
				"target_title": f"T-DLCB-{h}",
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
				"title": f"Sub-DLCB-{h}",
			}
		)
		self.sub.insert(ignore_permissions=True)
		self.budget = frappe.get_doc(
			{
				"doctype": "Budget",
				"budget_name": f"BUD-DLCB-{h}",
				"procuring_entity": self.entity,
				"fiscal_year": 2026,
				"strategic_plan": self.plan.name,
				"currency": "KES",
				"version_no": 1,
				"is_current_version": 1,
				"order_index": 0,
				"status": "Draft",
			}
		)
		self.budget.insert(ignore_permissions=True)
		self.bl = frappe.get_doc(
			{
				"doctype": "Budget Line",
				"budget_line_code": f"BL-DLCB-{h}",
				"budget_line_name": "DLCB Test Line",
				"budget": self.budget.name,
				"procuring_entity": self.entity,
				"fiscal_year": 2026,
				"amount_allocated": 5000,
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
		self._req_email = f"req_dlcb_{h}@test.local"
		self._hod_email = f"hod_dlcb_{h}@test.local"
		self._fin_email = f"fin_dlcb_{h}@test.local"
		upsert_seed_user(
			self._req_email, "REQ DLCB", "Requisitioner", entity_name=self.entity, department_docname=self.dept
		)
		upsert_seed_user(
			self._hod_email, "HOD DLCB", "Department Approver", entity_name=self.entity, department_docname=self.dept
		)
		upsert_seed_user(
			self._fin_email, "FIN DLCB", "Finance Reviewer", entity_name=self.entity, department_docname=self.dept
		)
		self.demand_name = None

	def tearDown(self):
		frappe.set_user("Administrator")
		if getattr(self, "_skipped_no_demand_doctype", False):
			return
		if self.demand_name and frappe.db.exists("Demand", self.demand_name):
			frappe.delete_doc("Demand", self.demand_name, force=True, ignore_permissions=True)
		for row in frappe.get_all("Budget Reservation", filters={"budget_line": self.bl.name}, pluck="name"):
			frappe.delete_doc("Budget Reservation", row, force=True, ignore_permissions=True)
		if frappe.db.exists("Budget Line", self.bl.name):
			frappe.flags.budget_line_force_delete = True
			try:
				frappe.delete_doc("Budget Line", self.bl.name, force=True, ignore_permissions=True)
			finally:
				frappe.flags.budget_line_force_delete = False
		if frappe.db.exists("Budget", self.budget.name):
			frappe.delete_doc("Budget", self.budget.name, force=True, ignore_permissions=True)
		for d, n in (
			("Sub Program", self.sub.name),
			("Strategy Target", self.target.name),
			("Strategy Objective", self.objective.name),
			("Strategy Program", self.program.name),
			("Strategic Plan", self.plan.name),
			("Procuring Department", self.dept),
		):
			if frappe.db.exists(d, n):
				frappe.delete_doc(d, n, force=True, ignore_permissions=True)
		for u in (getattr(self, "_fin_email", None), getattr(self, "_hod_email", None), getattr(self, "_req_email", None)):
			if u and frappe.db.exists("User", u):
				frappe.delete_doc("User", u, force=True, ignore_permissions=True)
		if frappe.db.exists("Procuring Entity", self.entity):
			frappe.delete_doc("Procuring Entity", self.entity, force=True, ignore_permissions=True)

	def _make_demand(self) -> str:
		d = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": f"DLCB demand {frappe.generate_hash(length=4)}",
				"specification_summary": "DLCB test demand — requested goods for budget reservation flow.",
				"delivery_location": "Nairobi",
				"requested_by": self._req_email,
				"procuring_entity": self.entity,
				"requesting_department": self.dept,
				"request_date": today(),
				"required_by_date": today(),
				"budget_line": self.bl.name,
				"items": [
					{
						"item_description": "Test item",
						"category": "Cat",
						"uom": "ea",
						"quantity": 2,
						"estimated_unit_cost": 150,
					}
				],
			}
		)
		d.insert(ignore_permissions=True)
		return d.name

	def test_finance_approve_reserves_cancel_releases_and_sets_source_business_id(self):
		if getattr(self, "_skipped_no_demand_doctype", False):
			self.skipTest("Demand DocType not on site; install kentender_procurement and bench migrate.")
		self.demand_name = self._make_demand()
		frappe.set_user(self._req_email)
		submit_demand(self.demand_name)
		frappe.set_user(self._hod_email)
		approve_hod(self.demand_name)
		did = frappe.db.get_value("Demand", self.demand_name, "demand_id")
		self.assertTrue(did)
		frappe.set_user(self._fin_email)
		approve_finance(self.demand_name)
		d = frappe.get_doc("Demand", self.demand_name)
		self.assertEqual(d.status, "Approved")
		self.assertEqual(d.reservation_status, "Reserved")
		self.assertTrue(d.reservation_reference)
		bl = frappe.get_doc("Budget Line", self.bl.name)
		self.assertAlmostEqual(flt(bl.amount_reserved), 300.0, places=2)
		res_name = frappe.db.get_value(
			"Budget Reservation",
			{"source_doctype": "Demand", "source_docname": self.demand_name, "status": "Active"},
			"name",
		)
		self.assertTrue(res_name)
		biz = frappe.db.get_value("Budget Reservation", res_name, "source_business_id")
		self.assertEqual(biz, did)
		frappe.set_user(self._req_email)
		cancel_demand(self.demand_name, cancellation_reason="Test cancel budget release")
		bl.reload()
		self.assertAlmostEqual(flt(bl.amount_reserved), 0.0, places=2)
		d = frappe.get_doc("Demand", self.demand_name)
		self.assertEqual(d.status, "Cancelled")
		self.assertEqual(d.reservation_status, "Released")

	def test_cancel_approved_releases_via_lookup_when_reference_cleared(self):
		"""If reservation_reference is missing but an active reservation exists, cancel still releases."""
		if getattr(self, "_skipped_no_demand_doctype", False):
			self.skipTest("Demand DocType not on site; install kentender_procurement and bench migrate.")
		self.demand_name = self._make_demand()
		frappe.set_user(self._req_email)
		submit_demand(self.demand_name)
		frappe.set_user(self._hod_email)
		approve_hod(self.demand_name)
		frappe.set_user(self._fin_email)
		approve_finance(self.demand_name)
		frappe.db.set_value("Demand", self.demand_name, "reservation_reference", None)
		frappe.set_user(self._req_email)
		cancel_demand(self.demand_name, cancellation_reason="Cancel after ref cleared")
		bl = frappe.get_doc("Budget Line", self.bl.name)
		self.assertAlmostEqual(flt(bl.amount_reserved), 0.0, places=2)
