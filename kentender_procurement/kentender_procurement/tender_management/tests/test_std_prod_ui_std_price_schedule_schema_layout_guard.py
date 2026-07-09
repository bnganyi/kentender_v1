# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — Price Schedule Schema screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdPriceScheduleSchemaLayoutGuard(UnitTestCase):
	def test_deployed_price_schedule_schema_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("14. Price Schedule Schema"),
			deployed_asset_path("std_price_schedule_schema.html"),
		)

	def test_price_schedule_schema_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_price_schedule_schema.html"))
		self.assertIn("<title>Price Schedule Schema | KenTender STD Engine</title>", deployed)
		self.assertIn("Price Schedule Master Definition", deployed)
		self.assertIn("System Integrity Log", deployed)
		self.assertIn("REVISION CONTEXT", deployed)

	def test_price_schedule_schema_preserves_search_script(self) -> None:
		deployed = read_text(deployed_asset_path("std_price_schedule_schema.html"))
		self.assertIn("searchInput.addEventListener('input'", deployed)
