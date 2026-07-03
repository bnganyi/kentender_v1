# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Regression guard — Workbench root must stay a faithful static design render.

The `renderPlanningWorkbenchV4` markup itself must never grow a new banner,
gate panel, or other visible element beyond the `needs_planning_default.html`
iframe. Backend wiring (e.g. W2 active-plan context) is only allowed to
mutate existing nodes *inside* that iframe's own document — never inject new
markup into the Desk-owned workbench root shell.
"""

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


def _design_source_path() -> Path:
	return (
		Path(__file__).resolve().parents[4]
		/ "docs"
		/ "prompts"
		/ "procurement planning v4"
		/ "workbench"
		/ "1. Needs planning - default"
		/ "code.html"
	)


def _deployed_design_path() -> Path:
	return (
		Path(__file__).resolve().parents[2]
		/ "public"
		/ "workbench_design"
		/ "needs_planning_default.html"
	)


class TestPP4WorkbenchStaticLayoutGuard(UnitTestCase):
	def test_render_function_only_contains_the_design_iframe(self) -> None:
		source = _router_path().read_text(encoding="utf-8", errors="replace")
		fn_block = source.split("function renderPlanningWorkbenchV4(root) {", 1)[1].split(
			"\n\t}\n", 1
		)[0]
		self.assertIn('data-testid="pp4-workbench-design-iframe"', fn_block)
		self.assertNotIn("pp3-active-plan-host", fn_block)
		self.assertNotIn("pp3-planning-work-unavailable", fn_block)
		self.assertNotIn("pp4-active-plan-context", fn_block)

	def test_mount_active_plan_wiring_does_not_inject_new_visible_markup(self) -> None:
		"""W2 wires an active-plan fetch on mount, but the gate/update helpers
		must only touch the iframe's own document (textContent updates) or
		redirect away entirely — never grow the Desk-owned workbench shell
		with a new banner/gate element."""
		source = _router_path().read_text(encoding="utf-8", errors="replace")
		mount_block = source.split("function mount() {", 1)[1].split("\n\tfunction scheduleBoot", 1)[0]
		self.assertIn("fetchAndApplyWorkbenchActivePlanContext(root)", mount_block)
		self.assertNotIn("applyPP4ActivePlanGate", mount_block)
		self.assertNotIn("pp4RouteToPlanningHub", mount_block)

		gate_fn = source.split(
			"function redirectWorkbenchToPlanningHubForNoActivePlan(payload) {", 1
		)[1].split("\n\t}\n", 1)[0]
		self.assertNotIn(".innerHTML", gate_fn)
		self.assertIn("/desk/planning-hub", gate_fn)

		card_fn = source.split("function applyWorkbenchActivePlanCard(doc, payload) {", 1)[1].split(
			"\n\t}\n", 1
		)[0]
		self.assertNotIn(".innerHTML", card_fn)
		self.assertNotIn("root.", card_fn)

	def test_mount_queue_tab_wiring_does_not_inject_new_visible_markup(self) -> None:
		"""W3 wires queue tab counts/active-state on mount, but must only
		toggle classes/text on the design's own six tab buttons — never add
		a new tab, badge, or other element the design does not already have."""
		source = _router_path().read_text(encoding="utf-8", errors="replace")
		mount_block = source.split("function mount() {", 1)[1].split("\n\tfunction scheduleBoot", 1)[0]
		self.assertIn("initializeWorkbenchQueueTabs(root)", mount_block)

		for fn_signature in (
			"function workbenchQueueTabButtons(doc) {",
			"function applyWorkbenchQueueActiveTab(doc, activeUiQueue) {",
			"function applyWorkbenchQueueTabCounts(doc, counts) {",
			"function bindWorkbenchQueueTabs(root, doc) {",
		):
			fn = source.split(fn_signature, 1)[1].split("\n\t}\n", 1)[0]
			self.assertNotIn(".innerHTML", fn)
			self.assertNotIn("appendChild", fn)
			self.assertNotIn("insertAdjacent", fn)

	def test_mount_selection_toolbar_wiring_only_toggles_existing_toolbar(self) -> None:
		"""W5 drives the floating selection toolbar (ported verbatim from the
		"2. Needs planning - selection" design) with real state, but must only
		toggle inline style / textContent on the design's own toolbar element
		— never build a second toolbar or inject extra markup."""
		source = _router_path().read_text(encoding="utf-8", errors="replace")
		mount_block = source.split("function mount() {", 1)[1].split("\n\tfunction scheduleBoot", 1)[0]
		self.assertIn("initializeWorkbenchNeedsPlanningList(root)", mount_block)

		for fn_signature in (
			"function workbenchSelectionToolbarEls(doc) {",
			"function workbenchUpdateSelectionToolbar(root, doc) {",
			"function bindWorkbenchSelectionToolbarActions(root, doc) {",
		):
			fn = source.split(fn_signature, 1)[1].split("\n\t}\n", 1)[0]
			self.assertNotIn(".innerHTML", fn)
			self.assertNotIn("appendChild", fn)
			self.assertNotIn("insertAdjacent", fn)
			self.assertNotIn("document.createElement", fn)

	def test_mount_needs_planning_list_wiring_clones_design_row_only(self) -> None:
		"""W4 binds real demand rows into the design's own table, but every
		generated row must be a clone of the design's pristine first `<tr>` —
		never freehand-built markup that could drift from the pixel design."""
		source = _router_path().read_text(encoding="utf-8", errors="replace")
		mount_block = source.split("function mount() {", 1)[1].split("\n\tfunction scheduleBoot", 1)[0]
		self.assertIn("initializeWorkbenchNeedsPlanningList(root)", mount_block)

		row_fn = source.split("function buildWorkbenchNeedsPlanningRow(template, doc, row) {", 1)[1].split(
			"\n\t}\n", 1
		)[0]
		self.assertIn("template.cloneNode(true)", row_fn)
		self.assertNotIn(".innerHTML", row_fn)
		self.assertNotIn("document.createElement", row_fn)

	def test_deployed_design_asset_only_suppresses_duplicate_desk_sidebar(self) -> None:
		"""Deployed copy must match the design pixel-for-pixel except for the
		design's own left nav `<aside>`, which duplicates Frappe Desk's native
		module sidebar and is intentionally suppressed for the embedded/iframe
		copy only, and the floating selection toolbar (W5), which the source
		screen only ever shipped as a placeholder comment — the real markup
		was ported verbatim from the companion "2. Needs planning -
		selection" design instead. The pristine design source is left
		untouched either way."""
		design_source = _design_source_path()
		deployed = _deployed_design_path()
		self.assertTrue(design_source.exists(), msg=f"missing {design_source}")
		self.assertTrue(deployed.exists(), msg=f"missing {deployed}")

		source_html = design_source.read_text(encoding="utf-8")
		deployed_html = deployed.read_text(encoding="utf-8")

		self.assertIn("Global Procurement", source_html)
		self.assertNotIn(
			"Global Procurement",
			deployed_html,
			"Deployed workbench design must not duplicate Desk's own left-hand navigation.",
		)
		self.assertNotIn('<aside class="h-screen w-64 fixed left-0 top-0', deployed_html)
		self.assertNotIn("ml-64", deployed_html)

		# Header, KPI cards, tabs, and table (everything up to the floating
		# toolbar placeholder) must remain byte-identical to the design.
		main_marker = '<main class="'
		toolbar_marker = "<!-- FLOATING SELECTION TOOLBAR"
		source_main = source_html.split(main_marker, 1)[1]
		deployed_main = deployed_html.split(main_marker, 1)[1]
		# Strip only the leading class attribute value (ml-64 vs not) before comparing.
		source_main_body = source_main.split(">", 1)[1]
		deployed_main_body = deployed_main.split(">", 1)[1]
		source_before_toolbar = source_main_body.split(toolbar_marker, 1)[0]
		deployed_before_toolbar = deployed_main_body.split(toolbar_marker, 1)[0]
		self.assertEqual(
			source_before_toolbar,
			deployed_before_toolbar,
			"Content before the floating toolbar must stay pixel-identical to the design.",
		)

		# Past the marker: source is still just the placeholder comment + the
		# design's own dead inline script (four hardcoded mock rows only);
		# deployed has the real, hidden-by-default toolbar markup and no
		# inline script (W5 drives it from pp2_planning_router.js instead).
		self.assertNotIn('id="selection-toolbar"', source_main_body)
		self.assertIn("Selection toolbar logic", source_main_body)
		self.assertIn('id="selection-toolbar"', deployed_main_body)
		self.assertNotIn("Selection toolbar logic", deployed_main_body)
