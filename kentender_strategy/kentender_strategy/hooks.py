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


def _asset_version(abs_path: Path) -> int:
	# mtime-based cache bust; touch the source file after edits so workers re-import hooks.
	try:
		return int(abs_path.stat().st_mtime)
	except OSError:
		return 1


_CORE_PUBLIC = Path(__file__).resolve().parent.parent.parent / "kentender_core" / "kentender_core" / "public"

# Phase 8 (STR-CHG-001 v1.3) deleted the last app_include_css/app_include_js
# entries this app owned (12 legacy strategy_alignment_*.css files, the
# strategy_ui_fixtures/*.js fixture set, strategy_live_bind.js,
# strategy_alignment_shell.js, strategy_alignment_workspace_redirect.js) —
# all backed only the 13 legacy Pages deleted in the same phase.
#
# kt_industry_tokens.css (owned by kentender_core, scoped under .kt-industry,
# never :root) is the one canonical design system for the whole application —
# see AGENTS.md §6.6. Strategy previously forked its own copy
# (strategy_shared_tokens.css / .kt-strategy-ui) rather than loading this
# file directly, on the mistaken belief that no precedent existed for one
# app consuming another's published CSS asset; that fork drifted from the
# canonical tokens and was deleted. Frappe serves every installed app's
# static assets from one shared /assets/<app_name>/ namespace, so loading
# kentender_core's file by URL here works the same way any of this app's
# own app_include_css entries do.
app_include_css = [
	f"/assets/kentender_core/css/kt_industry_tokens.css?v={_asset_version(_CORE_PUBLIC / 'css/kt_industry_tokens.css')}",
]

app_include_js = []

# Never append ?v= to page_js — Frappe resolves these as disk paths.
page_js = {
	# STR-CHG-001 v1.7 §10 — one Desk Page carries every canonical route:
	# /app/strategy, /app/strategy/plan/{plan_id}[/history |
	# /version/{n}/structure], /app/strategy/approval/{plan_version_id}[/tab].
	# The three Phase 7 Pages (strategy-portfolio / strategy-plan-workspace /
	# strategy-review-task) were replaced outright, not aliased (tracker
	# rule 4); str_chg_001_v1_7_delete_legacy_strategy_pages removes their
	# records from a synced site.
	"strategy": "public/js/strategy_page.js",
}
