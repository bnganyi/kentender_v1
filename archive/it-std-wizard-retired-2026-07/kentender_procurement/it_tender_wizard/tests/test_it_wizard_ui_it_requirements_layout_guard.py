# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT Wizard UI layout guard — Screen 03 IT Requirements (v2)."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.it_tender_wizard.tests.it_wizard_ui_layout_guard_util import (
	assert_it_requirements_reference_deploy,
	deployed_asset_path,
	it_requirements_design_source_path,
	read_text,
)


class TestItWizardUiItRequirementsLayoutGuard(UnitTestCase):
	"""Deployed it_wizard_it_requirements.html must match v2 Screen 03 design."""

	def test_deployed_matches_design_verbatim(self) -> None:
		assert_it_requirements_reference_deploy(
			it_requirements_design_source_path(),
			deployed_asset_path("it_wizard_it_requirements.html"),
		)

	def test_preserves_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_it_requirements.html"))
		self.assertIn("IT Requirements", deployed)
		self.assertIn("Define what bidders must supply, deliver, integrate, support, or prove.", deployed)
		self.assertIn("Requirements Guidance", deployed)
		self.assertIn("Add Requirement", deployed)
		self.assertIn("Import Requirements Template", deployed)
		self.assertIn("Continue to Implementation Schedule", deployed)
		self.assertIn("Section A — Requirement", deployed)
		self.assertIn("Section B — Bidder Response", deployed)
		self.assertIn("Section C — Evidence", deployed)
		self.assertIn("Section D — Acceptance", deployed)
		self.assertIn("References", deployed)
		self.assertIn("data-itw-req-context", deployed)
		self.assertIn("data-itw-req-table-host", deployed)
		self.assertIn("data-itw-req-drawer", deployed)
		self.assertIn("data-itw-req-guidance", deployed)
		self.assertIn("data-itw-req-actions", deployed)

	def test_forbidden_evaluation_form_labels_absent(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_it_requirements.html"))
		self.assertNotIn("Evidence Set", deployed)
		self.assertNotIn("Acceptance Set", deployed)
		self.assertNotIn("Scored (15%)", deployed)
		self.assertNotIn("Configuration Stats", deployed)
		self.assertNotIn("technical specifications for bidder evaluation", deployed)
		self.assertNotIn("Edit in Evaluation Setup", deployed)
		self.assertNotIn("3.0 Technical Requirements", deployed)

	def test_native_reference_has_no_tailwind_cdn(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_it_requirements.html"))
		self.assertNotIn("cdn.tailwindcss.com", deployed)
		self.assertNotIn('id="tailwind-config"', deployed)
