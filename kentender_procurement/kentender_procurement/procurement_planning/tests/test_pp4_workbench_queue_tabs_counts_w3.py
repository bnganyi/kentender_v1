# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""W3 — Workbench Queue Tabs + Counts.

Scope (Workbench Wiring Tracker, W3):
- Fetch `get_pp_workbench_queue_counts` once per fresh Workbench mount and
  write live totals into the four tab labels that already render a
  "(NN)" count in the pixel-perfect design (Needs Planning, In Creation,
  Awaiting Review, Ready for Release). Blocked/Released are left untouched
  since the design renders them as plain-text tabs with no count badge —
  adding one there would be a layout change beyond wiring.
- Bind clicks on all six tabs to toggle the design's own active/inactive
  class sets and update the W1 `queue` URL state. Per-queue list rendering
  for tabs other than Needs Planning is out of scope here (W4/W6/W7/W8).

Source-level assertions only (consistent with the rest of this router's
test suite, which has no JS runtime harness). The backend contract
(`get_workbench_queue_counts`) previously had no dedicated test — this
module adds one and pins the exact UI-facing queue keys the JS depends on.
Playwright UX validation runs separately against `kentender.midas.com`.
"""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.procurement_planning.services.workbench_queue_counts import (
	get_workbench_queue_counts,
)


def _router_path() -> Path:
	return Path(__file__).resolve().parents[2] / "public" / "js" / "pp2_planning_router.js"


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPP4WorkbenchQueueTabsCountsW3Source(UnitTestCase):
	"""Source-level wiring assertions for pp2_planning_router.js."""

	def setUp(self) -> None:
		super().setUp()
		self.source = _router_path().read_text(encoding="utf-8", errors="replace")

	def _fn_block(self, signature: str) -> str:
		return self.source.split(signature, 1)[1].split("\n\t}\n", 1)[0]

	def test_mount_initializes_queue_tabs(self) -> None:
		mount_block = self.source.split("function mount() {", 1)[1].split("\n\tfunction scheduleBoot", 1)[0]
		self.assertIn("initializeWorkbenchQueueTabs(root)", mount_block)

	def test_tab_order_maps_design_labels_to_backend_ui_queue_keys(self) -> None:
		order_block = self.source.split("const WORKBENCH_QUEUE_TAB_ORDER = [", 1)[1].split("];", 1)[0]
		expected_pairs = [
			("needs_planning", "Needs Planning", True),
			("draft_packages", "In Creation", True),
			("needs_review", "Awaiting Review", True),
			("ready_to_release", "Ready for Release", True),
			("blocked", "Blocked", False),
			("recently_released", "Released", False),
		]
		for ui_queue, label, show_count in expected_pairs:
			self.assertIn(f'uiQueue: "{ui_queue}"', order_block)
			self.assertIn(f'label: "{label}"', order_block)
			self.assertIn(f"showCount: {str(show_count).lower()}", order_block)

	def test_counts_only_applied_to_tabs_that_already_show_a_count(self) -> None:
		fn = self._fn_block("function applyWorkbenchQueueTabCounts(doc, counts) {")
		self.assertIn("if (!tab.showCount) return;", fn)
		self.assertIn("workbenchQueueTabButtons(doc)", fn)
		self.assertNotIn("root.", fn)
		self.assertNotIn(".innerHTML", fn)

	def test_tab_button_selector_targets_existing_design_tab_bar_only(self) -> None:
		fn = self._fn_block("function workbenchQueueTabButtons(doc) {")
		self.assertIn('.querySelector(".scrollbar-hide")', fn)
		self.assertNotIn("data-testid", fn)

	def test_tab_click_updates_shared_w1_url_state_and_active_classes(self) -> None:
		fn = self._fn_block("function bindWorkbenchQueueTabs(root, doc) {")
		self.assertIn("writeWorkbenchStateToUrl({ queue: tab.uiQueue, page: 1 })", fn)
		self.assertIn("applyWorkbenchQueueActiveTab(doc, tab.uiQueue)", fn)

	def test_fetch_uses_existing_queue_counts_api_constant(self) -> None:
		fn = self._fn_block("function fetchAndApplyWorkbenchQueueCounts(root) {")
		self.assertIn("method: WORKBENCH_QUEUE_COUNTS_API", fn)
		self.assertIn("withWorkbenchIframeDocument(root", fn)


class TestPP4WorkbenchQueueTabsCountsW3FieldContract(IntegrationTestCase):
	"""Pin the exact `get_workbench_queue_counts` UI-facing keys the JS reads."""

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not _pp_ok():
			self._skip = True
			return
		self._skip = False

	def test_counts_envelope_exposes_all_six_ui_queue_keys(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		out = get_workbench_queue_counts(actor="Administrator")
		self.assertTrue(out.get("ok"), msg=out)
		counts = out.get("counts") or {}
		for ui_queue in (
			"needs_planning",
			"draft_packages",
			"needs_review",
			"ready_to_release",
			"blocked",
			"recently_released",
		):
			self.assertIn(ui_queue, counts, msg=f"missing {ui_queue} in {counts}")
			self.assertIsInstance(counts[ui_queue], int)
			self.assertGreaterEqual(counts[ui_queue], 0)
