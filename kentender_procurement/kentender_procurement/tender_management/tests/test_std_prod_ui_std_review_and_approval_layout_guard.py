# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — Review and Approval screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdReviewAndApprovalLayoutGuard(UnitTestCase):
	def test_deployed_review_and_approval_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("18. Review and Approval"),
			deployed_asset_path("std_review_and_approval.html"),
		)

	def test_review_and_approval_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_review_and_approval.html"))
		self.assertIn("<title>Review and Approval | KenTender STD Engine</title>", deployed)
		self.assertIn("Review and Approval", deployed)
		self.assertIn("Final Approval", deployed)

	def test_review_and_approval_preserves_decision_input_script(self) -> None:
		deployed = read_text(deployed_asset_path("std_review_and_approval.html"))
		self.assertIn("decisionReason.addEventListener('input'", deployed)
