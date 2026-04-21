# Copyright (c) 2026, Midas and contributors
# License: MIT. See LICENSE
"""B0.1 Budget + Budget Allocation validation (BUD / ALLOC rules).

Run:
  bench --site <site> run-tests --app kentender_budget --module kentender_budget.tests.test_budget_b01
"""

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity


class TestBudgetB01(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_currency_kes()
		self.entity = ensure_procuring_entity("MOH_B01", "Ministry B01 Test")
		h = frappe.generate_hash(length=6)
		self.plan_a = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": f"Plan A B01 {h}",
				"procuring_entity": self.entity,
				"start_year": 2026,
				"end_year": 2030,
				"status": "Draft",
			}
		)
		self.plan_a.insert(ignore_permissions=True)
		self.plan_b = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": f"Plan B B01 {h}",
				"procuring_entity": self.entity,
				"start_year": 2026,
				"end_year": 2030,
				"status": "Draft",
			}
		)
		self.plan_b.insert(ignore_permissions=True)
		self.program_a = frappe.get_doc(
			{
				"doctype": "Strategy Program",
				"strategic_plan": self.plan_a.name,
				"program_title": f"P-A-{h}",
				"order_index": 0,
			}
		)
		self.program_a.insert(ignore_permissions=True)
		self.program_b = frappe.get_doc(
			{
				"doctype": "Strategy Program",
				"strategic_plan": self.plan_b.name,
				"program_title": f"P-B-{h}",
				"order_index": 0,
			}
		)
		self.program_b.insert(ignore_permissions=True)

	def _budget_doc(self, **extra):
		kw = {
			"doctype": "Budget",
			"budget_name": f"BUD Test {frappe.generate_hash(length=6)}",
			"procuring_entity": self.entity,
			"fiscal_year": 2026,
			"strategic_plan": self.plan_a.name,
			"currency": "KES",
			"version_no": 1,
			"is_current_version": 1,
			"order_index": 0,
		}
		kw.update(extra)
		return frappe.get_doc(kw)

	def test_create_budget_and_allocation_ok(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		a = frappe.get_doc(
			{
				"doctype": "Budget Allocation",
				"budget": b.name,
				"program": self.program_a.name,
				"amount": 100,
				"order_index": 0,
			}
		)
		a.insert(ignore_permissions=True)
		self.assertEqual(a.strategic_plan, self.plan_a.name)
		self.assertEqual(a.procuring_entity, self.entity)

	def test_bud_009_duplicate_budget_fails(self):
		b1 = self._budget_doc()
		b1.insert(ignore_permissions=True)
		b2 = self._budget_doc(budget_name="Dup attempt")
		with self.assertRaises(ValidationError):
			b2.insert(ignore_permissions=True)

	def test_fiscal_year_below_range_fails(self):
		with self.assertRaises(ValidationError):
			self._budget_doc(fiscal_year=1999).insert(ignore_permissions=True)

	def test_fiscal_year_above_range_fails(self):
		with self.assertRaises(ValidationError):
			self._budget_doc(fiscal_year=2100).insert(ignore_permissions=True)

	def test_alloc_007_duplicate_program_fails(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Budget Allocation",
				"budget": b.name,
				"program": self.program_a.name,
				"amount": 10,
				"order_index": 0,
			}
		).insert(ignore_permissions=True)
		dup = frappe.get_doc(
			{
				"doctype": "Budget Allocation",
				"budget": b.name,
				"program": self.program_a.name,
				"amount": 20,
				"order_index": 1,
			}
		)
		with self.assertRaises(ValidationError):
			dup.insert(ignore_permissions=True)

	def test_alloc_004_cross_plan_program_fails(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		bad = frappe.get_doc(
			{
				"doctype": "Budget Allocation",
				"budget": b.name,
				"program": self.program_b.name,
				"amount": 50,
				"order_index": 0,
			}
		)
		with self.assertRaises(ValidationError):
			bad.insert(ignore_permissions=True)

	def test_alloc_008_ceiling_enforced(self):
		b = self._budget_doc(total_budget_amount=100)
		b.insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Budget Allocation",
				"budget": b.name,
				"program": self.program_a.name,
				"amount": 60,
				"order_index": 0,
			}
		).insert(ignore_permissions=True)
		# Second program on same plan — need another Strategy Program on plan_a
		p2 = frappe.get_doc(
			{
				"doctype": "Strategy Program",
				"strategic_plan": self.plan_a.name,
				"program_title": f"P-A2-{frappe.generate_hash(length=4)}",
				"order_index": 1,
			}
		)
		p2.insert(ignore_permissions=True)
		overflow = frappe.get_doc(
			{
				"doctype": "Budget Allocation",
				"budget": b.name,
				"program": p2.name,
				"amount": 50,
				"order_index": 1,
			}
		)
		with self.assertRaises(ValidationError):
			overflow.insert(ignore_permissions=True)
