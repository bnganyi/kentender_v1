# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — Section and Clause Map screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdSectionClausesLayoutGuard(UnitTestCase):
	"""Deployed std_section_clauses.html must match ui/5. section-clauses/code.html verbatim."""

	def test_deployed_section_clauses_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("05. section-clauses"),
			deployed_asset_path("std_section_clauses.html"),
		)

	def test_section_clauses_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_section_clauses.html"))
		self.assertIn("<title>Section and Clause Map | KenTender STD Engine</title>", deployed)
		self.assertIn("Section and Clause Map", deployed)
		self.assertIn("Section 1: Instructions to Tenderers", deployed)
		self.assertIn("Clause Map: Section 1", deployed)

	def test_section_clauses_preserves_row_click_script(self) -> None:
		deployed = read_text(deployed_asset_path("std_section_clauses.html"))
		self.assertIn("row.addEventListener('click'", deployed)
		self.assertIn("summary.addEventListener('click'", deployed)
