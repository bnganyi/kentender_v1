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
		planning = items.get("procurement planning") or {}
		planning_labels = [row.get("label") for row in planning.get("items") or []]
		self.assertIn("Procurement Home", planning_labels)
		self.assertIn("Procurement Planning", planning_labels)
		self.assertIn("Procurement Plans", planning_labels)
		self.assertIn("Released to Tender", planning_labels)
		for key in (
			"my work",
			"my-work",
			"procurement journeys",
			"plc-procurement-journey",
			"audit event",
			"audit-event",
			"bid opening",
			"bid-opening",
			"evaluation and award",
			"evaluation-and-award",
			"contract management",
			"contract-management",
			"strategy management",
			"strategy-management",
			"budget management",
			"budget-management",
			"procurement home",
			"procurement-home",
			"demand intake and approval",
			"demand-intake-and-approval",
			"ktsm supplier registry",
			"ktsm-supplier-registry",
		):
			self.assertIn(
				key,
				items,
				msg=f"G0-012 workspace {key!r} requires boot sidebar fast-path key",
			)
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

	def test_procurement_sidebar_one_workspace_row_for_governance(self):
		"""Official STD Library should target std-library page while governance workspace stays reachable."""
		if not frappe.db.exists("Workspace Sidebar", "Procurement"):
			self.skipTest("Procurement Workspace Sidebar not on site")
		doc = frappe.get_doc("Workspace Sidebar", "Procurement")
		ws_links = [
			r
			for r in doc.items
			if r.type == "Link"
			and (r.link_type or "").lower() == "workspace"
			and r.link_to == "Governance & Configuration"
		]
		self.assertEqual(len(ws_links), 1)
		page_std_library = [
			r
			for r in doc.items
			if r.type == "Link"
			and (r.link_type or "").lower() == "page"
			and r.link_to == "std-library"
			and r.label == "Official STD Library"
		]
		self.assertEqual(len(page_std_library), 1)

	def test_procurement_boot_sidebar_includes_strategy_alignment_and_budget_links(self):
		"""Regression: G0-012 primary rail must list Strategy Alignment + Budget before DIA."""
		if not frappe.db.exists("Workspace Sidebar", "Procurement"):
			self.skipTest("Procurement Workspace Sidebar not on site")
		bootinfo: dict = {"workspace_sidebar_item": {}}
		patch_bootinfo(bootinfo)
		proc = (bootinfo.get("workspace_sidebar_item") or {}).get("procurement") or {}
		labels = [row.get("label") for row in proc.get("items") or []]
		self.assertIn(
			"Strategy Alignment",
			labels,
			msg="Strategy Management workspace link must survive boot sidebar rebuild",
		)
		self.assertIn(
			"Budget & Funding",
			labels,
			msg="Budget Management workspace link must survive boot sidebar rebuild",
		)
		try:
			i_strat = labels.index("Strategy Alignment")
			i_dia = next(i for i, lab in enumerate(labels) if lab and "Demand Intake" in lab)
			self.assertLess(
				i_strat,
				i_dia,
				msg="Strategy Alignment must appear before Demand Intake in the Procurement rail",
			)
		except ValueError:
			self.fail("Demand Intake sidebar label not found — cannot verify G0-012 order")

	def test_bootinfo_includes_builder_route_sidebar_keys(self):
		"""Context-preserving navigation: builder/form routes must map to Procurement sidebar."""
		if not frappe.db.exists("Workspace Sidebar", "Procurement"):
			self.skipTest("Procurement Workspace Sidebar not on site")
		bootinfo: dict = {"workspace_sidebar_item": {}}
		patch_bootinfo(bootinfo)
		items = bootinfo.get("workspace_sidebar_item") or {}
		proc = items.get("procurement") or {}
		self.assertTrue(len(proc.get("items") or []) > 0, msg="Procurement sidebar baseline required")
		for route_key in (
			"strategy-builder",
			"budget-builder",
			"form/demand",
			"procurement-home",
			"plc-procurement-journey",
			"tender-management-v2",
			"audit-event",
		):
			self.assertIn(
				route_key,
				items,
				msg=f"Route {route_key!r} requires boot sidebar fast-path key for hard refresh",
			)
			payload = items[route_key]
			self.assertIsInstance(payload, dict)
			self.assertTrue(len(payload.get("items") or []) > 0)
		self.assertEqual(
			payload.get("items"),
			proc.get("items"),
			msg=f"Route {route_key!r} should reuse Procurement sidebar rail",
		)

	def test_bootinfo_includes_procurement_planning_surface_route_keys(self):
		"""P1-002 — PP3 nested routes must keep main Procurement rail visible."""
		if not frappe.db.exists("Workspace Sidebar", "Procurement"):
			self.skipTest("Procurement sidebar not on site")
		bootinfo: dict = {"workspace_sidebar_item": {}}
		patch_bootinfo(bootinfo)
		items = bootinfo.get("workspace_sidebar_item") or {}
		proc = items.get("procurement") or {}
		self.assertTrue(len(proc.get("items") or []) > 0)
		for route_key in (
			"procurement-planning",
			"procurement-planning/plans",
			"procurement-planning/releases",
		):
			self.assertIn(route_key, items, msg=f"PP3 route {route_key!r} requires boot fast-path key")
			payload = items[route_key]
			self.assertEqual(payload.get("items"), proc.get("items"))

	def test_bootinfo_excludes_procurement_planning_evidence_route_key(self):
		"""P5A-004 — superseded evidence route must not be an ordinary planning fast-path."""
		if not frappe.db.exists("Workspace Sidebar", "Procurement"):
			self.skipTest("Procurement sidebar not on site")
		bootinfo: dict = {"workspace_sidebar_item": {}}
		patch_bootinfo(bootinfo)
		items = bootinfo.get("workspace_sidebar_item") or {}
		self.assertNotIn(
			"procurement-planning/evidence",
			items,
			msg="Planning Evidence must not be registered as an ordinary planning boot fast-path key",
		)
		self.assertNotIn(
			"evidence",
			items,
			msg="Standalone evidence slug must not be registered as an ordinary planning boot fast-path key",
		)

	def test_bootinfo_includes_module_fallback_sidebar_keys(self):
		"""DocType module routes should preserve Procurement rail context."""
		if not frappe.db.exists("Workspace Sidebar", "Procurement"):
			self.skipTest("Procurement Workspace Sidebar not on site")
		bootinfo: dict = {"workspace_sidebar_item": {}}
		patch_bootinfo(bootinfo)
		items = bootinfo.get("workspace_sidebar_item") or {}
		proc = items.get("procurement") or {}
		for key in ("budget", "strategy"):
			self.assertIn(
				key,
				items,
				msg=f"Module fallback key {key!r} should be injected for context-preserving sidebars",
			)
			payload = items[key]
			self.assertIsInstance(payload, dict)
			self.assertEqual(
				payload.get("items"),
				proc.get("items"),
				msg=f"Module key {key!r} should reuse Procurement sidebar rail",
			)
