# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Registry of Stitch Desk canvases that must carry the shared chrome baseline.

When you add a new Stitch Desk fixture (Strategy/Budget/… CL shell + code.html
main port), append a surface here in the **same change**. The chrome gate
fails if a registered fixture lacks `kt-stitch-canvas` or if the shared CSS
markers are missing.
"""

from __future__ import annotations

from typing import TypedDict


class StitchDeskSurface(TypedDict):
	id: str
	app: str
	fixture_rel: str
	desk_route: str
	primary_cta_testid: str
	select_filter_attr: str
	headline_selector: str


# Append-only for new Stitch Desk screens. Do not remove without replacing coverage.
STITCH_DESK_SURFACES: tuple[StitchDeskSurface, ...] = (
	{
		"id": "strategy-portfolio",
		"app": "kentender_strategy",
		"fixture_rel": "public/js/strategy_ui_fixtures/portfolio.js",
		"desk_route": "strategy-alignment",
		"primary_cta_testid": "kt-str-create-plan",
		"select_filter_attr": "data-kt-str-filter",
		"headline_selector": '.kt-str-root h1, [data-testid="kt-str-portfolio"] h1',
	},
	{
		"id": "strategy-plan-create",
		"app": "kentender_strategy",
		"fixture_rel": "public/js/strategy_ui_fixtures/create_plan.js",
		"desk_route": "strategy-plan-create",
		"primary_cta_testid": "kt-str-create-plan-submit",
		"select_filter_attr": "data-kt-str-field",
		"headline_selector": '.kt-str-root h1, [data-testid="kt-str-create-plan"] h1',
	},
	{
		"id": "budget-portfolio",
		"app": "kentender_budget",
		"fixture_rel": "public/js/budget_ui_fixtures/portfolio.js",
		"desk_route": "budget-funding",
		"primary_cta_testid": "kt-bud-register-budget",
		"select_filter_attr": "data-kt-bud-filter",
		"headline_selector": ".kt-bud-root h1, [data-testid='kt-bud-portfolio'] h1",
	},
	{
		"id": "budget-register",
		"app": "kentender_budget",
		"fixture_rel": "public/js/budget_ui_fixtures/register.js",
		"desk_route": "budget-register",
		"primary_cta_testid": "kt-bud-create-draft",
		"select_filter_attr": "data-kt-bud-field",
		"headline_selector": ".kt-bud-root h1, [data-testid='kt-bud-register'] h1",
	},
	{
		"id": "budget-overview",
		"app": "kentender_budget",
		"fixture_rel": "public/js/budget_ui_fixtures/overview.js",
		"desk_route": "budget-overview",
		"primary_cta_testid": "kt-bud-overview-primary",
		"select_filter_attr": "",
		"headline_selector": ".kt-bud-root h1, [data-testid='kt-bud-overview'] h1, [data-kt-bud-budget-title]",
	},
	{
		"id": "budget-lines",
		"app": "kentender_budget",
		"fixture_rel": "public/js/budget_ui_fixtures/lines.js",
		"desk_route": "budget-lines",
		"primary_cta_testid": "kt-bud-overview-primary",
		# Toolbar Budget Source / Strategic Target selects use data-kt-bud-lines-filter.
		"select_filter_attr": "data-kt-bud-lines-filter",
		"headline_selector": ".kt-bud-root h1, [data-testid='kt-bud-lines'] h1, [data-kt-bud-budget-title]",
	},
	{
		"id": "budget-funding-activity",
		"app": "kentender_budget",
		"fixture_rel": "public/js/budget_ui_fixtures/activity.js",
		"desk_route": "budget-funding-activity",
		"primary_cta_testid": "kt-bud-overview-primary",
		"select_filter_attr": "data-kt-bud-activity-filter",
		"headline_selector": ".kt-bud-root h1, [data-testid='kt-bud-activity'] h1, [data-kt-bud-budget-title]",
	},
	{
		"id": "budget-downstream",
		"app": "kentender_budget",
		"fixture_rel": "public/js/budget_ui_fixtures/downstream.js",
		"desk_route": "budget-downstream",
		"primary_cta_testid": "kt-bud-overview-primary",
		"select_filter_attr": "data-kt-bud-downstream-filter",
		"headline_selector": ".kt-bud-root h1, [data-testid='kt-bud-downstream'] h1, [data-kt-bud-budget-title]",
	},
	{
		"id": "budget-review",
		"app": "kentender_budget",
		"fixture_rel": "public/js/budget_ui_fixtures/review.js",
		"desk_route": "budget-review",
		"primary_cta_testid": "kt-bud-overview-primary",
		"select_filter_attr": "",
		"headline_selector": ".kt-bud-root h1, [data-testid='kt-bud-review'] h1, [data-kt-bud-budget-title]",
	},
	{
		"id": "budget-audit",
		"app": "kentender_budget",
		"fixture_rel": "public/js/budget_ui_fixtures/audit.js",
		"desk_route": "budget-audit",
		"primary_cta_testid": "kt-bud-audit-export",
		"select_filter_attr": "data-kt-bud-audit-filter",
		"headline_selector": ".kt-bud-root h1, [data-testid='kt-bud-audit'] h1, [data-kt-bud-budget-title]",
	},
	{
		"id": "budget-funding-performance",
		"app": "kentender_budget",
		"fixture_rel": "public/js/budget_ui_fixtures/performance.js",
		"desk_route": "budget-funding-performance",
		"primary_cta_testid": "kt-bud-performance-export",
		"select_filter_attr": "data-kt-bud-perf-filter",
		"headline_selector": ".kt-bud-root h1, [data-testid='kt-bud-performance'] h1",
	},
	{
		"id": "budget-check-reserve",
		"app": "kentender_budget",
		"fixture_rel": "public/js/budget_ui_fixtures/check_reserve.js",
		"desk_route": "budget-check-reserve",
		"primary_cta_testid": "kt-bud-check-reserve-reserve",
		"select_filter_attr": "data-kt-bud-cr-filter",
		"headline_selector": ".kt-bud-root h1, [data-testid='kt-bud-check-reserve'] h1",
	},
	{
		"id": "budget-revisions",
		"app": "kentender_budget",
		"fixture_rel": "public/js/budget_ui_fixtures/revisions.js",
		"desk_route": "budget-revisions",
		"primary_cta_testid": "kt-bud-overview-primary",
		"select_filter_attr": "",
		"headline_selector": ".kt-bud-root h1, [data-testid='kt-bud-revisions'] h1, [data-kt-bud-budget-title]",
	},
	{
		"id": "budget-revision-create",
		"app": "kentender_budget",
		"fixture_rel": "public/js/budget_ui_fixtures/revision_create.js",
		"desk_route": "budget-revision-create",
		"primary_cta_testid": "kt-bud-rev-submit",
		"select_filter_attr": "",
		"headline_selector": ".kt-bud-rev-create-title, [data-testid='kt-bud-revision-create'] h1",
	},
	{
		"id": "budget-revision-review",
		"app": "kentender_budget",
		"fixture_rel": "public/js/budget_ui_fixtures/revision_review.js",
		"desk_route": "budget-revision-review",
		"primary_cta_testid": "kt-bud-rev-review-apply",
		"select_filter_attr": "",
		"headline_selector": ".kt-bud-rev-review-title, [data-testid='kt-bud-revision-review'] h1",
	},
	{
		"id": "demands-workspace",
		"app": "kentender_procurement",
		"fixture_rel": "public/js/demands_ui_fixtures/workspace.js",
		"desk_route": "demands-workspace",
		"primary_cta_testid": "kt-dem-ui01-create",
		"select_filter_attr": "data-kt-dem-filter",
		"headline_selector": ".kt-dem-root h1, [data-testid='kt-dem-ui01-root'] h1",
	},
	{
		"id": "demand-form",
		"app": "kentender_procurement",
		"fixture_rel": "public/js/demands_ui_fixtures/form.js",
		"desk_route": "demand-form",
		"primary_cta_testid": "kt-dem-ui02-submit",
		"select_filter_attr": "data-kt-dem-field",
		"headline_selector": ".kt-dem-form h1, [data-testid='kt-dem-ui02-root'] h1",
	},
	{
		"id": "demand-review",
		"app": "kentender_procurement",
		"fixture_rel": "public/js/demands_ui_fixtures/review.js",
		"desk_route": "demand-review",
		"primary_cta_testid": "kt-dem-ui04-support",
		"select_filter_attr": "",
		"headline_selector": ".kt-dem-review h1, [data-testid='kt-dem-ui04-root'] h1",
	},
	{
		"id": "planning-workspace",
		"app": "kentender_procurement",
		"fixture_rel": "public/js/planning_ui_fixtures/workspace.js",
		"desk_route": "planning-workspace",
		"primary_cta_testid": "kt-pln-ui01-open-plan",
		"select_filter_attr": "data-kt-pln-filter",
		"headline_selector": ".kt-pln-root h1, [data-testid='kt-pln-ui01-root'] h1",
	},
	{
		"id": "procurement-plan-register",
		"app": "kentender_procurement",
		"fixture_rel": "public/js/planning_ui_fixtures/register.js",
		"desk_route": "procurement-plan-register",
		"primary_cta_testid": "kt-pln-ui02-submit",
		"select_filter_attr": "data-kt-field",
		"headline_selector": ".kt-pln-root h1, [data-testid='kt-pln-ui02-root'] h1",
	},
	{
		"id": "procurement-plan-builder",
		"app": "kentender_procurement",
		"fixture_rel": "public/js/planning_ui_fixtures/builder.js",
		"desk_route": "procurement-plan-builder",
		"primary_cta_testid": "kt-pln-ui03-add-demand",
		"select_filter_attr": "",
		"headline_selector": ".kt-pln-root h1, [data-testid='kt-pln-ui03-root'] h1",
	},
	{
		"id": "procurement-plan-item-editor",
		"app": "kentender_procurement",
		"fixture_rel": "public/js/planning_ui_fixtures/plan_item_editor.js",
		"desk_route": "procurement-plan-item-editor",
		"primary_cta_testid": "kt-pln-ui06-save-return",
		"select_filter_attr": "data-kt-pln-field",
		"headline_selector": ".kt-pln-root h1, [data-testid='kt-pln-ui06-root'] h1",
	},
)

SHARED_CHROME_CSS_REL = "public/css/kt_stitch_desk_chrome.css"
STITCH_CANVAS_CLASS = "kt-stitch-canvas"

# Markers that must exist in the shared CSS (Desk bleed + DS recipes).
REQUIRED_SHARED_CSS_MARKERS: tuple[str, ...] = (
	"kt-stitch-canvas",
	"Win98",
	"--weight-regular: 400",
	"button.bg-primary",
	"--kt-stitch-primary: #003d9b",
	"design_system_refactor",
	"data:image/svg+xml",
	"Manrope",
	"Inter",
	"appearance: none",
	# Permanent double-chevron kill (SVG Forms + Material expand_more).
	"select:has(+ .material-symbols-outlined)",
	"background-image: none !important",
	# Filled primary hover must stay white on lifted navy — never on-primary-container ink.
	"Filled primary hover: keep on-primary white",
	"button.bg-primary:hover",
	"#0052cc",
	"#002a6e",
	# Editable inputs: white fill — never surface (reads as disabled).
	"Editable inputs: white fill",
	"input[type=\"number\"]",
	"input[type=\"date\"]",
	"background-color: #ffffff !important",
	"background-color: #e2e2e8 !important",
	# DS section/table chrome — muted heads + rounded cards (not primary-fixed / square).
	"DS section/table chrome",
	"--kt-stitch-primary-fixed: #dae2ff",
	"--kt-stitch-table-head",
	"thead tr.bg-surface-container-low",
	"border-radius: 0.75rem !important",
	"kt-ds-section-title",
	"kt-ds-toolbar-band",
	"kt-ds-table-head",
	"kt-ds-data-block",
	# Softened card strokes — outline-variant / border-subtle.
	"Card borders use outline-variant",
	"--kt-stitch-outline-variant, #c3c6d6",
	".rounded-xl.border",
)
