# Copyright (c) 2026, Midas and contributors
# License: MIT. See LICENSE
"""B0.2 Budget Management workspace — Desk roles and sync.

Run:
  bench --site <site> run-tests --app kentender_budget --module kentender_budget.tests.test_budget_workspace_b02
"""

import frappe
from frappe.desk.desktop import Workspace
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
		# Strategy Manager: Draft tab + submit flows on Budget landing (B5.x / Playwright smoke).
		self.assertIn("Strategy Manager", role_names)
		# G0-015: Procurement spine roles that open the Budget wrapper from the shared rail.
		for r in (
			"Requisitioner",
			"Procurement Planner",
			"Procurement Officer",
			"Department Approver",
			"Auditor",
		):
			self.assertIn(r, role_names)
		self.assertIn("Planning Authority", role_names)
		self.assertIn("Finance Reviewer", role_names)
		self.assertIn("System Manager", role_names)
		self.assertIn("Administrator", role_names)

	def test_strategy_manager_permitted_on_budget_workspace(self):
		email = "strategy.manager@moh.test"
		if not frappe.db.exists("User", email):
			self.skipTest("Seed Strategy Manager user not present on this site")
		frappe.set_user(email)
		page = frappe.get_all(
			"Workspace",
			filters={"name": "Budget Management"},
			fields=["name", "title", "public", "for_user", "module"],
			limit=1,
		)[0]
		self.assertTrue(Workspace(page, minimal=True).is_permitted())

	def test_budget_workspace_has_no_list_shortcuts(self):
		"""Landing lists budgets in-app; EditorJS shortcuts would duplicate the list (UX)."""
		ws = frappe.get_doc("Workspace", "Budget Management")
		self.assertEqual(len(ws.shortcuts or []), 0)
