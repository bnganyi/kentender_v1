# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-007 — Workbench Ready to Release queue surface source contract."""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP3ReadyToReleaseQueueP3007(UnitTestCase):
	def test_work_list_maps_ready_to_release_queue(self) -> None:
		source = _pkg_public("js", "pp3_planning_work_list.js").read_text(encoding="utf-8", errors="replace")
		self.assertIn('ready_to_release: "ready_release"', source)

	def test_ready_to_release_empty_copy(self) -> None:
		empty_state = _pkg_public("js", "pp2_planning_empty_state.js").read_text(encoding="utf-8", errors="replace")
		self.assertIn('ready_to_release: __("No packages are ready for release.")', empty_state)

	def test_view_model_release_to_tender_action(self) -> None:
		source = (Path(__file__).resolve().parents[1] / "services" / "workbench_item_view_model.py").read_text(
			encoding="utf-8", errors="replace"
		)
		self.assertIn('"release_to_tender": ("Release to Tender", "release_to_tender")', source)
