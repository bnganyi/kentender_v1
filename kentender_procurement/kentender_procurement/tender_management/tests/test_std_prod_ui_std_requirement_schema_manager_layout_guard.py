# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — Requirement Schema Manager screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdRequirementSchemaManagerLayoutGuard(UnitTestCase):
	def test_deployed_requirement_schema_manager_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("13. Requirement Schema Manager"),
			deployed_asset_path("std_requirement_schema_manager.html"),
		)

	def test_requirement_schema_manager_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_requirement_schema_manager.html"))
		self.assertIn("<title>Requirement Schema Manager - KenTender Bureau</title>", deployed)
		self.assertIn("Requirement Schema Manager", deployed)
		self.assertIn("Requirement Categories", deployed)
		self.assertIn("Evaluation Linkage Model", deployed)

	def test_requirement_schema_manager_preserves_row_click_script(self) -> None:
		deployed = read_text(deployed_asset_path("std_requirement_schema_manager.html"))
		self.assertIn("row.addEventListener('click'", deployed)
		self.assertIn("DOMContentLoaded", deployed)
