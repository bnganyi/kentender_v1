# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""W1 — Workbench shell state and route query contract."""

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


class TestPP4WorkbenchShellRouteContractW1(UnitTestCase):
	def test_router_declares_workbench_state_query_keys(self) -> None:
		source = _router_path().read_text(encoding="utf-8", errors="replace")
		self.assertIn("const WORKBENCH_STATE_QUERY_KEYS = [", source)
		for key in (
			"queue",
			"item",
			"plan",
			"search",
			"department",
			"category",
			"value_range",
			"created_from",
			"created_to",
			"sort",
			"page",
		):
			self.assertIn(f'"{key}"', source, msg=f"Missing W1 route key '{key}'")

	def test_router_normalizes_and_writes_canonical_query_state(self) -> None:
		source = _router_path().read_text(encoding="utf-8", errors="replace")
		self.assertIn("function normalizeWorkbenchQueueValue", source)
		self.assertIn("function readWorkbenchStateFromUrl", source)
		self.assertIn("function writeWorkbenchStateToUrl", source)
		self.assertIn("function canonicalizeWorkbenchStateQuery", source)
		self.assertIn("if (!isPlanningWorkspaceRoute()) return;", source)
		self.assertNotIn("if (!isPlanningRoute()) return;", source)
		self.assertIn("writeWorkbenchStateToUrl({}, { replace: true });", source)

	def test_mount_preserves_and_canonicalizes_workbench_query_on_root(self) -> None:
		source = _router_path().read_text(encoding="utf-8", errors="replace")
		self.assertIn("const hasWorkbenchState = hasWorkbenchStateQuery(searchParams);", source)
		self.assertIn("preserveSearch: slug === \"\" && (hasPackageCode || hasWorkbenchState || hasApprovedDemandQuery || hasPlanCode)", source)
		self.assertIn("canonicalizeWorkbenchStateQuery();", source)
