# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — STD Library screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdLibraryLayoutGuard(UnitTestCase):
	"""Deployed std_library.html must match ui/1. std-lib/code.html verbatim."""

	def test_deployed_library_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("1. std-lib"),
			deployed_asset_path("std_library.html"),
		)

	def test_library_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_library.html"))
		self.assertIn("<title>STD Library | KenTender STD Engine</title>", deployed)
		self.assertIn("Standard Tender Documents", deployed)
		self.assertIn("STD FAMILIES", deployed)
		self.assertIn("Family Code", deployed)
		self.assertIn('id="filter-drawer"', deployed)
		self.assertIn("filter-drawer').classList.remove", deployed)

	def test_library_preserves_inline_interaction_script(self) -> None:
		deployed = read_text(deployed_asset_path("std_library.html"))
		self.assertIn("Action menu triggered for row", deployed)
		self.assertIn("btn.addEventListener('mousedown'", deployed)
