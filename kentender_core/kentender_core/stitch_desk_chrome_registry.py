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
#
# STR-CHG-001 v1.3 Phase 8: the 2 Strategy rows that used to live here
# ("strategy-portfolio" / "strategy-plan-create", fixture_rel pointing at
# strategy_ui_fixtures/portfolio.js / create_plan.js) were removed. Both
# backed pre-rebuild legacy Pages deleted in Phase 8, and both fixture files
# are deleted with them. This registry is specifically for the
# Tailwind/Stitch-HTML-ported canvas pattern (see module docstring); the
# Phase 7 Strategy replacements (strategy-portfolio, strategy-plan-workspace,
# strategy-review-task) are hand-authored Vue 3 components, not Stitch HTML
# ports, so they do not get a row here — no coverage is being dropped.
STITCH_DESK_SURFACES: tuple[StitchDeskSurface, ...] = (
	# BUD-CHG-001 v1.2: the 12 Budget rows that used to live here
	# (budget-portfolio, budget-register, budget-overview, budget-lines,
	# budget-funding-activity, budget-downstream, budget-review, budget-audit,
	# budget-funding-performance, budget-check-reserve, budget-revisions,
	# budget-revision-create, budget-revision-review, fixture_rel pointing at
	# budget_ui_fixtures/*.js) were removed. All backed the pre-rebuild
	# vanilla-JS Desk pages deleted in the BUD-CHG-001 v1.2 UI teardown, and
	# all fixture files are deleted with them. This registry is specifically
	# for the Tailwind/Stitch-HTML-ported canvas pattern (see module
	# docstring); the replacement Budget pages are hand-authored Vue 3
	# components in the Industry design system, not Stitch HTML ports (same
	# precedent as kentender_strategy's Phase 7 rebuild above), so they do
	# not get a row here — no coverage is being dropped.
	{
		"id": "departmental-needs",
		"app": "kentender_procurement",
		"fixture_rel": "public/js/departmental_needs_page.js",
		"desk_route": "departmental-needs",
		"primary_cta_testid": "",
		"select_filter_attr": "",
		"headline_selector": "[data-testid='departmental-needs-workspace'] h1",
	},
	{
		"id": "departmental-needs-new",
		"app": "kentender_procurement",
		"fixture_rel": "public/js/departmental_needs_create_page.js",
		"desk_route": "departmental-needs-new",
		"primary_cta_testid": "kt-nds-create-submit",
		"select_filter_attr": "",
		"headline_selector": "[data-testid='departmental-needs-new'] h1",
	},
	{
		"id": "planning-workspace",
		"app": "kentender_procurement",
		"fixture_rel": "public/js/planning_ui_fixtures/workspace.js",
		"desk_route": "planning-workspace",
		"primary_cta_testid": "kt-pln-ui01-primary-action",
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
		"primary_cta_testid": "kt-pln-ui06-request-finance",
		"select_filter_attr": "data-kt-pln-field",
		"headline_selector": ".kt-pln-root h1, [data-testid='kt-pln-ui06-root'] h1",
	},
	{
		"id": "procurement-plan-review",
		"app": "kentender_procurement",
		"fixture_rel": "public/js/planning_ui_fixtures/plan_review.js",
		"desk_route": "procurement-plan-review",
		"primary_cta_testid": "kt-pln-ui08-primary",
		"select_filter_attr": "",
		"headline_selector": ".kt-pln-root h1, [data-testid='kt-pln-ui08-root'] h1",
	},
	{
		"id": "procurement-plan-approved",
		"app": "kentender_procurement",
		"fixture_rel": "public/js/planning_ui_fixtures/plan_approved.js",
		"desk_route": "procurement-plan-approved",
		"primary_cta_testid": "kt-pln-ui09-add-item",
		"select_filter_attr": "data-kt-pln-ui09-filter",
		"headline_selector": ".kt-pln-root h1, [data-testid='kt-pln-ui09-root'] h1",
	},
	{
		"id": "procurement-plan-update",
		"app": "kentender_procurement",
		"fixture_rel": "public/js/planning_ui_fixtures/plan_update.js",
		"desk_route": "procurement-plan-update",
		"primary_cta_testid": "kt-pln-ui10-validate",
		"select_filter_attr": "",
		"headline_selector": ".kt-pln-root h1, [data-testid='kt-pln-ui10-root'] h1",
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
