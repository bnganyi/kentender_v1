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
		vc_fx = _read(FIXTURES / "value_commitments.js")
		self.assertIn("Plan value commitments", vc_fx)
		# Under Desk plan chrome: section title is headline-md, not competing headline-lg.
		self.assertIn("font-headline-md text-headline-md", vc_fx)
		self.assertIn("px-8 pt-6 pb-8", vc_fx)
		self.assertIn("kt-str-vc-table", vc_fx)
		self.assertIn("kt-str-vc-drawer", vc_fx)
		self.assertIn("Add commitment", vc_fx)
		self.assertNotIn("toggleDrawer()", vc_fx)
		self.assertIn("text-headline-md", vc_css)
		self.assertTrue(REMAINING_CSS.is_file())
		remaining_css = _read(REMAINING_CSS)
		self.assertIn("kt-str-root", remaining_css)
		self.assertGreater(len(remaining_css), 10_000)
		# Invalid `font-size:[10px` aborts the stylesheet in browsers and drops
		# later rules (including lg:col-span-2 used by Derived Result).
		self.assertNotIn("font-size:[", remaining_css)
		self.assertIn("lg\\:col-span-2", remaining_css)
		util_css = _read(UTILITIES)
		self.assertNotIn("font-size:[", util_css)
		self.assertNotIn("background:[", util_css)
		meas_fx = _read(FIXTURES / "measurements.js")
		self.assertIn("kt-str-measurements-table", meas_fx)
		self.assertIn('data-kt-str-action="submit-measurement"', meas_fx)
		self.assertIn("Performance measurements", meas_fx)
		self.assertIn("data-kt-str-meas-tbody", meas_fx)
		self.assertIn('data-kt-str-meas-count="verified"', meas_fx)
		submit_fx = _read(FIXTURES / "measurement_submit.js")
		self.assertIn("kt-str-meas-submit-header", submit_fx)
		self.assertIn("kt-str-meas-submit-canvas", submit_fx)
		self.assertIn("data-block", submit_fx)
		self.assertIn("Derived Result", submit_fx)
		self.assertIn("kt-str-meas-derived", submit_fx)
		self.assertNotIn("Digital Health Services", submit_fx)
		self.assertNotIn("chevron_right", submit_fx)
		live_js = _read(LIVE_BIND)
		# Register Submit must be plan-scoped — never fall back to FIXTURE_TARGET alone.
		self.assertIn('frappe.set_route("strategy-measurement-submit", plan, code)', live_js)
		self.assertIn("This plan has no Active performance targets", live_js)
		self.assertIn("args.plan_code = planCode", live_js)
		self.assertIn("m.is_new", live_js)
		self.assertTrue(
			(Path(__file__).resolve().parents[1] / "public/css/strategy_alignment_measurement_submit.css").is_file()
		)
		down_fx = _read(FIXTURES / "downstream.js")
		self.assertIn("kt-str-downstream-table", down_fx)
		audit_fx = _read(FIXTURES / "audit.js")
		self.assertIn("kt-str-audit-table", audit_fx)
		self.assertIn("Audit history", audit_fx)
		self.assertIn('data-kt-str-action="create-pvo"', _read(FIXTURES / "pvo_catalogue.js"))
		self.assertIn("Ready for submission", _read(FIXTURES / "review_ready.js"))
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
		self.assertIn("strategy-plan-overview", shell)
		self.assertIn("data-dismiss", shell)
		self.assertIn("bindSatelliteNav", shell)

	def test_fixture_roots_and_markers(self):
		cases = {
			"portfolio.js": ("kt-str-portfolio", "Strategy Alignment", "MOH-SP-2026-2030"),
			"overview.js": ("kt-str-overview", "Plan Details", "MOH-SP-2026-2030"),
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
			"measurement_verify.js": ("kt-str-measurement-verify", "Verify", "MOH-TGT-01"),
			"corrective_actions.js": ("kt-str-corrective-actions", "Corrective", "action"),
			"downstream.js": ("kt-str-downstream", "Downstream", "Budget"),
			"review_blockers.js": ("kt-str-review-blockers", "Readiness", "blocker"),
			"review_ready.js": ("kt-str-review-ready", "ready", "submission"),
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
