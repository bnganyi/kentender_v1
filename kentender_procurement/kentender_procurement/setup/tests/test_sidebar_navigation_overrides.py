# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""The shared Procurement rail honours `kt_navigation_overrides` (kentender_core.services.navigation_overrides; CM-CHG-001 FU-CM-58): an installed app can replace a
Planned placeholder with its live page and publish its routes as boot aliases of the rail, without editing procurement.json. With nothing contributed, nothing changes."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.setup.workspace_permissions import patch_bootinfo

OVERRIDE = {"Procurement": {"items": {"Contract Management": {"link_to": "contracts", "link_type": "Page", "route_options": None}}, "routes": ["contracts"]}}
NOTHING = {}


def contract_management(items):
	return next(row for row in items if row.get("label") == "Contract Management")


class TestSidebarNavigationOverrides(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("Workspace Sidebar", "Procurement"):
			self.skipTest("Procurement Workspace Sidebar not on site")

	def boot(self, contributed):
		bootinfo: dict = {"workspace_sidebar_item": {}}
		with patch("kentender_core.services.navigation_overrides._collected", return_value=contributed):
			patch_bootinfo(bootinfo)
		return bootinfo["workspace_sidebar_item"]

	def test_without_a_contributing_app_the_placeholder_stays_planned_and_points_at_coming_soon(self):
		row = contract_management(self.boot(NOTHING)["procurement"]["items"])
		self.assertEqual((row["link_to"], row.get("suffix")), ("coming-soon", "Planned"))
		self.assertNotIn("contracts", self.boot(NOTHING))

	def test_a_contributing_app_makes_the_item_live_and_its_route_shows_the_shared_rail(self):
		sidebars = self.boot(OVERRIDE)
		row = contract_management(sidebars["procurement"]["items"])
		self.assertEqual((row["link_to"], row["link_type"], row.get("suffix")), ("contracts", "Page", None))
		self.assertEqual(sidebars["contracts"], sidebars["procurement"], "the route of the contributing app resolves to the same rail")
		other = [r for r in sidebars["procurement"]["items"] if r.get("label") == "Supplier Management"]
		self.assertEqual(other[0].get("suffix"), "Planned", "a placeholder nobody replaced stays Planned")
