# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG layout guard — configurator shell design markers."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import UnitTestCase


def _shell_js_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_procurement"))
		/ "public"
		/ "js"
		/ "std_config"
		/ "std_configurator_shell.js"
	)


def _components_css_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_procurement"))
		/ "public"
		/ "css"
		/ "std_configurator_components.css"
	)


def _shared_ui_js_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_procurement"))
		/ "public"
		/ "js"
		/ "std_config"
		/ "std_configurator_shared_ui.js"
	)


class TestStdConfigConfiguratorLayoutGuard(UnitTestCase):
	def test_shell_js_exposes_design_markers(self) -> None:
		source = _shell_js_path().read_text(encoding="utf-8", errors="replace")
		for marker in (
			'data-testid="kt-std-cfg-topbar"',
			'data-testid="kt-std-cfg-breadcrumbs"',
			'data-testid="kt-std-cfg-doc-header"',
			"can_view_technical_json",
			"privileged: true",
		):
			self.assertIn(marker, source, msg=marker)

	def test_shared_ui_js_exposes_footer_marker(self) -> None:
		source = _shared_ui_js_path().read_text(encoding="utf-8", errors="replace")
		self.assertIn('data-testid="kt-std-cfg-footer-actions"', source)

	def test_components_css_exposes_drawer_and_footer(self) -> None:
		source = _components_css_path().read_text(encoding="utf-8", errors="replace")
		for selector in (
			".kt-std-cfg-footer",
			".kt-std-cfg-drawer",
			".kt-std-cfg-bento",
			".kt-std-cfg-stage-card",
		):
			self.assertIn(selector, source, msg=selector)
