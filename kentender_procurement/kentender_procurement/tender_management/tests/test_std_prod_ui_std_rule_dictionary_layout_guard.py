# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — Rule Dictionary screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdRuleDictionaryLayoutGuard(UnitTestCase):
	"""Deployed std_rule_dictionary.html must match ui/09. Rule-Dictionary/code.html verbatim."""

	def test_deployed_rule_dictionary_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("09. Rule-Dictionary"),
			deployed_asset_path("std_rule_dictionary.html"),
		)

	def test_rule_dictionary_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_rule_dictionary.html"))
		self.assertIn("<title>Rule Dictionary | KenTender STD Engine</title>", deployed)
		self.assertIn("Rule Dictionary", deployed)
		self.assertIn("Rule Tests Summary", deployed)
		self.assertIn("Smoke Contracts", deployed)

	def test_rule_dictionary_preserves_search_and_row_scripts(self) -> None:
		deployed = read_text(deployed_asset_path("std_rule_dictionary.html"))
		self.assertIn("searchInput.addEventListener('input'", deployed)
		self.assertIn("row.addEventListener('mouseenter'", deployed)
