# Copyright (c) 2026, KenTender and contributors
"""Regression: MOH seed users can read PE-MOH budgets in builder API."""

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds._common import ensure_moh_entity_permission_aliases, ensure_procuring_entity
from kentender_core.seeds import constants as C
from kentender_budget.api.builder import get_budget_builder_data


class TestMohEntityPermissionAliases(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_procuring_entity("PE-MOH", "Ministry of Health")

	def test_strategy_manager_can_read_pe_moh_budget(self):
		email = "strategy.manager@moh.test"
		if not frappe.db.exists("User", email):
			self.skipTest("Seed Strategy Manager user not present")
		budget = frappe.db.get_value("Budget", {"budget_name": "BUDGET-MOH-2026"}, "name")
		if not budget:
			self.skipTest("WORKS master budget not present")
		ensure_moh_entity_permission_aliases(email, C.ENTITY_MOH)
		frappe.set_user(email)
		self.assertTrue(frappe.has_permission("Budget", "read", budget))
		payload = get_budget_builder_data(budget)
		self.assertTrue(payload.get("budget_lines"))
