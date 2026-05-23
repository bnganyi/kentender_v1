# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase

from kentender_budget.api.audit import get_budget_audit_data
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity


class TestBudgetAuditAPI(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_currency_kes()
		self.entity = ensure_procuring_entity("MOH_AUDIT", "Ministry Audit Test")
		h = frappe.generate_hash(length=6)
		self.plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": f"Audit Plan {h}",
				"procuring_entity": self.entity,
				"start_year": 2026,
				"end_year": 2030,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		self.budget = frappe.get_doc(
			{
				"doctype": "Budget",
				"budget_name": f"Audit Budget {h}",
				"procuring_entity": self.entity,
				"fiscal_year": 2026,
				"strategic_plan": self.plan.name,
				"currency": "KES",
				"total_budget_amount": 1000,
				"version_no": 1,
				"is_current_version": 1,
				"order_index": 0,
			}
		).insert(ignore_permissions=True)

	def test_get_budget_audit_data_returns_timeline_and_downstream(self):
		out = get_budget_audit_data(self.budget.name)
		self.assertEqual(out["budget_name"], self.budget.name)
		self.assertTrue(out["timeline"])
		self.assertIsNotNone(out["timeline"][0].get("label"))
		self.assertIn("downstream", out)
		self.assertIn("reserved_sum", out["downstream"])
		self.assertIn("linked_demands", out["downstream"])
