# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — Version Diff and Supersession screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdVersionDiffAndSupersessionLayoutGuard(UnitTestCase):
	def test_deployed_version_diff_and_supersession_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("21. Version Diff and Supersession"),
			deployed_asset_path("std_version_diff_and_supersession.html"),
		)

	def test_version_diff_and_supersession_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_version_diff_and_supersession.html"))
		self.assertIn("<title>KenTender STD Engine - Version Diff and Supersession</title>", deployed)
		self.assertIn("Version Diff and Supersession", deployed)
		self.assertIn("Supersession Decision", deployed)

	def test_version_diff_and_supersession_preserves_button_click_script(self) -> None:
		deployed = read_text(deployed_asset_path("std_version_diff_and_supersession.html"))
		self.assertIn("button.addEventListener('click'", deployed)
