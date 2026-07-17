# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT Wizard UI layout guard — Screen 02 Tender Configuration Home (v2)."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.it_tender_wizard.tests.it_wizard_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	overview_design_source_path,
	read_text,
)


class TestItWizardUiStdConfigOverviewLayoutGuard(UnitTestCase):
	"""Deployed it_wizard_std_config_overview.html must match v2 Screen 02 design verbatim."""

	def test_deployed_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			overview_design_source_path(),
			deployed_asset_path("it_wizard_std_config_overview.html"),
		)

	def test_preserves_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_std_config_overview.html"))
		self.assertIn("Tender Configuration Home", deployed)
		self.assertIn("Configuration Steps", deployed)
		self.assertIn("STEP 01", deployed)
		self.assertIn("Tender Profile", deployed)
		self.assertIn("STEP 13", deployed)
		self.assertIn("Publication Readiness", deployed)
		self.assertIn("Next step:", deployed)

	def test_preserves_inline_script_or_config(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_std_config_overview.html"))
		self.assertIn('id="tailwind-config"', deployed)

	def test_rejects_v1_overview_markers(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_std_config_overview.html"))
		self.assertNotIn("Tender STD Configuration Overview", deployed)
		self.assertNotIn("Governance &amp; Audit", deployed)
		self.assertNotIn("STD Control Center", deployed)
		self.assertNotIn("Configuration Matrix", deployed)
