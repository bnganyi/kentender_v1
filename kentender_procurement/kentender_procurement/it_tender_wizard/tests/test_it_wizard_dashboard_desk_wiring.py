# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-DESK-DASH-001/002 — Desk wiring for Tender Configuration Dashboard."""

from __future__ import annotations

import json
import os

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase


def _procurement_sidebar_export_path() -> str:
	return os.path.join(
		frappe.get_app_path("kentender_procurement"),
		"workspace_sidebar",
		"procurement.json",
	)


class TestItWizardDashboardDeskWiring(UnitTestCase):
	def test_hooks_register_dashboard_page_js(self) -> None:
		from kentender_procurement.hooks import page_js

		self.assertEqual(
			page_js.get("it-tender-configuration-dashboard"),
			"public/js/it_wizard_dashboard_page.js",
		)

	def test_dashboard_page_js_embeds_static_asset_iframe(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard_dashboard_page.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn('frappe.pages["it-tender-configuration-dashboard"]', source)
		self.assertIn(
			"/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_dashboard.html",
			source,
		)
		self.assertIn('testid: "it-wizard-dashboard"', source)
		self.assertIn("kentender.it_wizard.mount_page", source)

	def test_engine_hydrates_dashboard_symbols(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard_engine.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("hydrate_dashboard_kpis", source)
		self.assertIn("hydrate_filter_selects", source)
		self.assertIn("format_method_reference", source)
		self.assertIn("format_entity_reference", source)
		self.assertIn("hydrate_dashboard_table", source)
		self.assertIn("hydrate_dashboard_pager", source)
		self.assertIn("read_route_context", source)
		self.assertIn("HYDRATORS", source)
		self.assertIn("install_hydration_gate", source)
		self.assertIn("enhance_dashboard_table_layout", source)
		self.assertIn("enhance_dashboard_kpi_layout", source)
		self.assertIn("enhance_dashboard_filter_layout", source)
		self.assertIn("enhance_dashboard_filter_drawer", source)
		self.assertIn("read_dashboard_filters", source)
		self.assertIn("read_drawer_filters", source)
		self.assertIn("wire_filter_drawer", source)
		self.assertIn("get_visible_page_numbers", source)
		self.assertIn("render_pager_page_buttons", source)
		self.assertIn("apply_drawer_stub_state", source)
		self.assertIn("data-itw-filter-bar", source)
		self.assertIn("data-itw-filter-drawer", source)
		self.assertIn("data-itw-pager-pages", source)
		self.assertIn("data-itw-page-size", source)
		self.assertIn("data-itw-drawer-capability-note", source)
		self.assertIn("it-wizard-table-scroll-host", source)
		self.assertIn("it-wizard-table-footer", source)
		self.assertIn("data-itw-kpi-grid", source)

	def test_dashboard_page_css_hides_frappe_page_head(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"css",
			"it_wizard_dashboard_page.css",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("body.it-wizard-dashboard-shell .page-head", source)
		self.assertIn("display: none !important", source)

	def test_procurement_sidebar_export_points_dashboard_after_tender_management(self) -> None:
		with open(_procurement_sidebar_export_path(), encoding="utf-8") as handle:
			data = json.load(handle)
		items = data.get("items") or []
		tm_idx = next(
			(i for i, row in enumerate(items) if row.get("label") == "Tender Management"),
			None,
		)
		dash_idx = next(
			(
				i
				for i, row in enumerate(items)
				if row.get("link_to") == "it-tender-configuration-dashboard"
			),
			None,
		)
		self.assertIsNotNone(tm_idx)
		self.assertIsNotNone(dash_idx)
		self.assertGreater(dash_idx, tm_idx)
		self.assertEqual(items[dash_idx]["label"], "Tender Configuration Dashboard")


class TestItWizardDashboardDeskWiringSite(IntegrationTestCase):
	def test_dashboard_page_exists_on_site(self) -> None:
		self.assertTrue(frappe.db.exists("Page", "it-tender-configuration-dashboard"))

	def test_procurement_sidebar_dashboard_targets_dashboard_page(self) -> None:
		if not frappe.db.exists("Workspace Sidebar", "Procurement"):
			self.skipTest("Procurement Workspace Sidebar not on site")
		doc = frappe.get_doc("Workspace Sidebar", "Procurement")
		rows = [
			row
			for row in doc.items
			if row.type == "Link"
			and row.label == "Tender Configuration Dashboard"
			and (row.link_type or "").lower() == "page"
		]
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0].link_to, "it-tender-configuration-dashboard")
