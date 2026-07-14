# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-DESK-OVERVIEW-001/002 — Desk wiring for STD Configuration Overview."""

from __future__ import annotations

import os

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase


class TestItWizardOverviewDeskWiring(UnitTestCase):
	def test_hooks_register_overview_page_js(self) -> None:
		from kentender_procurement.hooks import page_js

		self.assertEqual(
			page_js.get("it-tender-configuration-overview"),
			"public/js/it_wizard_overview_page.js",
		)

	def test_overview_page_js_embeds_static_asset_iframe(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard_overview_page.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn('frappe.pages["it-tender-configuration-overview"]', source)
		self.assertIn(
			"/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_std_config_overview.html",
			source,
		)
		self.assertIn('testid: "it-wizard-overview"', source)
		self.assertIn("kentender.it_wizard.mount_page", source)
		self.assertIn('screen: "std_config_overview"', source)

	def test_engine_hydrates_overview_symbols(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard_engine.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("navigate", source)
		self.assertIn("it-tender-configuration-overview", source)
		self.assertIn("hydrate_overview_header", source)
		self.assertIn("hydrate_overview_step_grid", source)
		self.assertIn("hydrate_overview_governance", source)
		self.assertIn("enhance_overview_layout", source)
		self.assertIn("harmonize_overview_page_layout", source)
		self.assertIn("data-itw-overview-scroll-host", source)
		self.assertIn("data-itw-overview-main", source)
		self.assertIn("it-wizard-overview-layout", source)
		self.assertIn("fetch_overview_data", source)
		self.assertIn("std_config_overview", source)
		self.assertIn("data-itw-overview-header", source)
		self.assertIn("data-itw-overview-step-grid", source)
		self.assertIn("data-itw-overview-governance", source)
		self.assertIn("data-itw-overview-actions", source)
		self.assertIn("get_configuration_summary_api", source)

	def test_overview_page_css_hides_frappe_page_head(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"css",
			"it_wizard_overview_page.css",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("body.it-wizard-overview-shell .page-head", source)
		self.assertIn("display: none !important", source)


class TestItWizardOverviewDeskWiringSite(IntegrationTestCase):
	def test_overview_page_exists_on_site(self) -> None:
		self.assertTrue(frappe.db.exists("Page", "it-tender-configuration-overview"))
