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
	# mtime-based cache bust; touch this file after CSS edits so workers re-import hooks.
	try:
		return int((Path(__file__).resolve().parent / rel_path).stat().st_mtime)
	except OSError:
		return 1


# Phase 8 (STR-CHG-001 v1.3) deleted the last app_include_css/app_include_js
# entries this app owned (12 legacy strategy_alignment_*.css files, the
# strategy_ui_fixtures/*.js fixture set, strategy_live_bind.js,
# strategy_alignment_shell.js, strategy_alignment_workspace_redirect.js) —
# all backed only the 13 legacy Pages deleted in the same phase.
#
# The 3 Phase 7 production bundles were originally built with a plain
# `import "../strategy_shared/styles/tokens.css"` inside each bundle.js,
# on the assumption frappe.require() would load a paired CSS file the way
# it loads the JS entry point. It doesn't: esbuild only writes an
# assets.json key for genuine metafile entry points, and a CSS file pulled
# in via a plain top-level import from a JS bundle is a build *output*,
# not an entry point — so it compiled to a real file on disk that nothing
# ever linked, and all 3 screens rendered with zero styling applied
# (discovered 2026-08-24, alongside the missing globalProperties.__ fix —
# see AGENTS.md §6.1/§6.6). Loading the shared token stylesheet globally
# here, the same way kentender_core loads kt_industry_tokens.css, is the
# fix: it is scoped under .kt-strategy-ui (never :root), so it is safe to
# load on every Desk page and simply does nothing outside that class.
app_include_css = [
	f"/assets/kentender_strategy/css/strategy_shared_tokens.css?v={_asset_version('public/css/strategy_shared_tokens.css')}",
]

app_include_js = []

# Never append ?v= to page_js — Frappe resolves these as disk paths.
page_js = {
	# STR-CHG-001 v1.3 Phase 7 — the 3 production Vue-in-Desk pages
	# (STR-UI-01/02/04). The 13 pre-rebuild legacy strategy-* pages and the
	# strategy-portfolio-pilot spike that used to live here were deleted in
	# Phase 8 (see IMPLEMENTATION_TRACKER.md).
	"strategy-portfolio": "public/js/strategy_portfolio_page.js",
	"strategy-plan-workspace": "public/js/strategy_plan_workspace_page.js",
	"strategy-review-task": "public/js/strategy_review_task_page.js",
}
