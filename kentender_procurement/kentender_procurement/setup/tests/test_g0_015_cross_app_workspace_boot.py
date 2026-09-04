# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""G0-015 — Cross-app Strategy/Budget workspaces: boot fast-path + Desk workspace gate."""

from __future__ import annotations

import frappe
from frappe.desk.desktop import Workspace as DeskWorkspace
from frappe.tests import IntegrationTestCase

from kentender_procurement.setup.workspace_permissions import patch_bootinfo


def _workspace_page_dict(name: str) -> dict:
	row = frappe.db.get_value(
		"Workspace",
		name,
		[
			"name",
			"title",
			"public",
			"module",
			"is_hidden",
			"app",
			"type",
			"link_type",
			"link_to",
			"external_link",
		],
		as_dict=True,
	)
	if not row:
		return {}
	row["label"] = row.get("name")
	return row


class TestG015CrossAppWorkspaceBoot(IntegrationTestCase):
	def setUp(self):
		super().setUp()

	def test_patch_bootinfo_maps_strategy_and_budget_to_procurement_rail(self):
		if not frappe.db.exists("Workspace Sidebar", "Procurement"):
			self.skipTest("Procurement Workspace Sidebar not on site")
		bootinfo: dict = {"workspace_sidebar_item": {}}
		frappe.set_user("Administrator")
		patch_bootinfo(bootinfo)
		items = bootinfo.get("workspace_sidebar_item") or {}
		proc = items.get("procurement") or {}
		strat = items.get("strategy management") or {}
		bud = items.get("budget management") or {}
		self.assertTrue(strat.get("items"), msg="strategy management boot key must carry Procurement rail items")
		self.assertTrue(bud.get("items"), msg="budget management boot key must carry Procurement rail items")
		self.assertEqual(strat.get("label"), proc.get("label"))
		self.assertEqual(bud.get("label"), proc.get("label"))

	def test_requisitioner_can_access_procurement_home_workspace_shell(self):
		user = "requisitioner@moh.test"
		if not frappe.db.exists("User", user):
			self.skipTest("Seeded requisitioner not on site")
		frappe.set_user(user)
		page = _workspace_page_dict("Procurement Home")
		self.assertTrue(page)
		dw = DeskWorkspace(page, True)
		self.assertTrue(dw.is_permitted(), msg=f"{user} must read Procurement Home for spine entry")

	def test_requisitioner_can_access_strategy_workspace_shell(self):
		"""Frappe ``desktop.Workspace.is_permitted`` requires a role overlap when Workspace.roles is non-empty.

		FOLLOW_UPS.md FU-01/FU-02 (closed): originally looped over
		("Strategy Management", "Budget Management") — Budget Management is
		retired (BUD-CHG-001 v1.3 has no Workspace of its own; Procurement's
		rail points at the budget-funding Page instead), so only Strategy
		Management is checked here now.

		FOLLOW_UPS.md FU-03 (still open): this same access check on Strategy
		Management is independently reported failing for the requisitioner
		persona (a Strategy-owned module allow-list / Workspace.app question,
		not Budget's) — left open, not investigated further here.
		"""
		user = "requisitioner@moh.test"
		if not frappe.db.exists("User", user):
			self.skipTest("Seeded requisitioner not on site")
		frappe.set_user(user)
		ws_name = "Strategy Management"
		page = _workspace_page_dict(ws_name)
		self.assertTrue(page, msg=f"Missing Workspace {ws_name}")
		try:
			dw = DeskWorkspace(page, True)
		except frappe.PermissionError as e:
			self.fail(f"{user} cannot load {ws_name} (module allow-list?): {e}")
		self.assertTrue(
			dw.is_permitted(),
			msg=f"{user} must be permitted to read {ws_name} for G0-012 spine wrappers (G0-015)",
		)
