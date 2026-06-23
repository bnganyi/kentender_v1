# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-005 — Workbench Draft Packages queue surface source contract."""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP3DraftPackagesQueueP3005(UnitTestCase):
	def test_work_list_maps_draft_packages_queue(self) -> None:
		path = _pkg_public("js", "pp3_planning_work_list.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn('draft_packages: "draft_packages"', source)

	def test_draft_packages_empty_copy(self) -> None:
		empty_state = _pkg_public("js", "pp2_planning_empty_state.js").read_text(encoding="utf-8", errors="replace")
		self.assertIn('draft_packages: __("No draft packages are waiting.")', empty_state)

	def test_view_model_open_package_for_draft_packages(self) -> None:
		path = Path(__file__).resolve().parents[1] / "services" / "workbench_item_view_model.py"
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn('"open_package": ("Open Package", "open_package")', source)
		self.assertIn('action_key = str(next_action.get("key") or "open_package")', source)
