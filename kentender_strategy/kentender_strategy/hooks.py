# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""kentender_strategy — MVP-1 Strategy Alignment (domain services + Stitch Desk UI)."""

app_name = "kentender_strategy"
app_title = "Kentender Strategy"
app_publisher = "KenTender"
app_description = "KenTender strategy alignment module (MVP-1 UI-first rebuild)."
app_email = "dev@kentender.local"
app_license = "mit"

required_apps = ["kentender_core"]

from pathlib import Path


def _asset_version(rel_path: str) -> int:
	"""Cache-bust browser URL hooks only (not page_js disk paths)."""
	try:
		return int((Path(__file__).resolve().parent / rel_path).stat().st_mtime)
	except OSError:
		return 1


_v = _asset_version

app_include_css = [
	f"/assets/kentender_strategy/css/strategy_alignment_tokens.css?v={_v('public/css/strategy_alignment_tokens.css')}",
	f"/assets/kentender_strategy/css/strategy_alignment_utilities.css?v={_v('public/css/strategy_alignment_utilities.css')}",
	f"/assets/kentender_strategy/css/strategy_alignment_portfolio.css?v={_v('public/css/strategy_alignment_portfolio.css')}",
	f"/assets/kentender_strategy/css/strategy_alignment_create.css?v={_v('public/css/strategy_alignment_create.css')}",
	f"/assets/kentender_strategy/css/strategy_alignment_overview.css?v={_v('public/css/strategy_alignment_overview.css')}",
	f"/assets/kentender_strategy/css/strategy_alignment_structure.css?v={_v('public/css/strategy_alignment_structure.css')}",
	f"/assets/kentender_strategy/css/strategy_alignment_value_commitments.css?v={_v('public/css/strategy_alignment_value_commitments.css')}",
	f"/assets/kentender_strategy/css/strategy_alignment_measurement_submit.css?v={_v('public/css/strategy_alignment_measurement_submit.css')}",
	f"/assets/kentender_strategy/css/strategy_alignment_measurement_verify.css?v={_v('public/css/strategy_alignment_measurement_verify.css')}",
	f"/assets/kentender_strategy/css/strategy_alignment_remaining.css?v={_v('public/css/strategy_alignment_remaining.css')}",
	f"/assets/kentender_strategy/css/strategy_alignment_performance.css?v={_v('public/css/strategy_alignment_performance.css')}",
	# Must stay last: restores md:/lg: direction + side paddings after per-screen !important dumps.
	f"/assets/kentender_strategy/css/strategy_alignment_responsive.css?v={_v('public/css/strategy_alignment_responsive.css')}",
]

# Fixture modules + shared shell before page_js runs.
app_include_js = [
	f"/assets/kentender_strategy/js/strategy_ui_fixtures/table_footer.js?v={_v('public/js/strategy_ui_fixtures/table_footer.js')}",
	f"/assets/kentender_strategy/js/strategy_ui_fixtures/portfolio.js?v={_v('public/js/strategy_ui_fixtures/portfolio.js')}",
	f"/assets/kentender_strategy/js/strategy_ui_fixtures/create_plan.js?v={_v('public/js/strategy_ui_fixtures/create_plan.js')}",
	f"/assets/kentender_strategy/js/strategy_ui_fixtures/overview.js?v={_v('public/js/strategy_ui_fixtures/overview.js')}",
	f"/assets/kentender_strategy/js/strategy_ui_fixtures/structure.js?v={_v('public/js/strategy_ui_fixtures/structure.js')}",
	f"/assets/kentender_strategy/js/strategy_ui_fixtures/structure_drawer.js?v={_v('public/js/strategy_ui_fixtures/structure_drawer.js')}",
	f"/assets/kentender_strategy/js/strategy_ui_fixtures/value_commitments.js?v={_v('public/js/strategy_ui_fixtures/value_commitments.js')}",
	f"/assets/kentender_strategy/js/strategy_ui_fixtures/measurements.js?v={_v('public/js/strategy_ui_fixtures/measurements.js')}",
	f"/assets/kentender_strategy/js/strategy_ui_fixtures/measurement_submit.js?v={_v('public/js/strategy_ui_fixtures/measurement_submit.js')}",
	f"/assets/kentender_strategy/js/strategy_ui_fixtures/measurement_verify.js?v={_v('public/js/strategy_ui_fixtures/measurement_verify.js')}",
	f"/assets/kentender_strategy/js/strategy_ui_fixtures/downstream.js?v={_v('public/js/strategy_ui_fixtures/downstream.js')}",
	f"/assets/kentender_strategy/js/strategy_ui_fixtures/review_blockers.js?v={_v('public/js/strategy_ui_fixtures/review_blockers.js')}",
	f"/assets/kentender_strategy/js/strategy_ui_fixtures/review_ready.js?v={_v('public/js/strategy_ui_fixtures/review_ready.js')}",
	f"/assets/kentender_strategy/js/strategy_ui_fixtures/audit.js?v={_v('public/js/strategy_ui_fixtures/audit.js')}",
	f"/assets/kentender_strategy/js/strategy_ui_fixtures/performance.js?v={_v('public/js/strategy_ui_fixtures/performance.js')}",
	f"/assets/kentender_strategy/js/strategy_live_bind.js?v={_v('public/js/strategy_live_bind.js')}",
	f"/assets/kentender_strategy/js/strategy_alignment_shell.js?v={_v('public/js/strategy_alignment_shell.js')}",
	f"/assets/kentender_strategy/js/strategy_alignment_workspace_redirect.js?v={_v('public/js/strategy_alignment_workspace_redirect.js')}",
]

# Never append ?v= to page_js — Frappe resolves these as disk paths.
page_js = {
	"strategy-alignment": "public/js/strategy_alignment_portfolio_page.js",
	"strategy-performance": "public/js/strategy_alignment_performance_page.js",
	"strategy-plan-create": "public/js/strategy_alignment_create_page.js",
	"strategy-plan-overview": "public/js/strategy_plan_overview_page.js",
	"strategy-plan-structure": "public/js/strategy_plan_structure_page.js",
	"strategy-value-commitments": "public/js/strategy_value_commitments_page.js",
	"strategy-plan-measurements": "public/js/strategy_plan_measurements_page.js",
	"strategy-plan-downstream-usage": "public/js/strategy_plan_downstream_usage_page.js",
	"strategy-plan-review": "public/js/strategy_plan_review_page.js",
	"strategy-plan-audit": "public/js/strategy_plan_audit_page.js",
	"strategy-measurement-submit": "public/js/strategy_measurement_submit_page.js",
	"strategy-measurement-verify": "public/js/strategy_measurement_verify_page.js",
	# Claude Design -> Vue 3 pilot (spike, not the shared shell/registry pattern).
	"strategy-portfolio-pilot": "public/js/strategy_portfolio_pilot_page.js",
	# STR-CHG-001 v1.3 Phase 7 — the 3 production Vue-in-Desk pages
	# (STR-UI-01..04). Additive: the legacy strategy-* pages above stay
	# until Phase 8 deletes them.
	"strategy-portfolio": "public/js/strategy_portfolio_page.js",
	"strategy-plan-workspace": "public/js/strategy_plan_workspace_page.js",
	"strategy-review-task": "public/js/strategy_review_task_page.js",
}
