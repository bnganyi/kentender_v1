# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — Evaluation Schema screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdEvaluationSchemaLayoutGuard(UnitTestCase):
	def test_deployed_evaluation_schema_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("15. Evaluation Schema"),
			deployed_asset_path("std_evaluation_schema.html"),
		)

	def test_evaluation_schema_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_evaluation_schema.html"))
		self.assertIn("<title>Evaluation Schema - KenTender STD Engine</title>", deployed)
		self.assertIn("Evaluation Schema", deployed)
		self.assertIn("TOTAL CRITERIA", deployed)

	def test_evaluation_schema_preserves_tab_click_script(self) -> None:
		deployed = read_text(deployed_asset_path("std_evaluation_schema.html"))
		self.assertIn("tab.addEventListener('click'", deployed)
		self.assertIn("btn.addEventListener('click'", deployed)
