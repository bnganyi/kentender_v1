# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-DESK-REQ-001/002 — Desk wiring for IT Requirements composer."""

from __future__ import annotations

import os

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase


class TestItWizardItRequirementsDeskWiring(UnitTestCase):
	def test_hooks_register_it_requirements_page_js(self) -> None:
		from kentender_procurement.hooks import page_js

		self.assertEqual(
			page_js.get("it-tender-configuration-it-requirements"),
			"public/js/it_wizard_it_requirements_page.js",
		)

	def test_it_requirements_page_js_embeds_static_asset_iframe(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard_it_requirements_page.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn('frappe.pages["it-tender-configuration-it-requirements"]', source)
		self.assertIn(
			"/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_it_requirements.html",
			source,
		)
		self.assertIn('testid: "it-wizard-it-requirements"', source)
		self.assertIn("kentender.it_wizard.mount_page", source)
		self.assertIn('screen: "it_requirements"', source)

	def test_engine_hydrates_it_requirements_symbols(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard_engine.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("it-tender-configuration-it-requirements", source)
		self.assertIn("STEP_ROUTE_MAP", source)
		self.assertIn("IT_REQUIREMENTS", source)
		self.assertIn("unwrap_envelope_data", source)
		self.assertIn("harmonize_it_requirements_page_layout", source)
		self.assertIn("data-itw-req-context", source)
		self.assertIn("data-itw-req-table-host", source)
		self.assertIn("data-itw-req-drawer", source)
		self.assertIn("data-itw-req-guidance", source)
		self.assertIn("data-itw-req-actions", source)
		self.assertIn("[data-itw-req-actions]", source)
		self.assertIn("hydrate_it_requirements_guidance", source)
		self.assertIn("open_it_requirements_drawer", source)
		self.assertIn("close_it_requirements_drawer", source)
		self.assertIn("fetch_it_requirements_data", source)
		self.assertIn("get_it_requirements_api", source)
		self.assertIn("save_it_requirements_api", source)
		self.assertIn("apply_it_requirements_payload", source)
		self.assertIn("requirements_payload_data", source)
		self.assertIn("strip_it_requirements_fixture_scripts", source)
		self.assertIn("hydrate_it_requirements_context", source)
		self.assertIn("hydrate_it_requirements_table", source)
		self.assertIn("hydrate_it_requirements_drawer", source)
		self.assertIn("wire_it_requirements_interactions", source)
		self.assertIn("disable_it_requirements_stub_actions", source)
		self.assertNotIn("Evidence: Set", source)
		self.assertNotIn("Acceptance: Set", source)

	def test_it_requirements_page_css_hides_frappe_page_head(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"css",
			"it_wizard_it_requirements_page.css",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("body.it-wizard-it-requirements-shell .page-head", source)
		self.assertIn("display: none !important", source)


class TestItWizardItRequirementsDeskWiringSite(IntegrationTestCase):
	def test_it_requirements_page_exists_on_site(self) -> None:
		self.assertTrue(frappe.db.exists("Page", "it-tender-configuration-it-requirements"))
