# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG-0100 — std-library Desk Page hooks and selectors."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

PAGE = "std-library"
EXPECTED_ROLES: frozenset[str] = frozenset(
	{
		"Administrator",
		"System Manager",
		"STD Template Administrator",
		"STD Template Importer",
		"STD Template Reviewer",
		"STD Template Approver",
		"STD Template Activator",
		"STD Template Auditor",
		"STD Technical Inspector",
	}
)


class TestStdConfigLibraryPage(IntegrationTestCase):
	def test_std_cfg_0100_page_exists(self) -> None:
		self.assertTrue(frappe.db.exists("Page", PAGE))
		doc = frappe.get_doc("Page", PAGE)
		self.assertEqual(doc.title, "STD Library")
		roles = {row.role for row in (doc.roles or [])}
		self.assertTrue(EXPECTED_ROLES.issubset(roles))

	def test_std_cfg_0100_page_js_hook_order(self) -> None:
		raw = frappe.get_hooks("page_js", default={}).get(PAGE)
		self.assertIsNotNone(raw)
		paths = raw if isinstance(raw, (list, tuple)) else [raw]
		for p in paths:
			self.assertNotIn("?", str(p))
		self.assertIn("public/js/std_config/std_library_page.js", paths)
		self.assertLess(
			paths.index("public/js/std_config/std_config_shared.js"),
			paths.index("public/js/std_config/std_library_page.js"),
		)

	def test_std_cfg_0100_library_css_contract(self) -> None:
		css = (
			Path(frappe.get_app_path("kentender_procurement"))
			/ "public"
			/ "css"
			/ "std_library_page.css"
		)
		source = css.read_text(encoding="utf-8", errors="replace")
		for selector in (
			".kt-std-lib-root",
			".kt-std-lib-title",
			".kt-std-lib-kpi-value",
			".kt-std-lib-table",
		):
			self.assertIn(selector, source)

	def test_std_cfg_0100_library_js_testids(self) -> None:
		js = (
			Path(frappe.get_app_path("kentender_procurement"))
			/ "public"
			/ "js"
			/ "std_config"
			/ "std_library_page.js"
		)
		source = js.read_text(encoding="utf-8", errors="replace")
		for testid in (
			"kt-std-lib-root",
			"kt-std-lib-topbar",
			"kt-std-lib-kpi-total",
			"kt-std-lib-health-panel",
			"kt-std-lib-table",
			"kt-std-lib-configure",
			"kt-std-lib-search",
			"kt-std-lib-pagination-pages",
		):
			self.assertIn(testid, source)
