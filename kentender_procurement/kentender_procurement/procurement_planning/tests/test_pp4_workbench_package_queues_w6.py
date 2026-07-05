# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""W6 — In Creation / Awaiting Review / Ready for Release Lists.

Scope (Workbench Wiring Tracker, W6):
- All three package-shaped queues (`draft_packages`, `needs_review`,
  `ready_release`) share one pixel design (`3. In creation`) and one row
  template, cloned once from the design's own pristine first `<tr>` — never
  freehand-built markup — mirroring the W4 discipline for Needs Planning.
- The active queue tab toggles which table section is visible (Needs
  Planning vs. the shared package table); Blocked/Released (W7/W8) still
  have no pixel design and are left unimplemented.
- Row primary action is a title-click that navigates to the package's Desk
  form (`/app/procurement-package/<underlying_object_id>`), using the
  internal Frappe name — not the business code — the same class of fix
  already applied once for demand rows in W5.
- The legacy pre-iframe PP4 package-grid/card implementation (confirmed
  unreachable from `mount()`) is removed as part of this pass.

Source-level assertions only (no JS runtime harness in this router's test
suite). Playwright UX validation runs separately against
`kentender.midas.com`.
"""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _router_path() -> Path:
	return Path(__file__).resolve().parents[2] / "public" / "js" / "pp2_planning_router.js"


class TestPP4WorkbenchPackageQueuesW6Source(UnitTestCase):
	"""Source-level wiring assertions for pp2_planning_router.js."""

	def setUp(self) -> None:
		super().setUp()
		self.source = _router_path().read_text(encoding="utf-8", errors="replace")

	def _fn_block(self, signature: str) -> str:
		return self.source.split(signature, 1)[1].split("\n\t}\n", 1)[0]

	def test_mount_initializes_package_queue_list(self) -> None:
		mount_block = self.source.split("function mount() {", 1)[1].split("\n\tfunction scheduleBoot", 1)[0]
		self.assertIn("initializeWorkbenchPackageQueueList(root)", mount_block)

	def test_legacy_pp4_package_grid_functions_are_removed(self) -> None:
		"""Regression: the pre-iframe, card-grid-based reimplementation of
		this same concept must stay removed, not silently reappear."""
		for removed_name in (
			"fetchAndRenderPP4PackageCards",
			"renderPP4PackageCardsFromState",
			"renderPP4ControlLabels",
			"renderPP4SortMenuState",
			"renderPP4FilterDrawerState",
			"bindPP4SortAndFilters",
			"bindPP4TabPackageList",
			"bindPP4Search",
			"pp4AvailableDepartments",
			"PP4_STATUS_FILTERS",
			"PP4_VALUE_RANGES",
			"pp4PackageItemsByRoot",
			"pp4QueueItemsByRoot",
		):
			self.assertNotIn(removed_name, self.source)

	def test_ui_queue_to_api_queue_mapping(self) -> None:
		tone_block = self.source.split("const WORKBENCH_PACKAGE_UI_QUEUE_TO_API_QUEUE = {", 1)[1].split("};", 1)[0]
		self.assertIn('draft_packages: "draft_packages"', tone_block)
		self.assertIn('needs_review: "needs_review"', tone_block)
		self.assertIn('ready_to_release: "ready_release"', tone_block)

	def test_fetch_reuses_existing_workbench_item_view_model_api_constant(self) -> None:
		fn = self._fn_block("function fetchAndRenderWorkbenchPackageQueueList(root, doc, uiQueue) {")
		self.assertIn("method: WORKBENCH_ITEM_VIEW_MODEL_API", fn)
		self.assertIn("queue: apiQueue", fn)

	def test_row_builder_clones_design_template_and_does_not_fabricate_markup(self) -> None:
		fn = self._fn_block("function buildWorkbenchPackageQueueRow(template, doc, item, uiQueue, root) {")
		self.assertIn("template.cloneNode(true)", fn)
		self.assertNotIn(".innerHTML", fn)
		self.assertNotIn("document.createElement", fn)

	def test_row_template_is_captured_once_from_the_pristine_first_row(self) -> None:
		fn = self._fn_block("function initializeWorkbenchPackageQueueList(root) {")
		self.assertIn("workbenchPackageQueueRowTemplateByRoot.has(root)", fn)
		self.assertIn("firstRow.cloneNode(true)", fn)

	def test_row_click_navigates_to_package_detail_using_business_code(self) -> None:
		"""Package title links route to the dedicated package-detail page
		using the business package code (PD9), not the raw desk form."""
		fn = self._fn_block("function buildWorkbenchPackageQueueRow(template, doc, item, uiQueue, root) {")
		self.assertIn("workbenchPackageRouteCode(data)", fn)
		self.assertIn("navigateToPackageDetailPage(packageCode)", fn)
		self.assertIn("buildPackageDetailUrl(packageCode)", fn)
		self.assertNotIn('frappe.set_route("procurement-package"', fn)

	def test_placeholder_row_opens_wizard_instead_of_routing(self) -> None:
		"""Demands "Added to Active Plan" but not yet packaged have no
		`Procurement Package` doc to route to (`is_placeholder`/
		`inclusion_code` instead of a real `underlying_object_id`) — closes
		the gap where such a demand would otherwise be unfindable anywhere
		on the Workbench once Needs Planning excludes it. Clicking the row
		must open the Package Creation Wizard pre-selected with the
		existing inclusion (PW11) rather than `frappe.set_route` or the
		retired single-call auto-create."""
		fn = self._fn_block("function buildWorkbenchPackageQueueRow(template, doc, item, uiQueue, root) {")
		self.assertIn("data.is_placeholder", fn)
		self.assertIn("workbenchCreatePackageFromInclusionRow(root, doc, inclusionCode)", fn)
		create_fn = self._fn_block("function workbenchCreatePackageFromInclusionRow(root, doc, inclusionCode) {")
		self.assertIn("openPlanningPackageWizard(root, doc,", create_fn)
		self.assertIn("inclusion_code: inclusionCode", create_fn)
		self.assertNotIn("method: CREATE_PACKAGE_FROM_INCLUSION_API", create_fn)

	def test_category_tone_map_is_reused_not_duplicated(self) -> None:
		"""UI-consistency pass: the category tone lookup now lives in one
		shared `applyWorkbenchCategoryChip` helper (used by every row
		builder), not duplicated inline per row builder."""
		self.assertIn("WORKBENCH_CATEGORY_TONE_BY_VALUE[value.toLowerCase()]", self.source)
		fn = self._fn_block("function buildWorkbenchPackageQueueRow(template, doc, item, uiQueue, root) {")
		self.assertIn("applyWorkbenchCategoryChip(doc, categoryBadge, data.category_label)", fn)

	def test_readiness_pill_uses_the_packages_own_real_readiness_fields(self) -> None:
		"""Corrected in the remaining-queues pass: this table's Readiness
		column used to hardcode one fake sample value per UI queue
		(`WORKBENCH_PACKAGE_READINESS_BY_UI_QUEUE`, now removed); it must
		read the package's own real `readiness_status`/`readiness_tone`
		fields instead."""
		self.assertNotIn("WORKBENCH_PACKAGE_READINESS_BY_UI_QUEUE", self.source)
		fn = self._fn_block("function buildWorkbenchPackageQueueRow(template, doc, item, uiQueue, root) {")
		self.assertIn("applyWorkbenchPackagePillReadiness(readinessWrap, data.readiness_tone, ", fn)

	def test_money_abbreviation_helper_matches_design_notation(self) -> None:
		fn = self._fn_block("function workbenchAbbreviateMoney(value) {")
		self.assertIn('+ "B"', fn)
		self.assertIn('+ "M"', fn)

	def test_tab_click_toggles_table_visibility(self) -> None:
		fn = self._fn_block("function bindWorkbenchQueueTabs(root, doc) {")
		self.assertIn("applyWorkbenchQueueTableVisibility(doc, tab.uiQueue)", fn)
		self.assertIn("fetchAndRenderWorkbenchPackageQueueList(root, doc, tab.uiQueue)", fn)

	def test_visibility_toggle_only_touches_hidden_attribute(self) -> None:
		fn = self._fn_block("function applyWorkbenchQueueTableVisibility(doc, activeUiQueue) {")
		self.assertIn("needsSection.hidden", fn)
		self.assertIn("packageSection.hidden", fn)
		self.assertNotIn(".innerHTML", fn)
		self.assertNotIn("appendChild", fn)

	def test_pagination_uses_shared_w1_page_state(self) -> None:
		render_fn = self._fn_block("function renderWorkbenchPackageQueueRows(root, doc, uiQueue, payload) {")
		self.assertIn("readWorkbenchStateFromUrl()", render_fn)
		bind_fn = self._fn_block("function bindWorkbenchPackageQueuePagination(root, doc) {")
		self.assertIn("writeWorkbenchStateToUrl({ page:", bind_fn)

	def test_empty_payload_clears_rows_and_shows_the_graceful_empty_state(self) -> None:
		"""UI-consistency pass: an empty queue (e.g. Released, which has no
		seeded data in some environments) must no longer render a confusing
		near-blank table (header floating over the footer's "0 to 0 of 0").
		Old rows are still cleared via `removeChild` (never `.innerHTML`),
		and the shared `appendWorkbenchEmptyStateRow` helper is called only
		when there are zero items."""
		fn = self._fn_block("function renderWorkbenchPackageQueueRows(root, doc, uiQueue, payload) {")
		self.assertIn("tbody.removeChild(tbody.firstChild)", fn)
		self.assertNotIn(".innerHTML", fn)
		self.assertIn("if (!items.length) {", fn)
		self.assertIn("appendWorkbenchEmptyStateRow(doc, tbody,", fn)

	def test_empty_state_row_helper_computes_colspan_from_the_tables_own_header(self) -> None:
		"""No design mockup shows an empty state for any table, so this row
		is fabricated (not ported) — but its `colspan` must still be derived
		from each table's own `<thead>` rather than a hardcoded number,
		since every table has a different column count."""
		fn = self._fn_block("function appendWorkbenchEmptyStateRow(doc, tbody, message) {")
		self.assertIn('table.querySelector("thead tr")', fn)
		self.assertIn("headerRow.children.length", fn)
		self.assertIn('tr.setAttribute("data-testid", "pp4-workbench-empty-row")', fn)
		self.assertIn("tbody.appendChild(tr)", fn)

	def test_needs_planning_rows_also_show_the_graceful_empty_state(self) -> None:
		fn = self._fn_block("function renderWorkbenchNeedsPlanningRows(root, doc, payload) {")
		self.assertIn("if (!rows.length) {", fn)
		self.assertIn("appendWorkbenchEmptyStateRow(doc, tbody,", fn)

	def test_package_detail_surface_redirects_to_dedicated_page(self) -> None:
		"""PD9: legacy mount helper now delegates to the package-detail page."""
		fn = self._fn_block("function mountPackageDetailSurface(mainHost, packageCode, root) {")
		self.assertIn("navigateToPackageDetailPage(packageCode)", fn)
