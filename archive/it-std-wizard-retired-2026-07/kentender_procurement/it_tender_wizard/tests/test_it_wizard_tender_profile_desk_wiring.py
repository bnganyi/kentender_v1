# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-DESK-PROFILE-001/002 — Desk wiring for Tender Profile."""

from __future__ import annotations

import os

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase


class TestItWizardTenderProfileDeskWiring(UnitTestCase):
	def test_hooks_register_profile_page_js(self) -> None:
		from kentender_procurement.hooks import page_js

		self.assertEqual(
			page_js.get("it-tender-configuration-tender-profile"),
			"public/js/it_wizard_tender_profile_page.js",
		)

	def test_profile_page_js_embeds_static_asset_iframe(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard_tender_profile_page.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn('frappe.pages["it-tender-configuration-tender-profile"]', source)
		self.assertIn(
			"/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_tender_profile.html",
			source,
		)
		self.assertIn('testid: "it-wizard-tender-profile"', source)
		self.assertIn("kentender.it_wizard.mount_page", source)
		self.assertIn('screen: "tender_profile"', source)

	def test_engine_hydrates_profile_symbols(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard_engine.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("it-tender-configuration-tender-profile", source)
		self.assertIn("STEP_ROUTE_MAP", source)
		self.assertIn("TENDER_PROFILE", source)
		self.assertIn("hydrate_profile_context", source)
		self.assertIn("hydrate_profile_form", source)
		self.assertIn("hydrate_profile_sidebar", source)
		self.assertIn("harmonize_tender_profile_page_layout", source)
		self.assertIn("data-itw-profile-context", source)
		self.assertIn("data-itw-profile-form", source)
		self.assertIn("data-itw-profile-sidebar", source)
		self.assertIn("data-itw-profile-actions", source)
		self.assertIn("fetch_tender_profile_data", source)
		self.assertIn("get_tender_profile_api", source)
		self.assertIn("save_tender_profile_api", source)
		self.assertIn("apply_profile_payload", source)
		self.assertIn("profile_payload_data", source)
		self.assertIn("reset_profile_toggle_node", source)
		self.assertIn("strip_profile_fixture_scripts", source)

	def test_profile_page_css_hides_frappe_page_head(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"css",
			"it_wizard_tender_profile_page.css",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("body.it-wizard-tender-profile-shell .page-head", source)
		self.assertIn("display: none !important", source)


class TestItWizardTenderProfileDeskWiringSite(IntegrationTestCase):
	def test_profile_page_exists_on_site(self) -> None:
		self.assertTrue(frappe.db.exists("Page", "it-tender-configuration-tender-profile"))
