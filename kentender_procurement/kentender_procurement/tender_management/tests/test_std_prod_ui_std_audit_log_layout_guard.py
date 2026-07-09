# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod UI layout guard — Audit Log screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.tests.std_prod_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestStdProdUiStdAuditLogLayoutGuard(UnitTestCase):
	def test_deployed_audit_log_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("22. Audit Log"),
			deployed_asset_path("std_audit_log.html"),
		)

	def test_audit_log_preserves_title_and_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("std_audit_log.html"))
		self.assertIn("<title>Audit Log | KenTender STD Engine</title>", deployed)
		self.assertIn("Audit Log", deployed)
		self.assertIn("Audit Events", deployed)

	def test_audit_log_preserves_filter_icon_script(self) -> None:
		deployed = read_text(deployed_asset_path("std_audit_log.html"))
		self.assertIn("icon.addEventListener('click'", deployed)
