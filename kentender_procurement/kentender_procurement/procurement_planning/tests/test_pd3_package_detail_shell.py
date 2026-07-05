# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PD3 — Package Detail shared shell + tab bar source contract."""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _package_detail_js() -> Path:
	return (
		Path(__file__).resolve().parents[2]
		/ "public"
		/ "js"
		/ "package_detail_page.js"
	)


def _package_detail_css() -> Path:
	return (
		Path(__file__).resolve().parents[2]
		/ "public"
		/ "css"
		/ "package_detail_page.css"
	)


class TestPD3PackageDetailShell(UnitTestCase):
	def test_shell_exposes_canvas_breadcrumb_footer_testids(self) -> None:
		source = _package_detail_js().read_text(encoding="utf-8", errors="replace")
		for tid in (
			"kt-pd-canvas",
			"kt-pd-breadcrumb",
			"kt-pd-meta",
			"kt-pd-footer",
		):
			self.assertIn(tid, source, msg=f"missing {tid} (PD3)")

	def test_header_title_and_status_pill_share_title_row(self) -> None:
		source = _package_detail_js().read_text(encoding="utf-8", errors="replace")
		shell_block = source.split("function _shellHtml", 1)[1].split("function _runAction", 1)[0]
		self.assertIn("kt-pd-header__title-row", shell_block)
		title_pos = shell_block.index("kt-pd-title")
		pill_pos = shell_block.index("kt-pd-status-pill")
		self.assertLess(title_pos, pill_pos, "title should precede status pill in title row (PD3)")

	def test_tab_switch_updates_tab_host_without_full_shell_removal(self) -> None:
		source = _package_detail_js().read_text(encoding="utf-8", errors="replace")
		bind_block = source.split("function _bind(wrapper)", 1)[1].split("function _load", 1)[0]
		self.assertIn("_updateTabButtons", bind_block)
		self.assertIn("_updateTabHost", bind_block)
		self.assertNotIn("wrapper.innerHTML = _shellHtml(_state.detail)", bind_block)

	def test_page_chrome_hooks_toggle_body_class(self) -> None:
		source = _package_detail_js().read_text(encoding="utf-8", errors="replace")
		self.assertIn("_activatePageChrome", source)
		self.assertIn("kt-pd-page-active", source)
		self.assertIn("on_page_hide", source)

	def test_css_ports_canvas_footer_and_desk_page_shell(self) -> None:
		css = _package_detail_css().read_text(encoding="utf-8", errors="replace")
		for needle in (
			".kt-pd-canvas",
			".kt-pd-footer",
			"body.kt-pd-page-active",
			"kt-pd-header__title-row",
		):
			self.assertIn(needle, css, msg=f"missing {needle} (PD3)")
