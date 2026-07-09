# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — Form Schema Manager screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdFormSchemaManagerLayoutGuard(UnitTestCase):
	"""Deployed std_form_schema_manager.html must match ui/11. Form Schema Manager/code.html verbatim."""

	def test_deployed_form_schema_manager_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("11. Form Schema Manager"),
			deployed_asset_path("std_form_schema_manager.html"),
		)

	def test_form_schema_manager_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_form_schema_manager.html"))
		self.assertIn("<title>Form Schema Manager | KenTender Bureau</title>", deployed)
		self.assertIn("Form Schema Manager", deployed)
		self.assertIn("TOTAL FORMS", deployed)
		self.assertIn("FORM-TECH-01", deployed)

	def test_form_schema_manager_preserves_tab_click_script(self) -> None:
		deployed = read_text(deployed_asset_path("std_form_schema_manager.html"))
		self.assertIn("button.addEventListener('click'", deployed)
		self.assertIn("nav button", deployed)
