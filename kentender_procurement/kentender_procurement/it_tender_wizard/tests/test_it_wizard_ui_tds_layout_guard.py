# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT Wizard UI layout guard — TDS screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.it_tender_wizard.tests.it_wizard_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestItWizardUiTdsLayoutGuard(UnitTestCase):
	"""Deployed it_wizard_tds.html must match design verbatim."""

	def test_deployed_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("04 tds"),
			deployed_asset_path("it_wizard_tds.html"),
		)

	def test_preserves_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_tds.html"))
		self.assertIn("Tender Data Sheet", deployed)
		self.assertIn("1. Tender Identity", deployed)
		self.assertIn("2. Eligibility &amp; Participation", deployed)
		self.assertIn("Save TDS", deployed)

	def test_preserves_inline_script_or_config(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_tds.html"))
		self.assertIn("blockerAlert.classList.add('animate-bounce')", deployed)
