# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG layout guard — library catalogue 1.lib mockup region markers."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import UnitTestCase


def _library_js_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_procurement"))
		/ "public"
		/ "js"
		/ "std_config"
		/ "std_library_page.js"
	)


def _library_css_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_procurement"))
		/ "public"
		/ "css"
		/ "std_library_page.css"
	)


class TestStdConfigLibraryLayoutGuard(UnitTestCase):
	"""Markers map 1:1 to apps/kentender_v1/docs/prompts/std config/1. lib/code.html regions."""

	def test_library_js_exposes_mockup_region_markers(self) -> None:
		source = _library_js_path().read_text(encoding="utf-8", errors="replace")
		for marker in (
			'data-testid="kt-std-lib-topbar"',
			'data-testid="kt-std-lib-body"',
			'data-testid="kt-std-lib-topbar-title"',
			'data-testid="kt-std-lib-topbar-notifications"',
			'data-testid="kt-std-lib-topbar-history"',
			'data-testid="kt-std-lib-topbar-help"',
			'data-testid="kt-std-lib-topbar-user"',
			'data-testid="kt-std-lib-page-header"',
			'data-testid="kt-std-lib-bento"',
			'testid: "kt-std-lib-kpi-total"',
			'testid: "kt-std-lib-kpi-active"',
			'testid: "kt-std-lib-kpi-pending"',
			'testid: "kt-std-lib-kpi-review"',
			'data-testid="kt-std-lib-health-panel"',
			'data-testid="kt-std-lib-filter-bar"',
			'data-testid="kt-std-lib-search-wrap"',
			'data-testid="kt-std-lib-filter-btn"',
			'data-testid="kt-std-lib-create-btn"',
			'data-testid="kt-std-lib-table-wrap"',
			'data-testid="kt-std-lib-col-method"',
			'data-testid="kt-std-lib-col-actions"',
			'data-testid="kt-std-lib-pagination"',
			'data-testid="kt-std-lib-pagination-summary"',
			'data-testid="kt-std-lib-pagination-size"',
			'data-testid="kt-std-lib-pagination-pages"',
			'placeholder="Search STDs..."',
			"Standard Tender Documents",
			"STD Library Health",
			"View Configuration",
		):
			self.assertIn(marker, source, msg=marker)

	def test_library_js_filter_bar_matches_mockup(self) -> None:
		source = _library_js_path().read_text(encoding="utf-8", errors="replace")
		self.assertNotIn('data-testid="kt-std-lib-filter-panel"', source)
		filter_start = source.index('data-testid="kt-std-lib-filter-bar"')
		filter_end = source.index('data-testid="kt-std-lib-table-wrap"')
		filter_bar = source[filter_start:filter_end]
		self.assertNotIn("Import Package", filter_bar)
		self.assertNotIn("data-kt-std-import", filter_bar)

	def test_shared_js_exposes_status_pill_marker(self) -> None:
		shared_path = (
			Path(frappe.get_app_path("kentender_procurement"))
			/ "public"
			/ "js"
			/ "std_config"
			/ "std_config_shared.js"
		)
		source = shared_path.read_text(encoding="utf-8", errors="replace")
		self.assertIn('data-testid="kt-std-lib-status-pill"', source)

	def test_library_css_exposes_mockup_region_classes(self) -> None:
		source = _library_css_path().read_text(encoding="utf-8", errors="replace")
		for selector in (
			".kt-std-lib-topbar",
			".kt-std-lib-body",
			".kt-std-lib-page-header",
			".kt-std-lib-bento",
			".kt-std-lib-health",
			".kt-std-lib-filter-bar",
			".kt-std-lib-search-wrap",
			".kt-std-lib-table-wrap",
			".kt-std-lib-th",
			".kt-std-lib-th--actions",
			".kt-std-lib-pagination",
			".kt-std-lib-pagination__pages",
			".kt-std-lib-pagination__page-btn",
			".kt-std-lib-pagination__page-btn--active",
			".kt-std-lib-pagination__ellipsis",
			".kt-std-lib-row-title",
			".kt-std-status-pill__dot",
			".kt-std-status-pill--available",
			".kt-std-status-pill--committed",
		):
			self.assertIn(selector, source, msg=selector)

	def test_library_css_topbar_is_sticky(self) -> None:
		source = _library_css_path().read_text(encoding="utf-8", errors="replace")
		topbar_block = source.split(".kt-std-lib-topbar {", 1)[1].split("}", 1)[0]
		self.assertIn("position: sticky", topbar_block)
		self.assertIn("top: 0", topbar_block)
