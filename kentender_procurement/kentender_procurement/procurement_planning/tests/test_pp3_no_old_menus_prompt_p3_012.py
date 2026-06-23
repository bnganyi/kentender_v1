# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-012 — Workbench must not prompt legacy Planning Home / Approved Demands / Packages menus."""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP3NoOldMenusPromptP3012(UnitTestCase):
	def test_workbench_header_uses_workbench_not_legacy_surfaces(self) -> None:
		path = _pkg_public("js", "pp2_planning_page_header.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn('title: __("Workbench")', source)
		self.assertNotIn('title: __("Planning Home")', source)
		self.assertNotIn("Go to Approved Demands", source)
		self.assertNotIn("Go to Packages", source)

	def test_router_root_does_not_mount_planning_home(self) -> None:
		path = _pkg_public("js", "pp2_planning_router.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		mount_block = source.split("function mount(", 1)[1].split("function mountPlanningHome", 1)[0]
		self.assertNotIn("mountPlanningHome(root)", mount_block)
		self.assertIn("mountWorkbenchRootWork", source)

	def test_workbench_queue_tabs_exclude_legacy_surfaces(self) -> None:
		path = _pkg_public("js", "pp3_planning_workbench_queue_tabs.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertNotIn("Planning Home", source)
		self.assertNotIn("Approved Demands", source)
		self.assertIn("Needs Planning", source)
		self.assertIn("Draft Packages", source)
