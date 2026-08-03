# Copyright (c) 2026, KenTender and contributors
"""Static layout guard — Strategy Alignment Stitch UI fixtures (UI-only phase)."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests.utils import FrappeTestCase

APP_PUBLIC = Path(frappe.get_app_path("kentender_strategy")) / "public"
FIXTURES = APP_PUBLIC / "js" / "strategy_ui_fixtures"
SHELL = APP_PUBLIC / "js" / "strategy_alignment_shell.js"
LIVE_BIND = APP_PUBLIC / "js" / "strategy_live_bind.js"
TOKENS = APP_PUBLIC / "css" / "strategy_alignment_tokens.css"
UTILITIES = APP_PUBLIC / "css" / "strategy_alignment_utilities.css"
PORTFOLIO_CSS = APP_PUBLIC / "css" / "strategy_alignment_portfolio.css"
PORTFOLIO_JS = APP_PUBLIC / "js" / "strategy_alignment_portfolio_page.js"
OVERVIEW_CSS = APP_PUBLIC / "css" / "strategy_alignment_overview.css"
STRUCTURE_CSS = APP_PUBLIC / "css" / "strategy_alignment_structure.css"
VC_CSS = APP_PUBLIC / "css" / "strategy_alignment_value_commitments.css"
REMAINING_CSS = APP_PUBLIC / "css" / "strategy_alignment_remaining.css"
RESPONSIVE_CSS = APP_PUBLIC / "css" / "strategy_alignment_responsive.css"


def _read(path: Path) -> str:
	return path.read_text(encoding="utf-8")


class TestStrategyUiStitchLayoutGuard(FrappeTestCase):
	def test_tokens_and_shell_exist(self):
		self.assertTrue(TOKENS.is_file())
		self.assertTrue(UTILITIES.is_file())
		self.assertTrue(SHELL.is_file())
		self.assertTrue(LIVE_BIND.is_file())
		live = _read(LIVE_BIND)
		self.assertIn("kentender_strategy.api.strategy_api", live)
		self.assertIn("get_strategy_portfolio", live)
		self.assertTrue(PORTFOLIO_CSS.is_file())
		self.assertTrue(PORTFOLIO_JS.is_file())
		tokens = _read(TOKENS)
		self.assertIn("kt-str-surface", tokens)
		self.assertIn("#kt-cl-page-header-host", tokens)
		self.assertIn("margin-top: 0 !important", tokens)
		self.assertIn("padding-top: 0.25rem !important", tokens)
		# Desk Espresso uses --weight-regular: 420 — Strategy canvas must force 400.
		self.assertIn("--weight-regular: 400", tokens)
		self.assertIn("letter-spacing: normal", tokens)
		# Stitch page titles use Manrope — must be self-hosted (not CDN / missing face).
		cl_fonts = Path(frappe.get_app_path("kentender_core")) / "public" / "css" / "kt_cl_fonts.css"
		self.assertTrue(cl_fonts.is_file())
		cl_fonts_css = _read(cl_fonts)
		self.assertIn('font-family: "Manrope"', cl_fonts_css)
		self.assertIn("/assets/kentender_core/fonts/manrope/manrope-700-latin.woff2", cl_fonts_css)
		self.assertIn('font-family: "Inter"', cl_fonts_css)
		manrope_woff = (
			Path(frappe.get_app_path("kentender_core"))
			/ "public"
			/ "fonts"
			/ "manrope"
			/ "manrope-700-latin.woff2"
		)
		self.assertTrue(manrope_woff.is_file())
		shell = _read(SHELL)
		self.assertIn('pageHeader: { title: ""', shell)
		self.assertIn('attr("hidden", "hidden")', shell)
		self.assertIn("kt-str-summary-strip", tokens)
		self.assertIn("kt-str-plan-tabs", tokens)
		portfolio_css = _read(PORTFOLIO_CSS)
		self.assertIn("kt-str-root", portfolio_css)
		self.assertIn("lg\\:col-span-9", portfolio_css)
		self.assertIn("grid-cols-12", portfolio_css)
		self.assertNotIn("cdn.tailwindcss.com", portfolio_css)
		portfolio_js = _read(PORTFOLIO_JS)
		self.assertIn("ui_fixtures.portfolio", portfolio_js)
		fixture = _read(APP_PUBLIC / "js" / "strategy_ui_fixtures" / "portfolio.js")
		self.assertIn("kt-str-summary-strip", fixture)
		self.assertIn("data-kt-str-plans-tbody", fixture)
		self.assertIn('data-kt-str-count="active"', fixture)
		self.assertIn("MOH-SP-2026-2030", fixture)  # seed reference in fixture header comment
		self.assertIn("Create strategic plan", fixture)
		self.assertIn("renderPlanRows", live)
		# Portfolio Effective period: compact 01-Jul-2026 - 30-Jun-2030, not digit soup.
		self.assertIn("effective_period_label || formatPeriod(p.start_date", live)
		self.assertIn("whitespace-nowrap", live)
		self.assertIn('["Jan", "Feb", "Mar"', live)
		fp_start = live.index("function formatPeriod")
		fp_end = live.index("\n\tfunction ", fp_start + 1)
		format_period_src = live[fp_start:fp_end]
		self.assertNotIn("str_to_user", format_period_src)
		self.assertIn('" - "', format_period_src)
		self.assertIn("padStart(2", format_period_src)
		# Plan column gets room; period stays compact.
		self.assertIn("kt-str-plans-col-plan", live)
		self.assertIn("kt-str-plans-col-plan", fixture)
		self.assertIn("kt-str-plans-col-plan", portfolio_css)
		self.assertIn("min-width: 18rem", portfolio_css)
		self.assertIn("list_strategy_plans", live)
		self.assertIn("bindCreatePlan", live)
		create_fx = _read(FIXTURES / "create_plan.js")
		self.assertIn("kt-str-create-plan", create_fx)
		self.assertIn('data-kt-str-field="plan_code"', create_fx)
		self.assertIn("Basic Information", create_fx)
		self.assertIn("Plan Context", create_fx)
		self.assertIn("lg:col-span-8", create_fx)
		self.assertIn("lg:col-span-4", create_fx)
		self.assertIn("Create plan", create_fx)
		self.assertIn("Cancel", create_fx)
		self.assertIn("successToast", create_fx)
		self.assertIn("Strategic procurement is the engine of institutional efficiency.", create_fx)
		self.assertIn("bg-surface-container-low p-section-gap", create_fx)
		self.assertIn('id="planForm"', create_fx)
		self.assertEqual(create_fx.count(">calendar_today<"), 2)
		self.assertIn("architecture", create_fx)
		self.assertNotIn("cdn.tailwindcss.com", create_fx)
		create_css = _read(PORTFOLIO_CSS.parent / "strategy_alignment_create.css")
		self.assertIn("data:image/svg+xml", create_css)
		self.assertIn("kt-str-create-plan", create_css)
		self.assertIn("kt-str-create-actions", create_css)
		responsive_css = _read(PORTFOLIO_CSS.parent / "strategy_alignment_responsive.css")
		self.assertIn("sm\\:flex-row", responsive_css)
		self.assertIn("sm\\:flex-none", responsive_css)
		self.assertIn("@media (min-width: 640px)", responsive_css)
		self.assertIn("grid grid-cols-12 gap-6", fixture)
		self.assertIn("lg:col-span-9", fixture)
		self.assertIn("font-headline-lg text-headline-lg text-primary", fixture)
		# Page intro byline must use header flex space — max-w-2xl orphans "procurement."
		self.assertIn('data-testid="kt-str-pf-header"', fixture)
		self.assertIn("min-w-0 flex-1", fixture)
		self.assertNotIn("max-w-2xl mt-1", fixture)
		self.assertIn(
			"Govern strategic outcomes, public-value commitments and performance targets used across procurement.",
			fixture,
		)
		self.assertIn('data-testid="kt-str-pf-filters"', fixture)
		self.assertIn('data-testid="kt-str-pf-filter-sep"', fixture)
		self.assertIn("|", fixture)
		# Search must share the filter panel (not a separate block above it).
		self.assertEqual(fixture.count("bg-surface-container-low p-3 rounded-lg border border-outline-variant"), 1)
		self.assertIn("--kt-str-focus-border", tokens)
		self.assertIn("#7bbeff", tokens)
		self.assertTrue(OVERVIEW_CSS.is_file())
		overview_css = _read(OVERVIEW_CSS)
		self.assertIn("lg\\:col-span-8", overview_css)
		self.assertIn("kt-str-overview-bento", overview_css)
		overview_fx = _read(FIXTURES / "overview.js")
		self.assertIn("lg:grid-cols-12", overview_fx)
		self.assertIn("lg:col-span-8", overview_fx)
		self.assertIn("Plan Details", overview_fx)
		self.assertIn("Performance Attention", overview_fx)
		self.assertIn("kt-str-successor-modal", overview_fx)
		self.assertIn("Create Successor Version", overview_fx)
		self.assertIn('data-kt-str-detail="plan_type"', overview_fx)
		self.assertIn("data-kt-str-attention-tbody", overview_fx)
		self.assertIn('data-kt-str-count="sub_programmes"', overview_fx)
		self.assertIn("data-kt-str-commit-count", overview_fx)
		self.assertNotIn("cdn.tailwindcss.com", overview_fx)
		# Plan chrome is shell-owned — fixtures must not embed divergent headers/tabs.
		self.assertNotIn('data-testid="kt-str-plan-chrome"', overview_fx)
		self.assertNotIn('data-testid="kt-str-plan-tabs"', overview_fx)
		live_js = _read(APP_PUBLIC / "js" / "strategy_live_bind.js")
		self.assertIn("get_plan_overview", live_js)
		self.assertIn("create_successor_version", live_js)
		self.assertTrue(STRUCTURE_CSS.is_file())
		structure_css = _read(STRUCTURE_CSS)
		self.assertIn("kt-str-structure-split", structure_css)
		self.assertIn("w-2\\/5", structure_css)
		structure_fx = _read(FIXTURES / "structure.js")
		self.assertIn("Structure Hierarchy", structure_fx)
		self.assertIn("kt-str-structure-split", structure_fx)
		self.assertIn("Add Structure Item", structure_fx)
		self.assertNotIn("Top App Bar", structure_fx)
		self.assertIn("data-kt-str-structure-issues", structure_fx)
		self.assertNotIn('data-testid="kt-str-plan-chrome"', structure_fx)
		self.assertNotIn('data-testid="kt-str-plan-tabs"', structure_fx)
		# Hierarchy pane is a card aligned with the detail pane (not a clipped border-r column).
		self.assertIn("p-section-gap gap-4", structure_fx)
		self.assertIn(
			'data-testid="kt-str-structure-tree"',
			structure_fx,
		)
		self.assertIn("rounded-xl shadow-sm", structure_fx)
		self.assertNotIn("border-r border-outline-variant bg-surface-container-lowest flex flex-col h-full", structure_fx)
		self.assertIn("padding: 24px !important", structure_css)
		self.assertIn(
			'[data-testid="kt-str-structure-tree"]',
			structure_css,
		)
		self.assertIn("border-radius: 0.75rem !important", structure_css)
		drawer_fx = _read(FIXTURES / "structure_drawer.js")
		self.assertIn("kt-str-structure-drawer-overlay", drawer_fx)
		self.assertIn("kt-str-structure-drawer-panel", drawer_fx)
		self.assertIn("Add performance target", drawer_fx)
		self.assertIn("Target value", drawer_fx)
		self.assertIn("rounded-l-lg", drawer_fx)
		self.assertIn("kt-str-tree-node:focus", structure_css)
		self.assertIn("--kt-str-focus-border", structure_css)
		self.assertIn("flex-direction: column", structure_css)
		# Empty structure-issue banner must stay hidden even when it also has .flex.
		self.assertIn("[data-kt-str-structure-issues].hidden", structure_css)
		self.assertIn("[data-kt-str-structure-issues][aria-hidden=\"true\"]", structure_css)
		self.assertTrue(VC_CSS.is_file())
		vc_css = _read(VC_CSS)
		self.assertIn("kt-str-vc-drawer", vc_css)
		self.assertIn("kt-str-vc-drawer-scroll", vc_css)
		self.assertIn("scrollbar-gutter: stable", vc_css)
		self.assertIn("kt-str-vc-drawer-filters", vc_css)
		self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr))", vc_css)
		vc_fx = _read(FIXTURES / "value_commitments.js")
		self.assertIn("Plan value commitments", vc_fx)
		# Section title matches Measurements (headline-md / 600), not plan chrome headline-lg.
		self.assertIn("font-headline-md text-headline-md text-on-surface", vc_fx)
		self.assertNotIn("font-headline-lg text-headline-lg text-primary", vc_fx)
		# Intro copy must not sit in a tight max-w-3xl that orphans the last word.
		self.assertIn('data-testid="kt-str-vc-header"', vc_fx)
		self.assertIn("min-w-0 flex-1", vc_fx)
		self.assertNotIn('<div class="max-w-3xl">', vc_fx)
		self.assertIn("px-8 pt-4 pb-8", vc_fx)
		self.assertIn("kt-str-vc-table", vc_fx)
		self.assertIn("kt-str-vc-drawer", vc_fx)
		self.assertIn('data-testid="kt-str-vc-drawer-scroll"', vc_fx)
		self.assertIn('data-testid="kt-str-vc-drawer-filters"', vc_fx)
		self.assertIn("grid grid-cols-2 gap-2", vc_fx)
		self.assertIn("Add commitment", vc_fx)
		self.assertNotIn("toggleDrawer()", vc_fx)
		# Pillar/Source must not use flex-1 without min-w-0 (unequal columns).
		self.assertNotRegex(
			vc_fx,
			r'data-kt-str-vc-drawer-pillar[^>]+\bflex-1\b',
		)
		self.assertIn("text-headline-md", vc_css)
		self.assertTrue(REMAINING_CSS.is_file())
		remaining_css = _read(REMAINING_CSS)
		self.assertIn("kt-str-root", remaining_css)
		self.assertGreater(len(remaining_css), 10_000)
		# Invalid `font-size:[10px` aborts the stylesheet in browsers and drops
		# later rules (including lg:col-span-2 used by Derived Result).
		self.assertNotIn("font-size:[", remaining_css)
		self.assertIn("lg\\:col-span-2", remaining_css)
		self.assertIn("font-size:28px !important", remaining_css)
		self.assertIn("letter-spacing:-0.02em !important", remaining_css)
		self.assertIn(
			'font-family: Manrope, "Public Sans", system-ui, sans-serif !important',
			remaining_css,
		)
		# Page-title pin must include Manrope so Desk h1 defaults cannot win.
		self.assertIn("h1.font-headline-lg", remaining_css)
		self.assertIn("h2.font-headline-lg", remaining_css)
		self.assertIn("h2.font-headline-sm", remaining_css)
		self.assertIn('font-body-md{font-family:Inter, "Public Sans", system-ui, sans-serif !important; font-weight:400 !important; letter-spacing:normal !important}', remaining_css)
		self.assertIn('data-kt-str-chrome-meta', remaining_css)
		shell = _read(SHELL)
		self.assertIn("font-body-md text-body-md", shell)
		self.assertIn("data-kt-str-chrome-meta", shell)
		util_css = _read(UTILITIES)
		self.assertNotIn("font-size:[", util_css)
		self.assertNotIn("background:[", util_css)
		meas_fx = _read(FIXTURES / "measurements.js")
		self.assertIn("kt-str-measurements-table", meas_fx)
		self.assertIn('data-kt-str-action="submit-measurement"', meas_fx)
		self.assertIn("Performance measurements", meas_fx)
		self.assertIn("font-headline-md text-headline-md text-on-surface", meas_fx)
		self.assertIn("px-8 pt-4 pb-8", meas_fx)
		self.assertIn("data-kt-str-meas-tbody", meas_fx)
		self.assertIn('data-kt-str-meas-count="verified"', meas_fx)
		self.assertIn("data-kt-str-meas-filter-period", meas_fx)
		self.assertIn("appearance-none", meas_fx)
		self.assertGreaterEqual(meas_fx.count("expand_more"), 3)
		submit_fx = _read(FIXTURES / "measurement_submit.js")
		self.assertIn("kt-str-meas-submit-header", submit_fx)
		self.assertIn("kt-str-meas-submit-canvas", submit_fx)
		self.assertIn("data-block", submit_fx)
		self.assertIn("Derived Result", submit_fx)
		self.assertIn("kt-str-meas-derived", submit_fx)
		self.assertIn('type="date"', submit_fx)
		self.assertIn("data-kt-str-meas-period-start", submit_fx)
		self.assertIn("data-kt-str-meas-period-end", submit_fx)
		self.assertIn("data-kt-str-meas-date", submit_fx)
		self.assertIn("data-kt-str-meas-guidance", submit_fx)
		self.assertIn("data-kt-str-meas-period-hint", submit_fx)
		self.assertNotIn("Digital Health Services", submit_fx)
		self.assertNotIn("chevron_right", submit_fx)
		live_js = _read(LIVE_BIND)
		# Register Submit must be plan-scoped — never fall back to FIXTURE_TARGET alone.
		self.assertIn('frappe.set_route("strategy-measurement-submit", plan, code)', live_js)
		self.assertIn("This plan has no Active performance targets", live_js)
		self.assertIn("args.plan_code = planCode", live_js)
		self.assertIn("m.is_new", live_js)
		self.assertIn("deriveClient", live_js)
		self.assertIn("input.ktStrMeasDerive", live_js)
		self.assertIn("kt-str-meas-period-range", live_js)
		self.assertIn("Persist current fields, then Submit", live_js)
		self.assertIn('action: "Submit"', live_js)
		self.assertIn("purpose: mode", live_js)
		self.assertIn("paintVerifySurface", live_js)
		self.assertIn("applyVerifyDecision", live_js)
		self.assertIn('apiAction === "Return"', live_js)
		self.assertIn("authorised_exception", live_js)
		verify_fx = _read(FIXTURES / "measurement_verify.js")
		self.assertIn("kt-str-meas-verify-header", verify_fx)
		self.assertIn("kt-str-meas-verify-compare", verify_fx)
		self.assertIn("kt-str-meas-verify-evidence", verify_fx)
		self.assertIn("kt-str-meas-verify-decision", verify_fx)
		self.assertIn("kt-str-meas-verify-actions", verify_fx)
		self.assertIn("Back to measurements", verify_fx)
		self.assertNotIn("Back to Contract", verify_fx)
		self.assertIn('data-kt-str-action="reject-measurement"', verify_fx)
		self.assertIn('data-kt-str-action="request-changes"', verify_fx)
		self.assertIn("data-kt-str-meas-exception", verify_fx)
		submit_css = _read(APP_PUBLIC / "css" / "strategy_alignment_measurement_submit.css")
		self.assertIn("kt-str-meas-period-range", submit_css)
		verify_css = _read(APP_PUBLIC / "css" / "strategy_alignment_measurement_verify.css")
		self.assertIn("kt-str-meas-verify-root", verify_css)
		self.assertIn("kt-str-meas-status-pill", verify_css)
		self.assertIn("translateY(-2px)", verify_css)
		self.assertIn("paintVerifyPills", live_js)
		self.assertIn("Stay on verify page", live_js)
		self.assertTrue(
			(Path(__file__).resolve().parents[1] / "public/css/strategy_alignment_measurement_submit.css").is_file()
		)
		down_fx = _read(FIXTURES / "downstream.js")
		self.assertIn("kt-str-downstream-table", down_fx)
		self.assertIn("data-kt-str-down-tbody", down_fx)
		self.assertIn('data-kt-str-down-count="Budget"', down_fx)
		self.assertIn("data-kt-str-down-filter-module", down_fx)
		self.assertIn("expand_more", down_fx)
		self.assertIn('data-kt-str-action="clear-down-filters"', down_fx)
		self.assertNotIn('data-testid="kt-str-plan-chrome"', down_fx)
		self.assertNotIn("DEM-MOH-2027-014", down_fx)
		self.assertIn("paintDownRows", live_js)
		self.assertIn("applyDownFilters", live_js)
		self.assertIn('action === "view-downstream"', live_js)
		# Downstream/Audit/Review must paint shared chrome via bindPlanChrome (not UPPERCASE / vN bylines).
		down_bind = live_js[live_js.index("function bindDownstream") : live_js.index("function bindAudit")]
		self.assertIn("bindPlanChrome($root, plan)", down_bind)
		self.assertNotIn(".toUpperCase()", down_bind)
		self.assertNotIn('"v" + plan.version_number', down_bind)
		audit_bind = live_js[live_js.index("function bindAudit") : live_js.index("function bindCorrective")]
		self.assertIn("bindPlanChrome($root, plan)", audit_bind)
		self.assertIn("get_plan_overview", audit_bind)
		review_paint = live_js[
			live_js.index("function paintReviewCanvas") : live_js.index("function remountReviewForReadyState")
		]
		self.assertIn("bindPlanChrome(", review_paint)
		self.assertIn("Object.assign({}, plan", review_paint)
		audit_fx = _read(FIXTURES / "audit.js")
		self.assertIn("kt-str-audit-table", audit_fx)
		self.assertIn("Audit history", audit_fx)
		# Wide audit table must expose a visible horizontal scrollbar (not scrollbar-hide).
		self.assertIn('data-testid="kt-str-audit-scroll"', audit_fx)
		self.assertIn("overflow-x-auto", audit_fx)
		self.assertNotIn("scrollbar-hide", audit_fx)
		down_fx = _read(FIXTURES / "downstream.js")
		self.assertIn('data-testid="kt-str-downstream-scroll"', down_fx)
		self.assertNotIn("scrollbar-hide", down_fx)
		# Shared table footer (range + Page Size 10/20/50/100 + page-of-pages).
		footer_fx = _read(FIXTURES / "table_footer.js")
		self.assertIn('data-testid="kt-str-table-footer"', footer_fx)
		self.assertIn("data-kt-str-footer-page-size", footer_fx)
		self.assertIn("data-kt-str-footer-page", footer_fx)
		self.assertIn('value="10"', footer_fx)
		self.assertIn('value="20"', footer_fx)
		self.assertIn('value="50"', footer_fx)
		self.assertIn('value="100"', footer_fx)
		self.assertIn("Page Size", footer_fx)
		self.assertIn("Showing 0 of 0 records", footer_fx)
		for name in ("portfolio.js", "pvo_catalogue.js", "measurements.js", "audit.js"):
			fx = _read(FIXTURES / name)
			self.assertIn(
				"tablePaginationFooterHtml",
				fx,
				f"{name} must use shared tablePaginationFooterHtml",
			)
			self.assertNotIn("Showing 0 entries", fx)
			self.assertNotIn("Showing 5 of 42 objectives", fx)
		self.assertIn("attachTablePagination", live_js)
		self.assertIn("function attachTablePagination", live_js)
		pvo_cat = _read(FIXTURES / "pvo_catalogue.js")
		self.assertIn('data-kt-str-action="create-pvo"', pvo_cat)
		self.assertIn("min-w-0 flex-1", pvo_cat)
		self.assertNotIn('<div class="max-w-3xl">', pvo_cat)
		review_blockers = _read(FIXTURES / "review_blockers.js")
		self.assertIn("kt-str-review-blockers", review_blockers)
		self.assertIn("data-kt-str-review-group", review_blockers)
		self.assertIn("data-kt-str-review-issues", review_blockers)
		self.assertIn('data-kt-str-action="run-readiness"', review_blockers)
		self.assertIn('data-kt-str-action="submit-for-review"', review_blockers)
		self.assertIn('data-kt-str-action="return-for-correction"', review_blockers)
		self.assertIn("kt-str-review-footer", review_blockers)
		self.assertIn("data-kt-str-blocker-count-label", review_blockers)
		review_ready = _read(FIXTURES / "review_ready.js")
		self.assertIn("Ready for submission", review_ready)
		self.assertIn("kt-str-review-ready-card", review_ready)
		self.assertIn('data-kt-str-action="submit-for-review"', review_ready)
		self.assertNotIn('data-testid="kt-str-plan-chrome"', review_ready)
		self.assertNotIn("sticky top-0", review_ready)
		# Submit must start hidden; live bind reveals only via allowed_actions.
		self.assertRegex(
			review_ready,
			r'data-kt-str-action="submit-for-review"[^>]*\bhidden\b'
			r'|\bhidden\b[^>]*data-kt-str-action="submit-for-review"',
		)
		live_js = _read(APP_PUBLIC / "js" / "strategy_live_bind.js")
		self.assertIn("get_plan_readiness_api", live_js)
		self.assertIn("paintReviewCanvas", live_js)
		self.assertIn("paintReviewActions", live_js)
		self.assertIn("paintPlanStatusPill", live_js)
		self.assertIn("paintReviewStatusPill", live_js)
		self.assertIn("data-kt-str-chrome-actions", live_js)
		self.assertIn("setReviewActionVisible", live_js)
		self.assertIn("allowed_actions", live_js)
		self.assertIn("return-for-correction", live_js)
		self.assertIn("Awaiting review", live_js)
		# Shared plan chrome — one builder owns code+status row for every plan tab.
		shell_js = _read(SHELL)
		self.assertIn("function planChromeHtml", shell_js)
		self.assertIn("data-kt-str-chrome-code-row", shell_js)
		self.assertIn("data-kt-str-plan-status-pill", shell_js)
		self.assertIn("data-kt-str-chrome-actions", shell_js)
		self.assertIn("data-kt-str-chrome-meta", shell_js)
		self.assertIn('data-testid="kt-str-plan-tabs"', shell_js)
		self.assertIn('find(\'[data-testid="kt-str-plan-chrome"]\').remove()', shell_js)
		meas_fx_chrome = _read(FIXTURES / "measurements.js")
		audit_fx_chrome = _read(FIXTURES / "audit.js")
		review_blockers_chrome = _read(FIXTURES / "review_blockers.js")
		for name, fx in (
			("measurements.js", meas_fx_chrome),
			("audit.js", audit_fx_chrome),
			("review_blockers.js", review_blockers_chrome),
		):
			self.assertNotIn('data-testid="kt-str-plan-chrome"', fx, name)
			self.assertNotIn('data-testid="kt-str-plan-tabs"', fx, name)
		remaining_css = _read(APP_PUBLIC / "css" / "strategy_alignment_remaining.css")
		self.assertIn("kt-str-review-footer", remaining_css)
		self.assertIn("--kt-a2-sidebar", remaining_css)
		self.assertTrue(RESPONSIVE_CSS.is_file())
		responsive = _read(RESPONSIVE_CSS)
		self.assertIn("md\\:flex-row", responsive)
		self.assertIn("lg\\:col-span-8", responsive)
		# Side paddings must beat later .p-2 shorthands (structure tree indent).
		self.assertIn(".pl-8", responsive)
		self.assertIn(".pl-14", responsive)
		self.assertIn(".pl-20", responsive)
		self.assertIn(".pl-28", responsive)
		shell = _read(SHELL)
		self.assertIn("registerPage", shell)
		# Soft tab show must not remountContent every time (page flash).
		self.assertIn("softShow", shell)
		self.assertIn("data-kt-str-mount-key", shell)
		self.assertIn("data-kt-str-mount-gen", shell)
		self.assertIn("Skip wipe when the same route/plan is already mounted", shell)
		self.assertIn("strategy-plan-overview", shell)
		self.assertIn("data-dismiss", shell)
		self.assertIn("bindSatelliteNav", shell)
		self.assertIn("get_plan_readiness_api", shell)
		self.assertIn("pickReviewHtml", shell)

	def test_fixture_roots_and_markers(self):
		cases = {
			"portfolio.js": ("kt-str-portfolio", "Strategy Alignment", "MOH-SP-2026-2030"),
			"overview.js": ("kt-str-overview", "Plan Details", "kt-str-successor-modal"),
			"structure.js": ("kt-str-structure", "Structure", "Add Structure Item"),
			"structure_drawer.js": ("kt-str-structure-drawer", "fixed inset-0", "Target"),
			"pvo_catalogue.js": ("kt-str-pvo-catalogue", "public value", "PVO-"),
			"pvo_editor.js": ("kt-str-pvo-editor", "public value", "Pillar"),
			"value_commitments.js": ("kt-str-value-commitments", "Value", "Commitment"),
			"measurements.js": ("kt-str-measurements", "Measurement", "data-kt-str-meas-tbody"),
			"measurement_submit.js": (
				"kt-str-measurement-submit",
				"Submit performance measurement",
				"kt-str-meas-submit-canvas",
			),
			"measurement_verify.js": (
				"kt-str-measurement-verify",
				"kt-str-meas-verify-compare",
				"Back to measurements",
			),
			"corrective_actions.js": ("kt-str-corrective-actions", "Corrective", "action"),
			"downstream.js": ("kt-str-downstream", "data-kt-str-down-tbody", "Downstream usage"),
			"review_blockers.js": ("kt-str-review-blockers", "data-kt-str-review-group", "run-readiness"),
			"review_ready.js": ("kt-str-review-ready", "Ready for submission", "submit-for-review"),
			"audit.js": ("kt-str-audit", "Audit", "MOH-SP-2026-2030"),
		}
		for name, markers in cases.items():
			path = FIXTURES / name
			self.assertTrue(path.is_file(), f"missing fixture {name}")
			html_l = _read(path).lower()
			for marker in markers:
				self.assertIn(marker.lower(), html_l, f"{name} missing {marker!r}")

	def test_desk_pages_registered(self):
		expected = [
			"strategy-alignment",
			"strategy-plan-create",
			"strategy-plan-overview",
			"strategy-plan-structure",
			"strategy-plan-value-commitments",
			"strategy-plan-measurements",
			"strategy-plan-downstream-usage",
			"strategy-plan-review",
			"strategy-plan-audit",
			"strategy-pvo-catalogue",
			"strategy-pvo-editor",
			"strategy-measurement-submit",
			"strategy-measurement-verify",
			"strategy-corrective-actions",
		]
		for name in expected:
			self.assertTrue(frappe.db.exists("Page", name), f"Page missing: {name}")

	def test_no_tailwind_cdn_in_strategy_assets(self):
		for path in APP_PUBLIC.rglob("*"):
			if path.suffix not in {".js", ".css", ".html"}:
				continue
			text = _read(path)
			self.assertNotIn("cdn.tailwindcss.com", text, f"Tailwind CDN in {path}")
