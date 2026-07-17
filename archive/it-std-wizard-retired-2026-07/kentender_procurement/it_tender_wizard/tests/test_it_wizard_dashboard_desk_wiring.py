# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-DESK-DASH-001/002 — Desk wiring for IT Tender Configurations (Screen 01, native page).

Screen 01 is a native Frappe Desk page (DIA Create-Demand pattern) — no iframe,
no static-HTML byte guard. These tests assert the native wiring/registration and
a lightweight structural guard on the page script and CSS (replacing the retired
verbatim-deploy guard).
"""

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


def _public_path(*parts: str) -> str:
	return os.path.join(frappe.get_app_path("kentender_procurement"), "public", *parts)


def _read_public_js(name: str) -> str:
	return open(_public_path("js", name), encoding="utf-8").read()


class TestItWizardDashboardDeskWiring(UnitTestCase):
	def test_hooks_register_dashboard_page_js(self) -> None:
		from kentender_procurement.hooks import page_js

		self.assertEqual(
			page_js.get("it-tender-configuration-dashboard"),
			"public/js/it_wizard_dashboard_page.js",
		)

	def test_hooks_no_longer_include_iframe_runtime_module(self) -> None:
		from kentender_procurement.hooks import app_include_css, app_include_js

		joined_js = "\n".join(app_include_js)
		# The native page replaces the iframe hydrator entirely.
		self.assertNotIn("it_wizard_dashboard.js", joined_js)
		# Native page CSS stays globally included.
		joined_css = "\n".join(app_include_css)
		self.assertIn("it_wizard_dashboard_page.css", joined_css)

	def test_iframe_runtime_module_removed(self) -> None:
		self.assertFalse(
			os.path.exists(_public_path("js", "it_wizard_dashboard.js")),
			"Legacy iframe dashboard hydrator must be deleted (no parallel legacy path).",
		)
		self.assertFalse(
			os.path.exists(_public_path("it_tender_wizard_impl", "it_wizard_dashboard.html")),
			"Legacy static dashboard HTML asset must be deleted.",
		)

	def test_dashboard_page_js_is_native_not_iframe(self) -> None:
		source = _read_public_js("it_wizard_dashboard_page.js")
		self.assertIn('frappe.pages["it-tender-configuration-dashboard"]', source)
		self.assertIn("on_page_show", source)
		self.assertNotIn("mount_page", source)
		self.assertIn("frappe.require", source)
		self.assertIn("screens/dashboard.js", source)
		self.assertIn("it_wizard/it_wizard_shell.js", source)

	def test_engine_no_longer_delegates_dashboard(self) -> None:
		engine = _read_public_js("it_wizard_engine.js")
		self.assertNotIn("kentender.it_wizard.dashboard.prepare", engine)
		self.assertNotIn("kentender.it_wizard.dashboard.fetch", engine)
		self.assertNotIn("kentender.it_wizard.dashboard.hydrate", engine)
		self.assertNotIn("open_create_modal", engine)
		# The route stays registered so screens 02–15 can navigate back here.
		self.assertIn("it-tender-configuration-dashboard", engine)

	def test_dashboard_page_css_hides_frappe_page_head(self) -> None:
		source = open(_public_path("css", "it_wizard_dashboard_page.css"), encoding="utf-8").read()
		self.assertIn("body.it-wizard-dashboard-shell .page-head", source)
		self.assertIn("display: none !important", source)
		# No external asset requests (CDN / web font URL). Strip /* */ comments
		# first so the header's prose ("no @import, no CDN") is not a false match.
		import re as _re

		css = _re.sub(r"/\*.*?\*/", "", source, flags=_re.DOTALL)
		self.assertNotIn("@import", css)
		self.assertNotIn("http://", css)
		self.assertNotIn("https://", css)

	def test_dashboard_css_keeps_sidebar_and_brand_fonts(self) -> None:
		"""Page-head/navbar are hidden; the Procurement sidebar rail stays visible and
		mockup chrome offsets for the sidebar width."""
		css = open(_public_path("css", "it_wizard_dashboard_page.css"), encoding="utf-8").read()
		self.assertIn("body.it-wizard-dashboard-shell .navbar", css)
		self.assertNotIn("body.it-wizard-dashboard-shell .body-sidebar-container", css)
		self.assertIn("--kt-itw-sidebar-offset", css)
		self.assertIn(".kt-itw-appbar", css)
		self.assertIn(".kt-itw-footer", css)
		self.assertIn("backdrop-filter", css)
		for family in ("Manrope", "Inter", "JetBrains Mono"):
			self.assertIn(family, css, family)

	def test_no_it_wizard_page_css_hides_desk_sidebar(self) -> None:
		"""Every IT Wizard Desk shell must keep the Procurement left rail visible."""
		css_dir = _public_path("css")
		for name in os.listdir(css_dir):
			if not name.startswith("it_wizard_") or not name.endswith("_page.css"):
				continue
			source = open(os.path.join(css_dir, name), encoding="utf-8").read()
			self.assertNotIn(
				".body-sidebar-container,",
				source,
				f"{name} must not hide the Desk sidebar rail",
			)
			self.assertNotIn(
				".body-sidebar-container {",
				source,
				f"{name} must not hide the Desk sidebar rail",
			)

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
		self.assertEqual(items[dash_idx]["label"], "IT Tender Configurations")


class TestItWizardDashboardNativeGuard(UnitTestCase):
	"""Structural guard for the native Screen 01 screen module (replaces the byte guard)."""

	def _source(self) -> str:
		return _read_public_js("it_wizard/screens/dashboard.js")

	def test_registrar_is_thin(self) -> None:
		registrar = _read_public_js("it_wizard_dashboard_page.js")
		self.assertIn("screens/dashboard.js", registrar)
		self.assertNotIn("data-itw-kpi-grid", registrar)

	def test_root_and_testids_present(self) -> None:
		source = self._source()
		self.assertIn('data-testid="it-wizard-dashboard"', source)
		for marker in (
			"data-itw-kpi-grid",
			"data-itw-search",
			"data-itw-filter-chips",
			"data-itw-open-filter-drawer",
			"data-itw-filter-drawer",
			"data-itw-tbody",
			"data-itw-table-footer",
		):
			self.assertIn(marker, source, marker)

	def test_create_modal_contract_markers(self) -> None:
		source = self._source()
		for marker in (
			"create_options",
			"data-itw-create-package",
			"data-itw-create-std",
			"data-itw-create-submit",
			"Approved Procurement Package",
			"Standard Tender Document",
			"Create Configuration",
		):
			self.assertIn(marker, source, marker)
		# Rejected v1 shell markers.
		self.assertNotIn("data-itw-create-shell", source)
		self.assertNotIn("Start Configuration", source)

	def test_path_a_and_api_contract(self) -> None:
		source = self._source()
		for marker in (
			"read_route_context",
			"get_dashboard_summary",
			"list_configurations_api",
			"get_create_configuration_context_api",
			"create_configuration_api",
			"ROUTES.OVERVIEW",
		):
			self.assertIn(marker, source, marker)

	def test_human_status_labels_not_enum_codes(self) -> None:
		source = self._source()
		# Human labels are rendered from the API (state_label) — never enum codes.
		self.assertIn("state_label", source)
		self.assertNotIn("OPEN_NATIONAL", source)

	def test_design_chrome_and_material_symbols(self) -> None:
		"""Screen 01 renders the mockup's top app bar + footer toolbar, Material
		Symbols icons, KPI progress bars, and numbered pagination + rows select."""
		source = self._source()
		components = _read_public_js("it_wizard/it_wizard_components.js")
		for marker in (
			"data-itw-kpi-bar",
			"data-itw-rows-select",
			"data-itw-pager-page",
			"components.appbar",
			"components.footer",
		):
			self.assertIn(marker, source, marker)
		for marker in (
			"data-itw-appbar",
			"data-itw-footer",
			"material-symbols-outlined",
			"account_balance",
			"notifications",
			"Export Report",
			"Audit Logs",
		):
			self.assertIn(marker, components, marker)
		self.assertNotIn('viewBox="0 0 24 24"', source)


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
			and row.link_to == "it-tender-configuration-dashboard"
			and (row.link_type or "").lower() == "page"
		]
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0].label, "IT Tender Configurations")
