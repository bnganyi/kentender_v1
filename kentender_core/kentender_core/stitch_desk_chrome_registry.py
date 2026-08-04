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
)

SHARED_CHROME_CSS_REL = "public/css/kt_stitch_desk_chrome.css"
STITCH_CANVAS_CLASS = "kt-stitch-canvas"

# Markers that must exist in the shared CSS (Desk bleed lessons).
REQUIRED_SHARED_CSS_MARKERS: tuple[str, ...] = (
	"kt-stitch-canvas",
	"Win98",
	"--weight-regular: 400",
	"button.bg-primary",
	"--kt-stitch-primary: #001f48",
	"data:image/svg+xml",
	"Manrope",
	"Inter",
	"appearance: none",
	# Permanent double-chevron kill (SVG Forms + Material expand_more).
	"select:has(+ .material-symbols-outlined)",
	"background-image: none !important",
)
