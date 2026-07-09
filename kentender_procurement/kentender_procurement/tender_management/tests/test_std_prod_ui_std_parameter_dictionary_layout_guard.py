# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — Parameter Dictionary screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdParameterDictionaryLayoutGuard(UnitTestCase):
	"""Deployed std_parameter_dictionary.html must match ui/07. parameter-dictionary/code.html verbatim."""

	def test_deployed_parameter_dictionary_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("07. parameter-dictionary"),
			deployed_asset_path("std_parameter_dictionary.html"),
		)

	def test_parameter_dictionary_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_parameter_dictionary.html"))
		self.assertIn("<title>Parameter Dictionary | KenTender STD Engine</title>", deployed)
		self.assertIn("Parameter Dictionary", deployed)
		self.assertIn("tender_ref_id", deployed)

	def test_parameter_dictionary_preserves_sort_and_button_scripts(self) -> None:
		deployed = read_text(deployed_asset_path("std_parameter_dictionary.html"))
		self.assertIn("btn.addEventListener('mousedown'", deployed)
		self.assertIn("th.addEventListener('click'", deployed)
