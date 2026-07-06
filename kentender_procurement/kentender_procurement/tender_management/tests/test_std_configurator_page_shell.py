# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG-0200 — std-configurator Desk Page shell contract."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

PAGE = "std-configurator"
TAB_SLUGS = (
	"overview",
	"applicability",
	"tender-fields",
	"supplier-requirements",
	"forms-attachments",
	"evaluation-setup",
	"contract-terms",
	"rules-validations",
	"preview",
	"approval",
	"technical-json",
)


class TestStdConfiguratorPageShell(IntegrationTestCase):
	def test_std_cfg_0200_page_exists(self) -> None:
		self.assertTrue(frappe.db.exists("Page", PAGE))
		doc = frappe.get_doc("Page", PAGE)
		self.assertEqual(doc.title, "STD Configurator")

	def test_std_cfg_0200_page_js_hook(self) -> None:
		raw = frappe.get_hooks("page_js", default={}).get(PAGE)
		self.assertIsNotNone(raw)
		paths = raw if isinstance(raw, (list, tuple)) else [raw]
		self.assertIn("public/js/std_config/std_configurator_page.js", paths)
		self.assertIn("public/js/std_config/std_configurator_shell.js", paths)
		self.assertIn("public/js/std_config/std_configurator_shared_ui.js", paths)

	def test_std_cfg_0200_shell_tab_slugs(self) -> None:
		js = (
			Path(frappe.get_app_path("kentender_procurement"))
			/ "public"
			/ "js"
			/ "std_config"
			/ "std_configurator_shell.js"
		)
		source = js.read_text(encoding="utf-8", errors="replace")
		for slug in TAB_SLUGS:
			self.assertIn(slug, source)

	def test_std_cfg_0200_css_typography_selectors(self) -> None:
		css = (
			Path(frappe.get_app_path("kentender_procurement"))
			/ "public"
			/ "css"
			/ "std_configurator_page.css"
		)
		source = css.read_text(encoding="utf-8", errors="replace")
		for selector in (
			".kt-std-cfg-root",
			".kt-std-cfg-title",
			".kt-std-cfg-section-title",
			".kt-std-cfg-table",
		):
			self.assertIn(selector, source)

	def test_std_cfg_0200_tab_renderers_registered(self) -> None:
		js = (
			Path(frappe.get_app_path("kentender_procurement"))
			/ "public"
			/ "js"
			/ "std_config"
			/ "std_configurator_tab_renderers.js"
		)
		source = js.read_text(encoding="utf-8", errors="replace")
		self.assertIn("std_configurator_tabs", source)
		for slug in ("overview", "applicability", "contract-terms", "technical-json"):
			self.assertIn(slug, source)
