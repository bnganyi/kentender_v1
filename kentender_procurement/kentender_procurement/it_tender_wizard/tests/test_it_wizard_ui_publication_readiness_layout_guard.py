# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT Wizard UI layout guard — Publication Readiness screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.it_tender_wizard.tests.it_wizard_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestItWizardUiPublicationReadinessLayoutGuard(UnitTestCase):
	"""Deployed it_wizard_publication_readiness.html must match design verbatim."""

	def test_deployed_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("15 publication-readiness"),
			deployed_asset_path("it_wizard_publication_readiness.html"),
		)

	def test_preserves_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_publication_readiness.html"))
		self.assertIn("Publication Readiness", deployed)
		self.assertIn("Readiness Checklist", deployed)
		self.assertIn("Mark as Publication Ready", deployed)

	def test_preserves_inline_script_or_config(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_publication_readiness.html"))
		self.assertIn('id="tailwind-config"', deployed)
