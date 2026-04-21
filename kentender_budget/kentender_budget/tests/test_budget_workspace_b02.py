# Copyright (c) 2026, Midas and contributors
# License: MIT. See LICENSE
"""B0.2 Budget Management workspace — Desk roles and sync.

Run:
  bench --site <site> run-tests --app kentender_budget --module kentender_budget.tests.test_budget_workspace_b02
"""

import frappe
from frappe.tests import IntegrationTestCase

import kentender_budget.install


class TestBudgetWorkspaceB02(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		kentender_budget.install.after_migrate()

	def test_budget_management_workspace_roles(self):
		self.assertTrue(frappe.db.exists("Workspace", "Budget Management"))
		ws = frappe.get_doc("Workspace", "Budget Management")
		role_names = {r.role for r in ws.roles}
		self.assertEqual(
			role_names,
			{"System Manager", "Strategy Manager", "Planning Authority"},
		)
		self.assertNotIn("Requisitioner", role_names)

	def test_budget_workspace_has_no_list_shortcuts(self):
		"""Landing lists budgets in-app; EditorJS shortcuts would duplicate the list (UX)."""
		ws = frappe.get_doc("Workspace", "Budget Management")
		self.assertEqual(len(ws.shortcuts or []), 0)
