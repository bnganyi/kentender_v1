# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT Wizard UI layout guard — Forms and Evidence screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.it_tender_wizard.tests.it_wizard_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestItWizardUiFormsAndEvidenceLayoutGuard(UnitTestCase):
	"""Deployed it_wizard_forms_and_evidence.html must match design verbatim."""

	def test_deployed_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("10 forms-and-evidence"),
			deployed_asset_path("it_wizard_forms_and_evidence.html"),
		)

	def test_preserves_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_forms_and_evidence.html"))
		self.assertIn("Forms &amp; Evidence", deployed)
		self.assertIn("Standard Tender Forms", deployed)
		self.assertIn("Continue to SCC / Contract Carry-Forward", deployed)

	def test_preserves_inline_script_or_config(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_forms_and_evidence.html"))
		self.assertIn('function toggleDrawer()', deployed)
