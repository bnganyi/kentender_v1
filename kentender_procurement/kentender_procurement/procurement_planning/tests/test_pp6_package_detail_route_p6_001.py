# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P6-001 — Package Detail dedicated page route source contract."""

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
		/ "package_detail_page.js"
	)


class TestPP6PackageDetailRouteP6001(UnitTestCase):
	def test_router_exposes_package_detail_navigation_helpers(self) -> None:
		path = _router_path()
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("function buildPackageDetailUrl(packageCode)", source)
		self.assertIn("function navigateToPackageDetailPage(packageCode)", source)
		self.assertIn("function workbenchPackageRouteCode(data)", source)
		self.assertIn("/app/package-detail/", source)

	def test_router_resolves_packages_code_to_package_detail_url(self) -> None:
		path = _router_path()
		source = path.read_text(encoding="utf-8", errors="replace")
		resolve_block = source.split("function resolvePlanningRoute", 1)[1].split(
			"function applyPlanningRouteRedirect", 1
		)[0]
		packages_block = resolve_block.split('if (head === "packages" && segments.length > 1)', 1)[1].split(
			"if (!CANONICAL_PLANNING_SLUGS[head])", 1
		)[0]
		self.assertIn("buildPackageDetailUrl(rawSegments[1]", packages_block)
		self.assertNotIn(
			"buildWorkbenchPackageRedirectUrl(rawSegments[1]",
			packages_block,
			"Legacy workbench query redirect must not remain for package codes (P6-001).",
		)

	def test_legacy_mount_redirects_to_dedicated_page(self) -> None:
		path = _router_path()
		source = path.read_text(encoding="utf-8", errors="replace")
		fn_block = source.split("function mountPackageDetailSurface", 1)[1].split(
			"function mountPlanningQueueTabs", 1
		)[0]
		self.assertIn("navigateToPackageDetailPage(packageCode)", fn_block)
		self.assertNotIn("PlanningPackageDetail", fn_block)

	def test_package_detail_page_exposes_required_route_testids(self) -> None:
		path = _package_detail_path()
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in (
			"kt-pd-detail",
			"kt-pd-header",
			"kt-pd-title",
			"kt-pd-tabs",
			"kt-pd-canvas",
			"kt-pd-footer",
		):
			self.assertIn(tid, source, msg=f"missing {tid} (P6-001)")

	def test_back_to_workbench_uses_workbench_deep_link_not_hub_redirect(self) -> None:
		path = _package_detail_path()
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn("function _buildWorkbenchBackUrl", source)
		self.assertIn("/desk/procurement-planning", source)
		self.assertIn('url.searchParams.set("queue"', source)
		self.assertIn('url.searchParams.set("package_code"', source)
		back_block = source.split('if (action === "back_workbench")', 1)[1].split(
			'if (action === "view_evidence")', 1
		)[0]
		self.assertIn("window.location.href = _buildWorkbenchBackUrl", back_block)
		self.assertNotIn('frappe.set_route("procurement-planning")', back_block)
