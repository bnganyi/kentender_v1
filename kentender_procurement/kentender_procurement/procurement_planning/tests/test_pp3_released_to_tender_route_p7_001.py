# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P7-001 (v3) — Released to Tender route opens dedicated follow-up list surface."""

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


def _released_list_path() -> Path:
	return (
		Path(__file__).resolve().parents[2]
		/ "public"
		/ "js"
		/ "pp3_planning_released_list.js"
	)


class TestPP3ReleasedToTenderRouteP7001(UnitTestCase):
	def test_releases_surface_marker_is_pp3_released_to_tender_page(self) -> None:
		path = _router_path()
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn(
			'testId: "pp3-released-to-tender-page"',
			source,
			"Released to Tender route must expose pp3-released-to-tender-page (P7-001).",
		)
		self.assertNotIn(
			'releases: {\n\t\t\ttestId: "pp2-released-to-tender-page"',
			source,
			"Legacy pp2-released-to-tender-page marker must not remain on releases slug.",
		)

	def test_router_mounts_dedicated_released_to_tender_surface(self) -> None:
		path = _router_path()
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("function isReleasedToTenderSlug", source)
		self.assertIn("function mountReleasedToTenderSurface", source)
		mount_block = source.split("function mount(", 1)[1].split("function scheduleBoot", 1)[0]
		self.assertIn("isReleasedToTenderSlug(slug)", mount_block)
		self.assertIn("mountReleasedToTenderSurface", mount_block)

	def test_released_surface_skips_workbench_queue_and_work_list(self) -> None:
		path = _router_path()
		source = path.read_text(encoding="utf-8", errors="replace")
		fn_block = source.split("function mountReleasedToTenderSurface", 1)[1].split(
			"function mountPackageDetailSurface", 1
		)[0]
		self.assertNotIn("mountPlanningQueueTabs", fn_block)
		self.assertNotIn("mountPlanningWorkList", fn_block)
		self.assertIn("clearWorkbenchHosts", fn_block)

	def test_released_list_component_exposes_required_route_testids(self) -> None:
		path = _released_list_path()
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in (
			"pp3-released-list",
			"pp3-released-row",
			"pp3-release-summary",
			"pp3-released-search",
		):
			self.assertIn(f'data-testid="{tid}"', source, msg=f"missing {tid} (P7-001)")

	def test_released_context_hides_active_plan_banner(self) -> None:
		path = _router_path()
		source = path.read_text(encoding="utf-8", errors="replace")
		ctx_block = source.split("function mountPlanningContext", 1)[1].split(
			"function mountProcurementPlansSurface", 1
		)[0]
		self.assertIn("isReleasedToTenderSlug(slug)", ctx_block)
