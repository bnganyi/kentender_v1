# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG-0003 — feature flag and shared assets contract."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.std_config_ui_feature import (
	expose_std_config_ui_boot,
	is_std_config_ui_v2_enabled,
)


class TestStdConfigFoundation(IntegrationTestCase):
	def test_feature_flag_defaults_off(self) -> None:
		orig = frappe.conf.get("std_config_ui_v2_enabled")
		try:
			frappe.conf.pop("std_config_ui_v2_enabled", None)
			self.assertFalse(is_std_config_ui_v2_enabled())
		finally:
			if orig is not None:
				frappe.conf["std_config_ui_v2_enabled"] = orig

	def test_feature_flag_reads_site_config(self) -> None:
		orig = frappe.conf.get("std_config_ui_v2_enabled")
		try:
			frappe.conf["std_config_ui_v2_enabled"] = 1
			self.assertTrue(is_std_config_ui_v2_enabled())
		finally:
			if orig is not None:
				frappe.conf["std_config_ui_v2_enabled"] = orig
			else:
				frappe.conf.pop("std_config_ui_v2_enabled", None)

	def test_boot_exposes_flag(self) -> None:
		boot: dict = {}
		expose_std_config_ui_boot(boot)
		self.assertIn("kentender_procurement", boot)
		self.assertIn("std_config_ui_v2_enabled", boot["kentender_procurement"])

	def test_shared_css_exists(self) -> None:
		path = (
			Path(frappe.get_app_path("kentender_procurement"))
			/ "public"
			/ "css"
			/ "std_config_shared.css"
		)
		self.assertTrue(path.is_file())

	def test_std_library_page_exists(self) -> None:
		self.assertTrue(frappe.db.exists("Page", "std-library"))

	def test_std_configurator_page_exists(self) -> None:
		self.assertTrue(frappe.db.exists("Page", "std-configurator"))
