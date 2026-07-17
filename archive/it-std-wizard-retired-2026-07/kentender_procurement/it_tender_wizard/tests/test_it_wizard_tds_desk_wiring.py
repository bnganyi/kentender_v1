# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-DESK-TDS-001/002 — Desk wiring for Tender Data Sheet."""

from __future__ import annotations

import os

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase


class TestItWizardTdsDeskWiring(UnitTestCase):
	def test_hooks_register_tds_page_js(self) -> None:
		from kentender_procurement.hooks import page_js

		self.assertEqual(
			page_js.get("it-tender-configuration-tds"),
			"public/js/it_wizard_tds_page.js",
		)

	def test_tds_page_js_embeds_static_asset_iframe(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard_tds_page.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn('frappe.pages["it-tender-configuration-tds"]', source)
		self.assertIn(
			"/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_tds.html",
			source,
		)
		self.assertIn('testid: "it-wizard-tds"', source)
		self.assertIn("kentender.it_wizard.mount_page", source)
		self.assertIn('screen: "tds"', source)

	def test_engine_hydrates_tds_symbols(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard_engine.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("it-tender-configuration-tds", source)
		self.assertIn("STEP_ROUTE_MAP", source)
		self.assertIn("TDS", source)
		self.assertIn("unwrap_envelope_data", source)
		self.assertIn("hydrate_tds_context", source)
		self.assertIn("hydrate_tds_form", source)
		self.assertIn("hydrate_tds_sidebar", source)
		self.assertIn("harmonize_tds_page_layout", source)
		self.assertIn("data-itw-tds-context", source)
		self.assertIn("data-itw-tds-form", source)
		self.assertIn("data-itw-tds-sidebar", source)
		self.assertIn("data-itw-tds-actions", source)
		self.assertIn("wrap_tds_content_shell", source)
		self.assertIn("data-itw-tds-shell", source)
		self.assertIn("fetch_tds_data", source)
		self.assertIn("get_tds_api", source)
		self.assertIn("save_tds_api", source)
		self.assertIn("apply_tds_payload", source)
		self.assertIn("tds_payload_data", source)
		self.assertIn("strip_tds_fixture_scripts", source)
		self.assertIn("normalize_tds_fixture_field_styles", source)

	def test_tds_page_css_hides_frappe_page_head(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"css",
			"it_wizard_tds_page.css",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("body.it-wizard-tds-shell .page-head", source)
		self.assertIn("display: none !important", source)


class TestItWizardTdsDeskWiringSite(IntegrationTestCase):
	def test_tds_page_exists_on_site(self) -> None:
		self.assertTrue(frappe.db.exists("Page", "it-tender-configuration-tds"))
