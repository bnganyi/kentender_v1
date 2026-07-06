# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-LIB-0001 / STD-CFG-0610 — std-engine redirect shim; std-library primary UI."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

PAGE = "std-engine"
PAGE_ADVANCED = "std-engine-advanced"
GOVERNANCE_WORKSPACE = "Governance & Configuration"
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


class TestStdEnginePageStdLib0001(IntegrationTestCase):
	def test_std_lib_0001_page_exists_title_and_roles(self) -> None:
		"""Page std-engine exists; title matches pack; roles align with Governance workspace."""
		self.assertTrue(frappe.db.exists("Page", PAGE))
		p = frappe.get_doc("Page", PAGE)
		self.assertEqual(p.title, "Official STD Library")
		self.assertEqual(p.module, "Kentender Procurement")
		roles = {row.role for row in (p.roles or [])}
		self.assertTrue(EXPECTED_ROLES.issubset(roles), msg=f"Page roles {roles} missing {EXPECTED_ROLES - roles}")
		ws = frappe.get_doc("Workspace", GOVERNANCE_WORKSPACE)
		ws_roles = {row.role for row in (ws.roles or [])}
		self.assertTrue(roles.issubset(ws_roles), msg=f"Page roles {roles - ws_roles} missing from workspace")

	def test_std_lib_0001_advanced_page_exists(self) -> None:
		self.assertTrue(frappe.db.exists("Page", PAGE_ADVANCED))
		p = frappe.get_doc("Page", PAGE_ADVANCED)
		self.assertEqual(p.module, "Kentender Procurement")
		roles = {row.role for row in (p.roles or [])}
		self.assertTrue(EXPECTED_ROLES.issubset(roles))

	def test_std_lib_0001_page_js_hook_is_plain_file_path(self) -> None:
		"""STD-CFG-0610 — std-engine is a redirect shim to std-library when v2 is enabled."""
		raw = frappe.get_hooks("page_js", default={}).get(PAGE)
		self.assertIsNotNone(raw)
		paths = raw if isinstance(raw, (list, tuple)) else [raw]
		self.assertGreaterEqual(len(paths), 1)
		for p in paths:
			self.assertIsInstance(p, str)
			self.assertNotIn("?", p, msg="page_js must be a disk path, not a URL with query string")
		self.assertIn(
			"public/js/std_engine_redirect_page.js",
			paths,
			msg="std-engine must load redirect bootstrap (STD-CFG-0610)",
		)
		library_paths = frappe.get_hooks("page_js", default={}).get("std-library") or []
		self.assertIn("public/js/std_config/std_library_page.js", library_paths)
		self.assertIn(
			"public/js/std_library/import_wizard_data.js",
			library_paths,
			msg="import wizard adapters load on std-library",
		)

	def test_ui_hard_0200_library_shell_includes_pack_selectors(self) -> None:
		"""UI-HARD-0200 — Desk shell exposes sentinel + advanced disclosure hooks for smoke / Playwright."""
		app = Path(frappe.get_app_path("kentender_procurement"))
		shell = (app / "public/js/std_library/std_library_shell.js").read_text(encoding="utf-8")
		self.assertIn("std-library-create-instance-button-absent", shell)
		self.assertIn("std-library-advanced-view-toggle", shell)
		self.assertIn("std-library-advanced-catalogue-open", shell)

	def test_ui_hard_0210_advanced_renderer_includes_pack_selectors(self) -> None:
		"""UI-HARD-0210 — Advanced tab HTML exposes pack `data-testid`s + role gate constant."""
		app = Path(frappe.get_app_path("kentender_procurement"))
		shell = (app / "public/js/std_library/std_library_shell.js").read_text(encoding="utf-8")
		self.assertIn("ADVANCED_TECHNICAL_TAB_ROLES", shell)
		self.assertIn("userMayUseAdvancedTechnicalTab", shell)
		renderers = (app / "public/js/std_library/std_library_shell_detail_renderers.js").read_text(encoding="utf-8")
		self.assertIn("std-advanced-technical-view", renderers)
		self.assertIn("std-advanced-technical-view-toggle", renderers)
		self.assertIn("std-advanced-readonly-banner", renderers)
