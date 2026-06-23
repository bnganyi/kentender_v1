# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-008 — Workbench Blocked queue surface source contract."""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP3BlockedQueueP3008(UnitTestCase):
	def test_work_list_maps_blocked_queue(self) -> None:
		source = _pkg_public("js", "pp3_planning_work_list.js").read_text(encoding="utf-8", errors="replace")
		self.assertIn('blocked: "blocked"', source)

	def test_blocked_empty_copy(self) -> None:
		empty_state = _pkg_public("js", "pp2_planning_empty_state.js").read_text(encoding="utf-8", errors="replace")
		self.assertIn('blocked: __("No planning blockers found.")', empty_state)

	def test_view_model_resolve_blocker_action(self) -> None:
		source = (Path(__file__).resolve().parents[1] / "services" / "workbench_item_view_model.py").read_text(
			encoding="utf-8", errors="replace"
		)
		fn_block = source.split("def _blocked_items", 1)[1].split("def _recently_released_items", 1)[0]
		self.assertIn('"Resolve Blocker"', fn_block)
		self.assertIn('"blockers":', fn_block)
