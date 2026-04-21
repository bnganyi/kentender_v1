# Copyright (c) 2026, Midas and contributors
# License: MIT. See LICENSE
"""B5.3 Lock Budget and Budget Allocation after submission (8.Budget-Approval-Flow.md).

Run:
  bench --site <site> run-tests --app kentender_budget --module kentender_budget.tests.test_budget_b53
"""

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity

import kentender_budget.install
from kentender_budget.api.approval import reject_budget


class TestBudgetB53(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		kentender_budget.install.after_migrate()
		ensure_currency_kes()
		self.entity = ensure_procuring_entity("MOH_B53", "Ministry B53 Test")
		h = frappe.generate_hash(length=6)
		self.plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": f"Plan B53 {h}",
				"procuring_entity": self.entity,
				"start_year": 2026,
				"end_year": 2030,
				"status": "Draft",
			}
		)
		self.plan.insert(ignore_permissions=True)
		self.program = frappe.get_doc(
			{
				"doctype": "Strategy Program",
				"strategic_plan": self.plan.name,
				"program_title": f"P-B53-{h}",
				"order_index": 0,
			}
		)
		self.program.insert(ignore_permissions=True)
		self.sm_email = f"b53_sm_{h}@example.com"
		self._ensure_user(self.sm_email, "SM B53", ["Strategy Manager"])

	def _ensure_user(self, email: str, first: str, roles: list[str]) -> str:
		if frappe.db.exists("User", email):
			user = frappe.get_doc("User", email)
		else:
			user = frappe.new_doc("User")
			user.email = email
			user.first_name = first
			user.enabled = 1
			user.send_welcome_email = 0
			user.new_password = "Test-B53-Password!"
		user.roles = []
		for role in roles:
			user.append("roles", {"role": role})
		user.save(ignore_permissions=True)
		return user.name

	def _budget_doc(self, **extra):
		kw = {
			"doctype": "Budget",
			"budget_name": f"BUD B53 {frappe.generate_hash(length=6)}",
			"procuring_entity": self.entity,
			"fiscal_year": 2026,
			"strategic_plan": self.plan.name,
			"currency": "KES",
			"version_no": 1,
			"is_current_version": 1,
			"order_index": 0,
		}
		kw.update(extra)
		return frappe.get_doc(kw)

	def test_submitted_budget_content_locked_even_with_ignore_permissions(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		frappe.set_user(self.sm_email)
		b = frappe.get_doc("Budget", b.name)
		b.status = "Submitted"
		b.save()
		b.reload()
		b.budget_name = b.budget_name + " X"
		with self.assertRaises(ValidationError):
			b.save(ignore_permissions=True)

	def test_approved_budget_cannot_change_fields(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		frappe.set_user(self.sm_email)
		b = frappe.get_doc("Budget", b.name)
		b.status = "Submitted"
		b.save()
		frappe.set_user("Administrator")
		b = frappe.get_doc("Budget", b.name)
		b.status = "Approved"
		b.save()
		frappe.set_user(self.sm_email)
		b = frappe.get_doc("Budget", b.name)
		b.notes = "try to edit"
		with self.assertRaises(ValidationError):
			b.save(ignore_permissions=True)

	def test_allocation_save_blocked_when_budget_submitted(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		a = frappe.get_doc(
			{
				"doctype": "Budget Allocation",
				"budget": b.name,
				"program": self.program.name,
				"amount": 50,
				"order_index": 0,
			}
		)
		a.insert(ignore_permissions=True)
		frappe.set_user(self.sm_email)
		bb = frappe.get_doc("Budget", b.name)
		bb.status = "Submitted"
		bb.save()
		a = frappe.get_doc("Budget Allocation", a.name)
		a.amount = 75
		with self.assertRaises(ValidationError):
			a.save(ignore_permissions=True)

	def test_allocation_save_allowed_when_budget_rejected(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		a = frappe.get_doc(
			{
				"doctype": "Budget Allocation",
				"budget": b.name,
				"program": self.program.name,
				"amount": 50,
				"order_index": 0,
			}
		)
		a.insert(ignore_permissions=True)
		frappe.set_user(self.sm_email)
		bb = frappe.get_doc("Budget", b.name)
		bb.status = "Submitted"
		bb.save()
		frappe.set_user("Administrator")
		reject_budget(budget_name=b.name, rejection_reason="Revise allocations")
		frappe.set_user(self.sm_email)
		a = frappe.get_doc("Budget Allocation", a.name)
		a.amount = 120
		a.save()
		a.reload()
		self.assertEqual(flt(a.amount), 120)

	def test_allocation_delete_blocked_when_budget_submitted(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		a = frappe.get_doc(
			{
				"doctype": "Budget Allocation",
				"budget": b.name,
				"program": self.program.name,
				"amount": 50,
				"order_index": 0,
			}
		)
		a.insert(ignore_permissions=True)
		frappe.set_user(self.sm_email)
		bb = frappe.get_doc("Budget", b.name)
		bb.status = "Submitted"
		bb.save()
		with self.assertRaises(ValidationError):
			frappe.delete_doc("Budget Allocation", a.name, ignore_permissions=True)
