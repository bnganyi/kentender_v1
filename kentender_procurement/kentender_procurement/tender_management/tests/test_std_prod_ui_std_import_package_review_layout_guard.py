# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — Import Package Review screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdImportPackageReviewLayoutGuard(UnitTestCase):
	def test_deployed_import_package_review_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("20. Import Package Review"),
			deployed_asset_path("std_import_package_review.html"),
		)

	def test_import_package_review_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_import_package_review.html"))
		self.assertIn("<title>Import Package Review | KenTender STD Engine</title>", deployed)
		self.assertIn("Import Package Review", deployed)
		self.assertIn("Upload Standardized Package", deployed)

	def test_import_package_review_preserves_button_click_script(self) -> None:
		deployed = read_text(deployed_asset_path("std_import_package_review.html"))
		self.assertIn("btn.addEventListener('click'", deployed)
