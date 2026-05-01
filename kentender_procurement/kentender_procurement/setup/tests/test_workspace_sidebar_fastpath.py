# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""Regression: key procurement workspaces must register boot sidebar fast-path keys.

Without ``workspace_sidebar_item["<workspace slug>"]``, a hard refresh on some
``/desk/Workspaces/…`` routes leaves the left rail blank (Frappe sidebar.js
cannot disambiguate when multiple sidebars link to workspaces and
``router.meta.module`` is undefined). See ``setup/workspace_permissions.py``.
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.setup.workspace_permissions import patch_bootinfo


class TestWorkspaceSidebarFastpath(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def test_bootinfo_includes_ktsm_supplier_registry_sidebar_key(self):
		if not frappe.db.exists("Workspace Sidebar", "Procurement"):
			self.skipTest("Procurement Workspace Sidebar not on site")
		bootinfo: dict = {"workspace_sidebar_item": {}}
		patch_bootinfo(bootinfo)
		items = bootinfo.get("workspace_sidebar_item") or {}
		self.assertIn(
			"ktsm supplier registry",
			items,
			msg="Hard refresh / direct URL to KTSM Supplier Registry workspace requires this boot key",
		)
		payload = items["ktsm supplier registry"]
		self.assertIsInstance(payload, dict)
		self.assertTrue(len(payload.get("items") or []) > 0)

	def test_procurement_workspace_keys_remain_injected(self):
		if not frappe.db.exists("Workspace Sidebar", "Procurement"):
			self.skipTest("Procurement Workspace Sidebar not on site")
		bootinfo: dict = {"workspace_sidebar_item": {}}
		patch_bootinfo(bootinfo)
		items = bootinfo.get("workspace_sidebar_item") or {}
		self.assertIn("procurement home", items)
		self.assertIn("procurement planning", items)
		self.assertIn(
			"governance & configuration",
			items,
			msg="Governance & Configuration workspace hard refresh requires boot sidebar key",
		)

	def test_governance_workspace_boot_key_for_limited_roles(self):
		if not frappe.db.exists("Workspace Sidebar", "Procurement"):
			self.skipTest("Procurement Workspace Sidebar not on site")
		bootinfo: dict = {"workspace_sidebar_item": {}}
		with patch(
			"kentender_procurement.setup.workspace_permissions.frappe.get_roles",
			return_value=["Accounts User"],
		):
			patch_bootinfo(bootinfo)
		items = bootinfo.get("workspace_sidebar_item") or {}
		self.assertIn(
			"governance & configuration",
			items,
			msg="Governance workspace must remain reachable without STD-only roles",
		)
