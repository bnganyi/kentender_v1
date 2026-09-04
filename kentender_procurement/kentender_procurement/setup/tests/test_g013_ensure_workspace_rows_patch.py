# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""g013 patch: Strategy Workspace shell row for Procurement rail G0-012.

FOLLOW_UPS.md FU-01/FU-02 (closed): this test originally also asserted a
**Budget Management** Workspace row. BUD-CHG-001 v1.3's rebuilt UI has no
Workspace of its own — Procurement's rail now points directly at the
``budget-funding`` Page — so g013 no longer creates one and this test no
longer asserts one exists.
"""

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
		self.assertFalse(
			frappe.db.exists("Workspace", "Budget Management"),
			msg="Budget Management is retired (BUD-CHG-001 v1.3) — g013 must not (re-)create it",
		)
		self.assertTrue(frappe.db.exists("Workspace", "Strategy Management"))
		sm = frappe.db.get_value(
			"Workspace",
			"Strategy Management",
			["public", "is_hidden"],
			as_dict=True,
		)
		self.assertEqual(sm.get("public"), 1)
		self.assertEqual(sm.get("is_hidden"), 0)
		# g013's update-existing-row branch only enforces public/is_hidden (see
		# its own source) — module/app are set only on first insert, never
		# corrected on a pre-existing row. This site's own Strategy Management
		# row already exists with app=None (a Strategy-owned configuration
		# question — see FOLLOW_UPS.md FU-03 — not something this patch
		# guarantees or this test should assert a specific value for).
		# idempotent
		execute()
		self.assertEqual(
			frappe.db.get_value("Workspace", "Strategy Management", "public"),
			1,
		)
