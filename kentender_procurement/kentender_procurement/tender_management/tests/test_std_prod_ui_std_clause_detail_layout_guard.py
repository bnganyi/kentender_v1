# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — Clause Detail screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdClauseDetailLayoutGuard(UnitTestCase):
	"""Deployed std_clause_detail.html must match ui/6. clause-detail/code.html verbatim."""

	def test_deployed_clause_detail_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("06. clause-detail"),
			deployed_asset_path("std_clause_detail.html"),
		)

	def test_clause_detail_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_clause_detail.html"))
		self.assertIn("<title>Clause Detail - KenTender STD Engine</title>", deployed)
		self.assertIn("Eligible Tenderers", deployed)
		self.assertIn("Audit History", deployed)
		self.assertIn("Clause Topology", deployed)
		self.assertIn("IMMUTABLE_CORE_v2.1", deployed)

	def test_clause_detail_preserves_button_interaction_script(self) -> None:
		deployed = read_text(deployed_asset_path("std_clause_detail.html"))
		self.assertIn("button.addEventListener('mousedown'", deployed)
		self.assertIn("scale-[0.98]", deployed)
