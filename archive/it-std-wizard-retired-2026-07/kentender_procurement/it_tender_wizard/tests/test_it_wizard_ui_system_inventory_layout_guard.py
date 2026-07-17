# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT Wizard UI layout guard — System Inventory screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.it_tender_wizard.tests.it_wizard_ownership_contract import (
	assert_inventory_ownership_html,
)
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
		self.assertIn("Infrastructure Environment", deployed)
		self.assertIn("User &amp; Location Scope", deployed)
		self.assertIn("Integration Points", deployed)
		self.assertIn("Data Migration Scope", deployed)
		self.assertIn("Licensing &amp; Support Context", deployed)
		self.assertIn("Security &amp; Access Context", deployed)
		self.assertIn("Out-of-Scope Items", deployed)
		self.assertIn("Save Inventory", deployed)
		self.assertIn("Continue to Price Schedule", deployed)
		self.assertIn("Price Schedule Link", deployed)
		self.assertIn("Not Priced", deployed)
		self.assertIn("Not configured", deployed)

	def test_preserves_stable_data_hooks_without_pricing_fields(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_system_inventory.html"))
		for hook in (
			"data-itw-inv-context",
			"data-itw-inv-categories",
			"data-itw-inv-table-host",
			"data-itw-inv-drawer",
			"data-itw-inv-guidance",
			"data-itw-inv-actions",
			"data-itw-inv-summary-host",
			"data-itw-inv-security-host",
		):
			self.assertIn(hook, deployed)
		assert_inventory_ownership_html(deployed, context="layout guard inventory")
		self.assertNotIn("toggleDrawer()", deployed)
