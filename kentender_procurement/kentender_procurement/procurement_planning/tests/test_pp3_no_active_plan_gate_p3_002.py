# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-002 — No active plan Workbench gate source contract."""

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


class TestPP3NoActivePlanGateP3002(UnitTestCase):
	def test_router_declares_planning_work_unavailable_marker(self) -> None:
		path = _router_path()
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn(
			"pp3-planning-work-unavailable",
			source,
			"Workbench no-active gate must expose pp3-planning-work-unavailable (P3-002).",
		)

	def test_router_gates_workbench_work_on_has_active_plan(self) -> None:
		path = _router_path()
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn(
			"mountPlanningWorkUnavailable",
			source,
			"Router must mount planning-work-unavailable panel (P3-002).",
		)
		self.assertIn(
			"has_active_plan",
			source,
			"Router must gate Workbench work chrome on has_active_plan (P3-002).",
		)
		workbench_mount = source.split("if (isPlanningHomeSlug(slug))", 1)[-1]
		self.assertNotIn(
			"mountPlanningWorkList(mainHost, slug, shell);\n\t\t\t\tbindWorkbenchQueueRefresh",
			workbench_mount.split("} else if (mainHost)")[0],
			"Workbench root must not unconditionally mount work list before active-plan gate (P3-002).",
		)
