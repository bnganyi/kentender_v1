# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — Validation Report screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdValidationReportLayoutGuard(UnitTestCase):
	def test_deployed_validation_report_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("17. Validation Report"),
			deployed_asset_path("std_validation_report.html"),
		)

	def test_validation_report_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_validation_report.html"))
		self.assertIn("<title>Validation Report | KenTender STD Engine</title>", deployed)
		self.assertIn("Validation Report", deployed)
		self.assertIn("Standard Validation Audit", deployed)

	def test_validation_report_preserves_row_click_script(self) -> None:
		deployed = read_text(deployed_asset_path("std_validation_report.html"))
		self.assertIn("row.addEventListener('click'", deployed)
