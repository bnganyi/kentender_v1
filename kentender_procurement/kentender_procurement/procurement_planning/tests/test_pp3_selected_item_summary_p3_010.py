# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-010 — Workbench selected item summary surface source contract."""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP3SelectedItemSummaryP3010(UnitTestCase):
	def test_selected_summary_renders_title_state_facts_blockers_next(self) -> None:
		path = _pkg_public("js", "pp3_planning_selected_work_summary.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("summary.stateLabel", source)
		self.assertIn("summary.facts", source)
		self.assertIn("blockersHtml", source)
		self.assertIn("summary.nextAction", source)
		self.assertIn('data-testid="pp3-selected-work-summary"', source)

	def test_router_mounts_workbench_selected_summary_on_select(self) -> None:
		path = _pkg_public("js", "pp2_planning_router.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		fn_block = source.split("function mountPlanningWorkList", 1)[1].split("function bindWorkbenchQueueRefresh", 1)[0]
		self.assertIn("PlanningWorkbenchSelectedSummary", fn_block)
		self.assertIn("summaryFromWorkItem", fn_block)
		self.assertIn("mountPlanningSelectedSummary", fn_block)

	def test_summary_from_work_item_maps_blockers_and_actions(self) -> None:
		path = _pkg_public("js", "pp3_planning_selected_work_summary.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		fn_block = source.split("function summaryFromWorkItem", 1)[1].split("function blockersHtml", 1)[0]
		self.assertIn("blockers: it.blockers", fn_block)
		self.assertIn("primary_action: it.primary_action", fn_block)
		self.assertIn("next_action_label: it.next_action_label", fn_block)
