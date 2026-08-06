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
DOWNSTREAM_FIXTURE = APP_PUBLIC / "js" / "budget_ui_fixtures" / "downstream.js"
REVIEW_FIXTURE = APP_PUBLIC / "js" / "budget_ui_fixtures" / "review.js"
AUDIT_FIXTURE = APP_PUBLIC / "js" / "budget_ui_fixtures" / "audit.js"
PERFORMANCE_FIXTURE = APP_PUBLIC / "js" / "budget_ui_fixtures" / "performance.js"
CHECK_RESERVE_FIXTURE = APP_PUBLIC / "js" / "budget_ui_fixtures" / "check_reserve.js"
REVISIONS_FIXTURE = APP_PUBLIC / "js" / "budget_ui_fixtures" / "revisions.js"
REVISION_CREATE_FIXTURE = APP_PUBLIC / "js" / "budget_ui_fixtures" / "revision_create.js"
REVISION_REVIEW_FIXTURE = APP_PUBLIC / "js" / "budget_ui_fixtures" / "revision_review.js"
LIVE_BIND = APP_PUBLIC / "js" / "budget_live_bind.js"
WORKSPACE_SHELL = APP_PUBLIC / "js" / "budget_workspace_shell.js"
TOKENS = APP_PUBLIC / "css" / "budget_funding_tokens.css"
UTILITIES = APP_PUBLIC / "css" / "budget_funding_utilities.css"
PORTFOLIO_CSS = APP_PUBLIC / "css" / "budget_funding_portfolio.css"
REGISTER_CSS = APP_PUBLIC / "css" / "budget_funding_register.css"
OVERVIEW_CSS = APP_PUBLIC / "css" / "budget_funding_overview.css"
LINES_CSS = APP_PUBLIC / "css" / "budget_funding_lines.css"
ACTIVITY_CSS = APP_PUBLIC / "css" / "budget_funding_activity.css"
DOWNSTREAM_CSS = APP_PUBLIC / "css" / "budget_funding_downstream.css"
REVIEW_CSS = APP_PUBLIC / "css" / "budget_funding_review.css"
AUDIT_CSS = APP_PUBLIC / "css" / "budget_funding_audit.css"
PERFORMANCE_CSS = APP_PUBLIC / "css" / "budget_funding_performance.css"
CHECK_RESERVE_CSS = APP_PUBLIC / "css" / "budget_funding_check_reserve.css"
REVISIONS_CSS = APP_PUBLIC / "css" / "budget_funding_revisions.css"
PORTFOLIO_JS = APP_PUBLIC / "js" / "budget_funding_portfolio_page.js"
REGISTER_JS = APP_PUBLIC / "js" / "budget_funding_register_page.js"
OVERVIEW_JS = APP_PUBLIC / "js" / "budget_funding_overview_page.js"
LINES_JS = APP_PUBLIC / "js" / "budget_funding_lines_page.js"
ACTIVITY_JS = APP_PUBLIC / "js" / "budget_funding_activity_page.js"
DOWNSTREAM_JS = APP_PUBLIC / "js" / "budget_funding_downstream_page.js"
REVIEW_JS = APP_PUBLIC / "js" / "budget_funding_review_page.js"
AUDIT_JS = APP_PUBLIC / "js" / "budget_funding_audit_page.js"
PERFORMANCE_JS = APP_PUBLIC / "js" / "budget_funding_performance_page.js"
CHECK_RESERVE_JS = APP_PUBLIC / "js" / "budget_funding_check_reserve_page.js"
REVISIONS_JS = APP_PUBLIC / "js" / "budget_funding_revisions_page.js"
REVISION_CREATE_JS = APP_PUBLIC / "js" / "budget_funding_revision_create_page.js"
REVISION_REVIEW_JS = APP_PUBLIC / "js" / "budget_funding_revision_review_page.js"
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
		# Filled primary hover: white on lifted navy — never inky #7b9ee0.
		self.assertIn("Filled primary hover: lifted navy + white", portfolio_css)
		self.assertIn("background-color: #00346f", portfolio_css)
		self.assertIn("#001536", portfolio_css)
		hover_idx = portfolio_css.find("Filled primary hover: lifted navy + white")
		self.assertGreaterEqual(hover_idx, 0)
		# Long selector list precedes the declarations — take enough of the block.
		hover_end = portfolio_css.find("/* Bordered secondary CTA", hover_idx)
		hover_slice = portfolio_css[hover_idx:hover_end] if hover_end > hover_idx else portfolio_css[hover_idx:]
		self.assertIn("background-color: #00346f", hover_slice)
		self.assertIn("color: #ffffff", hover_slice)
		self.assertNotIn("color: #7b9ee0", hover_slice)
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
			"budget-check-reserve",
			"budget-overview",
			"budget-lines",
			"budget-funding-activity",
			"budget-revisions",
			"budget-revision-create",
			"budget-revision-review",
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
			"budget-check-reserve",
			"budget-overview",
			"budget-lines",
			"budget-funding-activity",
			"budget-revisions",
			"budget-revision-create",
			"budget-revision-review",
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
		self.assertIn("bindLiveTab", shell)
		# Soft-show must skip chrome wipe / live rebind (title "—" flash regression).
		self.assertIn("Skip wipe when the same route/budget is already mounted", shell)
		self.assertNotIn("soft-show rebind", shell)
		self.assertIn("rememberBudgetChrome", shell)
		self.assertIn("hydrateBudgetChrome", shell)
		self.assertIn("isNativeActive", shell)
		self.assertIn("kt-bud-workspace-chrome", shell)
		self.assertIn("data-kt-bud-mount-key", shell)
		# Active tab must not use text-primary (Desk chrome zeros padding/border).
		self.assertIn("Do NOT add text-primary on the active tab", shell)
		self.assertNotIn("is-active text-primary", shell)

		live = _read(LIVE_BIND)
		self.assertIn("bindOverview", live)
		self.assertIn("get_budget_overview", live)
		self.assertIn("approved_display", live)
		self.assertIn("function paintChromeActions", live)
		self.assertIn("paintBudgetWorkspaceChrome", live)
		self.assertIn("rememberBudgetChrome", live)
		# Never invent a bare "Open" chrome label when primary_label is omitted.
		self.assertNotIn('__("Open")', live)
		shell = _read(WORKSPACE_SHELL)
		self.assertIn("Hidden until paintChromeActions", shell)

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
		# Search precedes filters in markup (left → right layout).
		self.assertLess(
			fixture.index('data-testid="kt-bud-activity-search-wrap"'),
			fixture.index('kt-bud-activity-toolbar-filters'),
		)
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

	def test_downstream_fixture_shell_and_bind(self):
		for path in (DOWNSTREAM_FIXTURE, DOWNSTREAM_JS, DOWNSTREAM_CSS, WORKSPACE_SHELL, LIVE_BIND):
			self.assertTrue(path.is_file(), path)

		fixture = _read(DOWNSTREAM_FIXTURE)
		self.assertIn("kt-stitch-canvas", fixture)
		self.assertIn('data-testid="kt-bud-downstream"', fixture)
		self.assertIn('data-testid="kt-bud-downstream-toolbar"', fixture)
		self.assertIn('data-testid="kt-bud-downstream-table"', fixture)
		self.assertIn('data-testid="kt-bud-downstream-notice"', fixture)
		self.assertIn('data-testid="kt-bud-downstream-search"', fixture)
		self.assertIn('data-testid="kt-bud-downstream-filter-status"', fixture)
		self.assertIn("Requirement", fixture)
		self.assertIn("Procurement plan item", fixture)
		self.assertIn("Reserved balance", fixture)
		self.assertIn("tablePaginationFooterHtml", fixture)
		self.assertIn('testid: "kt-bud-downstream-table-footer"', fixture)
		self.assertIn("expand_more", fixture)
		self.assertNotIn("cdn.tailwindcss.com", fixture)
		self.assertNotIn("KES 145M", fixture)
		self.assertNotIn("DM-MOH-2027-042", fixture)
		self.assertNotIn("next in the Budget MVP-1 build sequence", fixture)

		shell = _read(WORKSPACE_SHELL)
		self.assertIn('pageSlug === "budget-downstream"', shell)
		self.assertIn("bindDownstream", shell)
		self.assertNotIn("Downstream Usage is next", shell)

		live = _read(LIVE_BIND)
		self.assertIn("bindDownstream", live)
		self.assertIn("list_downstream_usage", live)
		self.assertIn("kt-bud-downstream-action-label", live)
		self.assertIn("showDownstreamNotice", live)

		page_js = _read(DOWNSTREAM_JS)
		self.assertIn('registerPage("budget-downstream"', page_js)
		self.assertIn('fixtureKey: "downstream"', page_js)

		css = _read(DOWNSTREAM_CSS)
		self.assertIn("kt-bud-downstream-select-wrap", css)
		self.assertIn("background-image: none !important", css)
		self.assertIn("11.5rem", css)
		self.assertIn("kt-bud-downstream-action-label", css)
		self.assertIn("Win98", css)

		from kentender_budget import hooks as bud_hooks

		self.assertEqual(
			bud_hooks.page_js.get("budget-downstream"),
			"public/js/budget_funding_downstream_page.js",
		)
		includes = "\n".join(bud_hooks.app_include_js or [])
		self.assertIn("budget_ui_fixtures/downstream.js", includes)
		css_includes = "\n".join(bud_hooks.app_include_css or [])
		self.assertIn("budget_funding_downstream.css", css_includes)

	def test_review_fixture_shell_and_bind(self):
		for path in (REVIEW_FIXTURE, REVIEW_JS, REVIEW_CSS, WORKSPACE_SHELL, LIVE_BIND):
			self.assertTrue(path.is_file(), path)

		fixture = _read(REVIEW_FIXTURE)
		self.assertIn("kt-stitch-canvas", fixture)
		self.assertIn('data-testid="kt-bud-review"', fixture)
		self.assertIn('data-testid="kt-bud-review-header"', fixture)
		self.assertIn('data-testid="kt-bud-review-groups"', fixture)
		self.assertIn('data-testid="kt-bud-review-footer"', fixture)
		self.assertIn('data-testid="kt-bud-review-notice"', fixture)
		self.assertIn('data-testid="kt-bud-review-reason-modal"', fixture)
		self.assertIn("Readiness Checklist", fixture)
		self.assertIn("Submit for review", fixture)
		self.assertIn("Activate budget", fixture)
		self.assertIn("does not constitute statutory budget approval", fixture)
		self.assertNotIn("cdn.tailwindcss.com", fixture)
		self.assertNotIn("next in the Budget MVP-1 build sequence", fixture)

		shell = _read(WORKSPACE_SHELL)
		self.assertIn('pageSlug === "budget-review"', shell)
		self.assertIn("bindReview", shell)
		self.assertNotIn("Budget Review is next", shell)

		live = _read(LIVE_BIND)
		self.assertIn("bindReview", live)
		self.assertIn("get_budget_readiness", live)
		self.assertIn("submit_budget", live)
		self.assertIn("return_budget", live)
		self.assertIn("mark_budget_reviewed", live)
		self.assertIn("activate_budget", live)
		self.assertIn("showReviewNotice", live)

		page_js = _read(REVIEW_JS)
		self.assertIn('registerPage("budget-review"', page_js)
		self.assertIn('fixtureKey: "review"', page_js)

		css = _read(REVIEW_CSS)
		self.assertIn("kt-bud-review-card", css)
		self.assertIn("kt-bud-review-footer", css)
		self.assertIn("kt-bud-review-action-label", css)

		from kentender_budget import hooks as bud_hooks

		self.assertEqual(
			bud_hooks.page_js.get("budget-review"),
			"public/js/budget_funding_review_page.js",
		)
		includes = "\n".join(bud_hooks.app_include_js or [])
		self.assertIn("budget_ui_fixtures/review.js", includes)
		css_includes = "\n".join(bud_hooks.app_include_css or [])
		self.assertIn("budget_funding_review.css", css_includes)

	def test_audit_fixture_shell_and_bind(self):
		for path in (AUDIT_FIXTURE, AUDIT_JS, AUDIT_CSS, WORKSPACE_SHELL, LIVE_BIND):
			self.assertTrue(path.is_file(), path)

		fixture = _read(AUDIT_FIXTURE)
		self.assertIn("kt-stitch-canvas", fixture)
		self.assertIn('data-testid="kt-bud-audit"', fixture)
		self.assertIn('data-testid="kt-bud-audit-toolbar"', fixture)
		self.assertIn('data-testid="kt-bud-audit-table"', fixture)
		self.assertIn('data-testid="kt-bud-audit-notice"', fixture)
		self.assertIn('data-testid="kt-bud-audit-filter-event"', fixture)
		self.assertIn("Date and time", fixture)
		self.assertIn("Before and after summary", fixture)
		self.assertIn("Date Range", fixture)
		self.assertIn('data-kt-bud-audit-filter-field="date_range"', fixture)
		# Export is chrome-header only (Stitch) — not inside the filter card.
		self.assertNotIn("kt-bud-audit-export", fixture)
		self.assertNotIn("Export audit history", fixture)
		self.assertIn("tablePaginationFooterHtml", fixture)
		self.assertIn('testid: "kt-bud-audit-table-footer"', fixture)
		self.assertIn("expand_more", fixture)
		self.assertNotIn("cdn.tailwindcss.com", fixture)
		self.assertNotIn("KES 455M", fixture)
		self.assertNotIn("next in the Budget MVP-1 build sequence", fixture)

		shell = _read(WORKSPACE_SHELL)
		self.assertIn('pageSlug === "budget-audit"', shell)
		self.assertIn("bindAudit", shell)
		self.assertIn('activeSlug === "budget-audit"', shell)
		self.assertIn("kt-bud-audit-export", shell)
		self.assertIn("Export audit history", shell)
		self.assertNotIn("Budget Audit is next", shell)

		live = _read(LIVE_BIND)
		self.assertIn("bindAudit", live)
		self.assertIn("get_budget_audit", live)
		self.assertIn("kt-bud-audit-action-label", live)
		self.assertIn("showAuditNotice", live)
		self.assertIn("csvEscape", live)

		page_js = _read(AUDIT_JS)
		self.assertIn('registerPage("budget-audit"', page_js)
		self.assertIn('fixtureKey: "audit"', page_js)

		css = _read(AUDIT_CSS)
		self.assertIn("kt-bud-audit-select-wrap", css)
		self.assertIn("background-image: none !important", css)
		self.assertIn("0.5rem 2.5rem 0.5rem 0.75rem", css)
		self.assertIn("11.5rem", css)
		self.assertIn("kt-bud-audit-action-label", css)
		self.assertIn("Win98", css)

		live = _read(LIVE_BIND)
		self.assertIn("paintBudgetWorkspaceChrome", live)
		self.assertIn("[data-kt-bud-budget-title]", live)
		# Review chrome title must be painted from readiness DTO (BUD-UI-11/12 regression).
		review_live = live
		self.assertIn("function applyReviewDto", review_live)
		idx = review_live.index("function applyReviewDto")
		chunk = review_live[idx : idx + 800]
		self.assertIn("paintBudgetWorkspaceChrome", chunk)
		self.assertIn("status: status", chunk)

		from kentender_budget import hooks as bud_hooks

		self.assertEqual(
			bud_hooks.page_js.get("budget-audit"),
			"public/js/budget_funding_audit_page.js",
		)
		includes = "\n".join(bud_hooks.app_include_js or [])
		self.assertIn("budget_ui_fixtures/audit.js", includes)
		css_includes = "\n".join(bud_hooks.app_include_css or [])
		self.assertIn("budget_funding_audit.css", css_includes)

	def test_performance_fixture_shell_and_bind(self):
		for path in (PERFORMANCE_FIXTURE, PERFORMANCE_JS, PERFORMANCE_CSS, LIVE_BIND):
			self.assertTrue(path.is_file(), path)

		fixture = _read(PERFORMANCE_FIXTURE)
		self.assertIn("kt-stitch-canvas", fixture)
		self.assertIn('data-testid="kt-bud-performance"', fixture)
		self.assertIn('data-testid="kt-bud-performance-header"', fixture)
		self.assertIn('data-testid="kt-bud-performance-export"', fixture)
		self.assertIn("Export report", fixture)
		self.assertIn('data-testid="kt-bud-performance-filters"', fixture)
		self.assertIn('data-kt-bud-perf-filter="fiscal_period"', fixture)
		self.assertIn('data-kt-bud-perf-filter="programme"', fixture)
		self.assertIn('data-kt-bud-perf-filter="primary_target"', fixture)
		self.assertIn('data-kt-bud-perf-filter="funding_status"', fixture)
		self.assertIn('data-testid="kt-bud-performance-kpis"', fixture)
		self.assertIn('data-testid="kt-bud-performance-coverage-table"', fixture)
		self.assertIn('data-testid="kt-bud-performance-exceptions-table"', fixture)
		self.assertIn('data-testid="kt-bud-performance-disclaimer"', fixture)
		self.assertIn('data-testid="kt-bud-performance-notice"', fixture)
		self.assertIn("Strategy Funding Coverage", fixture)
		self.assertIn("Funding Exceptions", fixture)
		self.assertIn("expand_more", fixture)
		self.assertIn(
			"Strategy alignment shows intended support",
			fixture,
		)
		self.assertNotIn("cdn.tailwindcss.com", fixture)
		self.assertNotIn("560M", fixture)
		self.assertNotIn("MOH-ST-04", fixture)
		self.assertNotIn("kt-bud-stub", fixture)
		self.assertNotIn("ProcureSystem", fixture)

		page_js = _read(PERFORMANCE_JS)
		self.assertIn("budget-funding-performance", page_js)
		self.assertIn("enterNative", page_js)
		self.assertIn("bindPerformance", page_js)
		self.assertIn("ui_fixtures.performance", page_js)
		# Soft-show rebind on return (Portfolio twin).
		self.assertIn("on_page_show", page_js)
		self.assertIn("_ktBudPerfMounted", page_js)

		live = _read(LIVE_BIND)
		self.assertIn("bindPerformance", live)
		self.assertIn("get_funding_performance", live)
		self.assertIn("export_funding_performance", live)
		self.assertIn("showPerfNotice", live)
		self.assertIn("csvEscape", live)
		self.assertIn("review_finance_sync", live)
		self.assertIn("view_details", live)

		css = _read(PERFORMANCE_CSS)
		self.assertIn("kt-bud-perf-select-wrap", css)
		self.assertIn("appearance: none", css)
		self.assertIn("Win98", css)
		self.assertIn("kt-bud-perf-export", css)
		self.assertIn("kt-bud-perf-kpi", css)

		reg = (
			Path(frappe.get_app_path("kentender_core"))
			/ "public"
			/ "js"
			/ "kt_cl_surface_registry.js"
		).read_text(encoding="utf-8")
		# BUD-UI-02 must map to Funding Performance route (not Register).
		idx = reg.index('"BUD-UI-02"')
		chunk = reg[idx : idx + 400]
		self.assertIn("budget-funding-performance", chunk)
		self.assertNotIn("budget-register", chunk)

		from kentender_budget import hooks as bud_hooks

		self.assertEqual(
			bud_hooks.page_js.get("budget-funding-performance"),
			"public/js/budget_funding_performance_page.js",
		)
		includes = "\n".join(bud_hooks.app_include_js or [])
		self.assertIn("budget_ui_fixtures/performance.js", includes)
		css_includes = "\n".join(bud_hooks.app_include_css or [])
		self.assertIn("budget_funding_performance.css", css_includes)

	def test_check_reserve_fixture_shell_and_bind(self):
		for path in (CHECK_RESERVE_FIXTURE, CHECK_RESERVE_JS, CHECK_RESERVE_CSS, LIVE_BIND):
			self.assertTrue(path.is_file(), path)

		fixture = _read(CHECK_RESERVE_FIXTURE)
		self.assertIn("kt-stitch-canvas", fixture)
		self.assertIn('data-testid="kt-bud-check-reserve"', fixture)
		self.assertIn('data-testid="kt-bud-check-reserve-scrim"', fixture)
		self.assertIn('data-testid="kt-bud-check-reserve-context"', fixture)
		self.assertIn('data-testid="kt-bud-check-reserve-line"', fixture)
		self.assertIn('data-kt-bud-cr-filter="budget_line"', fixture)
		self.assertIn("expand_more", fixture)
		self.assertIn("Funding available", fixture)
		self.assertIn("Insufficient funding", fixture)
		self.assertIn('data-testid="kt-bud-check-reserve-reserve"', fixture)
		self.assertIn('data-testid="kt-bud-check-reserve-reserve-disabled"', fixture)
		self.assertIn("Select another budget line", fixture)
		self.assertIn("Return to demand", fixture)
		self.assertIn("will not create additional funding holds", fixture)
		self.assertNotIn("cdn.tailwindcss.com", fixture)
		self.assertNotIn("455M", fixture)
		self.assertNotIn("reservation reference", fixture.lower())

		page_js = _read(CHECK_RESERVE_JS)
		self.assertIn("budget-check-reserve", page_js)
		self.assertIn("openCheckReserve", page_js)
		self.assertIn("MOH-BL-HWD-2027", page_js)
		self.assertIn("MOH-BL-DHI-2027", page_js)

		live = _read(LIVE_BIND)
		self.assertIn("openCheckReserve", live)
		self.assertIn("check_funding", live)
		self.assertIn("reserve_funding", live)
		self.assertIn("list_active_lines_for_check", live)
		self.assertIn("showCrNotice", live)

		css = _read(CHECK_RESERVE_CSS)
		self.assertIn("kt-bud-cr-select-wrap", css)
		self.assertIn("appearance: none", css)
		self.assertIn("Win98", css)
		self.assertIn("background-color: #001f48", css)

		reg = (
			Path(frappe.get_app_path("kentender_core"))
			/ "public"
			/ "js"
			/ "kt_cl_surface_registry.js"
		).read_text(encoding="utf-8")
		idx = reg.index('"BUD-UI-06"')
		chunk = reg[idx : idx + 400]
		self.assertIn("budget-check-reserve", chunk)

		from kentender_budget import hooks as bud_hooks

		self.assertEqual(
			bud_hooks.page_js.get("budget-check-reserve"),
			"public/js/budget_funding_check_reserve_page.js",
		)
		includes = "\n".join(bud_hooks.app_include_js or [])
		self.assertIn("budget_ui_fixtures/check_reserve.js", includes)
		css_includes = "\n".join(bud_hooks.app_include_css or [])
		self.assertIn("budget_funding_check_reserve.css", css_includes)

	def test_revisions_fixture_shell_and_bind(self):
		for path in (
			REVISIONS_FIXTURE,
			REVISION_CREATE_FIXTURE,
			REVISIONS_JS,
			REVISION_CREATE_JS,
			REVISIONS_CSS,
			WORKSPACE_SHELL,
			LIVE_BIND,
		):
			self.assertTrue(path.is_file(), path)

		# List tab — no in-tab create form, no redundant page title.
		list_fixture = _read(REVISIONS_FIXTURE)
		self.assertIn("kt-stitch-canvas", list_fixture)
		self.assertIn('data-testid="kt-bud-revisions"', list_fixture)
		self.assertIn('data-testid="kt-bud-revisions-list"', list_fixture)
		self.assertIn("tablePaginationFooterHtml", list_fixture)
		self.assertIn('testid: "kt-bud-revisions-table-footer"', list_fixture)
		self.assertIn(">Action</th>", list_fixture)
		self.assertNotIn("Budget revisions", list_fixture)
		self.assertNotIn('data-testid="kt-bud-rev-create"', list_fixture)
		self.assertNotIn('data-testid="kt-bud-rev-create-form"', list_fixture)
		self.assertNotIn("cdn.tailwindcss.com", list_fixture)
		self.assertNotIn("next in the Budget MVP-1 build sequence", list_fixture)

		# Dedicated create page fixture (Stitch create canvas).
		create_fixture = _read(REVISION_CREATE_FIXTURE)
		self.assertIn('data-testid="kt-bud-revision-create"', create_fixture)
		self.assertIn('data-testid="kt-bud-rev-create-form"', create_fixture)
		self.assertIn('data-testid="kt-bud-rev-lines-table"', create_fixture)
		self.assertIn('data-testid="kt-bud-rev-impact"', create_fixture)
		self.assertIn('data-testid="kt-bud-rev-save-draft"', create_fixture)
		self.assertIn('data-testid="kt-bud-rev-submit"', create_fixture)
		self.assertIn('data-testid="kt-bud-rev-cancel"', create_fixture)
		self.assertIn('data-testid="kt-bud-rev-footer-error"', create_fixture)
		self.assertIn("(optional)", create_fixture)
		self.assertIn('data-testid="kt-bud-rev-add-line"', create_fixture)
		self.assertIn('data-kt-bud-error="external_approval_reference"', create_fixture)
		self.assertIn("Create budget revision", create_fixture)
		self.assertIn("Constraint: Revised amount cannot be below Reserved + Committed.", create_fixture)
		self.assertNotIn("KES 1,720.5M", create_fixture)
		self.assertNotIn('data-kt-bud-field="generated_reference"', create_fixture)

		shell = _read(WORKSPACE_SHELL)
		self.assertIn('pageSlug === "budget-revisions"', shell)
		self.assertIn("bindRevisions", shell)
		self.assertIn('budget-revision-create', shell)
		self.assertNotIn("Budget Revisions is next", shell)

		live = _read(LIVE_BIND)
		self.assertIn("bindRevisions", live)
		self.assertIn("bindRevisionCreate", live)
		self.assertIn("data-kt-bud-rev-list-action", live)
		self.assertIn("list_budget_revisions", live)
		self.assertIn("get_budget_revision_create_context", live)
		self.assertIn("create_budget_revision", live)
		self.assertIn("submit_budget_revision", live)
		self.assertIn('set_route("budget-revision-create"', live)
		self.assertIn("ktFormErrors", live)
		self.assertNotIn("frappe.msgprint", live)

		page_js = _read(REVISIONS_JS)
		self.assertIn('registerPage("budget-revisions"', page_js)
		self.assertIn('fixtureKey: "revisions"', page_js)
		self.assertIn("isStub: false", page_js)

		create_page = _read(REVISION_CREATE_JS)
		self.assertIn("budget-revision-create", create_page)
		self.assertIn("bindRevisionCreate", create_page)
		self.assertIn("revision_create", create_page)

		css = _read(REVISIONS_CSS)
		self.assertIn("kt-bud-rev-footer", css)
		self.assertIn("kt-bud-rev-change-input", css)
		# Editable revision fields: white fill — never surface gray (#f9f9fe / #f4f3f9).
		field_idx = css.find(".kt-bud-rev-field input[type=\"text\"]")
		self.assertGreaterEqual(field_idx, 0)
		field_slice = css[field_idx : field_idx + 450]
		self.assertIn("background: #ffffff", field_slice)
		self.assertNotIn("background: #f9f9fe", field_slice)
		change_idx = css.find(".kt-bud-rev-change-input {")
		self.assertGreaterEqual(change_idx, 0)
		change_slice = css[change_idx : change_idx + 350]
		self.assertIn("background: #ffffff", change_slice)
		self.assertNotIn("background: #f4f3f9", change_slice)
		self.assertIn("kt-bud-rev-impact", css)
		self.assertIn("kt-bud-rev-main-grid", css)
		self.assertIn("grid-template-columns: minmax(0, 1fr) minmax(0, 2fr) !important", css)
		self.assertIn("kt-bud-rev-main-grid", create_fixture)
		# Dates stack full-width in 1/3 column (side-by-side overflows on Win Chrome).
		self.assertIn("grid-template-columns: minmax(0, 1fr) !important", css)
		self.assertIn(".kt-bud-rev-dates", css)
		self.assertIn("::-webkit-calendar-picker-indicator", css)
		self.assertIn("kt-bud-rev-date-wrap", create_fixture)
		self.assertIn("calendar_today", create_fixture)
		self.assertIn(">event<", create_fixture)

		from kentender_budget import hooks as bud_hooks

		self.assertEqual(
			bud_hooks.page_js.get("budget-revisions"),
			"public/js/budget_funding_revisions_page.js",
		)
		self.assertEqual(
			bud_hooks.page_js.get("budget-revision-create"),
			"public/js/budget_funding_revision_create_page.js",
		)
		includes = "\n".join(bud_hooks.app_include_js or [])
		self.assertIn("budget_ui_fixtures/revisions.js", includes)
		self.assertIn("budget_ui_fixtures/revision_create.js", includes)
		css_includes = "\n".join(bud_hooks.app_include_css or [])
		self.assertIn("budget_funding_revisions.css", css_includes)

	def test_revision_review_fixture_shell_and_bind(self):
		for path in (
			REVISION_REVIEW_FIXTURE,
			REVISION_REVIEW_JS,
			REVISIONS_CSS,
			LIVE_BIND,
		):
			self.assertTrue(path.is_file(), path)

		fixture = _read(REVISION_REVIEW_FIXTURE)
		self.assertIn("kt-stitch-canvas", fixture)
		self.assertIn('data-testid="kt-bud-revision-review"', fixture)
		self.assertIn('data-testid="kt-bud-rev-review-back"', fixture)
		self.assertIn('data-testid="kt-bud-rev-review-details"', fixture)
		self.assertIn('data-testid="kt-bud-rev-review-blocker"', fixture)
		self.assertIn('data-testid="kt-bud-rev-review-groups"', fixture)
		self.assertIn('data-testid="kt-bud-rev-review-financial"', fixture)
		self.assertIn('data-testid="kt-bud-rev-review-strategy"', fixture)
		self.assertIn('data-testid="kt-bud-rev-review-downstream"', fixture)
		self.assertIn('data-testid="kt-bud-rev-review-footer"', fixture)
		self.assertNotIn('data-testid="kt-bud-rev-review-comment"', fixture)
		self.assertIn('data-testid="kt-bud-rev-reason-modal"', fixture)
		self.assertIn('data-testid="kt-bud-rev-reason-comment"', fixture)
		self.assertIn('data-testid="kt-bud-rev-reason-confirm"', fixture)
		self.assertIn("Reject budget revision", fixture)
		self.assertIn('data-testid="kt-bud-rev-review-reject"', fixture)
		self.assertIn('data-testid="kt-bud-rev-review-return"', fixture)
		self.assertIn('data-testid="kt-bud-rev-review-apply"', fixture)
		self.assertIn("Strategy and value-treatment impact", fixture)
		self.assertNotIn("cdn.tailwindcss.com", fixture)
		self.assertNotIn("BR-2027-042", fixture)
		self.assertNotIn("KES 45.2M", fixture)

		live = _read(LIVE_BIND)
		self.assertIn("bindRevisionReview", live)
		self.assertIn("get_budget_revision_review_context", live)
		self.assertIn("openReasonModal", live)
		self.assertIn("data-kt-bud-rev-reason-modal", live)
		self.assertIn("return_budget_revision", live)
		self.assertIn("reject_budget_revision", live)
		self.assertIn("apply_budget_revision", live)
		self.assertIn('set_route("budget-revision-review"', live)
		self.assertIn('data-open-action', live)

		page_js = _read(REVISION_REVIEW_JS)
		self.assertIn("budget-revision-review", page_js)
		self.assertIn("bindRevisionReview", page_js)

		css = _read(REVISIONS_CSS)
		self.assertIn("kt-bud-rev-review-footer", css)
		self.assertIn("kt-bud-rev-review-groups", css)
		self.assertIn("kt-bud-rev-review-apply", css)

		from kentender_budget import hooks as bud_hooks

		self.assertEqual(
			bud_hooks.page_js.get("budget-revision-review"),
			"public/js/budget_funding_revision_review_page.js",
		)
		includes = "\n".join(bud_hooks.app_include_js or [])
		self.assertIn("budget_ui_fixtures/revision_review.js", includes)

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
