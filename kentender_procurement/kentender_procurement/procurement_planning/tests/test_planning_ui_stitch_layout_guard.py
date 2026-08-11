# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Static layout guard — Planning Stitch UI (PLN-UI-01…08)."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

APP_PUBLIC = Path(frappe.get_app_path("kentender_procurement")) / "public"
WS_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "workspace.js"
REG_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "register.js"
BLD_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "builder.js"
ADD_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "add_demand_dialog.js"
ED_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "plan_item_editor.js"
CONTRIB_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "contribution_drawer.js"
REVIEW_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "plan_review.js"
REVIEW_PAGE = APP_PUBLIC / "js" / "planning_review_page.js"
LIVE_BIND = APP_PUBLIC / "js" / "planning_live_bind.js"
CSS = APP_PUBLIC / "css" / "planning_workspace.css"
WS_PAGE = APP_PUBLIC / "js" / "planning_workspace_page.js"
REG_PAGE = APP_PUBLIC / "js" / "planning_register_page.js"
BLD_PAGE = APP_PUBLIC / "js" / "planning_builder_page.js"
ED_PAGE = APP_PUBLIC / "js" / "planning_item_editor_page.js"


def _read(path: Path) -> str:
	return path.read_text(encoding="utf-8")


class TestPlanningUiStitchLayoutGuard(IntegrationTestCase):
	def test_assets_exist(self):
		for path in (
			WS_FIXTURE,
			REG_FIXTURE,
			BLD_FIXTURE,
			ADD_FIXTURE,
			ED_FIXTURE,
			CONTRIB_FIXTURE,
			REVIEW_FIXTURE,
			LIVE_BIND,
			CSS,
			WS_PAGE,
			REG_PAGE,
			BLD_PAGE,
			ED_PAGE,
			REVIEW_PAGE,
		):
			self.assertTrue(path.is_file(), path)

	def test_workspace_fixture_markers(self):
		text = _read(WS_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui01-root"', text)
		self.assertIn('data-testid="kt-pln-ui01-filters"', text)
		self.assertIn('data-testid="kt-pln-ui01-plan-panel"', text)
		self.assertIn('data-testid="kt-pln-ui01-queue"', text)
		self.assertIn('data-testid="kt-pln-ui01-open-plan"', text)
		self.assertIn("data-kt-pln-filter", text)
		self.assertIn("Work Requiring Action", text)
		# Literal Stitch utility classes retained (not parallel BEM layout).
		self.assertIn("font-headline-lg", text)
		self.assertIn("bg-surface-container-lowest", text)
		self.assertIn("grid grid-cols-1 md:grid-cols-4", text)
		self.assertNotIn("kt-pln-wrap", text)
		self.assertNotIn("cdn.tailwindcss.com", text)

	def test_register_fixture_markers(self):
		text = _read(REG_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui02-root"', text)
		self.assertIn('data-testid="kt-pln-ui02-form"', text)
		self.assertIn('data-testid="kt-pln-ui02-submit"', text)
		self.assertIn('data-testid="kt-pln-ui02-no-budget"', text)
		self.assertIn("data-kt-field-error", text)
		self.assertIn("Create annual procurement plan", text)
		self.assertIn("font-headline-lg", text)
		self.assertIn("Plan ownership", text)
		self.assertNotIn("kt-pln-wrap", text)
		self.assertNotIn("cdn.tailwindcss.com", text)
		self.assertNotIn("budget_amount", text.lower())
		# Desk chrome already provides breadcrumbs — no in-canvas crumb trail.
		self.assertNotIn('aria-label="Breadcrumb"', text)
		self.assertNotIn("chevron_right", text)

	def test_builder_fixture_markers(self):
		text = _read(BLD_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui03-root"', text)
		self.assertIn('data-testid="kt-pln-ui03-empty"', text)
		self.assertIn('data-testid="kt-pln-ui03-add-demand"', text)
		self.assertIn("No Plan Items yet", text)
		self.assertIn("font-headline-lg", text)
		self.assertIn("Back to Planning", text)
		# PLN-UI-05 populated regions share the builder fixture.
		self.assertIn('data-testid="kt-pln-ui05-issue-strip"', text)
		self.assertIn('data-testid="kt-pln-ui05-run-validation"', text)
		self.assertIn("Submit for sign-off", text)
		self.assertIn("Dept. Contributions", text)
		# Summary metrics use primary; status chips use semantic available/reserved (not flat grey).
		self.assertIn('data-kt-pln-builder-total', text)
		self.assertIn("text-primary", text)
		self.assertIn("bg-status-reserved/10", text)
		self.assertIn("data-kt-pln-dialog-host", text)
		# Stitch PLN-UI-05 summary has no Preference cell / no extra Next-step card.
		self.assertNotIn("kt-pln-ui05-pref-coverage", text)
		self.assertNotIn("kt-pln-ui05-next-step", text)
		self.assertNotIn("kt-pln-wrap", text)
		self.assertNotIn("cdn.tailwindcss.com", text)
		self.assertNotIn('aria-label="Breadcrumb"', text)
		self.assertNotIn("chevron_right", text)

	def test_add_demand_dialog_fixture_markers(self):
		text = _read(ADD_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui04-dialog"', text)
		self.assertIn('data-testid="kt-pln-ui04-add"', text)
		self.assertIn("Add approved Demand", text)
		self.assertIn("data-kt-pln-elig-body", text)
		self.assertIn("data-kt-pln-elig-search", text)
		self.assertIn("Available to plan", text)
		self.assertIn("font-headline-md", text)
		self.assertIn("bg-surface-container-lowest", text)
		# Literal Stitch search / checkbox / footer structure
		self.assertIn("material-symbols-outlined text-outline text-sm", text)
		self.assertIn(">search</span>", text)
		self.assertIn("arrow_drop_down", text)
		self.assertIn("w-4 h-4 text-primary bg-surface border-outline-variant rounded", text)
		self.assertIn("pl-10 pr-3 py-2", text)
		self.assertIn("inset-y-0 left-0 pl-3", text)
		# Pack v1.3 / Stitch: source selection footer — no packaging radios.
		self.assertIn("Add Demand and continue", text)
		self.assertIn("Plan Need Items separately", text)
		self.assertIn('data-testid="kt-pln-ui04-plan-separately"', text)
		self.assertIn('data-testid="kt-pln-ui04-separation-reason"', text)
		self.assertIn('data-testid="kt-pln-ui04-aggregate-reason"', text)
		# Stitch summary chip: Funding reserved (verified icon)
		self.assertIn("Funding reserved", text)
		self.assertIn('data-testid="kt-pln-ui04-funding-reserved"', text)
		self.assertIn(">verified</span>", text)
		self.assertIn("kt-pln-ui04-summary-chip", text)
		self.assertIn("gap-x-6 gap-y-2", text)
		self.assertNotIn('data-testid="kt-pln-ui04-package"', text)
		self.assertNotIn('data-testid="kt-pln-ui04-package-one"', text)
		self.assertNotIn("Create one Plan Item for the selected Need Items", text)
		self.assertNotIn("Create a separate Plan Item for each Need Item", text)
		self.assertNotIn("kt-pln-wrap", text)
		self.assertNotIn("cdn.tailwindcss.com", text)

	def test_live_bind_elig_rows_match_stitch(self):
		live = _read(LIVE_BIND)
		self.assertIn("End of available demands based on current filters.", live)
		self.assertIn("bg-primary/5", live)
		self.assertIn("align-top", live)
		self.assertIn(
			"font-body-md text-body-md text-on-surface font-semibold leading-tight",
			live,
		)
		self.assertIn("text-[11px] font-bold tracking-wide uppercase", live)
		self.assertIn("moneyCellHtml", live)
		self.assertIn("is-selected", live)
		self.assertIn("data-kt-pln-elig-title", live)
		self.assertIn("data-kt-pln-elig-ou-cell", live)
		# Legal data: never truncate Organisation Unit (or similar identity fields).
		self.assertNotIn("truncate max-w-[180px]", live)
		self.assertNotIn("truncate max-w-", live)
		# Never use an absolute <td> for the selection bar — it shifts columns.
		self.assertNotIn('class="absolute inset-y-0 left-0 w-1 bg-primary', live)
		# tr::before also becomes an anonymous table-cell in Chrome — forbid it.
		css = _read(APP_PUBLIC / "css" / "planning_workspace.css")
		self.assertNotIn("[data-kt-pln-elig-row].is-selected::before", css)
		self.assertIn(
			"[data-kt-pln-elig-row].is-selected > td:first-child",
			css,
		)
		self.assertIn("box-shadow: inset 4px 0 0", css)
		# Stitch data-md / body-md size pins (not chrome 14px / dialog 13px).
		self.assertIn("font-size: 16px !important", css)
		self.assertIn("[data-kt-pln-elig-amount]", css)
		# UI-05 populated composition gates
		self.assertIn('data-testid="kt-pln-ui03-filters"', live)
		self.assertIn("data-kt-pln-builder-period", live)

	def test_plan_item_editor_fixture_markers(self):
		text = _read(ED_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui06-root"', text)
		self.assertIn('data-testid="kt-pln-ui06-footer"', text)
		self.assertIn('data-testid="kt-pln-ui06-save-return"', text)
		self.assertIn("data-kt-field-error", text)
		self.assertIn("data-kt-pln-field", text)
		self.assertIn("Confirmed method", text)
		self.assertIn("Save and return to Plan update", text)
		self.assertIn("font-headline-lg", text)
		self.assertIn("font-headline-md", text)
		# Literal Stitch PLN-UI-06 regions (REQ v1.5 Preference and reservation).
		self.assertIn("Planning approach", text)
		self.assertIn("Planned schedule", text)
		self.assertIn("Preference and reservation", text)
		self.assertIn("None assigned", text)
		self.assertIn("Strategy Context", text)
		self.assertIn('data-testid="kt-pln-ui06-pref-section"', text)
		self.assertIn('data-testid="kt-pln-ui06-pref-none"', text)
		self.assertIn("Source Demand", text)
		self.assertIn("Indicative lotting", text)
		self.assertIn('data-testid="kt-pln-ui06-lotting-details"', text)
		self.assertIn("data-kt-pln-lotting-details", text)
		self.assertIn('data-testid="kt-pln-ui06-lifecycle"', text)
		self.assertIn("bg-status-reserved/10", text)
		self.assertIn("text-status-reserved", text)
		self.assertIn("border-status-reserved/20", text)
		# Chip sits above the title (Stitch), not inline after amount.
		life_idx = text.find('data-testid="kt-pln-ui06-lifecycle"')
		title_idx = text.find('data-testid="kt-pln-ui06-title"')
		self.assertGreater(title_idx, life_idx)
		self.assertNotIn("bg-tertiary-fixed text-tertiary font-label-caps", text)
		self.assertIn("lg:grid-cols-12", text)
		self.assertIn("lg:col-span-8", text)
		self.assertIn("lg:col-span-4", text)
		self.assertIn("lg:sticky", text)
		self.assertIn('data-testid="kt-pln-ui06-source-sidebar"', text)
		self.assertIn("data-kt-pln-source-sidebar", text)
		self.assertIn("max-w-7xl", text)
		self.assertNotIn("max-w-5xl", text)
		self.assertNotIn("flat-input", text)
		self.assertNotIn("Approved source", text)
		self.assertNotIn("Statutory and strategy treatment", text)
		self.assertNotIn("Statutory allocation treatment", text)
		self.assertNotIn("Statutory rationale", text)
		self.assertNotIn("Planned treatment value", text)
		self.assertNotIn("Value treatment note", text)
		self.assertNotIn("Plan-level coverage", text)
		# Pack v1.3: no aggregation radios; Add another Demand CTA for exceptional combine.
		self.assertIn('data-testid="kt-pln-ui06-add-another"', text)
		self.assertIn("Add another approved Demand to this Plan Item", text)
		self.assertIn('data-testid="kt-pln-ui06-source-allocation"', text)
		self.assertNotIn('data-testid="kt-pln-ui06-package-structure"', text)
		self.assertNotIn("Package structure set when added", text)
		self.assertNotIn("Combine in this Plan Item", text)
		self.assertNotIn("Keep separate", text)
		self.assertNotIn('name="aggregation_decision"', text)
		self.assertNotIn("kt-pln-wrap", text)
		self.assertNotIn("cdn.tailwindcss.com", text)
		# Desk chrome already provides breadcrumbs — no in-canvas crumb trail.
		self.assertNotIn('aria-label="Breadcrumb"', text)
		self.assertNotIn("data-kt-pln-editor-plan-crumb", text)
		self.assertNotIn("chevron_right", text)
		# Milestone dates have inline error slots for soft validation flagging.
		self.assertIn('data-kt-field-error="ms_evaluation_completed"', text)
		self.assertIn('data-kt-field-error="ms_invitation_published"', text)

	def test_contribution_drawer_fixture_markers(self):
		text = _read(CONTRIB_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui07-root"', text)
		self.assertIn('data-testid="kt-pln-ui07-footer"', text)
		self.assertIn('data-testid="kt-pln-ui07-confirm"', text)
		self.assertIn('data-testid="kt-pln-ui07-declaration"', text)
		self.assertIn("Confirm contribution", text)
		self.assertIn("Submit departmental contribution", text)
		self.assertIn("Included Items", text)
		self.assertIn("data-kt-field-error", text)
		self.assertIn("data-kt-pln-field", text)
		self.assertNotIn("truncate", text)
		self.assertNotIn("cdn.tailwindcss.com", text)

	def test_plan_review_fixture_markers(self):
		text = _read(REVIEW_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui08-root"', text)
		self.assertIn('data-testid="kt-pln-ui08-summary"', text)
		self.assertIn('data-testid="kt-pln-ui08-items"', text)
		self.assertIn('data-testid="kt-pln-ui08-statutory"', text)
		self.assertIn('data-testid="kt-pln-ui08-issues"', text)
		self.assertIn('data-testid="kt-pln-ui08-rail"', text)
		self.assertIn('data-testid="kt-pln-ui08-primary"', text)
		self.assertIn('data-testid="kt-pln-ui08-return"', text)
		self.assertIn('data-testid="kt-pln-ui08-trail"', text)
		self.assertIn("Review annual procurement plan", text)
		self.assertIn("Statutory allocation coverage", text)
		self.assertIn("Prior-decision trail", text)
		self.assertIn("Recommend approval", text)
		self.assertIn("Return plan", text)
		self.assertIn('data-kt-field="decision_comment"', text)
		self.assertIn('data-kt-field-error="decision_comment"', text)
		self.assertNotIn("approval matrix", text.lower())
		self.assertNotIn("truncate", text)
		self.assertNotIn("cdn.tailwindcss.com", text)
		self.assertNotIn('aria-label="Breadcrumb"', text)

	def test_live_bind_and_pages(self):
		live = _read(LIVE_BIND)
		self.assertIn("get_planning_workspace", live)
		self.assertIn("get_planning_create_scope", live)
		self.assertIn("create_procurement_plan", live)
		self.assertIn("get_plan_builder", live)
		self.assertIn("next_step_message", live)
		self.assertIn("version_status", live)
		self.assertIn("Submit for sign-off", live)
		# Semantic status tones shared with workspace / Budget / Strategy chips.
		self.assertIn("status-available", live)
		self.assertIn("validationTone", live)
		self.assertIn("contributionTone", live)
		self.assertIn("lifecycleTone", live)
		# Semantic status tones — Ready = available (green), Open = primary (blue).
		self.assertIn("function validationTone", live)
		self.assertIn("function lifecycleTone", live)
		self.assertIn("status-available", live)
		self.assertIn('s === "ready"', live)
		self.assertIn('s === "open"', live)
		self.assertNotIn(
			'bg-surface-variant text-on-surface-variant border-outline-variant") +\n\t\t\t\t\t\t\t\'">\' +\n\t\t\t\t\t\t\t(needs',
			live,
		)
		self.assertIn("list_eligible_demands", live)
		self.assertIn("add_demand_to_plan", live)
		self.assertIn("aggregate_plan_allocations", live)
		self.assertIn("formation_mode", live)
		self.assertIn("plan-separately", live)
		self.assertIn("update_plan_item", live)
		self.assertIn("validate_plan", live)
		self.assertIn("get_plan_item_editor", live)
		self.assertIn("preference_reservation", live)
		self.assertIn("pref-assign", live)
		self.assertNotIn("builder-pref-coverage", live)
		self.assertIn("lotting-details", live)
		self.assertIn("lotting_decision", live)
		self.assertIn("get_departmental_contribution", live)
		self.assertIn("submit_departmental_contribution", live)
		self.assertIn("ensureContributionDrawer", live)
		self.assertIn("ktFormErrors", live)
		self.assertIn("get_plan_review", live)
		self.assertIn("submit_plan_for_review", live)
		self.assertIn("record_plan_decision", live)
		self.assertIn("approve_plan_version", live)
		self.assertIn("bindPlanningWorkspace", live)
		self.assertIn("bindPlanningRegister", live)
		self.assertIn("bindPlanningBuilder", live)
		self.assertIn("bindPlanningItemEditor", live)
		self.assertIn("bindPlanningReview", live)
		self.assertIn("submit-for-review", live)

		self.assertIn("enterNative", _read(WS_PAGE))
		self.assertIn("enterNative", _read(REG_PAGE))
		self.assertIn("enterNative", _read(BLD_PAGE))
		self.assertIn("enterNative", _read(ED_PAGE))
		self.assertIn("enterNative", _read(REVIEW_PAGE))

	def test_hooks_wire_pages(self):
		from kentender_procurement import hooks

		page_js = hooks.page_js or {}
		self.assertEqual(
			page_js.get("planning-workspace"),
			"public/js/planning_workspace_page.js",
		)
		js_includes = "\n".join(hooks.app_include_js or [])
		self.assertIn("planning_workspace_redirect.js", js_includes)
		self.assertEqual(
			page_js.get("procurement-plan-register"),
			"public/js/planning_register_page.js",
		)
		self.assertEqual(
			page_js.get("procurement-plan-builder"),
			"public/js/planning_builder_page.js",
		)
		self.assertEqual(
			page_js.get("procurement-plan-item-editor"),
			"public/js/planning_item_editor_page.js",
		)
		self.assertEqual(
			page_js.get("procurement-plan-review"),
			"public/js/planning_review_page.js",
		)
		includes = "\n".join(hooks.app_include_css or [])
		self.assertIn("planning_workspace.css", includes)
		self.assertIn("planning_live_bind.js", js_includes)
		self.assertIn("planning_ui_fixtures/workspace.js", js_includes)
		self.assertIn("planning_ui_fixtures/add_demand_dialog.js", js_includes)
		self.assertIn("planning_ui_fixtures/contribution_drawer.js", js_includes)
		self.assertIn("planning_ui_fixtures/plan_item_editor.js", js_includes)
		self.assertIn("planning_ui_fixtures/plan_review.js", js_includes)
		self.assertIn("planning_review_page.js", js_includes)
