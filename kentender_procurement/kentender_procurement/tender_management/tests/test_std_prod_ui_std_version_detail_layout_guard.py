# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — STD Version Detail screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdVersionDetailLayoutGuard(UnitTestCase):
	"""Deployed std_version_detail.html must match ui/3. std-version-detail/code.html verbatim."""

	def test_deployed_version_detail_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("3. std-version-detail"),
			deployed_asset_path("std_version_detail.html"),
		)

	def test_version_detail_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_version_detail.html"))
		self.assertIn("<title>STD Version Detail | KenTender STD Engine</title>", deployed)
		self.assertIn("ACTIVE VERSION — READ ONLY", deployed)
		self.assertIn("Module Integrity Status", deployed)
		self.assertIn("Operational Integrity", deployed)
		self.assertIn("KE-PPRA-IT-2024-01", deployed)

	def test_version_detail_preserves_button_scale_script(self) -> None:
		deployed = read_text(deployed_asset_path("std_version_detail.html"))
		self.assertIn("scale-95", deployed)
		self.assertIn("setTimeout(() => this.classList.remove('scale-95')", deployed)
