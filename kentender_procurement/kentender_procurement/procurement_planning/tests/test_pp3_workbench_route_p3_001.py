# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-001 — Workbench root route source contract."""

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


class TestPP3WorkbenchRouteP3001(UnitTestCase):
	def test_root_surface_marker_is_pp3_workbench(self) -> None:
		path = _router_path()
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn(
			'testId: "pp4-workbench"',
			source,
			"Root Planning surface must be tagged as PP4 Workbench (P3-001).",
		)

	def test_root_route_does_not_mount_legacy_planning_home(self) -> None:
		path = _router_path()
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertNotIn(
			"mountPlanningHome(root);",
			source,
			"Workbench route must not mount legacy Planning Home surface (P3-001).",
		)
