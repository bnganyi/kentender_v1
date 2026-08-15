# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Static layout guard — active Planning Stitch UI (PLN-UI-01…09)."""

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
			LIVE_BIND,
			CSS,
			WS_PAGE,
			REG_PAGE,
			BLD_PAGE,
			ED_PAGE,
			REVIEW_PAGE,
			APPROVED_PAGE,
		):
			self.assertTrue(path.is_file(), path)

	def test_workspace_fixture_markers(self):
		text = _read(WS_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui01-root"', text)
		self.assertIn('data-testid="kt-pln-ui01-filters"', text)
		self.assertIn('data-testid="kt-pln-ui01-plan-panel"', text)
		self.assertIn('data-testid="kt-pln-ui01-work-section"', text)
		self.assertIn('data-testid="kt-pln-ui01-waiting-section"', text)
		self.assertIn('data-testid="kt-pln-ui01-primary-action"', text)
		self.assertIn("data-kt-pln-filter", text)
		self.assertIn("Work requiring action", text)
		# Stitch v1.9 literal port markers.
		self.assertIn(
			"Turn approved needs into funded, approved Plan Items ready for tendering.",
			text,
		)
		self.assertIn('data-kt-pln-action="change-context"', text)
		self.assertIn("All pending actions have been completed.", text)
		self.assertNotIn('aria-label="Breadcrumb"', text)
		self.assertNotIn("chevron_right", text)
		self.assertNotIn(">Current Plan<", text)
		self.assertIn("kt-pln-table-block", text)
		self.assertIn("arrow_forward", text)
		self.assertIn('data-kt-pln-filter="work_type"', text)
		self.assertIn('placeholder="Search work"', text)
		# The exact four options are server-owned and bound into this select.
		self.assertIn("data-kt-pln-work-body", text)
		self.assertIn("data-kt-pln-waiting-body", text)
		self.assertIn("Nothing is currently waiting on another reviewer.", text)
		self.assertIn("data-kt-pln-loading", text)
		self.assertIn("data-kt-pln-error", text)
		self.assertIn("font-headline-lg", text)
		self.assertIn("max-w-7xl", text)
		css = _read(CSS)
		self.assertIn(".kt-pln-workspace-canvas", css)
		self.assertIn(".kt-pln-summary-grid", css)
		self.assertIn("grid-template-columns: repeat(4", css)
		self.assertIn("@media (max-width: 599px)", css)
		self.assertIn("font-family: \"JetBrains Mono\"", css)
		self.assertIn(".kt-pln-icon-filled", css)
		self.assertIn("font-family: Manrope", css)
		self.assertIn("font-family: Inter", css)
		# Forbidden: contribution-era scaffold.
		self.assertNotIn("md:grid-cols-4", text)
		self.assertNotIn("data-kt-pln-plan-contributions", text)
		self.assertNotIn('role="tablist"', text)
		self.assertNotIn("data-kt-pln-context-label", text)
		self.assertNotIn("approved and funded needs", text.lower())
		self.assertNotIn("truncate", text)
		self.assertNotIn("kt-pln-wrap", text)
		self.assertNotIn("cdn.tailwindcss.com", text)
		self.assertIn(
			'.page-container[data-page-route="procurement-plan-item-editor"]',
			css,
		)
		self.assertNotIn("body.kt-pln-editor-active .page-container,", css)

	def test_register_fixture_markers(self):
		text = _read(REG_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui02-root"', text)
		self.assertIn('data-testid="kt-pln-ui02-form"', text)
		self.assertIn('data-testid="kt-pln-ui02-submit"', text)
		self.assertIn("Create annual procurement plan", text)
		self.assertIn(
			"Confirm the annual Plan that will contain approved needs for this Procuring Entity and financial year.",
			text,
		)
		self.assertIn("font-headline-lg", text)
		self.assertIn("Plan identity", text)
		self.assertIn("data-kt-pln-register-identity", text)
		self.assertIn("Draft Version 1", text)
		self.assertIn("add_task", text)
		self.assertIn('data-testid="kt-pln-ui02-actions"', text)
		self.assertIn(">Cancel</button>", text)
		self.assertIn("Create plan", text)
		self.assertNotIn("<input", text)
		self.assertNotIn("<select", text)
		self.assertNotIn("coordinating", text.lower())
		self.assertNotIn("budget", text.lower())
		self.assertNotIn("kt-pln-wrap", text)
		self.assertNotIn("cdn.tailwindcss.com", text)
		self.assertNotIn('aria-label="Breadcrumb"', text)
		self.assertNotIn("chevron_right", text)

	def test_builder_fixture_markers(self):
		text = _read(BLD_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui03-root"', text)
		self.assertIn('data-testid="kt-pln-ui03-empty"', text)
		self.assertIn('data-testid="kt-pln-ui03-add-demand"', text)
		self.assertIn("No Plan Items yet", text)
		self.assertIn("Approved Demands are ready to add to this annual Plan.", text)
		self.assertIn("font-headline-lg", text)
		self.assertIn("Back to Procurement Planning", text)
		self.assertIn("Open Plan", text)
		self.assertIn("Finance Confirmed", text)
		self.assertIn("Draft Planned Value", text)
		self.assertIn("Validation", text)
		self.assertIn("assignment_late", text)
		self.assertIn("All Organisation Units", text)
		self.assertIn("All statuses", text)
		self.assertIn("Search Plan Items", text)
		self.assertIn("expand_more", text)
		self.assertIn('data-kt-pln-builder-finance', text)
		self.assertIn('data-testid="kt-pln-builder-header"', text)
		self.assertIn('data-kt-pln-outstanding', text)
		self.assertIn("Add approved Demands", text)
		self.assertIn(">Finance</th>", text)
		self.assertIn(">Planned Value</th>", text)
		self.assertIn(">Planning</th>", text)
		self.assertIn(">Validation</th>", text)
		self.assertNotIn(">Category</th>", text)
		self.assertNotIn(">Method</th>", text)
		self.assertNotIn(">Schedule</th>", text)
		self.assertNotIn("<tfoot", text)
		self.assertIn('data-kt-pln-builder-total', text)
		self.assertIn("data-kt-pln-dialog-host", text)
		self.assertNotIn("kt-pln-wrap", text)
		self.assertNotIn("cdn.tailwindcss.com", text)
		self.assertNotIn('aria-label="Breadcrumb"', text)
		self.assertNotIn("chevron_right", text)

	def test_remove_item_dialog_fixture_markers(self):
		text = _read(REMOVE_FIXTURE)
		self.assertIn("data-kt-pln-removal-dialog", text)
		self.assertIn('role="dialog"', text)
		self.assertIn('aria-modal="true"', text)
		self.assertIn("Keep item", text)
		self.assertIn("Reason for removal", text)
		self.assertIn("data-kt-pln-removal-reason", text)
		self.assertIn("data-kt-pln-removal-source-rows", text)
		self.assertIn("data-kt-pln-removal-confirm", text)
		self.assertIn("max-w-2xl", text)
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
		# Revision HTML: checkbox plus seven governed source columns.
		self.assertIn(">Demand</th>", text)
		self.assertIn(">Organisation Unit</th>", text)
		self.assertIn(">Available Need Items</th>", text)
		self.assertIn(">Available value</th>", text)
		self.assertIn(">Required By</th>", text)
		self.assertIn(">Proposed Funding</th>", text)
		self.assertIn(">Status</th>", text)
		self.assertNotIn(">Already planned</th>", text)
		self.assertNotIn(">Available to plan</th>", text)
		self.assertNotIn(">Funding status</th>", text)
		self.assertNotIn(">Approved amount</th>", text)
		# Formation progressive disclosure (multi-Demand).
		self.assertIn("Plan Item formation", text)
		self.assertIn("One Plan Item for each Demand", text)
		self.assertIn("One combined Plan Item for all selected Demands", text)
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
		live = "\n".join(
			(
				_read(APP_PUBLIC / "js" / "planning_demand_dialog.js"),
				_read(APP_PUBLIC / "js" / "planning_builder_bind.js"),
				_read(APP_PUBLIC / "js" / "planning_ui_fixtures" / "add_demand_dialog.js"),
				_read(APP_PUBLIC / "js" / "planning_ui_fixtures" / "builder.js"),
			)
		)
		self.assertIn("kt-pln-selected-row", live)
		self.assertIn(
			"Select from pre-approved strategic demands to allocate to this procurement plan.",
			live,
		)
		self.assertIn('font-data-md text-data-md', live)
		self.assertIn("organisation_unit_label", live)
		self.assertIn("proposed_budget_line_display", live)
		self.assertIn("Planning Ready", live)
		self.assertIn("selected", live)
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
		self.assertIn("data-kt-pln-builder-period", live)

	def test_plan_item_editor_fixture_markers(self):
		text = _read(ED_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui06-root"', text)
		self.assertIn('data-kt-pln-action="request-finance"', text)
		self.assertIn("overflow-y-auto", text)
		self.assertIn("data-kt-field-error", text)
		self.assertIn("data-kt-pln-field", text)
		self.assertIn("Request Finance confirmation", text)
		self.assertIn("font-headline-lg", text)
		self.assertIn("font-headline-sm", text)
		self.assertIn("Procurement approach", text)
		self.assertIn("Planned schedule", text)
		self.assertIn("Approved requirement", text)
		self.assertIn("No lots expected", text)
		self.assertIn(
			"The Approved Demand controls the business scope, quantity, required-by date, owner and planned value.",
			text,
		)
		self.assertNotIn("Preference and reservation", text)
		self.assertIn("Indicative lotting", text)
		self.assertIn('"ms_notification_of_award"', text)
		self.assertIn('data-kt-pln-action="back"', text)
		self.assertIn('data-kt-pln-action="save"', text)
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
		self.assertIn('"ms_evaluation_completed"', text)
		self.assertIn('"ms_invitation_published"', text)
		self.assertIn("Invitation or advertisement", text)
		self.assertIn("Contract completion", text)
		css = _read(CSS)
		self.assertIn("body.kt-pln-editor-active .main-section > #body", css)
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
		self.assertNotIn("submit-for-review", bld)
		self.assertNotIn("kt-pln-ui05-submit-review", bld)
		ed = _read(ED_FIXTURE)
		self.assertNotIn("kt-pln-ui06-pref-section", ed)
		self.assertNotIn('data-kt-pln-field="preference_reservation_scheme"', ed)

	def test_plan_review_fixture_markers(self):
		text = _read(REVIEW_FIXTURE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui08-root"', text)
		self.assertIn("Review Plan update", text)
		self.assertIn("Professional decision", text)
		self.assertIn("Return to planner", text)
		self.assertIn("Approve update", text)
		self.assertIn("Decision history", text)
		self.assertNotIn("recommend", text.lower())
		self.assertNotIn("Preference &amp; Reservation", text)
		self.assertNotIn("truncate", text)
		self.assertNotIn("cdn.tailwindcss.com", text)
		self.assertNotIn('aria-label="Breadcrumb"', text)

	def test_plan_approved_fixture_markers(self):
		text = _read(APPROVED_FIXTURE)
		page = _read(APPROVED_PAGE)
		self.assertIn("kt-stitch-canvas", text)
		self.assertIn('data-testid="kt-pln-ui09-root"', text)
		self.assertIn('data-testid="kt-pln-ui09-summary"', text)
		self.assertIn("Add Plan Item", text)
		self.assertIn("Export approved plan", text)
		self.assertIn("Plan implementation", text)
		self.assertIn("Version history", text)
		self.assertNotIn("Publication", text)
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
		self.assertFalse((APP_PUBLIC / "js" / "planning_ui_fixtures" / "plan_update.js").exists())
		self.assertFalse((APP_PUBLIC / "js" / "planning_update_page.js").exists())
		self.assertNotIn('"procurement-plan-update"', _read(Path(frappe.get_app_path("kentender_procurement")) / "hooks.py"))

	def test_revision_split_binders_and_pages(self):
		workspace = _read(LIVE_BIND)
		register = _read(APP_PUBLIC / "js" / "planning_register_bind.js")
		builder = _read(APP_PUBLIC / "js" / "planning_builder_bind.js")
		dialog = _read(APP_PUBLIC / "js" / "planning_demand_dialog.js")
		utils = _read(APP_PUBLIC / "js" / "planning_client_utils.js")
		self.assertIn("get_planning_workspace", workspace)
		self.assertIn("get_planning_create_scope", register)
		self.assertIn("create_procurement_plan", register)
		self.assertIn("get_plan_builder", builder)
		self.assertIn("list_eligible_demands", dialog)
		self.assertIn("add_demand_to_plan", dialog)
		self.assertIn("formation_mode", dialog)
		self.assertIn("idempotency_key", dialog)
		self.assertIn('aria-busy', utils)
		self.assertIn("frappe.set_route", utils)
		self.assertNotIn("window.location.href", register)
		self.assertNotIn("window.location.href", builder)
		self.assertNotIn("window.location.href", dialog)
		self.assertNotIn("bindPlanningItemEditor", workspace)
		self.assertIn("bindPlanningItemEditor", _read(APP_PUBLIC / "js" / "planning_item_editor_bind.js"))
		self.assertIn("bindPlanningReview", _read(APP_PUBLIC / "js" / "planning_review_bind.js"))
		self.assertIn("bindPlanningApproved", _read(APP_PUBLIC / "js" / "planning_approved_bind.js"))
		self.assertNotIn("bindPlanningUpdate =", workspace)
		for page in (WS_PAGE, REG_PAGE, BLD_PAGE, ED_PAGE, REVIEW_PAGE, APPROVED_PAGE):
			self.assertIn("enterNative", _read(page))

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
		self.assertNotIn("procurement-plan-update", page_js)
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
		self.assertIn("planning_ui_fixtures/plan_approved.js", js_includes)
		self.assertNotIn("planning_ui_fixtures/plan_update.js", js_includes)
		self.assertIn("planning_finance_bind.js", js_includes)
		self.assertIn("planning_review_bind.js", js_includes)
		self.assertIn("planning_approved_bind.js", js_includes)
