# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-001 — Procurement Plans route source contract."""

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


def _page_header_path() -> Path:
	return (
		Path(__file__).resolve().parents[2]
		/ "public"
		/ "js"
		/ "pp2_planning_page_header.js"
	)


class TestPP4ProcurementPlansRouteP4001(UnitTestCase):
	def test_plans_surface_marker_is_pp3_procurement_plans_page(self) -> None:
		path = _router_path()
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn(
			'testId: "pp3-procurement-plans-page"',
			source,
			"Plans route must use PP3 procurement plans surface marker (P4-001).",
		)
		self.assertNotIn(
			'testId: "pp2-plans-page"',
			source,
			"Legacy pp2-plans-page marker must be retired (P4-001).",
		)

	def test_router_mounts_dedicated_procurement_plans_surface(self) -> None:
		path = _router_path()
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("function mountProcurementPlansSurface", source)
		self.assertIn("function isProcurementPlansSlug", source)
		mount_block = source.split("function mount(", 1)[1].split("function scheduleBoot", 1)[0]
		self.assertIn("isProcurementPlansSlug(slug)", mount_block)
		self.assertIn("mountProcurementPlansSurface", mount_block)

	def test_plans_route_skips_workbench_queue_and_work_list(self) -> None:
		path = _router_path()
		source = path.read_text(encoding="utf-8", errors="replace")
		fn_block = source.split("function mountProcurementPlansSurface", 1)[1].split(
			"function mountPlanningQueueTabs", 1
		)[0]
		self.assertNotIn("mountPlanningQueueTabs", fn_block)
		self.assertNotIn("mountPlanningWorkList", fn_block)
		self.assertIn("clearWorkbenchHosts", fn_block)

	def test_plans_page_header_uses_setup_oversight_copy(self) -> None:
		path = _page_header_path()
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn('title: __("Procurement Plans")', source)
		self.assertIn(
			'purpose: __("Create, activate, and review procurement plans.")',
			source,
		)
