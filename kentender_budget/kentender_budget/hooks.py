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
	f"/assets/kentender_budget/css/budget_funding_responsive.css?v={_v('public/css/budget_funding_responsive.css')}",
]

app_include_js = [
	f"/assets/kentender_budget/js/budget_ui_fixtures/portfolio.js?v={_v('public/js/budget_ui_fixtures/portfolio.js')}",
	f"/assets/kentender_budget/js/budget_ui_fixtures/register.js?v={_v('public/js/budget_ui_fixtures/register.js')}",
	f"/assets/kentender_budget/js/budget_live_bind.js?v={_v('public/js/budget_live_bind.js')}",
	f"/assets/kentender_budget/js/budget_funding_workspace_redirect.js?v={_v('public/js/budget_funding_workspace_redirect.js')}",
]

# Never append ?v= to page_js — Frappe resolves these as disk paths.
page_js = {
	"budget-funding": "public/js/budget_funding_portfolio_page.js",
	"budget-register": "public/js/budget_funding_register_page.js",
	"budget-funding-performance": "public/js/budget_stub_page.js",
	"budget-overview": "public/js/budget_stub_page.js",
}

after_migrate = "kentender_budget.install.after_migrate"
