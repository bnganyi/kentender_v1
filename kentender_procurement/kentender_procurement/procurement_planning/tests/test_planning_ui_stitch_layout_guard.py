# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Static layout guard — Planning Stitch UI (PLN-UI-01…10)."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

APP_PUBLIC = Path(frappe.get_app_path("kentender_procurement")) / "public"
WS_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "workspace.js"
REG_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "register.js"
BLD_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "builder.js"
ADD_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "add_demand_dialog.js"
REMOVE_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "remove_plan_item_dialog.js"
FINANCE_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "finance_confirm_drawer.js"
ED_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "plan_item_editor.js"
REVIEW_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "plan_review.js"
REVIEW_PAGE = APP_PUBLIC / "js" / "planning_review_page.js"
APPROVED_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "plan_approved.js"
APPROVED_PAGE = APP_PUBLIC / "js" / "planning_approved_page.js"
UPDATE_FIXTURE = APP_PUBLIC / "js" / "planning_ui_fixtures" / "plan_update.js"
UPDATE_PAGE = APP_PUBLIC / "js" / "planning_update_page.js"
LIVE_BIND = APP_PUBLIC / "js" / "planning_live_bind.js"
GET_PLAN_BUILDER = (
	Path(frappe.get_app_path("kentender_procurement"))
	/ "procurement_planning"
	/ "services"
	/ "get_plan_builder.py"
)
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
			REMOVE_FIXTURE,
			FINANCE_FIXTURE,
			ED_FIXTURE,
			REVIEW_FIXTURE,
			APPROVED_FIXTURE,
			UPDATE_FIXTURE,
			LIVE_BIND,
			CSS,
			WS_PAGE,
			REG_PAGE,
			BLD_PAGE,
			ED_PAGE,
			REVIEW_PAGE,
			APPROVED_PAGE,
			UPDATE_PAGE,
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
		# Stitch v1.9 literal port markers.
		self.assertIn(
			"Turn approved needs into funded, approved Plan Items ready for tendering.",
			text,
		)
		self.assertIn(
			"These controls define the workspace scope; they do not assign ownership to records.",
			text,
		)
		self.assertIn("border-l-4 border-l-primary", text)
		self.assertIn("arrow_forward", text)
		self.assertIn('data-kt-pln-filter="work_type"', text)
		self.assertIn('placeholder="Search work..."', text)
		self.assertIn("Plan Items returned by Finance", text)
		self.assertIn("Awaiting Finance confirmation", text)
		self.assertIn("Plan Items needing attention", text)
		self.assertIn('testid: "kt-pln-ui01-table-footer"', text)
		self.assertIn("tablePaginationFooterHtml", text)
		self.assertIn("font-headline-lg", text)
		self.assertIn("bg-surface-container-lowest", text)
		self.assertIn("max-w-[1400px]", text)
		# CSS must defeat md:w-64 or PE select crushes to "Min…".
		css = _read(CSS)
		self.assertIn(r".md\:w-64", css)
		self.assertIn('data-testid="kt-pln-ui01-filters"] .md\\:w-64', css)
		self.assertIn("flex: 0 0 16rem", css)
		self.assertIn("min-width: 14rem", css)
		self.assertIn("gap-x-4", css)
		self.assertIn("border-l-primary", css)
		# Forbidden: contribution-era scaffold.
		self.assertNotIn("md:grid-cols-4", text)
		self.assertNotIn("data-kt-pln-plan-contributions", text)
		self.assertNotIn('role="tablist"', text)
		self.assertNotIn("data-kt-pln-context-label", text)
		self.assertNotIn("approved and funded needs", text.lower())
		self.assertNotIn("truncate", text)
		self.assertNotIn("kt-pln-wrap", text)
		self.assertNotIn("cdn.tailwindcss.com", text)

	def test_register_fixture_markers(self):
		text = _read(REG_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui02-root"', text)
		self.assertIn('data-testid="kt-pln-ui02-form"', text)
		self.assertIn('data-testid="kt-pln-ui02-submit"', text)
		self.assertIn("data-kt-field-error", text)
		self.assertIn("Create annual procurement plan", text)
		self.assertIn(
			"Register the plan that will contain approved needs for one Procuring Entity and financial year.",
			text,
		)
		self.assertIn("font-headline-lg", text)
		self.assertIn("1. Plan ownership", text)
		self.assertIn("2. Plan details", text)
		self.assertIn("input-glow", text)
		self.assertIn("calendar_month", text)
		self.assertIn("add_task", text)
		self.assertIn("arrow_drop_down", text)
		self.assertIn('data-testid="kt-pln-ui02-period"', text)
		self.assertIn('data-testid="kt-pln-ui02-actions"', text)
		self.assertIn("absolute bottom-0", text)
		self.assertIn("KES - Kenyan Shilling", text)
		self.assertNotIn("kt-pln-ui02-no-budget", text)
		self.assertNotIn("kt-pln-wrap", text)
		self.assertNotIn("cdn.tailwindcss.com", text)
		self.assertNotIn("budget_amount", text.lower())
		self.assertNotIn('data-kt-field="budget"', text)
		# Desk chrome already provides breadcrumbs — no in-canvas crumb trail.
		self.assertNotIn('aria-label="Breadcrumb"', text)
		self.assertNotIn("chevron_right", text)
		css = _read(CSS)
		self.assertIn("input-glow", css)
		# Wrapper owns focus — nested controls must not draw a second ring.
		self.assertIn(".input-glow:focus-within", css)
		self.assertIn(".input-glow input:focus", css)
		self.assertIn("--kt-pln-focus-border", css)

	def test_builder_fixture_markers(self):
		text = _read(BLD_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui03-root"', text)
		self.assertIn('data-testid="kt-pln-ui03-empty"', text)
		self.assertIn('data-testid="kt-pln-ui03-add-demand"', text)
		self.assertIn("No Plan Items yet", text)
		self.assertIn(
			"Add an Approved Demand to begin building this annual Plan.",
			text,
		)
		self.assertIn("font-headline-lg", text)
		self.assertIn("Back to Planning", text)
		self.assertIn("Open Plan", text)
		self.assertIn("Finance Confirmed", text)
		self.assertIn("Total Planned Value", text)
		self.assertIn("Validation Status", text)
		self.assertIn("assignment_late", text)
		self.assertIn("All permitted units", text)
		self.assertIn("All categories", text)
		self.assertIn("All statuses", text)
		self.assertIn("Search Plan Items", text)
		self.assertIn("expand_more", text)
		self.assertIn("pb-24", text)
		self.assertIn("absolute bottom-0", text)
		# Standardized summary strip (horizontal flex + dividers — not icon grid).
		self.assertIn("flex flex-row items-center justify-between", text)
		self.assertIn("h-8 w-px", text)
		self.assertIn('data-kt-pln-builder-finance', text)
		self.assertNotIn("md:grid-cols-4", text)
		self.assertNotIn("account_balance_wallet", text)
		self.assertNotIn("list_alt", text)
		self.assertNotIn(">payments<", text)
		# PLN-UI-05 populated regions share the builder fixture.
		self.assertIn('data-testid="kt-pln-ui05-header"', text)
		self.assertIn('data-testid="kt-pln-ui05-issue-strip"', text)
		self.assertIn('data-testid="kt-pln-ui05-run-validation"', text)
		self.assertIn("Submit for review", text)
		self.assertIn("Add approved demands", text)
		self.assertIn("Complete the Plan Item before requesting Finance confirmation.", text)
		self.assertIn("No further plan items added yet.", text)
		self.assertIn(">Finance</th>", text)
		self.assertIn(">Planned Value</th>", text)
		self.assertIn("Not requested", text)
		self.assertNotIn(">Category</th>", text)
		self.assertNotIn("<tfoot", text)
		self.assertNotIn("Items ready", text)
		self.assertNotIn("Org Units", text)
		self.assertNotIn("Dept. Contributions", text)
		self.assertNotIn("Submit for sign-off", text)
		self.assertNotIn("inventory_2", text)
		# Summary metrics + dialog host.
		self.assertIn('data-kt-pln-builder-total', text)
		self.assertIn("bg-status-reserved/10", text)
		self.assertIn("data-kt-pln-dialog-host", text)
		# Stitch PLN-UI-05 summary has no Preference cell / no extra Next-step card.
		self.assertNotIn("kt-pln-ui05-pref-coverage", text)
		self.assertNotIn("kt-pln-ui05-next-step", text)
		self.assertNotIn("kt-pln-wrap", text)
		self.assertNotIn("cdn.tailwindcss.com", text)
		# Desk owns crumbs — no in-canvas Stitch breadcrumb trail on empty or populated.
		self.assertIn('data-testid="kt-pln-ui05-header"', text)
		self.assertNotIn('aria-label="Breadcrumb"', text)
		self.assertNotIn("chevron_right", text)
		self.assertIn("No changes remain", text)
		self.assertIn("Cancel update", text)
		self.assertIn('data-testid="kt-pln-ui05-cancel-update"', text)

	def test_remove_item_dialog_fixture_markers(self):
		text = _read(REMOVE_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui05a-dialog"', text)
		self.assertIn("Remove Plan Item from draft?", text)
		self.assertIn("Propose Plan Item removal?", text)
		self.assertIn("Keep item", text)
		self.assertIn("Remove from draft", text)
		self.assertIn("Propose removal", text)
		self.assertIn("No funding confirmed; no reservation to release", text)
		self.assertIn("Funding confirmation will be cancelled", text)
		self.assertIn("The item remains active in the current Approved Plan", text)
		self.assertIn("Reason for removal", text)
		self.assertIn('data-kt-field="reason"', text)
		self.assertIn('data-kt-field-error="reason"', text)
		self.assertIn("delete_forever", text)
		self.assertIn("max-w-[560px]", text)
		self.assertNotIn(">Delete<", text)
		self.assertNotIn("type=\"checkbox\"", text)
		self.assertNotIn("cdn.tailwindcss.com", text)
		self.assertNotIn("truncate", text)

	def test_finance_confirm_drawer_fixture_markers(self):
		text = _read(FINANCE_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui07-drawer"', text)
		self.assertIn("absolute inset-0", text)
		self.assertIn("max-w-2xl", text)
		self.assertIn("Confirm Plan Item funding", text)
		self.assertIn("Plan Item Context", text)
		self.assertIn("Funding to confirm", text)
		self.assertIn("Amount to reserve", text)
		self.assertIn("Available allocation", text)
		self.assertIn("Derived balance", text)
		self.assertIn("Confirm funding", text)
		self.assertIn("Return to planner", text)
		self.assertIn("Funding shortfall", text)
		self.assertIn("Resolve in Budget &amp; Funding", text)
		self.assertIn("/app/budget-funding", text)
		self.assertIn('data-kt-field="reason"', text)
		self.assertIn('data-kt-field-error="reason"', text)
		self.assertIn("grid-cols-1 sm:grid-cols-3", text)
		self.assertIn('data-testid="kt-pln-ui07-money"', text)
		self.assertIn('data-testid="kt-pln-ui07-confirm"', text)
		self.assertIn('data-testid="kt-pln-ui07a-resolve"', text)
		self.assertNotIn("cdn.tailwindcss.com", text)
		self.assertNotIn("truncate", text)
		self.assertNotIn("position:fixed", text)
		self.assertNotIn("position: fixed", text)
		start = text.find('data-kt-pln-07-variant="shortfall"')
		self.assertGreater(start, 0)
		shortfall = text[start:]
		self.assertNotIn("Confirm funding", shortfall)
		self.assertNotIn('data-kt-pln-action="confirm-finance"', shortfall)
		self.assertIn("Funding shortfall", shortfall)

	def test_add_demand_dialog_fixture_markers(self):
		text = _read(ADD_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui04-dialog"', text)
		self.assertIn('data-testid="kt-pln-ui04-add"', text)
		self.assertIn("Add approved Demands", text)
		self.assertIn(
			"Select from pre-approved strategic demands to allocate to this procurement plan.",
			text,
		)
		self.assertIn("data-kt-pln-elig-body", text)
		self.assertIn("data-kt-pln-elig-search", text)
		self.assertIn("Search approved Demands", text)
		self.assertIn("All permitted units", text)
		self.assertIn("All categories", text)
		self.assertIn("arrow_drop_down", text)
		self.assertIn("bg-surface-bright", text)
		self.assertIn("Available to plan only", text)
		self.assertIn("font-headline-md", text)
		self.assertIn("bg-surface-container-lowest", text)
		self.assertIn("max-h-[921px]", text)
		self.assertIn("shadow-[0_8px_30px_rgb(0,61,155,0.1)]", text)
		# Stitch v1.9 corrected 7-column table (checkbox + 6 data headers).
		self.assertIn(">Demand</th>", text)
		self.assertIn(">Organisation Unit</th>", text)
		self.assertIn(">Approved Value</th>", text)
		self.assertIn(">Required By</th>", text)
		self.assertIn(">Proposed Funding</th>", text)
		self.assertIn(">Status</th>", text)
		self.assertNotIn(">Already planned</th>", text)
		self.assertNotIn(">Available to plan</th>", text)
		self.assertNotIn(">Funding status</th>", text)
		self.assertNotIn(">Approved amount</th>", text)
		# Formation progressive disclosure (multi-Demand).
		self.assertIn("Plan Item formation", text)
		self.assertIn("Create separate Plan Items", text)
		self.assertIn("Combine into one Plan Item", text)
		self.assertIn('data-testid="kt-pln-ui04-formation"', text)
		self.assertIn('data-testid="kt-pln-ui04-formation-reason"', text)
		self.assertIn('data-kt-field-error="formation_reason"', text)
		self.assertIn("View source breakdown", text)
		# Never an absolute selection <td> (shifts columns vs headers).
		self.assertNotIn("absolute left-0 top-0 bottom-0 w-1 bg-primary", text)
		self.assertNotIn("max-w-[200px] truncate", text)
		self.assertNotIn('data-testid="kt-pln-ui04-package"', text)
		self.assertNotIn("kt-pln-wrap", text)
		self.assertNotIn("cdn.tailwindcss.com", text)
		self.assertNotIn("expand_more", text)

	def test_planning_css_stitch_spacing_tokens(self):
		"""PLN Stitch spacing: section-gap=1.5rem, gutter-md=1rem; py-gutter-md required for UI-04."""
		css = _read(APP_PUBLIC / "css" / "planning_workspace.css")
		self.assertIn(".px-section-gap { padding-left: 1.5rem !important; padding-right: 1.5rem !important; }", css)
		self.assertIn(".py-gutter-md { padding-top: 1rem !important; padding-bottom: 1rem !important; }", css)
		self.assertIn(".p-section-gap { padding: 1.5rem !important; }", css)
		self.assertIn(".gap-section-gap { gap: 1.5rem !important; }", css)
		self.assertIn(".gap-gutter-md { gap: 1rem !important; }", css)
		# Regression: never ship the inflated 2rem section-gap that crushed dialog rhythm.
		self.assertNotIn(".p-section-gap { padding: 2rem !important; }", css)
		self.assertNotIn(".gap-gutter-md { gap: 1.5rem !important; }", css)
		# Desk chrome already has crumbs — canvas top under the toolbar stays tight.
		self.assertIn("main > .max-w-7xl", css)
		self.assertIn("padding-top: 0.5rem !important;", css)

	def test_stitch_ui04_table_columns_aligned(self):
		"""Stitch authority must keep equal th/td counts (no absolute selection td)."""
		stitch = (
			Path(frappe.get_app_path("kentender_procurement")).resolve().parents[1]
			/ "docs"
			/ "mvp-1"
			/ "04_planning"
			/ "ui_design"
			/ "PLN-UI-04.html"
		)
		self.assertTrue(stitch.is_file(), f"missing Stitch file: {stitch}")
		text = _read(stitch)
		self.assertIn(">Approved Value</th>", text)
		self.assertIn(">Proposed Funding</th>", text)
		self.assertNotIn("absolute left-0 top-0 bottom-0 w-1 bg-primary", text)
		self.assertNotIn("max-w-[200px] truncate", text)
		import re

		thead = re.search(r"<thead[\s\S]*?</thead>", text).group(0)
		tbody = re.search(r"<tbody[\s\S]*?</tbody>", text).group(0)
		th_count = len(re.findall(r"<th\b", thead))
		first_tr = re.search(r"<tr[\s\S]*?</tr>", tbody).group(0)
		td_count = len(re.findall(r"<td\b", first_tr))
		self.assertEqual(th_count, 7)
		self.assertEqual(td_count, 7)

	def test_live_bind_elig_rows_match_stitch(self):
		live = _read(LIVE_BIND)
		self.assertIn("End of available demands based on current filters.", live)
		self.assertIn("is-selected", live)
		self.assertIn(
			"Select from pre-approved strategic demands to allocate to this procurement plan.",
			live,
		)
		self.assertIn('font-data-md text-data-md text-on-surface font-semibold', live)
		self.assertIn("data-kt-pln-elig-title", live)
		self.assertIn("data-kt-pln-elig-ou-cell", live)
		self.assertIn("proposed_funding", live)
		self.assertIn("Planning Ready", live)
		self.assertIn("selectedIds", live)
		# Legal data: never truncate Organisation Unit / proposed funding.
		self.assertNotIn("truncate max-w-[180px]", live)
		self.assertNotIn("truncate max-w-", live)
		self.assertNotIn("max-w-[200px] truncate", live)
		# Never use an absolute <td> for the selection bar — it shifts columns.
		self.assertNotIn("absolute left-0 top-0 bottom-0 w-1 bg-primary", live)
		self.assertNotIn('class="absolute inset-y-0 left-0 w-1 bg-primary', live)
		# tr::before also becomes an anonymous table-cell in Chrome — forbid it.
		css = _read(APP_PUBLIC / "css" / "planning_workspace.css")
		self.assertNotIn("[data-kt-pln-elig-row].is-selected::before", css)
		self.assertIn(
			"[data-kt-pln-elig-row].is-selected > td:first-child",
			css,
		)
		self.assertIn("box-shadow: inset 4px 0 0", css)
		self.assertIn("font-size: 16px !important", css)
		self.assertIn("[data-kt-pln-elig-amount]", css)
		self.assertIn('data-testid="kt-pln-ui03-filters"', live)
		self.assertIn("data-kt-pln-builder-period", live)

	def test_plan_item_editor_fixture_markers(self):
		text = _read(ED_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui06-root"', text)
		self.assertIn('data-testid="kt-pln-ui06-footer"', text)
		self.assertIn("data-kt-pln-editor-scroll", text)
		self.assertIn("overflow-y-auto", text)
		self.assertLess(text.find("data-kt-pln-editor-scroll"), text.find('data-testid="kt-pln-ui06-footer"'))
		self.assertIn('data-testid="kt-pln-ui06-request-finance"', text)
		self.assertIn("data-kt-field-error", text)
		self.assertIn("data-kt-pln-field", text)
		self.assertIn("Confirmed method", text)
		self.assertIn("Save and request Finance confirmation", text)
		self.assertIn("font-headline-lg", text)
		self.assertIn("font-headline-sm", text)
		self.assertIn("Procurement approach", text)
		self.assertIn("Planned schedule", text)
		self.assertIn("Approved source", text)
		self.assertIn("Indicative lots expected", text)
		self.assertIn("No lots expected", text)
		self.assertIn("Not requested", text)
		self.assertIn(
			"Business scope, quantity, owner, delivery requirement and approved value come from the Approved Demand source(s) and cannot be changed here.",
			text,
		)
		self.assertIn("Confirm all milestone dates before requesting Finance confirmation.", text)
		self.assertNotIn("Preference and reservation", text)
		self.assertNotIn('data-testid="kt-pln-ui06-pref-section"', text)
		self.assertNotIn('data-testid="kt-pln-ui06-pref-none"', text)
		self.assertIn("Strategy target", text)
		self.assertIn("Indicative lotting", text)
		self.assertIn('data-testid="kt-pln-ui06-lotting-details"', text)
		self.assertIn("data-kt-pln-lotting-details", text)
		self.assertIn('data-testid="kt-pln-ui06-lifecycle"', text)
		# Chip sits to the right of the title (Stitch), not above it.
		life_idx = text.find('data-testid="kt-pln-ui06-lifecycle"')
		title_idx = text.find('data-testid="kt-pln-ui06-title"')
		self.assertGreater(life_idx, title_idx)
		self.assertIn("lg:grid-cols-12", text)
		self.assertIn("lg:col-span-8", text)
		self.assertIn("lg:col-span-4", text)
		self.assertIn("sticky", text)
		self.assertIn('data-testid="kt-pln-ui06-source-sidebar"', text)
		self.assertIn("data-kt-pln-source-sidebar", text)
		self.assertIn("max-w-[1440px]", text)
		self.assertNotIn("flat-input", text)
		self.assertNotIn("Planning approach", text)
		self.assertNotIn("Source Demand", text)
		self.assertNotIn("Save and return to Plan update", text)
		self.assertNotIn('data-testid="kt-pln-ui06-save-return"', text)
		self.assertNotIn("Statutory and strategy treatment", text)
		self.assertNotIn("Statutory allocation treatment", text)
		self.assertNotIn("Statutory rationale", text)
		self.assertNotIn("Planned treatment value", text)
		self.assertNotIn("Value treatment note", text)
		self.assertNotIn("Plan-level coverage", text)
		self.assertNotIn('data-testid="kt-pln-ui06-add-another"', text)
		self.assertNotIn("Add another approved Demand to this Plan Item", text)
		self.assertNotIn('data-testid="kt-pln-ui06-package-structure"', text)
		self.assertNotIn("Package structure set when added", text)
		self.assertNotIn("Combine in this Plan Item", text)
		self.assertNotIn("Keep separate", text)
		self.assertNotIn('name="aggregation_decision"', text)
		self.assertNotIn("kt-pln-wrap", text)
		self.assertNotIn("cdn.tailwindcss.com", text)
		self.assertNotIn("<tfoot", text)
		# Desk chrome already provides breadcrumbs — no in-canvas crumb trail.
		self.assertNotIn('aria-label="Breadcrumb"', text)
		self.assertNotIn("data-kt-pln-editor-plan-crumb", text)
		self.assertNotIn("chevron_right", text)
		self.assertIn('data-kt-field-error="form"', text)
		self.assertIn('data-kt-field-error="ms_evaluation_completed"', text)
		self.assertIn('data-kt-field-error="ms_invitation_published"', text)
		self.assertIn("Invitation published", text)
		self.assertIn("Delivery and completion", text)
		css = _read(CSS)
		self.assertIn("body.kt-pln-editor-active .main-section > #body", css)
		self.assertIn("[data-kt-pln-editor-scroll]", css)
		self.assertIn("body.kt-pln-editor-active .main-section", css)
		self.assertIn('.kt-pln-root[data-testid="kt-pln-ui06-root"]', css)
		self.assertNotIn('.kt-pln-root [data-testid="kt-pln-ui06-root"]', css)

	def test_contribution_structures_absent(self):
		drawer = APP_PUBLIC / "js" / "planning_ui_fixtures" / "contribution_drawer.js"
		self.assertFalse(drawer.exists())
		for path in (
			BLD_FIXTURE,
			ED_FIXTURE,
			REVIEW_FIXTURE,
			APPROVED_FIXTURE,
			UPDATE_FIXTURE,
			LIVE_BIND,
			CSS,
		):
			body = _read(path)
			lower = body.lower()
			self.assertNotIn("submit-dept", body)
			self.assertNotIn("departmental contribution", lower)
			self.assertNotIn("contribution_drawer", body)
			self.assertNotIn("get_departmental_contribution", body)
			self.assertNotIn("submit_departmental_contribution", body)
			self.assertNotIn("ensureContributionDrawer", body)
		bld = _read(BLD_FIXTURE)
		self.assertIn("submit-for-review", bld)
		self.assertIn("kt-pln-ui05-submit-review", bld)
		ed = _read(ED_FIXTURE)
		self.assertNotIn("kt-pln-ui06-pref-section", ed)
		self.assertNotIn('data-kt-pln-field="preference_reservation_scheme"', ed)

	def test_plan_review_fixture_markers(self):
		text = _read(REVIEW_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui08-root"', text)
		self.assertIn('data-testid="kt-pln-ui08-summary"', text)
		self.assertIn('data-testid="kt-pln-ui08-items"', text)
		self.assertIn('data-testid="kt-pln-ui08-items-table"', text)
		self.assertIn('data-testid="kt-pln-ui08-statutory"', text)
		self.assertIn('data-testid="kt-pln-ui08-issues"', text)
		self.assertIn('data-testid="kt-pln-ui08-rail"', text)
		self.assertIn('data-testid="kt-pln-ui08-primary"', text)
		self.assertIn('data-testid="kt-pln-ui08-return"', text)
		self.assertIn('data-testid="kt-pln-ui08-trail"', text)
		self.assertIn("Review and approve procurement plan", text)
		self.assertIn("Finance Confirmed", text)
		self.assertIn("Preference &amp; Reservation Coverage", text)
		self.assertIn("Derived automatically", text)
		self.assertIn("Professional approval", text)
		self.assertIn("Return to planner", text)
		self.assertIn("Approve plan", text)
		self.assertIn(">Finance<", text)
		self.assertIn("gavel", text)
		self.assertIn("Prior-decision trail", text)
		self.assertIn('data-kt-field="decision_comment"', text)
		self.assertIn('data-kt-field-error="decision_comment"', text)
		self.assertNotIn("Review annual procurement plan", text)
		self.assertNotIn("Items ready", text)
		self.assertNotIn("Statutory allocation coverage", text)
		self.assertNotIn("Departmental submission", text)
		self.assertNotIn("Return plan", text)
		self.assertNotIn("approval matrix", text.lower())
		self.assertNotIn("truncate", text)
		self.assertNotIn("cdn.tailwindcss.com", text)
		self.assertNotIn('aria-label="Breadcrumb"', text)

	def test_plan_approved_fixture_markers(self):
		text = _read(APPROVED_FIXTURE)
		page = _read(APPROVED_PAGE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui09-root"', text)
		self.assertIn('data-testid="kt-pln-ui09-header"', text)
		self.assertIn('data-testid="kt-pln-ui09-add-item"', text)
		self.assertIn('data-testid="kt-pln-ui09-export"', text)
		self.assertIn('data-testid="kt-pln-ui09-successor-notice"', text)
		self.assertIn('data-testid="kt-pln-ui09-summary"', text)
		self.assertIn('data-testid="kt-pln-ui09-filters"', text)
		self.assertIn('data-testid="kt-pln-ui09-implementation-table"', text)
		self.assertIn('data-testid="kt-pln-ui09-publication"', text)
		self.assertIn("Add Plan Item", text)
		self.assertIn("Export approved plan", text)
		self.assertIn("Approved baseline is read-only", text)
		self.assertIn("Plan implementation", text)
		self.assertIn("Publication Evidence", text)
		self.assertIn("Tender take-up", text)
		self.assertIn("Organisation Unit", text)
		self.assertIn("<h1", text)
		self.assertIn("bindPlanningApproved", page)
		self.assertNotIn("truncate", text)
		self.assertNotIn("cdn.tailwindcss.com", text)
		self.assertNotIn("Create Tender", text)
		self.assertNotIn("contribution", text.lower())
		self.assertNotIn("Procurement Planning</a>", text)
		self.assertNotIn("<nav class=\"font-body-sm", text)

	def test_plan_update_fixture_markers(self):
		text = _read(UPDATE_FIXTURE)
		page = _read(UPDATE_PAGE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui10-root"', text)
		self.assertIn('data-testid="kt-pln-ui10-header"', text)
		self.assertIn('data-testid="kt-pln-ui10-validate"', text)
		self.assertIn('data-testid="kt-pln-ui10-banner"', text)
		self.assertIn('data-testid="kt-pln-ui10-summary"', text)
		self.assertIn('data-testid="kt-pln-ui10-context"', text)
		self.assertIn('data-testid="kt-pln-ui10-reason"', text)
		self.assertIn('data-kt-field-error="update_reason"', text)
		self.assertIn('data-testid="kt-pln-ui10-changes-table"', text)
		self.assertIn('data-testid="kt-pln-ui10-unchanged"', text)
		self.assertIn('data-testid="kt-pln-ui10-issue"', text)
		self.assertIn('data-testid="kt-pln-ui10-no-changes"', text)
		self.assertIn('data-testid="kt-pln-ui10-cancel"', text)
		self.assertIn('data-testid="kt-pln-ui10-save"', text)
		self.assertIn('data-testid="kt-pln-ui10-submit"', text)
		self.assertIn("Plan update", text)
		self.assertIn("Update context", text)
		self.assertIn("Changes in this update", text)
		self.assertIn("Run validation", text)
		self.assertIn("Submit update for review", text)
		self.assertIn("No changes remain in this update.", text)
		self.assertIn("<h1", text)
		self.assertIn("bindPlanningUpdate", page)
		self.assertNotIn("truncate", text)
		self.assertNotIn("cdn.tailwindcss.com", text)
		self.assertNotIn("Create Tender", text)
		self.assertNotIn("contribution", text.lower())
		self.assertNotIn("Procurement Planning</a>", text)
		self.assertNotIn("<nav class=\"font-body-sm", text)

	def test_live_bind_and_pages(self):
		live = _read(LIVE_BIND)
		self.assertIn("get_planning_workspace", live)
		self.assertIn("get_planning_create_scope", live)
		self.assertIn("create_procurement_plan", live)
		self.assertIn("get_plan_builder", live)
		self.assertIn("next_step_message", live)
		self.assertIn("version_status", live)
		self.assertIn("Submit for review", live)
		self.assertIn("attachPagination", live)
		self.assertIn("helper_text", live)
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
		self.assertIn("selectedIds", live)
		self.assertIn("data-kt-pln-formation-mode", live)
		self.assertIn("formation_reason", live)
		self.assertIn("update_plan_item", live)
		self.assertIn("validate_plan", live)
		self.assertIn("finance_status_label", live)
		self.assertIn("Not completed", live)
		self.assertIn("Not requested", live)
		self.assertIn("Complete the Plan Item before requesting Finance confirmation.", live)
		self.assertIn("more_vert", live)
		self.assertIn("Remove from draft", live)
		self.assertIn("top-full", live)
		self.assertIn(">delete<", live)
		self.assertIn("text-status-exhausted", live)
		self.assertIn("justify-end", live)
		self.assertNotIn('position: "fixed"', live)
		self.assertIn("remove_plan_item_from_plan", live)
		self.assertIn("cancel_plan_update", live)
		self.assertIn("data-kt-pln-05a-variant", live)
		self.assertIn("kt-pln-ui05-remove-from-draft", live)
		self.assertNotIn(">Delete from", live)
		dto = _read(GET_PLAN_BUILDER)
		self.assertIn("finance_status_label", dto)
		self.assertIn("can_remove_from_draft", dto)
		self.assertIn("can_propose_removal", dto)
		self.assertIn("no_changes_remain", dto)
		self.assertIn("Not requested", dto)
		self.assertIn("Complete the Plan Item before requesting Finance confirmation.", dto)
		self.assertIn("get_plan_item_editor", live)
		self.assertIn(".catch(", live)
		self.assertIn('errors.form', live)
		self.assertIn("request-finance", live)
		self.assertIn("Confirm all milestone dates before requesting Finance confirmation.", live)
		self.assertNotIn("add-another-demand", live)
		self.assertNotIn("pref-assign", live)
		self.assertNotIn("builder-pref-coverage", live)
		self.assertIn("lotting-details", live)
		self.assertIn("lotting_decision", live)
		self.assertNotIn("get_departmental_contribution", live)
		self.assertNotIn("submit_departmental_contribution", live)
		self.assertNotIn("ensureContributionDrawer", live)
		self.assertIn("ktFormErrors", live)
		self.assertIn("get_plan_finance_task", live)
		self.assertIn("confirm_plan_item_funding", live)
		self.assertIn("return_plan_item_from_finance", live)
		self.assertIn("open-finance", live)
		self.assertIn("data-kt-pln-finance-drawer", live)
		self.assertIn("budget_funding_route", live)
		self.assertIn("kt-pln-ui07a-resolve", live)
		self.assertIn("get_plan_review", live)
		self.assertIn("submit_plan_for_review", live)
		self.assertIn("record_plan_decision", live)
		self.assertIn("approve_plan_version", live)
		self.assertIn("bindPlanningWorkspace", live)
		self.assertIn("bindPlanningRegister", live)
		self.assertIn("bindPlanningBuilder", live)
		self.assertIn("bindPlanningItemEditor", live)
		self.assertIn("bindPlanningReview", live)
		self.assertIn("bindPlanningApproved", live)
		self.assertIn("bindPlanningUpdate", live)
		self.assertIn("get_plan_implementation", live)
		self.assertIn("get_plan_update", live)
		self.assertIn("save_plan_update", live)
		self.assertIn("publish_approved_plan", live)
		self.assertIn("finance_confirmed_label", live)
		self.assertIn("data-kt-pln-review-finance-confirmed", live)
		self.assertIn("kt-pln-ui08-statutory", live)
		self.assertIn("submit-for-review", live)

		self.assertIn("enterNative", _read(WS_PAGE))
		self.assertIn("enterNative", _read(REG_PAGE))
		self.assertIn("enterNative", _read(BLD_PAGE))
		self.assertIn("enterNative", _read(ED_PAGE))
		self.assertIn("enterNative", _read(REVIEW_PAGE))
		self.assertIn("enterNative", _read(APPROVED_PAGE))
		self.assertIn("enterNative", _read(UPDATE_PAGE))

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
		self.assertEqual(
			page_js.get("procurement-plan-approved"),
			"public/js/planning_approved_page.js",
		)
		self.assertEqual(
			page_js.get("procurement-plan-update"),
			"public/js/planning_update_page.js",
		)
		includes = "\n".join(hooks.app_include_css or [])
		self.assertIn("planning_workspace.css", includes)
		self.assertIn("planning_live_bind.js", js_includes)
		self.assertIn("planning_ui_fixtures/workspace.js", js_includes)
		self.assertIn("planning_ui_fixtures/add_demand_dialog.js", js_includes)
		self.assertIn("planning_ui_fixtures/remove_plan_item_dialog.js", js_includes)
		self.assertIn("planning_ui_fixtures/finance_confirm_drawer.js", js_includes)
		self.assertNotIn("contribution_drawer.js", js_includes)
		self.assertIn("planning_ui_fixtures/plan_item_editor.js", js_includes)
		self.assertIn("planning_ui_fixtures/plan_review.js", js_includes)
		self.assertIn("planning_review_page.js", js_includes)
		self.assertIn("planning_ui_fixtures/plan_approved.js", js_includes)
		self.assertIn("planning_approved_page.js", js_includes)
		self.assertIn("planning_ui_fixtures/plan_update.js", js_includes)
		self.assertIn("planning_update_page.js", js_includes)
