# Copyright (c) 2026, Midas and contributors
# License: MIT. See LICENSE
"""B5.2 Budget role-based approval permissions (8.Budget-Approval-Flow.md).

Run:
  bench --site <site> run-tests --app kentender_budget --module kentender_budget.tests.test_budget_b52
"""

import frappe
from frappe.exceptions import PermissionError, ValidationError
from frappe.tests import IntegrationTestCase

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity

import kentender_budget.install


class TestBudgetB52(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		kentender_budget.install.after_migrate()
		ensure_currency_kes()
		self.entity = ensure_procuring_entity("MOH_B52", "Ministry B52 Test")
		h = frappe.generate_hash(length=6)
		self.plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": f"Plan B52 {h}",
				"procuring_entity": self.entity,
				"start_year": 2026,
				"end_year": 2030,
				"status": "Draft",
			}
		)
		self.plan.insert(ignore_permissions=True)
		self.sm_email = f"b52_sm_{h}@example.com"
		self.pa_email = f"b52_pa_{h}@example.com"
		self._ensure_user(self.sm_email, "SM B52", ["Strategy Manager"])
		self._ensure_user(self.pa_email, "PA B52", ["Planning Authority"])

	def _ensure_user(self, email: str, first: str, roles: list[str]) -> str:
		if frappe.db.exists("User", email):
			user = frappe.get_doc("User", email)
		else:
			user = frappe.new_doc("User")
			user.email = email
			user.first_name = first
			user.enabled = 1
			user.send_welcome_email = 0
			user.new_password = "Test-B52-Password!"
		user.roles = []
		for role in roles:
			user.append("roles", {"role": role})
		user.save(ignore_permissions=True)
		return user.name

	def _budget_doc(self, **extra):
		kw = {
			"doctype": "Budget",
			"budget_name": f"BUD B52 {frappe.generate_hash(length=6)}",
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

	def test_strategy_manager_can_submit(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		frappe.set_user(self.sm_email)
		b = frappe.get_doc("Budget", b.name)
		b.status = "Submitted"
		b.save()
		self.assertEqual(b.status, "Submitted")

	def test_planning_authority_cannot_submit(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		frappe.set_user(self.pa_email)
		b = frappe.get_doc("Budget", b.name)
		b.status = "Submitted"
		with self.assertRaises(PermissionError):
			b.save()

	def test_planning_authority_can_approve(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		frappe.set_user(self.sm_email)
		b = frappe.get_doc("Budget", b.name)
		b.status = "Submitted"
		b.save()
		frappe.set_user(self.pa_email)
		b = frappe.get_doc("Budget", b.name)
		b.status = "Approved"
		b.save()
		self.assertEqual(b.status, "Approved")

	def test_strategy_manager_cannot_approve(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		frappe.set_user(self.sm_email)
		b = frappe.get_doc("Budget", b.name)
		b.status = "Submitted"
		b.save()
		b.reload()
		b.status = "Approved"
		with self.assertRaises(PermissionError):
			b.save()

	def test_planning_authority_cannot_create_budget(self):
		frappe.set_user(self.pa_email)
		b = self._budget_doc()
		with self.assertRaises(PermissionError):
			b.insert()

	def test_planning_authority_cannot_write_draft_budget(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		frappe.set_user(self.pa_email)
		b = frappe.get_doc("Budget", b.name)
		b.budget_name = b.budget_name + " X"
		with self.assertRaises(PermissionError):
			b.save()

	def test_planning_authority_cannot_edit_submitted_fields_except_approve(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		frappe.set_user(self.sm_email)
		b = frappe.get_doc("Budget", b.name)
		b.status = "Submitted"
		b.save()
		frappe.set_user(self.pa_email)
		b = frappe.get_doc("Budget", b.name)
		b.budget_name = b.budget_name + " Z"
		with self.assertRaises(ValidationError):
			b.save()

	def test_administrator_user_bypasses_transition_roles(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		b.reload()
		b.status = "Submitted"
		b.save()
		b.reload()
		b.status = "Approved"
		b.save()
		self.assertEqual(b.status, "Approved")
