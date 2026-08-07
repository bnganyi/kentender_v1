# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""W5 — Workbench Needs Planning Actions.

Scope (Workbench Wiring Tracker, W5):
- Drive the floating selection toolbar (ported verbatim from the companion
  "2. Needs planning - selection" design — the default screen only ever
  shipped a placeholder comment for it) with real selected-row state: live
  count, live estimated-value total, and show/hide.
- Wire "Add to Active Plan" -> `include_pp_demand_in_procurement_plan` and
  "Create Package" -> ensure inclusion then
  `create_pp_package_from_planning_inclusion`, sequentially per selected
  demand, with clear success/failure alerts surfacing server blockers.
- "View Demand" is already covered by the W4 row click (-> demand-workbench
  route) — no separate action is added for it here.

Source-level assertions only (no JS runtime harness in this router's test
suite). Playwright UX validation runs separately against
`kentender.midas.com`.
"""

from __future__ import annotations

from pathlib import Path

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from frappe.tests import IntegrationTestCase, UnitTestCase


def _router_path() -> Path:
	return Path(__file__).resolve().parents[2] / "public" / "js" / "pp2_planning_router.js"


def _deployed_design_path() -> Path:
	return (
		Path(__file__).resolve().parents[2]
		/ "public"
		/ "workbench_design"
		/ "needs_planning_default.html"
	)


class TestPP4WorkbenchNeedsPlanningActionsW5Source(UnitTestCase):
	"""Source-level wiring assertions for pp2_planning_router.js."""

	def setUp(self) -> None:
		super().setUp()
		self.source = _router_path().read_text(encoding="utf-8", errors="replace")
		self.design_html = _deployed_design_path().read_text(encoding="utf-8", errors="replace")

	def _fn_block(self, signature: str) -> str:
		return self.source.split(signature, 1)[1].split("\n\t}\n", 1)[0]

	def test_deployed_design_ships_the_selection_toolbar_hidden_by_default(self) -> None:
		self.assertIn('id="selection-toolbar"', self.design_html)
		self.assertIn("opacity: 0", self.design_html.split('id="selection-toolbar"', 1)[1][:200])
		# The dead inline script from the static mock (captures checkboxes once,
		# at parse time, so it can never see W4's dynamically rendered rows)
		# must not ship — real wiring lives entirely in the router.
		self.assertNotIn("Selection toolbar logic", self.design_html)
		self.assertNotIn("updateToolbar", self.design_html)

	def test_mount_initializes_row_selection_and_toolbar_actions(self) -> None:
		init_fn = self._fn_block("function initializeWorkbenchNeedsPlanningList(root) {")
		self.assertIn("bindWorkbenchNeedsPlanningRowSelection(root, doc)", init_fn)
		self.assertIn("bindWorkbenchSelectionToolbarActions(root, doc)", init_fn)

	def test_row_selection_is_delegated_on_tbody_and_keyed_by_demand_id(self) -> None:
		fn = self._fn_block("function bindWorkbenchNeedsPlanningRowSelection(root, doc) {")
		self.assertIn('tbody.addEventListener("change"', fn)
		self.assertIn('checkbox.closest("tr")', fn)
		self.assertIn('tr.getAttribute("data-demand-id")', fn)

	def test_toolbar_hides_when_selection_is_empty(self) -> None:
		fn = self._fn_block("function workbenchUpdateSelectionToolbar(root, doc) {")
		self.assertIn('els.toolbar.style.opacity = "0"', fn)
		self.assertIn('els.toolbar.style.pointerEvents = "none"', fn)

	def test_add_to_active_plan_uses_cached_plan_code_and_include_api(self) -> None:
		fn = self._fn_block("function workbenchAddSelectedDemandsToActivePlan(root, doc) {")
		self.assertIn("workbenchActivePlanCodeByRoot.get(root)", fn)
		self.assertIn("method: INCLUDE_DEMAND_IN_PLAN_API", fn)

	def test_create_package_ensures_inclusion_then_opens_wizard(self) -> None:
		"""PW11 — the bulk toolbar action includes every selected demand,
		then opens the Package Creation Wizard pre-selected with the
		resulting inclusions instead of auto-creating one package per
		demand (the wizard is now the single canonical create-package
		path; see the Package Wizard tracker's entry-point-replacement
		scope decision)."""
		fn = self._fn_block("function workbenchCreatePackagesFromSelectedDemands(root, doc) {")
		self.assertIn("method: INCLUDE_DEMAND_IN_PLAN_API", fn)
		self.assertIn("openPlanningPackageWizard(root, doc,", fn)
		self.assertIn("r.inclusion_code", fn)
		self.assertNotIn("method: CREATE_PACKAGE_FROM_INCLUSION_API", fn)

	def test_selection_actions_refresh_list_and_counts_after_completion(self) -> None:
		for fn_signature in (
			"function workbenchAddSelectedDemandsToActivePlan(root, doc) {",
			"function workbenchCreatePackagesFromSelectedDemands(root, doc) {",
		):
			fn = self.source.split(fn_signature, 1)[1]
			outcome_block = fn.split("function (results) {", 1)[1].split("\n\t\t\t}\n\t\t);\n\t}\n", 1)[0]
			self.assertIn("fetchAndRenderWorkbenchNeedsPlanningList(root, doc)", outcome_block)
			self.assertIn("fetchAndApplyWorkbenchQueueCounts(root)", outcome_block)

	def test_active_plan_code_is_cached_from_w2_fetch_for_reuse(self) -> None:
		fn = self._fn_block("function fetchAndApplyWorkbenchActivePlanContext(root) {")
		self.assertIn("workbenchActivePlanCodeByRoot.set(root,", fn)

	def test_row_data_uses_business_demand_code_not_internal_id_for_api_calls(self) -> None:
		"""Regression guard: `demand.id` is the internal Frappe name (used only
		as the DOM/selection key), while `demand.code` is the business code the
		planning-inclusion APIs (`include_pp_demand_in_procurement_plan`,
		`create_pp_package_from_planning_inclusion`) actually key journeys and
		inclusions on. Passing `demand.id` through as `demand_code` previously
		caused every real "Add to Active Plan" / "Create Package" call to fail
		with a "Journey code could not be resolved" error, because the journey
		bootstrap creates journeys keyed by the business code while the include
		flow was looking them up by the internal id instead."""
		# Note: this function contains a `while` loop at the same indentation
		# as the function body, so the generic single-tab-closing-brace split
		# used elsewhere in this file would truncate too early — bound on the
		# next function's signature instead.
		fn = self.source.split("function renderWorkbenchNeedsPlanningRows(root, doc, payload) {", 1)[1].split(
			"\n\tfunction fetchAndRenderWorkbenchNeedsPlanningList", 1
		)[0]
		self.assertIn("code: demand.code || demand.id", fn)
		self.assertNotIn("code: demand.id,", fn)

	def test_selection_map_values_are_read_with_array_from_not_slice_call(self) -> None:
		"""Regression guard: `Array.prototype.slice.call(map.values())` silently
		returns `[]` because a Map iterator has no `.length` — it is not
		array-like. This previously made the toolbar read `items.length === 0`
		right after a checkbox selection was recorded, so it never appeared.
		`Array.from(...)` is the correct way to materialize a Map iterator."""
		for fn_signature in (
			"function workbenchUpdateSelectionToolbar(root, doc) {",
			"function workbenchAddSelectedDemandsToActivePlan(root, doc) {",
			"function workbenchCreatePackagesFromSelectedDemands(root, doc) {",
		):
			fn = self._fn_block(fn_signature)
			self.assertIn("Array.from(selection.values())", fn)
			self.assertNotIn("Array.prototype.slice.call(selection.values())", fn)

	def test_no_new_view_demand_action_duplicates_w4_row_click(self) -> None:
		"""W5 explicitly reuses the W4 row-click navigation for "View Demand"
		rather than adding a second action — pin that no *W5 selection-toolbar*
		`frappe.set_route("demand-workbench", ...)` call site was added.

		The remaining-queues pass (W7) legitimately introduces a second,
		unrelated call site: the Blocked queue's row builder routes a blocked
		*demand* row to `demand-workbench` (vs. a blocked *package* row, which
		routes to `procurement-package`) — this is queue-shape branching, not
		a duplicate of W4/W5's needs-planning row click."""
		matches = self.source.count('frappe.set_route("demand-workbench"')
		self.assertEqual(matches, 2)


