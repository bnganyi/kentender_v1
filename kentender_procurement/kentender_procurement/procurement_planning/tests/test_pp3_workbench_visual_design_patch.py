# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP3 workbench visual design patch — demo scope, queue counts, copy."""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase

from kentender_procurement.procurement_planning.services.workbench_demo_scope import (
	filter_demo_workbench_items,
	is_demo_pollution,
)
from kentender_procurement.procurement_planning.services.workbench_queue_counts import (
	get_workbench_queue_counts,
)


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP3WorkbenchVisualDesignPatch(UnitTestCase):
	def test_demo_pollution_heuristics(self) -> None:
		self.assertTrue(is_demo_pollution(title="PW Draft 178", code="DEM-TEST-001"))
		self.assertTrue(is_demo_pollution(title="Test", code="DEM-TEST-002"))
		self.assertFalse(is_demo_pollution(title="District Hospital Renovation Works", code="DEM-MOH-2026-001"))

	def test_demo_scope_prefers_works_master_rows(self) -> None:
		items = [
			{"title": "PW Draft 178", "underlying_object_code": "DEM-TEST-001"},
			{"title": "District Hospital Renovation Works", "underlying_object_code": "DEM-MOH-2026-001"},
		]
		filtered = filter_demo_workbench_items(items, include_test_data=False)
		self.assertEqual(len(filtered), 1)
		self.assertEqual(filtered[0]["underlying_object_code"], "DEM-MOH-2026-001")

	def test_queue_counts_returns_ui_queue_keys(self) -> None:
		out = get_workbench_queue_counts(actor="Administrator", include_test_data=False)
		self.assertTrue(out.get("ok"))
		counts = out.get("counts") or {}
		for key in (
			"needs_planning",
			"draft_packages",
			"needs_review",
			"ready_to_release",
			"blocked",
			"recently_released",
		):
			self.assertIn(key, counts)

	def test_active_plan_banner_renders_card_heading(self) -> None:
		source = _pkg_public("js", "pp3_planning_active_plan_banner.js").read_text(
			encoding="utf-8", errors="replace"
		)
		self.assertIn("Active Procurement Plan", source)
		self.assertIn("pp3-active-plan-card__title", source)
		self.assertNotIn("Active plan:", source)

	def test_queue_tabs_render_counts(self) -> None:
		source = _pkg_public("js", "pp3_planning_workbench_queue_tabs.js").read_text(
			encoding="utf-8", errors="replace"
		)
		self.assertIn("get_pp_workbench_queue_counts", source)
		self.assertIn("Work Queues", source)

	def test_work_list_rows_use_status_and_next_labels(self) -> None:
		source = _pkg_public("js", "pp3_planning_work_list.js").read_text(
			encoding="utf-8", errors="replace"
		)
		self.assertIn("pp3-work-list__status-pill", source)
		self.assertIn("status_pill_tone", source)
		self.assertIn("list_next_action", source)

	def test_selected_summary_uses_decision_panel_sections(self) -> None:
		source = _pkg_public("js", "pp3_planning_selected_work_summary.js").read_text(
			encoding="utf-8", errors="replace"
		)
		self.assertIn("Selected Work", source)
		self.assertIn("Next step", source)
		self.assertNotIn('esc(__("State"))', source)

	def test_view_model_uses_add_to_active_plan_copy(self) -> None:
		path = Path(__file__).resolve().parents[1] / "services" / "workbench_item_view_model.py"
		source = path.read_text(encoding="utf-8", errors="replace")
		fn_block = source.split("def _needs_planning_items", 1)[1].split("def _package_queue_items", 1)[0]
		self.assertIn('"Add to Active Plan"', fn_block)
		self.assertIn('"Add to active plan"', fn_block)
		self.assertNotIn('"Include in Plan"', fn_block)

	def test_view_model_exposes_design_display_fields(self) -> None:
		path = Path(__file__).resolve().parents[1] / "services" / "workbench_item_view_model.py"
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn('"category_label"', source)
		self.assertIn('"status_pill_label"', source)
		self.assertIn('"status_pill_tone"', source)
		self.assertIn('"budget_status_label"', source)
		self.assertIn('"updated_relative"', source)
