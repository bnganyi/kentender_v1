# Copyright (c) 2026, Midas and contributors
# License: MIT. See LICENSE
"""G0-016: harmonised Workspace `label` must not change Frappe Desk `title` used in routes.

Frappe builds module-tile → first-workspace links using `workspaces.title` in
`frappe.utils.generate_route` (see `frappe/desk/page/desktop/desktop.js`).
`title` must therefore stay the stable headline that matches the historical slug
(`strategy-management`, `budget-management`).

Run:
  bench --site <site> run-tests --app kentender_strategy --module kentender_strategy.tests.test_g0_016_workspace_route_labels
"""

import frappe
from frappe.tests import IntegrationTestCase


class TestG016WorkspaceRouteLabels(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def test_strategy_management_title_and_label(self):
		self.assertTrue(frappe.db.exists("Workspace", "Strategy Management"))
		doc = frappe.get_doc("Workspace", "Strategy Management")
		self.assertEqual(doc.title, "Strategy Management")
		self.assertEqual(doc.label, "Strategy Alignment")

	def test_budget_management_title_and_label(self):
		self.assertTrue(frappe.db.exists("Workspace", "Budget Management"))
		doc = frappe.get_doc("Workspace", "Budget Management")
		self.assertEqual(doc.title, "Budget Management")
		self.assertEqual(doc.label, "Budget & Funding")
