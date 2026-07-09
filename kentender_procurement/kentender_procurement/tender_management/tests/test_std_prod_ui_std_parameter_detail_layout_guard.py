# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — Parameter Detail screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdParameterDetailLayoutGuard(UnitTestCase):
	"""Deployed std_parameter_detail.html must match ui/08. parameter-detail/code.html verbatim."""

	def test_deployed_parameter_detail_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("08. parameter-detail"),
			deployed_asset_path("std_parameter_detail.html"),
		)

	def test_parameter_detail_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_parameter_detail.html"))
		self.assertIn("<title>Parameter Detail | KenTender STD Engine</title>", deployed)
		self.assertIn("Tender Reference ID", deployed)
		self.assertIn("tender_ref_id", deployed)
		self.assertIn("FIELD DEFINITION", deployed)
		self.assertIn("VALIDATION RULES", deployed)

	def test_parameter_detail_preserves_card_hover_script(self) -> None:
		deployed = read_text(deployed_asset_path("std_parameter_detail.html"))
		self.assertIn("card.addEventListener('mouseenter'", deployed)
		self.assertIn("card.addEventListener('mouseleave'", deployed)
