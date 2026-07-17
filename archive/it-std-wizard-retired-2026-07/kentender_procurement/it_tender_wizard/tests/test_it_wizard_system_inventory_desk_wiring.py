# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-DESK-INV-001/002 — Desk wiring for System Inventory."""

from __future__ import annotations

import os

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase


class TestItWizardSystemInventoryDeskWiring(UnitTestCase):
	def test_hooks_register_system_inventory_assets(self) -> None:
		from kentender_procurement.hooks import app_include_css, page_js

		self.assertEqual(
			page_js.get("it-tender-configuration-system-inventory"),
			"public/js/it_wizard_system_inventory_page.js",
		)
		self.assertTrue(any("it_wizard_system_inventory_page.css" in asset for asset in app_include_css))

	def test_system_inventory_page_js_embeds_stable_static_asset_iframe(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard_system_inventory_page.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn('frappe.pages["it-tender-configuration-system-inventory"]', source)
		self.assertIn(
			"/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_system_inventory.html",
			source,
		)
		self.assertIn('testid: "it-wizard-system-inventory"', source)
		self.assertIn("kentender.it_wizard.mount_page", source)
		self.assertIn('screen: "system_inventory"', source)

	def test_engine_hydrates_system_inventory_contract(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard_engine.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("it-tender-configuration-system-inventory", source)
		self.assertIn('SYSTEM_INVENTORY: "it-tender-configuration-system-inventory"', source)
		self.assertIn("harmonize_system_inventory_page_layout", source)
		self.assertIn("data-itw-inv-context", source)
		self.assertIn("data-itw-inv-drawer", source)
		self.assertIn("data-itw-inv-guidance", source)
		self.assertIn("fetch_system_inventory_data", source)
		self.assertIn("get_system_inventory_api", source)
		self.assertIn("save_system_inventory_api", source)
		self.assertIn("apply_system_inventory_payload", source)
		self.assertIn("wire_system_inventory_interactions", source)
		self.assertIn("open_system_inventory_drawer", source)
		self.assertIn("close_system_inventory_drawer", source)
		self.assertIn("PRICE_REQUIRED", source)
		self.assertIn("PRICE_OPTIONAL", source)
		self.assertIn("NOT_PRICED", source)
		self.assertNotIn("data-itw-inv-field=\"quantity\"", source)
		self.assertNotIn("data-itw-inv-field=\"unit\"", source)
		self.assertNotIn("data-itw-inv-field=\"pricing_class\"", source)

	def test_system_inventory_page_css_hides_frappe_page_head(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"css",
			"it_wizard_system_inventory_page.css",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("body.it-wizard-system-inventory-shell .page-head", source)
		self.assertIn("display: none !important", source)


class TestItWizardSystemInventoryDeskWiringSite(IntegrationTestCase):
	def test_system_inventory_page_exists_on_site(self) -> None:
		self.assertTrue(frappe.db.exists("Page", "it-tender-configuration-system-inventory"))
