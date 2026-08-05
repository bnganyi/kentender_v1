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
OVERVIEW_FIXTURE = APP_PUBLIC / "js" / "budget_ui_fixtures" / "overview.js"
LINES_FIXTURE = APP_PUBLIC / "js" / "budget_ui_fixtures" / "lines.js"
ACTIVITY_FIXTURE = APP_PUBLIC / "js" / "budget_ui_fixtures" / "activity.js"
LIVE_BIND = APP_PUBLIC / "js" / "budget_live_bind.js"
WORKSPACE_SHELL = APP_PUBLIC / "js" / "budget_workspace_shell.js"
TOKENS = APP_PUBLIC / "css" / "budget_funding_tokens.css"
UTILITIES = APP_PUBLIC / "css" / "budget_funding_utilities.css"
PORTFOLIO_CSS = APP_PUBLIC / "css" / "budget_funding_portfolio.css"
REGISTER_CSS = APP_PUBLIC / "css" / "budget_funding_register.css"
OVERVIEW_CSS = APP_PUBLIC / "css" / "budget_funding_overview.css"
LINES_CSS = APP_PUBLIC / "css" / "budget_funding_lines.css"
ACTIVITY_CSS = APP_PUBLIC / "css" / "budget_funding_activity.css"
PORTFOLIO_JS = APP_PUBLIC / "js" / "budget_funding_portfolio_page.js"
REGISTER_JS = APP_PUBLIC / "js" / "budget_funding_register_page.js"
OVERVIEW_JS = APP_PUBLIC / "js" / "budget_funding_overview_page.js"
LINES_JS = APP_PUBLIC / "js" / "budget_funding_lines_page.js"
ACTIVITY_JS = APP_PUBLIC / "js" / "budget_funding_activity_page.js"
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
			"budget-lines",
			"budget-funding-activity",
			"budget-revisions",
			"budget-downstream",
			"budget-review",
			"budget-audit",
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
			"budget-lines",
			"budget-funding-activity",
			"budget-revisions",
			"budget-downstream",
			"budget-review",
			"budget-audit",
		):
			self.assertIn(slug, reg, msg=f"{slug} must be in cl_surface_registry")
		self.assertIn("BUD-UI-01", reg)
		self.assertIn("BUD-UI-02", reg)
		self.assertIn("BUD-UI-04", reg)

	def test_overview_fixture_shell_and_bind(self):
		for path in (OVERVIEW_FIXTURE, OVERVIEW_JS, OVERVIEW_CSS, WORKSPACE_SHELL, LIVE_BIND):
			self.assertTrue(path.is_file(), path)

		fixture = _read(OVERVIEW_FIXTURE)
		self.assertIn("kt-stitch-canvas", fixture)
		self.assertIn('data-testid="kt-bud-overview"', fixture)
		self.assertIn('data-testid="kt-bud-overview-identity"', fixture)
		self.assertIn('data-testid="kt-bud-overview-funding"', fixture)
		self.assertIn('data-testid="kt-bud-overview-kpis"', fixture)
		self.assertIn('data-testid="kt-bud-overview-bar"', fixture)
		self.assertIn('data-testid="kt-bud-overview-strategy"', fixture)
		self.assertIn('data-testid="kt-bud-overview-definition"', fixture)
		self.assertIn("Definitional Note", fixture)
		self.assertIn("Funding Guardrails", fixture)
		self.assertNotIn("cdn.tailwindcss.com", fixture)
		self.assertNotIn("ProcureSystem", fixture)
		self.assertNotIn("GovProcure Suite", fixture)

		shell = _read(WORKSPACE_SHELL)
		self.assertIn("BUDGET_TABS", shell)
		self.assertIn("ensureBudgetRoute", shell)
		self.assertIn("registerPage", shell)
		self.assertIn("softShow", shell)
		self.assertIn("kt-bud-workspace-chrome", shell)
		self.assertIn("data-kt-bud-mount-key", shell)
		# Active tab must not use text-primary (Desk chrome zeros padding/border).
		self.assertIn("Do NOT add text-primary on the active tab", shell)
		self.assertNotIn("is-active text-primary", shell)

		live = _read(LIVE_BIND)
		self.assertIn("bindOverview", live)
		self.assertIn("get_budget_overview", live)
		self.assertIn("approved_display", live)

		page_js = _read(OVERVIEW_JS)
		self.assertIn('registerPage("budget-overview"', page_js)
		self.assertIn('fixtureKey: "overview"', page_js)

		ov_css = _read(OVERVIEW_CSS)
		self.assertIn("kt-bud-overview-primary", ov_css)
		self.assertIn("#001f48", ov_css)
		self.assertIn("Win98", ov_css)
		# Bento + surface pins — portfolio .grid-cols-1 !important must not crush Overview.
		self.assertIn('kt-bud-overview-canvas"] > .grid', ov_css)
		self.assertIn("repeat(3, minmax(0, 1fr))", ov_css)
		self.assertIn("lg\\:col-span-2", ov_css)
		self.assertIn("bg-surface-container-lowest", ov_css)
		self.assertIn("rounded-xl", ov_css)
		self.assertIn("kt-bud-overview-kpis", ov_css)
		self.assertIn("kt-bud-overview-identity", ov_css)
		self.assertIn("kt-bud-overview-strategy", ov_css)
		self.assertIn("kt-bud-overview-attention", ov_css)
		# Tab underline must beat Desk button reset + stitch text-primary zero-pad.
		self.assertIn("button.kt-bud-tab", ov_css)
		self.assertIn("border-bottom-color: #001f48", ov_css)
		self.assertIn("padding: 0 0 0.75rem 0", ov_css)
		self.assertIn("font-weight: 500", ov_css)

		from kentender_budget import hooks as bud_hooks

		self.assertEqual(
			bud_hooks.page_js.get("budget-overview"),
			"public/js/budget_funding_overview_page.js",
		)
		includes = "\n".join(bud_hooks.app_include_js or [])
		self.assertIn("budget_ui_fixtures/overview.js", includes)
		self.assertIn("budget_workspace_shell.js", includes)
		css_includes = "\n".join(bud_hooks.app_include_css or [])
		self.assertIn("budget_funding_overview.css", css_includes)

	def test_lines_fixture_shell_and_bind(self):
		for path in (LINES_FIXTURE, LINES_JS, LINES_CSS, WORKSPACE_SHELL, LIVE_BIND):
			self.assertTrue(path.is_file(), path)

		fixture = _read(LINES_FIXTURE)
		self.assertIn("kt-stitch-canvas", fixture)
		self.assertIn('data-testid="kt-bud-lines"', fixture)
		self.assertIn('data-testid="kt-bud-lines-table"', fixture)
		self.assertIn('data-testid="kt-bud-lines-toolbar"', fixture)
		self.assertIn("kt-bud-lines-toolbar", fixture)
		self.assertIn("kt-bud-lines-select-wrap", fixture)
		self.assertIn("kt-bud-lines-new-btn", fixture)
		self.assertIn('data-testid="kt-bud-lines-search"', fixture)
		self.assertIn('data-testid="kt-bud-lines-filter-source"', fixture)
		self.assertIn('data-testid="kt-bud-lines-filter-target"', fixture)
		self.assertIn('data-testid="kt-bud-lines-new"', fixture)
		self.assertIn("New Line", fixture)
		self.assertIn('data-testid="kt-bud-lines-notice"', fixture)
		self.assertIn("Revision required", fixture)
		self.assertIn("Budget Source", fixture)
		self.assertIn("Strategic Target", fixture)
		self.assertIn("tablePaginationFooterHtml", fixture)
		self.assertIn('testid: "kt-bud-lines-table-footer"', fixture)
		self.assertIn('data-testid="kt-bud-line-drawer"', fixture)
		self.assertIn('data-testid="kt-bud-line-section-funding"', fixture)
		self.assertIn('data-testid="kt-bud-line-section-strategy"', fixture)
		self.assertIn('data-testid="kt-bud-line-section-pvc"', fixture)
		self.assertIn('data-testid="kt-bud-line-drawer-footer"', fixture)
		self.assertIn('data-testid="kt-bud-line-save"', fixture)
		self.assertIn("Edit Budget Line", fixture)
		self.assertIn("Funding details", fixture)
		self.assertIn("Plan Value Commitment treatment", fixture)
		self.assertIn("expand_more", fixture)
		self.assertNotIn("cdn.tailwindcss.com", fixture)
		self.assertNotIn("GovProcure Suite", fixture)
		self.assertNotIn("Ref:", fixture)
		self.assertNotIn("MOH-LINE-01", fixture)
		self.assertNotIn('data-testid="kt-bud-lines-filter"', fixture)  # generic Filter removed
		self.assertNotIn('data-testid="kt-bud-lines-columns"', fixture)
		self.assertNotIn("view_column", fixture)
		self.assertNotIn(">Filter\n", fixture)
		self.assertNotIn(">Columns<", fixture)
		self.assertNotIn(">Columns\n", fixture)

		shell = _read(WORKSPACE_SHELL)
		self.assertIn('pageSlug === "budget-lines"', shell)
		self.assertIn("bindLines", shell)
		self.assertNotIn("is-active text-primary", shell)

		live = _read(LIVE_BIND)
		self.assertIn("bindLines", live)
		self.assertIn("list_budget_lines", live)
		self.assertIn("get_budget_line", live)
		self.assertIn("save_budget_line", live)
		self.assertIn("openLineDrawer", live)
		self.assertIn("kt-bud-line-drawer", live)
		self.assertIn("attachPagination", live)
		self.assertIn("action_label", live)
		self.assertIn("showLinesNotice", live)
		self.assertIn("kt-bud-lines-notice", live)
		self.assertNotIn("frappe.msgprint", live)

		page_js = _read(LINES_JS)
		self.assertIn('registerPage("budget-lines"', page_js)
		self.assertIn('fixtureKey: "lines"', page_js)

		lines_css = _read(LINES_CSS)
		self.assertIn("680px", lines_css)
		self.assertIn("kt-bud-line-drawer", lines_css)
		self.assertIn("kt-bud-lines-scrim", lines_css)
		self.assertIn("select:has(+ .material-symbols-outlined)", lines_css)
		self.assertIn("#001f48", lines_css)
		self.assertIn("Win98", lines_css)
		self.assertIn("kt-bud-lines-table", lines_css)
		self.assertIn("kt-bud-lines-search-icon", lines_css)
		self.assertIn("kt-bud-lines-select-wrap", lines_css)
		self.assertIn("kt-bud-lines-new-btn", lines_css)
		self.assertIn("background-image: none !important", lines_css)
		self.assertIn("11.5rem", lines_css)
		self.assertIn("14rem", lines_css)
		self.assertIn("kt-bud-line-action", lines_css)
		self.assertIn("kt-bud-line-action-label", lines_css)
		self.assertIn("text-decoration: underline !important", lines_css)
		self.assertIn("kt-bud-lines-notice", lines_css)

		from kentender_budget import hooks as bud_hooks

		self.assertEqual(
			bud_hooks.page_js.get("budget-lines"),
			"public/js/budget_funding_lines_page.js",
		)
		includes = "\n".join(bud_hooks.app_include_js or [])
		self.assertIn("budget_ui_fixtures/lines.js", includes)
		css_includes = "\n".join(bud_hooks.app_include_css or [])
		self.assertIn("budget_funding_lines.css", css_includes)

	def test_hooks_page_js_no_query_string(self):
		hooks = frappe.get_hooks("page_js") or {}
		# get_hooks may nest; resolve from module
		from kentender_budget import hooks as bud_hooks

		for slug, path in (bud_hooks.page_js or {}).items():
			self.assertNotIn("?", path, f"page_js {slug} must not use ?v=")

	def test_activity_fixture_shell_and_bind(self):
		for path in (ACTIVITY_FIXTURE, ACTIVITY_JS, ACTIVITY_CSS, WORKSPACE_SHELL, LIVE_BIND):
			self.assertTrue(path.is_file(), path)

		fixture = _read(ACTIVITY_FIXTURE)
		self.assertIn("kt-stitch-canvas", fixture)
		self.assertIn('data-testid="kt-bud-activity"', fixture)
		self.assertIn('data-testid="kt-bud-activity-strip"', fixture)
		self.assertIn('data-testid="kt-bud-activity-toolbar"', fixture)
		self.assertIn('data-testid="kt-bud-activity-table"', fixture)
		self.assertIn('data-testid="kt-bud-activity-notice"', fixture)
		self.assertIn('data-testid="kt-bud-activity-filter-type"', fixture)
		self.assertIn('data-testid="kt-bud-activity-filter-status"', fixture)
		self.assertIn('data-testid="kt-bud-activity-search"', fixture)
		self.assertIn("Outstanding commitment", fixture)
		self.assertIn("tablePaginationFooterHtml", fixture)
		self.assertIn('testid: "kt-bud-activity-table-footer"', fixture)
		self.assertIn("expand_more", fixture)
		self.assertNotIn("cdn.tailwindcss.com", fixture)
		self.assertNotIn("KES 145M", fixture)

		shell = _read(WORKSPACE_SHELL)
		self.assertIn('pageSlug === "budget-funding-activity"', shell)
		self.assertIn("bindFundingActivity", shell)

		live = _read(LIVE_BIND)
		self.assertIn("bindFundingActivity", live)
		self.assertIn("list_funding_activity", live)
		self.assertIn("kt-bud-activity-action-label", live)
		self.assertIn("showActivityNotice", live)
		self.assertNotIn("frappe.msgprint", live)

		page_js = _read(ACTIVITY_JS)
		self.assertIn('registerPage("budget-funding-activity"', page_js)
		self.assertIn('fixtureKey: "activity"', page_js)

		css = _read(ACTIVITY_CSS)
		self.assertIn("kt-bud-activity-strip", css)
		self.assertIn("kt-bud-activity-select-wrap", css)
		self.assertIn("background-image: none !important", css)
		self.assertIn("11.5rem", css)
		self.assertIn("kt-bud-activity-action-label", css)
		self.assertIn("text-decoration: underline !important", css)
		self.assertIn("Win98", css)

		from kentender_budget import hooks as bud_hooks

		self.assertEqual(
			bud_hooks.page_js.get("budget-funding-activity"),
			"public/js/budget_funding_activity_page.js",
		)
		includes = "\n".join(bud_hooks.app_include_js or [])
		self.assertIn("budget_ui_fixtures/activity.js", includes)
		css_includes = "\n".join(bud_hooks.app_include_css or [])
		self.assertIn("budget_funding_activity.css", css_includes)

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
		self.assertIn('data-testid="kt-bud-register-notice"', fixture)
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
		self.assertIn("kt-bud-register-notice", reg_css)
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
