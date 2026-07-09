# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — Usage and Tender Bindings screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdUsageAndTenderBindingsLayoutGuard(UnitTestCase):
	def test_deployed_usage_and_tender_bindings_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("19. Usage and Tender Bindings"),
			deployed_asset_path("std_usage_and_tender_bindings.html"),
		)

	def test_usage_and_tender_bindings_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_usage_and_tender_bindings.html"))
		self.assertIn("<title>Usage and Tender Bindings | KenTender STD Engine</title>", deployed)
		self.assertIn("Usage and Tender Bindings", deployed)
		self.assertIn("ACTIVE TENDERS (THIS VERSION)", deployed)

	def test_usage_and_tender_bindings_preserves_row_click_script(self) -> None:
		deployed = read_text(deployed_asset_path("std_usage_and_tender_bindings.html"))
		self.assertIn("row.addEventListener('click'", deployed)
