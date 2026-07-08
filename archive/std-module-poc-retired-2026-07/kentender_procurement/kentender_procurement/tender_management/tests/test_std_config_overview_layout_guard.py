# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG — Overview tab layout guard (2. overview/code.html structure)."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import UnitTestCase


def _tab_renderers_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_procurement"))
		/ "public"
		/ "js"
		/ "std_config"
		/ "std_configurator_tab_renderers.js"
	)


def _shared_ui_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_procurement"))
		/ "public"
		/ "js"
		/ "std_config"
		/ "std_configurator_shared_ui.js"
	)


def _mockup_css_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_procurement"))
		/ "public"
		/ "css"
		/ "std_configurator_mockup.css"
	)


class TestStdConfigOverviewLayoutGuard(UnitTestCase):
	def test_overview_tab_markers_in_renderer(self) -> None:
		source = _tab_renderers_path().read_text(encoding="utf-8", errors="replace")
		for marker in (
			'data-testid="kt-std-cfg-overview"',
			'ui.identityCard(__("Document Identity")',
			"ui.guidanceRow",
			"ui.appliesToSection",
			"ui.tabFooterHtml",
			'"document_family"',
			'"procurement_category"',
			'"procurement_method"',
			'"version_label"',
			'"effective_date"',
			'"change_summary"',
		):
			self.assertIn(marker, source, msg=marker)
		self.assertNotIn('fieldTextarea("description"', source)

	def test_overview_shared_ui_markers(self) -> None:
		source = _shared_ui_path().read_text(encoding="utf-8", errors="replace")
		for marker in (
			'data-testid="kt-std-cfg-identity-card"',
			'data-testid="kt-std-cfg-progress-card"',
			'data-testid="kt-std-cfg-applies-to-preview"',
			'data-testid="kt-std-cfg-applies-copy"',
			"Expert Tip: Version Control",
			"Applies To Preview",
			"kt-std-cfg-applies-footnote",
			"fieldDate",
		):
			self.assertIn(marker, source, msg=marker)

	def test_overview_mockup_css_regions(self) -> None:
		source = _mockup_css_path().read_text(encoding="utf-8", errors="replace")
		for selector in (
			".kt-std-cfg-tabbar-wrap",
			".kt-std-cfg-date-wrap",
			".kt-std-cfg-applies-copy",
			".kt-std-cfg-applies-footnote",
			".kt-std-cfg-progress-card__glow",
		):
			self.assertIn(selector, source, msg=selector)
