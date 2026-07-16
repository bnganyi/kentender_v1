# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT Wizard UI layout guard — IT Requirements screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.it_tender_wizard.tests.it_wizard_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestItWizardUiItRequirementsLayoutGuard(UnitTestCase):
	"""Deployed it_wizard_it_requirements.html must match design verbatim."""

	def test_deployed_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("05 it-requirements"),
			deployed_asset_path("it_wizard_it_requirements.html"),
		)

	def test_preserves_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_it_requirements.html"))
		self.assertIn("Requirements Guidance", deployed)
		self.assertIn("Define clear bidder-facing IT requirements", deployed)
		self.assertIn("3.0 Technical Requirements", deployed)
		self.assertIn("data-itw-req-drawer-hidden", deployed)
		self.assertIn("data-itw-req-guidance", deployed)
		self.assertIn("Continue to Implementation Schedule", deployed)
		self.assertIn("Bidder Evidence", deployed)
		self.assertIn("Acceptance Criteria", deployed)

	def test_forbidden_evaluation_form_labels_absent(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_it_requirements.html"))
		self.assertNotIn("Evidence Set", deployed)
		self.assertNotIn("Acceptance Set", deployed)
		self.assertNotIn("Scored (15%)", deployed)
		self.assertNotIn("Configuration Stats", deployed)
		self.assertNotIn("technical specifications for bidder evaluation", deployed)

	def test_preserves_inline_script_or_config(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_it_requirements.html"))
		self.assertIn('id="tailwind-config"', deployed)
