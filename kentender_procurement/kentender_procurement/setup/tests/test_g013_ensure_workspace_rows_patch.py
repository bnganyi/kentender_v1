# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""g013 patch: Strategy / Budget Workspace shell rows for Procurement rail G0-012."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.patches.g013_ensure_strategy_budget_workspace_rows import execute


class TestG013EnsureWorkspaceRowsPatch(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def test_g013_execute_ensures_cross_app_workspaces(self):
		execute()
		self.assertTrue(frappe.db.exists("Workspace", "Strategy Management"))
		self.assertTrue(frappe.db.exists("Workspace", "Budget Management"))
		sm = frappe.db.get_value(
			"Workspace",
			"Strategy Management",
			["public", "is_hidden", "module", "app"],
			as_dict=True,
		)
		bm = frappe.db.get_value(
			"Workspace",
			"Budget Management",
			["public", "is_hidden", "module", "app"],
			as_dict=True,
		)
		self.assertEqual(sm.get("public"), 1)
		self.assertEqual(sm.get("is_hidden"), 0)
		self.assertEqual(sm.get("module"), "Kentender Strategy")
		self.assertEqual(sm.get("app"), "kentender_strategy")
		self.assertEqual(bm.get("public"), 1)
		self.assertEqual(bm.get("is_hidden"), 0)
		self.assertEqual(bm.get("module"), "Kentender Budget")
		self.assertEqual(bm.get("app"), "kentender_budget")
		# idempotent
		execute()
		self.assertEqual(
			frappe.db.get_value("Workspace", "Strategy Management", "public"),
			1,
		)
