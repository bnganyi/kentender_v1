# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P6-001 — Package Detail contextual route source contract."""

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


def _package_detail_path() -> Path:
	return (
		Path(__file__).resolve().parents[2]
		/ "public"
		/ "js"
		/ "pp3_planning_package_detail.js"
	)


class TestPP6PackageDetailRouteP6001(UnitTestCase):
	def test_package_detail_surface_marker_is_pp3_package_detail(self) -> None:
		path = _router_path()
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn(
			'testId: "pp3-package-detail-surface"',
			source,
			"Package detail route must use PP3 package detail surface marker (P6-001).",
		)

	def test_router_resolves_packages_code_as_package_detail_action(self) -> None:
		path = _router_path()
		source = path.read_text(encoding="utf-8", errors="replace")
		resolve_block = source.split("function resolvePlanningRoute", 1)[1].split(
			"function applyPlanningRouteRedirect", 1
		)[0]
		packages_block = resolve_block.split('if (head === "packages" && segments.length > 1)', 1)[1].split(
			"if (!CANONICAL_PLANNING_SLUGS[head])", 1
		)[0]
		self.assertIn('action: "package_detail"', packages_block)
		self.assertIn("packageCode", packages_block)
		self.assertNotIn(
			"buildPackagesRedirectUrl(rawSegments[1]",
			packages_block,
			"Package code path must not redirect to workbench query (P6-001).",
		)

	def test_router_mounts_dedicated_package_detail_surface(self) -> None:
		path = _router_path()
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("function mountPackageDetailSurface", source)
		self.assertIn("function buildPackageDetailUrl", source)
		mount_block = source.split("function mount(", 1)[1].split("function scheduleBoot", 1)[0]
		self.assertIn('resolution.action === "package_detail"', mount_block)
		self.assertIn("mountPackageDetailSurface", mount_block)

	def test_package_detail_route_skips_workbench_queue_and_work_list(self) -> None:
		path = _router_path()
		source = path.read_text(encoding="utf-8", errors="replace")
		fn_block = source.split("function mountPackageDetailSurface", 1)[1].split(
			"function mountPlanningQueueTabs", 1
		)[0]
		self.assertNotIn("mountPlanningQueueTabs", fn_block)
		self.assertNotIn("mountPlanningWorkList", fn_block)
		self.assertIn("clearWorkbenchHosts", fn_block)

	def test_package_detail_component_exposes_required_route_testids(self) -> None:
		path = _package_detail_path()
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in (
			"pp3-package-detail",
			"pp3-package-header",
			"pp3-back-to-workbench",
		):
			self.assertIn(f'data-testid="{tid}"', source, msg=f"missing {tid} (P6-001)")
