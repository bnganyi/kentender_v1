# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Phase G2 — Verify stable Procurement Planning ``data-testid`` hooks in desk JS.

8. Smoke Test Contracts §6 — fast regression that UI assets still expose the hooks
E2E and Playwright use. Dynamic ids (e.g. ``pp-row-``) are covered by pattern checks.
"""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _pkg_root() -> Path:
	""".../kentender_procurement (inner — contains ``public/`` and ``procurement_planning/``)."""
	return Path(__file__).resolve().parents[2]


def _app_public(*parts: str) -> Path:
	return _pkg_root().joinpath("public", *parts)


# KPI testids are emitted from ``api/landing.py``; keep them in sync (§6).
KPI_TESTIDS = (
	"pp-kpi-total-packages",
	"pp-kpi-total-value",
	"pp-kpi-approved-packages",
	"pp-kpi-ready-for-tender",
	"pp-kpi-high-risk",
)

REQUIRED_STABLE = (
	"pp-landing-page",
	"pp-control-bar",
	"pp-package-search",
	"pp-package-list",
	"pp-detail-panel",
	"pp-empty-list",
	"pp-detail-title",
	"pp-detail-template",
	"pp-detail-method",
	"pp2-package-detail-canonical",
	"pp2-package-workflow",
	"pp2-package-handoff-stack",
	"pp2-surface-empty-state",
	"pp2-canonical-error",
	"pp-builder-page",
	"pp-builder-section-demand-lines",
	"pp-builder-save",
	"pp-builder-submit",
)


REQUIRED_PAGE_HEADER_TESTIDS = (
	"pp2-page-header",
	"pp2-page-title",
	"pp2-page-purpose",
	"pp2-page-primary-action",
)

REQUIRED_QUEUE_TABS_TESTIDS = (
	"pp2-queue-tabs",
	"pp2-queue-tab-",
)

REQUIRED_WORK_LIST_TESTIDS = (
	"pp2-work-list",
	"pp2-work-list-row",
	"pp2-work-list-row-title",
	"pp2-work-list-row-meta",
	"pp2-work-list-row-status",
	"pp2-work-list-row-blocker",
)

REQUIRED_APPROVED_DEMAND_LIST_TESTIDS = (
	"pp2-approved-demand-row",
	"pp2-approved-demand-row-title",
	"pp2-approved-demand-row-category-value",
	"pp2-approved-demand-row-funding-status",
	"pp2-approved-demand-row-planning-status",
	"pp2-approved-demand-row-blocker",
)

REQUIRED_SELECTED_SUMMARY_TESTIDS = (
	"pp2-selected-summary-panel",
	"pp2-selected-summary-title",
	"pp2-selected-summary-status",
	"pp2-selected-summary-facts",
	"pp2-selected-summary-funding",
	"pp2-selected-summary-blockers",
	"pp2-selected-summary-next-action",
	"pp2-selected-summary-primary-action",
	"pp2-selected-summary-secondary-action",
	"pp2-view-evidence-button",
)

REQUIRED_APPROVED_DEMAND_SUMMARY_TESTIDS = (
	"pp2-approved-demand-summary",
	"pp2-include-in-plan-button",
	"pp2-view-demand-button",
	"pp2-view-demand-evidence",
	"pp2-approved-demand-include-alert",
)

REQUIRED_INCLUDE_PLAN_MODAL_TESTIDS = (
	"pp2-include-plan-modal",
	"pp2-target-plan-select",
	"pp2-confirm-include-plan",
)

REQUIRED_INCLUDE_PLAN_SUCCESS_TESTIDS = (
	"pp2-include-plan-success",
	"pp2-create-package-next-action",
	"pp2-back-to-approved-demands",
)

REQUIRED_BLOCKER_SUMMARY_TESTIDS = (
	"pp2-blocker-summary",
	"pp2-blocker-summary-empty",
	"pp2-blocker-summary-item",
)

REQUIRED_EMPTY_STATE_TESTIDS = (
	"pp2-empty-state",
	"pp2-empty-state-message",
)

REQUIRED_ADVANCED_FILTERS_TESTIDS = (
	"pp2-advanced-filters",
	"pp2-advanced-filters-toggle",
	"pp2-advanced-filters-panel",
)

REQUIRED_EVIDENCE_DRAWER_TESTIDS = (
	"pp2-evidence-drawer",
	"pp2-evidence-title",
	"pp2-evidence-timeline",
	"pp2-evidence-record-list",
	"pp2-technical-details-toggle",
	"pp2-technical-details-panel",
)

REQUIRED_PLANNING_HOME_TESTIDS = (
	"pp2-planning-home-surface",
	"pp2-planning-home-body",
	"pp2-planning-home-queues",
)

REQUIRED_PLANNING_SUMMARY_TESTIDS = (
	"pp2-planning-summary",
)

REQUIRED_PLANNING_HOME_QUEUE_TESTIDS = (
	"pp2-queue-needs-planning",
	"pp2-queue-needs-review",
	"pp2-queue-ready-release",
	"pp2-queue-released-recently",
	"pp2-queue-blocked",
	"pp2-home-item-card",
	"pp2-home-primary-action",
	"pp2-home-secondary-action",
)


class TestProcurementPlanningTestIdsG2(UnitTestCase):
	def test_g2_required_testids_in_workspace_and_builder_js(self) -> None:
		js_paths = [
			_js("js", "procurement_planning_workspace.js"),
			_js("js", "procurement_package.js"),
			_js("js", "pp_template_selector.js"),
		]
		merged = ""
		for p in js_paths:
			if not p.exists():
				raise self.failureException(f"missing {p}")
			merged += p.read_text(encoding="utf-8", errors="replace")
		for tid in REQUIRED_STABLE:
			# In-template `data-testid="…"`, DOM setters, jQuery `.attr(...)`, or explicit constants.
			if f'data-testid="{tid}"' in merged or f'setAttribute("data-testid", "{tid}")' in merged:
				continue
			if f"setAttribute('data-testid', '{tid}')" in merged:
				continue
			if f'.attr("data-testid", "{tid}")' in merged:
				continue
			if f'"{tid}"' in merged:
				continue
			self.fail(f"Missing data-testid hook {tid!r} (8. §6, G2).")
		landing = _pkg_root() / "procurement_planning" / "api" / "landing.py"
		landing_text = landing.read_text(encoding="utf-8", errors="replace")
		for tid in KPI_TESTIDS:
			self.assertIn(f'"{tid}"', landing_text, f"KPI testid {tid!r} missing in landing API (G2).")
		# dynamic row + queue
		self.assertIn("pp-row-", merged)
		self.assertIn("pp-queue-", merged)

	def test_g2_page_header_testids_in_planning_page_header_js(self) -> None:
		path = _js("js", "pp2_planning_page_header.js")
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in REQUIRED_PAGE_HEADER_TESTIDS:
			self.assertIn(f'data-testid="{tid}"', source, f"Missing page header testid {tid!r} (P5B-001).")

	def test_g2_queue_tabs_testids_in_planning_queue_tabs_js(self) -> None:
		path = _js("js", "pp2_planning_queue_tabs.js")
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn('data-testid="pp2-queue-tabs"', source, "Missing queue tabs container testid (P5B-002).")
		self.assertIn("pp2-queue-tab-", source, "Missing queue tab chip testid prefix (P5B-002).")

	def test_g2_work_list_testids_in_planning_work_list_js(self) -> None:
		path = _js("js", "pp2_planning_work_list.js")
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in REQUIRED_WORK_LIST_TESTIDS:
			self.assertIn(f'data-testid="{tid}"', source, f"Missing work list testid {tid!r} (P5B-003).")

	def test_g2_approved_demand_list_testids_in_planning_work_list_js(self) -> None:
		path = _js("js", "pp2_planning_work_list.js")
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in REQUIRED_APPROVED_DEMAND_LIST_TESTIDS:
			self.assertIn(
				f'data-testid="{tid}"',
				source,
				f"Missing approved demand row testid {tid!r} (P5C-011).",
			)

	def test_g2_selected_summary_testids_in_planning_selected_summary_panel_js(self) -> None:
		path = _js("js", "pp2_planning_selected_summary_panel.js")
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in REQUIRED_SELECTED_SUMMARY_TESTIDS:
			self.assertIn(
				f'data-testid="{tid}"',
				source,
				f"Missing selected summary testid {tid!r} (P5B-004).",
			)
		for tid in REQUIRED_APPROVED_DEMAND_SUMMARY_TESTIDS:
			self.assertIn(
				f'data-testid="{tid}"',
				source,
				f"Missing approved-demand summary testid {tid!r} (P5C-012).",
			)

	def test_g2_include_plan_modal_testids_in_planning_include_plan_modal_js(self) -> None:
		path = _js("js", "pp2_planning_include_plan_modal.js")
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in REQUIRED_INCLUDE_PLAN_MODAL_TESTIDS:
			literal = f'data-testid="{tid}"'
			attr_set_double = f'.attr("data-testid", "{tid}")'
			attr_set_single = f".attr('data-testid', '{tid}')"
			set_attr_double = f'setAttribute("data-testid", "{tid}")'
			set_attr_single = f"setAttribute('data-testid', '{tid}')"
			if literal in source:
				continue
			if attr_set_double in source or attr_set_single in source:
				continue
			if set_attr_double in source or set_attr_single in source:
				continue
			self.fail(f"Missing include-plan modal testid {tid!r} (P5C-013).")

	def test_g2_include_plan_success_testids_in_selected_summary_panel_js(self) -> None:
		path = _js("js", "pp2_planning_selected_summary_panel.js")
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in REQUIRED_INCLUDE_PLAN_SUCCESS_TESTIDS:
			self.assertIn(
				f'data-testid="{tid}"',
				source,
				f"Missing include-plan success testid {tid!r} (P5C-014).",
			)

	def test_g2_blocker_summary_testids_in_planning_blocker_summary_js(self) -> None:
		path = _js("js", "pp2_planning_blocker_summary.js")
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in REQUIRED_BLOCKER_SUMMARY_TESTIDS:
			self.assertIn(
				f'data-testid="{tid}"',
				source,
				f"Missing blocker summary testid {tid!r} (P5B-005).",
			)

	def test_g2_empty_state_testids_in_planning_empty_state_js(self) -> None:
		path = _js("js", "pp2_planning_empty_state.js")
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in REQUIRED_EMPTY_STATE_TESTIDS:
			self.assertIn(
				f'data-testid="{tid}"',
				source,
				f"Missing empty state testid {tid!r} (P5B-006).",
			)

	def test_g2_advanced_filters_testids_in_planning_advanced_filters_js(self) -> None:
		path = _js("js", "pp2_planning_advanced_filters.js")
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in REQUIRED_ADVANCED_FILTERS_TESTIDS:
			self.assertIn(
				f'data-testid="{tid}"',
				source,
				f"Missing advanced filters testid {tid!r} (P5B-007).",
			)

	def test_g2_evidence_drawer_testids_in_planning_evidence_drawer_js(self) -> None:
		path = _js("js", "pp2_planning_evidence_drawer.js")
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in REQUIRED_EVIDENCE_DRAWER_TESTIDS:
			self.assertIn(
				f'data-testid="{tid}"',
				source,
				f"Missing evidence drawer testid {tid!r} (P5B-008).",
			)

	def test_g2_planning_home_testids_in_planning_home_js(self) -> None:
		path = _js("js", "pp2_planning_home.js")
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in REQUIRED_PLANNING_HOME_TESTIDS:
			self.assertIn(
				f'data-testid="{tid}"',
				source,
				f"Missing planning home testid {tid!r} (P5C-001).",
			)

	def test_g2_planning_summary_testids_in_planning_summary_js(self) -> None:
		path = _js("js", "pp2_planning_summary.js")
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in REQUIRED_PLANNING_SUMMARY_TESTIDS:
			self.assertIn(
				f'data-testid="{tid}"',
				source,
				f"Missing planning summary testid {tid!r} (P5C-002).",
			)

	def test_g2_planning_home_queue_testids_in_planning_home_queue_js(self) -> None:
		paths = [
			_js("js", "pp2_planning_home_queue_section.js"),
			_js("js", "pp2_planning_home_item_card.js"),
			_js("js", "pp2_planning_home_queues.js"),
		]
		merged = ""
		for path in paths:
			self.assertTrue(path.exists(), msg=f"missing {path}")
			merged += path.read_text(encoding="utf-8", errors="replace")
		for tid in REQUIRED_PLANNING_HOME_QUEUE_TESTIDS:
			if tid in (
				"pp2-queue-needs-planning",
				"pp2-queue-needs-review",
				"pp2-queue-ready-release",
				"pp2-queue-released-recently",
				"pp2-queue-blocked",
			):
				self.assertIn(
					tid,
					merged,
					f"Missing planning home queue testid {tid!r} (P5C-003/P5C-004/P5C-005/P5C-006/P5C-007).",
				)
				continue
			self.assertIn(
				f'data-testid="{tid}"',
				merged,
				f"Missing planning home queue testid {tid!r} (P5C-003).",
			)


def _js(*p: str) -> Path:
	return _app_public(*p)
