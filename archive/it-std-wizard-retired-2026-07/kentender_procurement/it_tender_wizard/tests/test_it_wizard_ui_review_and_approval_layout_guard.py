# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT Wizard UI layout guard — Review and Approval screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.it_tender_wizard.tests.it_wizard_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestItWizardUiReviewAndApprovalLayoutGuard(UnitTestCase):
	"""Deployed it_wizard_review_and_approval.html must match design verbatim."""

	def test_deployed_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("13 review-and-approval"),
			deployed_asset_path("it_wizard_review_and_approval.html"),
		)

	def test_preserves_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_review_and_approval.html"))
		self.assertIn("Review &amp; Approval", deployed)
		self.assertIn("Approval Workflow Tracker", deployed)
		self.assertIn("Continue to Render Preview", deployed)

	def test_preserves_inline_script_or_config(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_review_and_approval.html"))
		self.assertIn('id="tailwind-config"', deployed)
