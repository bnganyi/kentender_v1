# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-003 — Workbench active plan banner surface source contract."""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _router_path() -> Path:
	return (
		Path(__file__).resolve().parents[2]
		/ "public"
		/ "js"
		/ "pp2_planning_router.js"
	)


class TestPP3ActivePlanBannerP3003(UnitTestCase):
	def test_router_wires_active_plan_banner_host(self) -> None:
		path = _router_path()
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn(
			"pp3-active-plan-host",
			source,
			"Workbench must render active plan banner host (P3-003).",
		)
		self.assertIn(
			"mountPlanningContextWithPayload",
			source,
			"Workbench must render banner from active-plan payload (P3-003).",
		)

	def test_active_plan_path_mounts_banner_before_queue_chrome(self) -> None:
		path = _router_path()
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn(
			"function mountWorkbenchRootWork",
			source,
			"Workbench root must orchestrate active-plan surface (P3-003).",
		)
		fn_block = source.split("function mountWorkbenchRootWork", 1)[1].split("function mountActivePlanBanner", 1)[0]
		self.assertIn("mountPlanningContextWithPayload", fn_block)
		self.assertIn("has_active_plan", fn_block)
		self.assertIn("mountPlanningQueueTabs", fn_block)
		self.assertIn("mountPlanningWorkList", fn_block)
		mount_context_pos = fn_block.find("mountPlanningContextWithPayload")
		queue_tabs_pos = fn_block.find("mountPlanningQueueTabs")
		self.assertGreater(
			queue_tabs_pos,
			mount_context_pos,
			"Active plan banner must mount before queue tabs (P3-003).",
		)
