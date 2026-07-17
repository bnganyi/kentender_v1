# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT Wizard UI layout guard — Validation Report screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.it_tender_wizard.tests.it_wizard_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestItWizardUiValidationReportLayoutGuard(UnitTestCase):
	"""Deployed it_wizard_validation_report.html must match design verbatim."""

	def test_deployed_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("12 validation-report"),
			deployed_asset_path("it_wizard_validation_report.html"),
		)

	def test_preserves_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_validation_report.html"))
		self.assertIn("Validation Report", deployed)
		self.assertIn("Validation Findings", deployed)
		self.assertIn("Run Full Validation", deployed)

	def test_preserves_inline_script_or_config(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_validation_report.html"))
		self.assertIn('id="tailwind-config"', deployed)
