# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-DESK-OVERVIEW-001/002 — Desk wiring for Tender Configuration Home (Screen 02, native)."""

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

	def test_hooks_include_shared_native_modules_not_iframe_hydrator(self) -> None:
		from kentender_procurement.hooks import app_include_js

		joined = "\n".join(app_include_js)
		self.assertIn("it_wizard/it_wizard_shell.js", joined)
		self.assertNotIn("it_wizard_overview.js", joined)

	def test_overview_page_js_is_native_not_iframe(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard_overview_page.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn('frappe.pages["it-tender-configuration-overview"]', source)
		self.assertNotIn("mount_page", source)
		self.assertNotIn("it_wizard_std_config_overview.html", source)
		self.assertNotIn("it-wizard-overview-iframe", source)
		self.assertIn("frappe.require", source)
		self.assertIn("it_wizard/it_wizard_shell.js", source)
		self.assertIn("screens/configuration_home.js", source)
		self.assertIn("kentender.it_wizard.screens.configuration_home", source)

	def test_configuration_home_module_exists(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard",
			"screens",
			"configuration_home.js",
		)
		self.assertTrue(os.path.isfile(path), path)
		source = open(path, encoding="utf-8").read()
		self.assertIn("data-itw-step-grid", source)
		self.assertIn("data-itw-next-action", source)
		self.assertIn("data-itw-home-context", source)
		self.assertIn("get_configuration_summary_api", source)
		self.assertIn("data-itw-native-loaded", source)

	def test_overview_page_css_hides_frappe_page_head(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"css",
			"it_wizard_overview_page.css",
		)
		source = open(path, encoding="utf-8").read()
		shared = open(
			os.path.join(
				frappe.get_app_path("kentender_procurement"),
				"public",
				"css",
				"kt_it_wizard.css",
			),
			encoding="utf-8",
		).read()
		self.assertIn("body.it-wizard-overview-shell .page-head", shared)
		self.assertIn("display: none !important", shared)


class TestItWizardOverviewDeskWiringSite(IntegrationTestCase):
	def test_overview_page_exists_on_site(self) -> None:
		self.assertTrue(frappe.db.exists("Page", "it-tender-configuration-overview"))
