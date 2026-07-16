# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT Wizard UI layout guard — Dashboard screen (v2 Screen 01)."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.it_tender_wizard.tests.it_wizard_ui_layout_guard_util import (
	assert_verbatim_deploy,
	dashboard_design_source_path,
	deployed_asset_path,
	read_text,
)


class TestItWizardUiDashboardLayoutGuard(UnitTestCase):
	"""Deployed it_wizard_dashboard.html must match v2 Screen 01 design verbatim."""

	def test_deployed_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			dashboard_design_source_path(),
			deployed_asset_path("it_wizard_dashboard.html"),
		)

	def test_preserves_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_dashboard.html"))
		self.assertIn("IT Tender Configurations", deployed)
		self.assertIn("Needs Action", deployed)
		self.assertIn("Create Tender Configuration", deployed)
		self.assertIn('id="create-modal"', deployed)
		self.assertIn("Ready for Review", deployed)
		self.assertIn("Publication Ready", deployed)

	def test_preserves_create_modal_shell(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_dashboard.html"))
		self.assertIn("Tender Shell / Tender Ref", deployed)
		self.assertIn("STD Package", deployed)
