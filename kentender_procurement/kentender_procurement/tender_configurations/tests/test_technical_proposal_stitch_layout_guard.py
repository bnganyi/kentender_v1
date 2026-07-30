# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Static Stitch fidelity gate for Technical Proposal and Implementation Plan UI.

Fails if shipped templates regress to form-stack approximations (missing tables /
drawers / columns required by 09_Technical _Proposal/*_code.html).
"""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

_APP = Path(frappe.get_app_path("kentender_procurement"))
_WWW = _APP / "www" / "tenders"
_INCL = _APP / "templates" / "includes" / "technical_proposal"
_CSS = _APP / "public" / "css" / "technical_proposal_web.css"
_JS = _APP / "public" / "js" / "technical_proposal_web.js"


def _read(path: Path) -> str:
	return path.read_text(encoding="utf-8")


class TestTechnicalProposalStitchLayoutGuard(IntegrationTestCase):
	def test_overview_has_subsection_table_columns(self) -> None:
		html = _read(_WWW / "technical_proposal_and_implementation_plan.html")
		self.assertIn('data-testid="kt-tp-root"', html)
		self.assertIn("kt-s600-table", html)
		for col in (
			"Subsection",
			"What to provide",
			"Requirement",
			"Status",
			"Action",
		):
			self.assertIn(col, html)
		self.assertIn("<table", html)
		self.assertNotIn("cdn.tailwindcss.com", html)
		self.assertIn('data-testid="kt-tp-progress-label"', html)
		self.assertIn('data-testid="kt-tp-progress-percent"', html)
		self.assertIn("kt-tp-progress-card", html)
		self.assertIn("kt-tp-progress-card__bar", html)
		self.assertIn('data-testid="kt-tp-subsection-row"', html)
		# Status column is badge-only — no issue/summary prose under the chip.
		self.assertNotIn("kt-tp-row-issue", html)
		self.assertNotIn("kt-s600-issue", html)

	def test_subsection_shell_includes_renderers_and_drawer(self) -> None:
		html = _read(_WWW / "technical_proposal_subsection.html")
		self.assertIn('data-testid="kt-tp-subsection-root"', html)
		for partial in (
			"kt_tp_org.html",
			"kt_tp_approach.html",
			"kt_tp_work_plan.html",
			"kt_tp_training.html",
			"kt_tp_testing.html",
			"kt_tp_warranty.html",
			"kt_tp_transition.html",
			"kt_tp_risks.html",
			"kt_tp_alternatives.html",
		):
			self.assertIn(partial, html)
		self.assertIn('data-testid="kt-tp-drawer"', html)
		self.assertIn('data-tp-save="draft"', html)
		self.assertIn('data-tp-save="continue"', html)
		self.assertNotIn("cdn.tailwindcss.com", html)

	def test_hide_header_kpi_for_in_body_progress(self) -> None:
		html = _read(_WWW / "technical_proposal_subsection.html")
		self.assertIn("hide_header_kpi", html)
		self.assertIn("implementation_work_plan", html)

	def test_org_has_roles_and_matrix_tables(self) -> None:
		html = _read(_INCL / "kt_tp_org.html")
		self.assertIn("Project roles and key personnel", html)
		self.assertIn("Responsibility and coordination matrix", html)
		self.assertIn('data-testid="kt-tp-roles"', html)
		self.assertIn('data-testid="kt-tp-coordination-matrix"', html)
		self.assertIn("Assigned person", html)
		self.assertGreaterEqual(html.count("<table"), 2)

	def test_approach_has_question_cards_and_evidence(self) -> None:
		html = _read(_INCL / "kt_tp_approach.html")
		self.assertIn('data-testid="kt-tp-approach"', html)
		self.assertIn('data-testid="kt-tp-question-cards"', html)
		self.assertIn('data-testid="kt-tp-topic-guidance"', html)
		self.assertIn('data-testid="kt-tp-topic-status"', html)
		self.assertIn("Add supporting material", html)
		self.assertIn('data-testid="kt-tp-evidence"', html)
		self.assertIn("data-tp-evidence-id", html)

	def test_work_plan_has_activity_table_and_drawer_hooks(self) -> None:
		html = _read(_INCL / "kt_tp_work_plan.html")
		self.assertIn('data-testid="kt-tp-work-plan"', html)
		self.assertIn('data-testid="kt-tp-add-activity"', html)
		self.assertIn("Phase / Activity", html)
		self.assertIn("End", html)
		self.assertIn("Status", html)
		self.assertIn("Responsible role", html)
		self.assertIn("data-tp-edit-activity", html)
		self.assertIn("dependency_label", html)
		self.assertIn('data-testid="kt-tp-completion-week"', html)
		self.assertIn('data-testid="kt-tp-work-plan-help"', html)
		self.assertIn("contractual_period_label", html)
		self.assertIn("Weeks", html)

	def test_testing_training_risks_alternatives_tables(self) -> None:
		testing = _read(_INCL / "kt_tp_testing.html")
		self.assertIn("<table", testing)
		self.assertIn("Status", testing)
		self.assertIn("data-status-kind", testing)
		self.assertIn("data-tp-status-cell", testing)
		self.assertIn("data-tp-action-cell", testing)
		# Status column must appear before Action in the testing table markup.
		self.assertLess(testing.find("Status"), testing.find("Action"))
		self.assertLess(testing.find("data-tp-status-cell"), testing.find("data-tp-action-cell"))
		training = _read(_INCL / "kt_tp_training.html")
		self.assertIn("<table", training)
		risks = _read(_INCL / "kt_tp_risks.html")
		self.assertIn("Risk register", risks)
		self.assertIn("Assumptions", risks)
		self.assertIn("Dependencies", risks)
		alts = _read(_INCL / "kt_tp_alternatives.html")
		self.assertIn("<table", alts)
		self.assertIn("Permitted Scope", alts)
		self.assertIn('data-testid="kt-tp-permitted-scope"', alts)
		self.assertIn("Status", alts)
		self.assertIn("Alternatives Register", alts)

	def test_js_status_cell_precedes_action_for_registers(self) -> None:
		js = _read(_JS)
		self.assertIn("repairRegisterStatusColumns", js)
		self.assertIn("statusBadgeHtml", js)
		# genericRowHtml must emit status badge markup before the delete/action cell.
		fn_start = js.find("function genericRowHtml")
		self.assertGreater(fn_start, 0)
		chunk = js[fn_start : fn_start + 3500]
		self.assertIn("statusBadgeHtml", chunk)
		self.assertLess(chunk.find("statusBadgeHtml(rowStatus)"), chunk.find("data-tp-remove-row"))

	def test_review_has_confirmation_controls(self) -> None:
		html = _read(_WWW / "technical_proposal_review.html")
		self.assertIn('data-testid="kt-tp-review-root"', html)
		self.assertIn('data-testid="kt-tp-confirm-checkbox"', html)
		self.assertIn('data-testid="kt-tp-confirm-btn"', html)
		self.assertIn('data-testid="kt-tp-save-draft"', html)
		self.assertIn('data-tp-review-save="draft"', html)
		self.assertIn('data-tp-review-save="complete"', html)
		self.assertIn('data-section-url="{{ r.section_url }}"', html)
		self.assertNotIn('data-section-url="{{ r.review_url }}"', html)
		self.assertIn('data-testid="kt-tp-consolidated-summary"', html)
		self.assertIn("Consolidated Summary", html)
		self.assertIn("kt-tp-progress-card", html)
		self.assertIn('data-testid="kt-tp-review-progress-percent"', html)
		self.assertIn("<table", html)
		self.assertNotIn("cdn.tailwindcss.com", html)

	def test_review_js_persists_confirm_and_navigates(self) -> None:
		js = _read(_JS)
		self.assertIn("Confirmation saved", js)
		self.assertIn("navigate: true", js)
		self.assertIn("goToSectionOverview", js)
		self.assertIn("kt-tp-save-draft", js)

	def test_transition_has_handover_checklist(self) -> None:
		html = _read(_INCL / "kt_tp_transition.html")
		self.assertIn('data-testid="kt-tp-handover"', html)
		self.assertIn("Handover deliverables", html)
		self.assertIn("data-handover-provided", html)
		self.assertIn("row.provided", html)

	def test_handover_checkbox_has_checked_styles(self) -> None:
		"""Frappe website.bundle uses appearance:none — without :checked rules ticks look blank."""
		css = _read(_CSS)
		self.assertIn(".kt-tp-handover-item input[type=\"checkbox\"]:checked", css)
		self.assertIn("background-image", css)

	def test_org_has_manage_personnel_link(self) -> None:
		html = _read(_INCL / "kt_tp_org.html")
		self.assertIn('data-testid="kt-tp-manage-personnel"', html)
		self.assertIn("Manage Key Personnel", html)

	def test_assets_exist_and_js_uses_canonical_api(self) -> None:
		self.assertTrue(_CSS.is_file())
		self.assertTrue(_JS.is_file())
		js = _read(_JS)
		self.assertIn("save_technical_proposal_subsection", js)
		self.assertIn("confirm_technical_proposal_integration", js)
		self.assertIn("KT_TP_CONFLICT", js)
		css = _read(_CSS)
		# Do not wipe radio/checkbox chrome inside tables.
		self.assertTrue(
			"input[type='checkbox']" in css
			or "input:not([type='checkbox'])" in css
			or "kt-tp-evidence" in css
		)
