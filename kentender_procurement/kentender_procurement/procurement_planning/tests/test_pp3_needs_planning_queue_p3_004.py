# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-004 — Workbench Needs Planning queue surface source contract."""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP3NeedsPlanningQueueP3004(UnitTestCase):
	def test_work_list_defaults_to_needs_planning_queue(self) -> None:
		path = _pkg_public("js", "pp3_planning_work_list.js")
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn(
			'needs_planning: "needs_planning"',
			source,
			"Workbench work list must map Needs Planning queue to API (P3-004).",
		)
		self.assertIn(
			'return "needs_planning"',
			source,
			"Workbench work list must default to needs_planning when queue is absent (P3-004).",
		)
		self.assertIn(
			"get_pp_workbench_item_view_model",
			source,
			"Needs Planning queue must load approved demands via workbench view-model (P3-004).",
		)

	def test_work_list_uses_needs_planning_empty_copy(self) -> None:
		work_list = _pkg_public("js", "pp3_planning_work_list.js")
		empty_state = _pkg_public("js", "pp2_planning_empty_state.js")
		self.assertTrue(work_list.exists(), msg=f"missing {work_list}")
		self.assertTrue(empty_state.exists(), msg=f"missing {empty_state}")
		work_list_source = work_list.read_text(encoding="utf-8", errors="replace")
		empty_state_source = empty_state.read_text(encoding="utf-8", errors="replace")
		self.assertIn(
			"emptyMessageForQueue",
			work_list_source,
			"Workbench work list must resolve queue-specific empty copy (P3-004).",
		)
		self.assertIn(
			"HOME_QUEUE_MESSAGES",
			work_list_source,
			"Needs Planning empty state must reuse shared Planning empty messages (P3-004).",
		)
		self.assertIn(
			'needs_planning: __("No approved demands need planning.")',
			empty_state_source,
			"Needs Planning empty state copy must match PP3 UX spec (P3-004).",
		)

	def test_router_mounts_work_list_with_needs_planning_default(self) -> None:
		path = _pkg_public("js", "pp2_planning_router.js")
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		fn_block = source.split("function mountPlanningWorkList", 1)[1].split("function bindWorkbenchQueueRefresh", 1)[0]
		self.assertIn('let queueKey = "needs_planning"', fn_block)
		self.assertIn("PlanningWorkbenchWorkList", fn_block)
		self.assertIn("{ queue: queueKey, onSelect: onSelect }", fn_block)

	def test_workbench_view_model_include_in_plan_for_needs_planning(self) -> None:
		path = (
			Path(__file__).resolve().parents[1]
			/ "services"
			/ "workbench_item_view_model.py"
		)
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn('"action": "include_in_plan"', source)
		self.assertIn('object_type="approved_demand"', source)
		fn_block = source.split("def _needs_planning_items", 1)[1].split("def _package_queue_items", 1)[0]
		self.assertIn('"Include in Plan"', fn_block)
