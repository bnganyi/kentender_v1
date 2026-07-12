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
		self.assertIn('// Mock interaction: clicking any row opens the drawer', deployed)
