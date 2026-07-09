# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — Render Blocks screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdRenderBlocksLayoutGuard(UnitTestCase):
	def test_deployed_render_blocks_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("16. Render Blocks"),
			deployed_asset_path("std_render_blocks.html"),
		)

	def test_render_blocks_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_render_blocks.html"))
		self.assertIn("<title>KenTender STD Engine - Render Blocks</title>", deployed)
		self.assertIn("Render Blocks", deployed)
		self.assertIn("TOTAL RENDER BLOCKS", deployed)
		self.assertIn("RB-001", deployed)

	def test_render_blocks_preserves_row_click_script(self) -> None:
		deployed = read_text(deployed_asset_path("std_render_blocks.html"))
		self.assertIn("row.addEventListener('click'", deployed)
