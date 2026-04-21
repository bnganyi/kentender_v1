# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""B5.9–B5.11 Rejection flow (8.a.Budget-Approval-Flow - 2.md).

Run:
  bench --site <site> run-tests --app kentender_budget --module kentender_budget.tests.test_budget_rejection
"""

import frappe
from frappe.exceptions import PermissionError, ValidationError
from frappe.tests import IntegrationTestCase

from kentender_budget.api.approval import reject_budget, submit_budget
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity

import kentender_budget.install


class TestBudgetRejection(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		kentender_budget.install.after_migrate()
		ensure_currency_kes()
		self.entity = ensure_procuring_entity("MOH_REJ", "Ministry REJ Test")
		h = frappe.generate_hash(length=6)
		self.plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": f"Plan REJ {h}",
				"procuring_entity": self.entity,
				"start_year": 2026,
				"end_year": 2030,
				"status": "Draft",
			}
		)
		self.plan.insert(ignore_permissions=True)
		self.sm_email = f"rej_sm_{h}@example.com"
		self.pa_email = f"rej_pa_{h}@example.com"
		self._ensure_user(self.sm_email, "SM REJ", ["Strategy Manager"])
		self._ensure_user(self.pa_email, "PA REJ", ["Planning Authority"])

	def _ensure_user(self, email: str, first: str, roles: list[str]) -> str:
		if frappe.db.exists("User", email):
			user = frappe.get_doc("User", email)
		else:
			user = frappe.new_doc("User")
			user.email = email
			user.first_name = first
			user.enabled = 1
			user.send_welcome_email = 0
			user.new_password = "Test-REJ-Password!"
		user.roles = []
		for role in roles:
			user.append("roles", {"role": role})
		user.save(ignore_permissions=True)
		return user.name

	def _budget_doc(self, **extra):
		kw = {
			"doctype": "Budget",
			"budget_name": f"BUD REJ {frappe.generate_hash(length=6)}",
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

	def test_reject_budget_sets_metadata(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		frappe.set_user(self.sm_email)
		b = frappe.get_doc("Budget", b.name)
		b.status = "Submitted"
		b.save()
		frappe.set_user(self.pa_email)
		out = reject_budget(budget_name=b.name, rejection_reason="  Need more detail  ")
		self.assertEqual(out["status"], "Rejected")
		b = frappe.get_doc("Budget", b.name)
		self.assertEqual(b.status, "Rejected")
		self.assertEqual(b.rejection_reason.strip(), "Need more detail")
		self.assertEqual(b.rejected_by, self.pa_email)
		self.assertTrue(b.rejected_at)

	def test_reject_budget_requires_reason(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		frappe.set_user(self.sm_email)
		b = frappe.get_doc("Budget", b.name)
		b.status = "Submitted"
		b.save()
		frappe.set_user(self.pa_email)
		with self.assertRaises(ValidationError):
			reject_budget(budget_name=b.name, rejection_reason="   ")

	def test_strategy_manager_resubmits_rejected(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		frappe.set_user(self.sm_email)
		b = frappe.get_doc("Budget", b.name)
		b.status = "Submitted"
		b.save()
		frappe.set_user(self.pa_email)
		reject_budget(budget_name=b.name, rejection_reason="Fix totals")
		frappe.set_user(self.sm_email)
		out = submit_budget(budget_name=b.name)
		self.assertEqual(out["status"], "Submitted")
		b = frappe.get_doc("Budget", b.name)
		self.assertEqual(b.status, "Submitted")

	def test_strategy_manager_cannot_reject(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		frappe.set_user(self.sm_email)
		b = frappe.get_doc("Budget", b.name)
		b.status = "Submitted"
		b.save()
		with self.assertRaises(PermissionError):
			reject_budget(budget_name=b.name, rejection_reason="no")
