# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT Wizard UI layout guard — System Inventory screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.it_tender_wizard.tests.it_wizard_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestItWizardUiSystemInventoryLayoutGuard(UnitTestCase):
	"""Deployed it_wizard_system_inventory.html must match design verbatim."""

	def test_deployed_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("07 system-inventory"),
			deployed_asset_path("it_wizard_system_inventory.html"),
		)

	def test_preserves_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_system_inventory.html"))
		self.assertIn("Systems &amp; Inventory Items", deployed)
		self.assertIn("Systems in Scope", deployed)
		self.assertIn("Save Inventory", deployed)
		self.assertIn("Continue to Price Schedule", deployed)

	def test_preserves_inline_script_or_config(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_system_inventory.html"))
		self.assertIn('// Mock interaction for edit buttons', deployed)
