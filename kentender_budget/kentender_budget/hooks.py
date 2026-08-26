# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""kentender_budget — MVP-1 Budget & Funding (portfolio-first rebuild)."""

from pathlib import Path

app_name = "kentender_budget"
app_title = "Kentender Budget"
app_publisher = "KenTender"
app_description = "KenTender budget module (MVP-1 UI-first rebuild)."
app_email = "dev@kentender.local"
app_license = "mit"

required_apps = ["kentender_core", "kentender_strategy"]


def _asset_version(rel_path: str) -> int:
	try:
		return int((Path(__file__).resolve().parent / rel_path).stat().st_mtime)
	except OSError:
		return 1


_v = _asset_version

app_include_css = [
	f"/assets/kentender_budget/css/budget_funding_tokens.css?v={_v('public/css/budget_funding_tokens.css')}",
	f"/assets/kentender_budget/css/budget_funding_utilities.css?v={_v('public/css/budget_funding_utilities.css')}",
	f"/assets/kentender_budget/css/budget_funding_portfolio.css?v={_v('public/css/budget_funding_portfolio.css')}",
	f"/assets/kentender_budget/css/budget_funding_register.css?v={_v('public/css/budget_funding_register.css')}",
	f"/assets/kentender_budget/css/budget_funding_overview.css?v={_v('public/css/budget_funding_overview.css')}",
	f"/assets/kentender_budget/css/budget_funding_lines.css?v={_v('public/css/budget_funding_lines.css')}",
	f"/assets/kentender_budget/css/budget_funding_activity.css?v={_v('public/css/budget_funding_activity.css')}",
	f"/assets/kentender_budget/css/budget_funding_downstream.css?v={_v('public/css/budget_funding_downstream.css')}",
	f"/assets/kentender_budget/css/budget_funding_review.css?v={_v('public/css/budget_funding_review.css')}",
	f"/assets/kentender_budget/css/budget_funding_audit.css?v={_v('public/css/budget_funding_audit.css')}",
	f"/assets/kentender_budget/css/budget_funding_performance.css?v={_v('public/css/budget_funding_performance.css')}",
	f"/assets/kentender_budget/css/budget_funding_check_reserve.css?v={_v('public/css/budget_funding_check_reserve.css')}",
	f"/assets/kentender_budget/css/budget_funding_revisions.css?v={_v('public/css/budget_funding_revisions.css')}",
	f"/assets/kentender_budget/css/budget_funding_responsive.css?v={_v('public/css/budget_funding_responsive.css')}",
]

app_include_js = [
	# 6 of the 13 budget routes are standalone controllers (own dedicated
	# fixture, no shared dispatcher) — each now lazy-loads its own fixture +
	# budget_live_bind.js + kt_form_errors.js via frappe.require() instead
	# (portfolio/register/performance/check_reserve/revision_create/
	# revision_review _page.js). The other 7 (overview/lines/activity/
	# downstream/review/audit/revisions) call
	# kentender_budget.workspace.registerPage(...) synchronously at their own
	# controller's top level, which requires budget_workspace_shell.js (and
	# transitively budget_live_bind.js/kt_form_errors.js) to already be loaded
	# — registerPage itself assigns on_page_load, so deferring that load with
	# frappe.require() races Frappe's own page-load sequencer calling
	# on_page_load right after the controller script finishes. Fixing that
	# needs mountBudgetPage itself (inside budget_workspace_shell.js) to defer
	# its own fixture lookup, not a per-route change — left global for now,
	# a real follow-up, not forgotten.
	f"/assets/kentender_budget/js/budget_ui_fixtures/overview.js?v={_v('public/js/budget_ui_fixtures/overview.js')}",
	f"/assets/kentender_budget/js/budget_ui_fixtures/lines.js?v={_v('public/js/budget_ui_fixtures/lines.js')}",
	f"/assets/kentender_budget/js/budget_ui_fixtures/activity.js?v={_v('public/js/budget_ui_fixtures/activity.js')}",
	f"/assets/kentender_budget/js/budget_ui_fixtures/downstream.js?v={_v('public/js/budget_ui_fixtures/downstream.js')}",
	f"/assets/kentender_budget/js/budget_ui_fixtures/review.js?v={_v('public/js/budget_ui_fixtures/review.js')}",
	f"/assets/kentender_budget/js/budget_ui_fixtures/audit.js?v={_v('public/js/budget_ui_fixtures/audit.js')}",
	f"/assets/kentender_budget/js/budget_ui_fixtures/revisions.js?v={_v('public/js/budget_ui_fixtures/revisions.js')}",
	f"/assets/kentender_budget/js/budget_live_bind.js?v={_v('public/js/budget_live_bind.js')}",
	f"/assets/kentender_budget/js/budget_workspace_shell.js?v={_v('public/js/budget_workspace_shell.js')}",
	f"/assets/kentender_budget/js/budget_funding_workspace_redirect.js?v={_v('public/js/budget_funding_workspace_redirect.js')}",
]

# Never append ?v= to page_js — Frappe resolves these as disk paths.
page_js = {
	"budget-funding": "public/js/budget_funding_portfolio_page.js",
	"budget-register": "public/js/budget_funding_register_page.js",
	"budget-funding-performance": "public/js/budget_funding_performance_page.js",
	"budget-check-reserve": "public/js/budget_funding_check_reserve_page.js",
	"budget-overview": "public/js/budget_funding_overview_page.js",
	"budget-lines": "public/js/budget_funding_lines_page.js",
	"budget-funding-activity": "public/js/budget_funding_activity_page.js",
	"budget-revisions": "public/js/budget_funding_revisions_page.js",
	"budget-revision-create": "public/js/budget_funding_revision_create_page.js",
	"budget-revision-review": "public/js/budget_funding_revision_review_page.js",
	"budget-downstream": "public/js/budget_funding_downstream_page.js",
	"budget-review": "public/js/budget_funding_review_page.js",
	"budget-audit": "public/js/budget_funding_audit_page.js",
}

after_migrate = "kentender_budget.install.after_migrate"
before_tests = "kentender_budget.install.before_tests"
