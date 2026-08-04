# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Static layout guard — Budget & Funding Stitch UI (BUD-UI-01 / Register)."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests.utils import FrappeTestCase

APP_PUBLIC = Path(frappe.get_app_path("kentender_budget")) / "public"
FIXTURE = APP_PUBLIC / "js" / "budget_ui_fixtures" / "portfolio.js"
REGISTER_FIXTURE = APP_PUBLIC / "js" / "budget_ui_fixtures" / "register.js"
LIVE_BIND = APP_PUBLIC / "js" / "budget_live_bind.js"
TOKENS = APP_PUBLIC / "css" / "budget_funding_tokens.css"
UTILITIES = APP_PUBLIC / "css" / "budget_funding_utilities.css"
PORTFOLIO_CSS = APP_PUBLIC / "css" / "budget_funding_portfolio.css"
REGISTER_CSS = APP_PUBLIC / "css" / "budget_funding_register.css"
PORTFOLIO_JS = APP_PUBLIC / "js" / "budget_funding_portfolio_page.js"
REGISTER_JS = APP_PUBLIC / "js" / "budget_funding_register_page.js"
REDIRECT = APP_PUBLIC / "js" / "budget_funding_workspace_redirect.js"
RESPONSIVE = APP_PUBLIC / "css" / "budget_funding_responsive.css"


def _read(path: Path) -> str:
	return path.read_text(encoding="utf-8")


