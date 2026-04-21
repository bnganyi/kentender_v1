# Copyright (c) 2026, Midas and contributors
# License: MIT. See LICENSE
"""B5.1 Budget status model and transitions (8.Budget-Approval-Flow.md).

Run:
  bench --site <site> run-tests --app kentender_budget --module kentender_budget.tests.test_budget_b51
"""

import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity


class TestBudgetB51(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_currency_kes()
		self.entity = ensure_procuring_entity("MOH_B51", "Ministry B51 Test")
		h = frappe.generate_hash(length=6)
		self.plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": f"Plan B51 {h}",
				"procuring_entity": self.entity,
				"start_year": 2026,
				"end_year": 2030,
				"status": "Draft",
			}
		)
		self.plan.insert(ignore_permissions=True)

	def _budget_doc(self, **extra):
		kw = {
			"doctype": "Budget",
			"budget_name": f"BUD B51 {frappe.generate_hash(length=6)}",
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

	def test_new_budget_must_be_draft(self):
		with self.assertRaises(ValidationError):
			self._budget_doc(status="Submitted").insert(ignore_permissions=True)

	def test_transition_draft_to_submitted(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		b.reload()
		b.status = "Submitted"
		b.save(ignore_permissions=True)
		self.assertEqual(b.status, "Submitted")

	def test_transition_submitted_to_approved(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		b.reload()
		b.status = "Submitted"
		b.save(ignore_permissions=True)
		b.reload()
		b.status = "Approved"
		b.save(ignore_permissions=True)
		self.assertEqual(b.status, "Approved")

	def test_transition_submitted_to_rejected(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		b.reload()
		b.status = "Submitted"
		b.save(ignore_permissions=True)
		b.reload()
		b.status = "Rejected"
		b.rejection_reason = "Insufficient detail"
		b.rejected_by = frappe.session.user
		b.rejected_at = frappe.utils.now_datetime()
		b.save(ignore_permissions=True)
		self.assertEqual(b.status, "Rejected")

	def test_transition_rejected_to_submitted(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		b.reload()
		b.status = "Submitted"
		b.save(ignore_permissions=True)
		b.reload()
		b.status = "Rejected"
		b.rejection_reason = "x"
		b.rejected_by = frappe.session.user
		b.rejected_at = frappe.utils.now_datetime()
		b.save(ignore_permissions=True)
		b.reload()
		b.status = "Submitted"
		b.save(ignore_permissions=True)
		self.assertEqual(b.status, "Submitted")

	def test_invalid_transition_draft_to_approved(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		b.reload()
		b.status = "Approved"
		with self.assertRaises(ValidationError):
			b.save(ignore_permissions=True)

	def test_invalid_transition_submitted_to_draft(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		b.reload()
		b.status = "Submitted"
		b.save(ignore_permissions=True)
		b.reload()
		b.status = "Draft"
		with self.assertRaises(ValidationError):
			b.save(ignore_permissions=True)

	def test_invalid_transition_approved_to_submitted(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		b.reload()
		b.status = "Submitted"
		b.save(ignore_permissions=True)
		b.reload()
		b.status = "Approved"
		b.save(ignore_permissions=True)
		b.reload()
		b.status = "Submitted"
		with self.assertRaises(ValidationError):
			b.save(ignore_permissions=True)

	def test_no_status_change_save_ok_when_submitted(self):
		b = self._budget_doc()
		b.insert(ignore_permissions=True)
		b.reload()
		b.status = "Submitted"
		b.save(ignore_permissions=True)
		b.reload()
		b.save(ignore_permissions=True)
		self.assertEqual(b.status, "Submitted")