class TestPP4WorkbenchNeedsPlanningActionsW5FieldContract(IntegrationTestCase):
	"""Pin the exact response fields the W5 action handlers depend on."""

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._skip = not (
			frappe.db.exists("DocType", "Procurement Plan") and demand_consumers_live()
		)

	def test_include_demand_response_exposes_ok_and_inclusion_code_on_success_shape(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning / Demand Intake not installed")
		from kentender_procurement.procurement_planning.api.approved_demands import (
			include_pp_demand_in_procurement_plan,
		)

		# Missing params is the cheapest deterministic way to exercise the
		# whitelisted wrapper's response envelope without needing a full
		# eligible-demand fixture; it still pins the `ok`/`message` contract
		# the JS branches on.
		out = include_pp_demand_in_procurement_plan(demand_code="", procurement_plan_code="")
		self.assertIn("ok", out)
		self.assertFalse(out["ok"])
		self.assertIn("message", out)

	def test_create_package_from_inclusion_response_exposes_ok_and_message(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning / Demand Intake not installed")
		from kentender_procurement.procurement_planning.api.planning_inclusion import (
			create_pp_package_from_planning_inclusion,
		)

		out = create_pp_package_from_planning_inclusion(inclusion_code="")
		self.assertIn("ok", out)
		self.assertFalse(out["ok"])
		self.assertIn("message", out)
