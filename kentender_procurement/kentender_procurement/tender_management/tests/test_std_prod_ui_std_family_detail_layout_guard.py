# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — STD Family Detail screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdFamilyDetailLayoutGuard(UnitTestCase):
	"""Deployed std_family_detail.html must match ui/2. std-family-detail/code.html verbatim."""

	def test_deployed_family_detail_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("02. std-family-detail"),
			deployed_asset_path("std_family_detail.html"),
		)

	def test_family_detail_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_family_detail.html"))
		self.assertIn("<title>KenTender STD Engine - STD Family Detail</title>", deployed)
		self.assertIn("KE-PPRA-IT", deployed)
		self.assertIn("VERSIONS REPOSITORY", deployed)
		self.assertIn("REVIEW POLICY", deployed)
		self.assertIn("STD for Procurement of Information Technology", deployed)

	def test_family_detail_preserves_governance_constraints_region(self) -> None:
		deployed = read_text(deployed_asset_path("std_family_detail.html"))
		self.assertIn("GOVERNANCE CONSTRAINTS", deployed)
		self.assertIn("MANDATORY REVIEW", deployed)
