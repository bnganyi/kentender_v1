# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Static layout guard — Planning Stitch UI (PLN-UI-01…03)."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

APP_PUBLIC = Path(frappe.get_app_path("kentender_procurement")) / "public"
WS_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "workspace.js"
REG_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "register.js"
BLD_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "builder.js"
LIVE_BIND = APP_PUBLIC / "js" / "planning_live_bind.js"
CSS = APP_PUBLIC / "css" / "planning_workspace.css"
WS_PAGE = APP_PUBLIC / "js" / "planning_workspace_page.js"
REG_PAGE = APP_PUBLIC / "js" / "planning_register_page.js"
BLD_PAGE = APP_PUBLIC / "js" / "planning_builder_page.js"


def _read(path: Path) -> str:
	return path.read_text(encoding="utf-8")


class TestPlanningUiStitchLayoutGuard(IntegrationTestCase):
	def test_assets_exist(self):
		for path in (
			WS_FIXTURE,
			REG_FIXTURE,
			BLD_FIXTURE,
			LIVE_BIND,
			CSS,
			WS_PAGE,
			REG_PAGE,
			BLD_PAGE,
		):
			self.assertTrue(path.is_file(), path)

	def test_workspace_fixture_markers(self):
		text = _read(WS_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui01-root"', text)
		self.assertIn('data-testid="kt-pln-ui01-filters"', text)
		self.assertIn('data-testid="kt-pln-ui01-plan-panel"', text)
		self.assertIn('data-testid="kt-pln-ui01-queue"', text)
		self.assertIn('data-testid="kt-pln-ui01-open-plan"', text)
		self.assertIn("data-kt-pln-filter", text)
		self.assertIn("Work Requiring Action", text)
		# Literal Stitch utility classes retained (not parallel BEM layout).
		self.assertIn("font-headline-lg", text)
		self.assertIn("bg-surface-container-lowest", text)
		self.assertIn("grid grid-cols-1 md:grid-cols-4", text)
		self.assertNotIn("kt-pln-wrap", text)
		self.assertNotIn("cdn.tailwindcss.com", text)

	def test_register_fixture_markers(self):
		text = _read(REG_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui02-root"', text)
		self.assertIn('data-testid="kt-pln-ui02-form"', text)
		self.assertIn('data-testid="kt-pln-ui02-submit"', text)
		self.assertIn('data-testid="kt-pln-ui02-no-budget"', text)
		self.assertIn("data-kt-field-error", text)
		self.assertIn("Create annual procurement plan", text)
		self.assertIn("font-headline-lg", text)
		self.assertIn("Plan ownership", text)
		self.assertNotIn("kt-pln-wrap", text)
		self.assertNotIn("cdn.tailwindcss.com", text)
		self.assertNotIn("budget_amount", text.lower())

	def test_builder_fixture_markers(self):
		text = _read(BLD_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui03-root"', text)
		self.assertIn('data-testid="kt-pln-ui03-empty"', text)
		self.assertIn('data-testid="kt-pln-ui03-add-demand"', text)
		self.assertIn("No Plan Items yet", text)
		self.assertIn("font-headline-lg", text)
		self.assertIn("Back to Planning", text)
		self.assertNotIn("kt-pln-wrap", text)
		self.assertNotIn("cdn.tailwindcss.com", text)

	def test_live_bind_and_pages(self):
		live = _read(LIVE_BIND)
		self.assertIn("get_planning_workspace", live)
		self.assertIn("get_planning_create_scope", live)
		self.assertIn("create_procurement_plan", live)
		self.assertIn("get_plan_builder", live)
		self.assertIn("ktFormErrors", live)
		self.assertIn("bindPlanningWorkspace", live)
		self.assertIn("bindPlanningRegister", live)
		self.assertIn("bindPlanningBuilder", live)

		self.assertIn("enterNative", _read(WS_PAGE))
		self.assertIn("enterNative", _read(REG_PAGE))
		self.assertIn("enterNative", _read(BLD_PAGE))

	def test_hooks_wire_pages(self):
		from kentender_procurement import hooks

		page_js = hooks.page_js or {}
		self.assertEqual(
			page_js.get("planning-workspace"),
			"public/js/planning_workspace_page.js",
		)
		js_includes = "\n".join(hooks.app_include_js or [])
		self.assertIn("planning_workspace_redirect.js", js_includes)
		self.assertEqual(
			page_js.get("procurement-plan-register"),
			"public/js/planning_register_page.js",
		)
		self.assertEqual(
			page_js.get("procurement-plan-builder"),
			"public/js/planning_builder_page.js",
		)
		includes = "\n".join(hooks.app_include_css or [])
		self.assertIn("planning_workspace.css", includes)
		self.assertIn("planning_live_bind.js", js_includes)
		self.assertIn("planning_ui_fixtures/workspace.js", js_includes)
