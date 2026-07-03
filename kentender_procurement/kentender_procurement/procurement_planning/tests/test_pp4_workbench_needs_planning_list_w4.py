# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""W4 — Workbench Needs Planning List (Primary Screen).

Scope (Workbench Wiring Tracker, W4):
- Bind the design's own static table rows to the live
  `get_pp_approved_demands_awaiting_planning` payload (`demand`, `department`,
  `category`, `estimated_value`/`currency`, `budget_line`) — cloning the
  design's own pristine first `<tr>` as a template rather than inventing new
  markup, so every generated row stays pixel-identical to the design.
- Wire the footer "X to Y of Z" summary and Prev/Next pagination against the
  shared W1 `page` URL state.
- Wire row click -> `demand-workbench` navigation (the same route
  `demand_hub_page.js` already uses for "view demand"), skipping the
  checkbox so native row-selection still works.

Only the "Needs Planning" (default) queue has a pixel design today, so this
always renders that dataset regardless of which tab is active — the same
accepted limitation already documented for W3.

Source-level assertions only (no JS runtime harness in this router's test
suite). Playwright UX validation runs separately against
`kentender.midas.com`.
"""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.procurement_planning.services.approved_demand_queue import (
	get_approved_demands_awaiting_planning,
)


def _router_path() -> Path:
	return Path(__file__).resolve().parents[2] / "public" / "js" / "pp2_planning_router.js"


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan")) and bool(frappe.db.exists("DocType", "Demand"))


class TestPP4WorkbenchNeedsPlanningListW4Source(UnitTestCase):
	"""Source-level wiring assertions for pp2_planning_router.js."""

	def setUp(self) -> None:
		super().setUp()
		self.source = _router_path().read_text(encoding="utf-8", errors="replace")

	def _fn_block(self, signature: str) -> str:
		return self.source.split(signature, 1)[1].split("\n\t}\n", 1)[0]

	def test_mount_initializes_needs_planning_list(self) -> None:
		mount_block = self.source.split("function mount() {", 1)[1].split("\n\tfunction scheduleBoot", 1)[0]
		self.assertIn("initializeWorkbenchNeedsPlanningList(root)", mount_block)

	def test_fetch_reuses_existing_approved_demands_queue_api_constant(self) -> None:
		fn = self._fn_block("function fetchAndRenderWorkbenchNeedsPlanningList(root, doc) {")
		self.assertIn("method: APPROVED_DEMANDS_QUEUE_API", fn)

	def test_row_builder_clones_design_template_and_does_not_fabricate_markup(self) -> None:
		fn = self._fn_block("function buildWorkbenchNeedsPlanningRow(template, doc, row) {")
		self.assertIn("template.cloneNode(true)", fn)
		self.assertNotIn(".innerHTML", fn)

	def test_row_template_is_captured_once_from_the_pristine_first_row(self) -> None:
		fn = self._fn_block("function initializeWorkbenchNeedsPlanningList(root) {")
		self.assertIn("workbenchNeedsPlanningRowTemplateByRoot.has(root)", fn)
		self.assertIn("firstRow.cloneNode(true)", fn)

	def test_category_tone_map_matches_demand_requisition_type_enum(self) -> None:
		tone_block = self.source.split("const WORKBENCH_CATEGORY_TONE_BY_VALUE = {", 1)[1].split("};", 1)[0]
		for value, tone in (
			("goods", "cat-goods"),
			("works", "cat-works"),
			("services", "cat-services"),
			("consultancy", "cat-consultancy"),
		):
			self.assertIn(f'{value}: "{tone}"', tone_block)

	def test_row_click_navigates_to_demand_workbench_route_and_skips_checkbox(self) -> None:
		fn = self._fn_block("function buildWorkbenchNeedsPlanningRow(template, doc, row) {")
		self.assertIn('event.target.closest(\'input[type="checkbox"]\')', fn)
		self.assertIn('frappe.set_route("demand-workbench", demandId)', fn)

	def test_pagination_uses_shared_w1_page_state(self) -> None:
		render_fn = self._fn_block("function renderWorkbenchNeedsPlanningRows(root, doc, payload) {")
		self.assertIn("readWorkbenchStateFromUrl()", render_fn)
		bind_fn = self._fn_block("function bindWorkbenchNeedsPlanningPagination(root, doc) {")
		self.assertIn("writeWorkbenchStateToUrl({ page:", bind_fn)

	def test_footer_summary_group_uses_direct_child_index_not_nth_child_query(self) -> None:
		"""Regression: `footer.querySelector("div:nth-child(2)")` matches the
		*nested* "rows per page" dropdown div (which is itself a 2nd child of
		its own parent) before it ever reaches the real summary/pagination
		div, because :nth-child is scoped per-parent and querySelector walks
		the whole subtree in document order. Must use direct child indexing
		instead."""
		fn = self._fn_block("function workbenchNeedsPlanningFooterEls(doc) {")
		code_lines = [line for line in fn.splitlines() if not line.strip().startswith("//")]
		code_only = "\n".join(code_lines)
		self.assertIn("footer.children[1]", code_only)
		self.assertNotIn('querySelector("div:nth-child(2)")', code_only)

	def test_empty_payload_clears_rows_without_fabricating_empty_state_markup(self) -> None:
		fn = self._fn_block("function renderWorkbenchNeedsPlanningRows(root, doc, payload) {")
		self.assertIn("tbody.removeChild(tbody.firstChild)", fn)
		self.assertNotIn(".innerHTML", fn)


class TestPP4WorkbenchNeedsPlanningListW4FieldContract(IntegrationTestCase):
	"""Pin the exact `get_approved_demands_awaiting_planning` row fields the
	JS reads from, so an unnoticed backend rename cannot silently break the
	W4 list binding."""

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._skip = not _pp_ok()

	def test_row_envelope_exposes_fields_the_row_builder_depends_on(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning / Demand Intake not installed")
		out = get_approved_demands_awaiting_planning({"start": 0, "limit": 5}, "Administrator")
		self.assertTrue(out.get("ok"), msg=out)
		self.assertIn("total", out)
		self.assertIsInstance(out.get("rows"), list)
		for row in out["rows"]:
			demand = row.get("demand") or {}
			self.assertIn("id", demand)
			self.assertIn("code", demand)
			self.assertIn("name", demand)
			self.assertIn("department", row)
			self.assertIn("category", row)
			self.assertIn("estimated_value", row)
			self.assertIn("currency", row)
			budget_line = row.get("budget_line") or {}
			self.assertIn("id", budget_line)
			self.assertIn("code", budget_line)
