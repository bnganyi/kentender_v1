# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG-0620 — advanced catalogue + technical JSON access layout guard."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import UnitTestCase


def _app_public(*parts: str) -> Path:
	return Path(frappe.get_app_path("kentender_procurement")).joinpath("public", *parts)


class TestStdConfigAdvancedAccessLayoutGuard(UnitTestCase):
	def test_boot_exposes_technical_access_flags(self) -> None:
		from kentender_procurement.tender_management.services.std_config_ui_feature import (
			expose_std_config_ui_boot,
		)

		boot: dict = {}
		expose_std_config_ui_boot(boot)
		proc = boot.get("kentender_procurement") or {}
		for key in (
			"std_technical_view_roles",
			"std_advanced_catalogue_roles",
			"std_configurator_write_roles",
			"can_use_std_advanced_catalogue",
			"can_view_technical_json",
			"can_edit_technical_json",
		):
			self.assertIn(key, proc, msg=key)

	def test_v2_library_disclosure_markers(self) -> None:
		source = _app_public("js", "std_config", "std_library_page.js").read_text(encoding="utf-8")
		for marker in (
			"std-library-advanced-view-toggle",
			"std-library-advanced-catalogue-open",
			"canUseStdAdvancedCatalogue",
			"_advancedDisclosureHtml",
		):
			self.assertIn(marker, source, msg=marker)

	def test_advanced_page_bootstrap_markers(self) -> None:
		source = _app_public("js", "std_engine_advanced_page.js").read_text(encoding="utf-8")
		for marker in (
			'frappe.pages["std-engine-advanced"]',
			"shell.mountInto",
			"canUseStdAdvancedCatalogue",
		):
			self.assertIn(marker, source, msg=marker)

	def test_advanced_page_js_hook_order(self) -> None:
		paths = frappe.get_hooks("page_js", default={}).get("std-engine-advanced") or []
		self.assertIn("public/js/std_library/std_library_shell.js", paths)
		self.assertIn("public/js/std_engine_advanced_page.js", paths)
		self.assertLess(
			paths.index("public/js/std_library/std_library_shell.js"),
			paths.index("public/js/std_engine_advanced_page.js"),
		)
		self.assertLess(
			paths.index("public/js/std_library/summary_data.js"),
			paths.index("public/js/std_library/std_library_api.js"),
		)
		self.assertLess(
			paths.index("public/js/std_library/templates_data.js"),
			paths.index("public/js/std_library/std_library_api.js"),
		)

	def test_desk_boot_no_list_redirect(self) -> None:
		source = _app_public("js", "std_engine_desk_boot.js").read_text(encoding="utf-8")
		self.assertNotIn('set_route("List", "STD Template")', source)

	def test_shared_ui_technical_json_editor_markers(self) -> None:
		source = _app_public("js", "std_config", "std_configurator_shared_ui.js").read_text(
			encoding="utf-8"
		)
		for marker in (
			"data-kt-std-technical-json-editor",
			"data-kt-std-technical-json-save",
			"kt-std-cfg-technical-json-toolbar",
		):
			self.assertIn(marker, source, msg=marker)

	def test_advanced_detail_crosslink_marker(self) -> None:
		source = _app_public("js", "std_library", "std_library_shell_detail_renderers.js").read_text(
			encoding="utf-8"
		)
		self.assertIn("std-advanced-open-technical-json", source)

	def test_advanced_renderer_projects_section_tables_and_raw_json(self) -> None:
		source = _app_public("js", "std_library", "std_library_shell_detail_renderers.js").read_text(
			encoding="utf-8"
		)
		for marker in (
			"std-advanced-section-table",
			"std-advanced-raw-package-json",
			"renderSectionTable",
		):
			self.assertIn(marker, source, msg=marker)

	def test_save_technical_json_api_whitelisted(self) -> None:
		from kentender_procurement.tender_management.api import std_configurator as cfg_api

		self.assertTrue(hasattr(cfg_api, "save_std_configurator_technical_json"))
