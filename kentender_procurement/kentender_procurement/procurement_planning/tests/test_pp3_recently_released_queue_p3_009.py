# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-009 — Workbench Recently Released queue surface source contract."""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP3RecentlyReleasedQueueP3009(UnitTestCase):
	def test_work_list_maps_recently_released_queue(self) -> None:
		source = _pkg_public("js", "pp3_planning_work_list.js").read_text(encoding="utf-8", errors="replace")
		self.assertIn('recently_released: "recently_released"', source)

	def test_recently_released_empty_copy(self) -> None:
		empty_state = _pkg_public("js", "pp2_planning_empty_state.js").read_text(encoding="utf-8", errors="replace")
		self.assertIn('released_recently: __("No packages have been released recently.")', empty_state)

	def test_view_model_open_tender_action(self) -> None:
		source = (Path(__file__).resolve().parents[1] / "services" / "workbench_item_view_model.py").read_text(
			encoding="utf-8", errors="replace"
		)
		fn_block = source.split("def _recently_released_items", 1)[1].split("def get_workbench_item_view_model", 1)[0]
		self.assertIn('"Open Tender"', fn_block)
		self.assertIn('"Continue in Tender Management"', fn_block)
