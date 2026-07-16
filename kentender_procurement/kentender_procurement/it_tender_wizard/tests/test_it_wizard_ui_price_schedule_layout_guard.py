# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT Wizard UI layout guard — Price Schedule screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.it_tender_wizard.tests.it_wizard_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestItWizardUiPriceScheduleLayoutGuard(UnitTestCase):
	"""Deployed it_wizard_price_schedule.html must match design verbatim."""

	def test_deployed_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("08 price-schedule"),
			deployed_asset_path("it_wizard_price_schedule.html"),
		)

	def test_preserves_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_price_schedule.html"))
		self.assertIn("Download Price Schedule Preview", deployed)
		self.assertIn("Goods / Equipment", deployed)
		self.assertIn("USE STANDARD IT PRICE TEMPLATE", deployed)
		self.assertIn("CONTINUE TO EVALUATION SETUP", deployed)

	def test_preserves_inline_script_or_config(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_price_schedule.html"))
		self.assertIn("data-itw-price-drawer", deployed)
		self.assertIn("data-itw-price-field", deployed)
		self.assertIn("Drawer open/close and row binding are owned by Desk hydration", deployed)

	def test_owned_fields_do_not_show_not_configured_source(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_price_schedule.html"))
		self.assertNotIn("Source: Not configured", deployed)
		self.assertIn('data-itw-price-owned="1"', deployed)
		self.assertIn("Reference: System Inventory", deployed)
		self.assertIn("Source: Tender Profile", deployed)
		self.assertIn("translate-x-full", deployed)