class TestBudgetUiStitchLayoutGuard(FrappeTestCase):
	def test_assets_and_hooks_exist(self):
		for path in (TOKENS, UTILITIES, PORTFOLIO_CSS, PORTFOLIO_JS, FIXTURE, LIVE_BIND, REDIRECT, RESPONSIVE):
			self.assertTrue(path.is_file(), path)

		tokens = _read(TOKENS)
		self.assertIn("kt-bud-surface", tokens)
		self.assertIn("#kt-cl-page-header-host", tokens)
		self.assertIn("--weight-regular: 400", tokens)

		fixture = _read(FIXTURE)
		self.assertIn("kt-stitch-canvas", fixture)
		self.assertIn('data-testid="kt-bud-portfolio"', fixture)
		self.assertIn('data-testid="kt-bud-summary-strip"', fixture)
		self.assertIn('data-kt-bud-count="active"', fixture)
		self.assertIn("data-kt-bud-budgets-tbody", fixture)
		self.assertIn("Register approved budget", fixture)
		self.assertIn("View funding performance", fixture)
		self.assertIn("No procurement budget has been registered", fixture)
		self.assertIn("tablePaginationFooterHtml", fixture)
		self.assertIn("kt-bud-table-footer", fixture)
		self.assertIn("w-80", fixture)
		self.assertNotIn("cdn.tailwindcss.com", fixture)
		self.assertNotIn("ProcureSystem", fixture)
		self.assertNotIn("Ref:", fixture)
		self.assertNotIn(">tag<", fixture)

		live = _read(LIVE_BIND)
		self.assertIn("kentender_budget.api.budget_api", live)
		self.assertIn("get_budget_portfolio", live)
		self.assertIn("list_budgets", live)
		self.assertIn("renderBudgetRows", live)
		self.assertIn("attachPagination", live)
		self.assertIn("font-data-mono", live)
		self.assertNotIn("Ref:", live)
		self.assertNotIn("truncate", live)

		page_js = _read(PORTFOLIO_JS)
		self.assertIn("ui_fixtures.portfolio", page_js)
		self.assertIn("bindPortfolio", page_js)
		self.assertIn("enterNative", page_js)

		redirect = _read(REDIRECT)
		self.assertIn("Budget Management", redirect)
		self.assertIn("budget-funding", redirect)

		portfolio_css = _read(PORTFOLIO_CSS)
		self.assertNotIn("cdn.tailwindcss.com", portfolio_css)
		# Desk chrome defeat — same lessons as Strategy portfolio.
		self.assertIn("kt-bud-root button", portfolio_css)
		self.assertIn("appearance: none", portfolio_css)
		# Hard-pin primary CTA navy (var() alone was insufficient after Desk bleed).
		self.assertIn("background-color: #001f48", portfolio_css)
		self.assertIn("kt-bud-register-budget", portfolio_css)
		self.assertIn("Win98", portfolio_css)  # comment documents the Desk bleed we pin against
		self.assertIn("data:image/svg+xml", portfolio_css)
		self.assertIn("Manrope", portfolio_css)
		self.assertIn("--weight-regular: 400", portfolio_css)
		# Filter search must not collapse to icon-sized box (md:w-auto vs w-full !important).
		self.assertIn('kt-bud-pf-filters', portfolio_css)
		self.assertIn('[data-kt-bud-filter="search"]', portfolio_css)
		self.assertIn("min-width: 16rem", portfolio_css)

		responsive = _read(RESPONSIVE)
		self.assertIn(r".md\:w-auto", responsive)
		self.assertIn("width: auto !important", responsive)
		self.assertIn(r".sm\:w-40", responsive)

	def test_desk_pages_registered(self):
		for name in (
			"budget-funding",
			"budget-register",
			"budget-funding-performance",
			"budget-overview",
		):
			self.assertTrue(frappe.db.exists("Page", name), name)

	def test_budget_routes_in_cl_surface_registry(self):
		"""Router leaveNative strips kt-cl-shell unless these prefixes are registered."""
		reg = (
			Path(frappe.get_app_path("kentender_core"))
			/ "public"
			/ "js"
			/ "kt_cl_surface_registry.js"
		).read_text(encoding="utf-8")
		for slug in (
			"budget-funding",
			"budget-register",
			"budget-funding-performance",
			"budget-overview",
		):
			self.assertIn(slug, reg, msg=f"{slug} must be in cl_surface_registry")
		self.assertIn("BUD-UI-01", reg)
		self.assertIn("BUD-UI-02", reg)

	def test_hooks_page_js_no_query_string(self):
		hooks = frappe.get_hooks("page_js") or {}
		# get_hooks may nest; resolve from module
		from kentender_budget import hooks as bud_hooks

		for slug, path in (bud_hooks.page_js or {}).items():
			self.assertNotIn("?", path, f"page_js {slug} must not use ?v=")

	def test_register_fixture_and_bind(self):
		for path in (REGISTER_FIXTURE, REGISTER_JS, REGISTER_CSS, LIVE_BIND):
			self.assertTrue(path.is_file(), path)

		fixture = _read(REGISTER_FIXTURE)
		self.assertIn("kt-stitch-canvas", fixture)
		self.assertIn('data-testid="kt-bud-register"', fixture)
		self.assertIn('data-testid="kt-bud-register-identity"', fixture)
		self.assertIn('data-testid="kt-bud-register-approval"', fixture)
		self.assertIn('data-testid="kt-bud-create-draft"', fixture)
		self.assertIn('data-testid="kt-bud-register-cancel"', fixture)
		self.assertIn("Create draft budget", fixture)
		self.assertIn("Register approved budget", fixture)
		self.assertIn('data-kt-bud-field="fiscal_period"', fixture)
		self.assertIn('data-kt-bud-field="approval_evidence"', fixture)
		self.assertNotIn("cdn.tailwindcss.com", fixture)
		self.assertNotIn("source-mode", fixture.lower())
		self.assertNotIn("Controlled import", fixture)
		self.assertNotIn('data-kt-bud-field="generated_reference"', fixture)
		self.assertNotIn('data-kt-bud-field="code"', fixture)
		self.assertNotIn('name="generated_reference"', fixture)

		live = _read(LIVE_BIND)
		self.assertIn("bindRegister", live)
		self.assertIn("get_register_form_context", live)
		self.assertIn("register_budget", live)
		self.assertIn("budget-overview", live)

		page_js = _read(REGISTER_JS)
		self.assertIn("ui_fixtures.register", page_js)
		self.assertIn("bindRegister", page_js)
		self.assertIn("enterNative", page_js)
		# Must not remount Stitch DOM on every show (flash / broken back-nav).
		self.assertIn("ensureMounted", page_js)
		self.assertIn("_ktBudRegisterMounted", page_js)
		self.assertIn("Re-enter shell + rebind only", page_js)

		reg_css = _read(REGISTER_CSS)
		self.assertIn("kt-bud-register-info-note", reg_css)
		self.assertIn("display: flex !important", reg_css)
		self.assertIn("grid-template-columns", reg_css)
		self.assertIn("#001f48", reg_css)
		self.assertIn("Win98", reg_css)  # comment documents Desk bleed pin

		pf_css = _read(PORTFOLIO_CSS)
		self.assertIn("kt-bud-register-budget", pf_css)
		self.assertIn(".kt-bud-root .flex", pf_css)
		self.assertIn(".kt-bud-root .gap-4", pf_css)

		from kentender_budget import hooks as bud_hooks

		self.assertEqual(
			bud_hooks.page_js.get("budget-register"),
			"public/js/budget_funding_register_page.js",
		)
		includes = "\n".join(bud_hooks.app_include_js or [])
		self.assertIn("budget_ui_fixtures/register.js", includes)
		css_includes = "\n".join(bud_hooks.app_include_css or [])
		self.assertIn("budget_funding_register.css", css_includes)
