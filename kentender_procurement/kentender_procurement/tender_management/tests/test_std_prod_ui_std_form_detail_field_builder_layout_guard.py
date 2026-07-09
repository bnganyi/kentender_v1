# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — Form Detail & Field Builder screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdFormDetailFieldBuilderLayoutGuard(UnitTestCase):
	"""Deployed std_form_detail_field_builder.html must match ui/12. Form Detail & Field Builder/code.html verbatim."""

	def test_deployed_form_detail_field_builder_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("12. Form Detail & Field Builder"),
			deployed_asset_path("std_form_detail_field_builder.html"),
		)

	def test_form_detail_field_builder_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_form_detail_field_builder.html"))
		self.assertIn(
			"<title>Form Detail &amp; Field Builder | KenTender STD Engine</title>",
			deployed,
		)
		self.assertIn("Technical Proposal Submission", deployed)
		self.assertIn("Field Configuration", deployed)

	def test_form_detail_field_builder_preserves_button_scale_script(self) -> None:
		deployed = read_text(deployed_asset_path("std_form_detail_field_builder.html"))
		self.assertIn("btn.addEventListener('mousedown'", deployed)
		self.assertIn("scale(0.98)", deployed)
