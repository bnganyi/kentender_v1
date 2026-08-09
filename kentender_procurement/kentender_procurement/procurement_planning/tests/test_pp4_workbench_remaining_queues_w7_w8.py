# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Remaining-queues pass (corrects W6, delivers W7 + W8).

Scope (Workbench Wiring Tracker):
- Corrects the W6 assumption that Awaiting Review / Ready for Release could
  reuse the In Creation table — the newly-supplied per-queue designs reveal
  each queue group has its own real table shape. `WORKBENCH_QUEUE_GROUPS` is
  now the single source of truth mapping each non-Needs-Planning uiQueue to
  its own DOM section + row-builder function.
- Awaiting Review + Ready for Release share one table (their two source
  designs ship byte-identical `<thead>`s).
- Blocked (W7) and Released (W8) each get their own table shape and are no
  longer unimplemented placeholder tabs.
- The Workbench Insights card's heading stays static text ("Workbench
  Insights") for every queue; only its insight-items content becomes two
  hidden-toggled variants (default vs. Released's own copy).
- The Blocked tab now shows a real count badge, matching its own design.

Source-level assertions only (no JS runtime harness in this router's test
suite). Playwright UX validation runs separately against
`kentender.midas.com`.
"""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _router_path() -> Path:
	return Path(__file__).resolve().parents[2] / "public" / "js" / "pp2_planning_router.js"


class TestPP4WorkbenchRemainingQueuesW7W8Source(UnitTestCase):
	"""Source-level wiring assertions for pp2_planning_router.js."""

	def setUp(self) -> None:
		super().setUp()
		self.source = _router_path().read_text(encoding="utf-8", errors="replace")

	def _fn_block(self, signature: str) -> str:
		return self.source.split(signature, 1)[1].split("\n\t}\n", 1)[0]

	def test_group_config_covers_all_five_non_needs_planning_queues(self) -> None:
		block = self.source.split("const WORKBENCH_QUEUE_GROUPS = {", 1)[1].split("\n\t};", 1)[0]
		self.assertIn(
			"draft_packages: { sectionTestId: WORKBENCH_PACKAGE_TABLE_SECTION_TESTID, rowBuilder: buildWorkbenchPackageQueueRow }",
			block,
		)
		self.assertIn(
			"needs_review: { sectionTestId: WORKBENCH_REVIEW_RELEASE_TABLE_SECTION_TESTID, rowBuilder: buildWorkbenchReviewReleaseRow }",
			block,
		)
		self.assertIn(
			"ready_to_release: { sectionTestId: WORKBENCH_REVIEW_RELEASE_TABLE_SECTION_TESTID, rowBuilder: buildWorkbenchReviewReleaseRow }",
			block,
		)
		self.assertIn(
			"blocked: { sectionTestId: WORKBENCH_BLOCKED_TABLE_SECTION_TESTID, rowBuilder: buildWorkbenchBlockedRow }",
			block,
		)
		self.assertIn(
			"recently_released: { sectionTestId: WORKBENCH_RELEASED_TABLE_SECTION_TESTID, rowBuilder: buildWorkbenchReleasedRow }",
			block,
		)

	def test_api_queue_mapping_extended_for_blocked_and_released(self) -> None:
		block = self.source.split("const WORKBENCH_PACKAGE_UI_QUEUE_TO_API_QUEUE = {", 1)[1].split("};", 1)[0]
		self.assertIn('blocked: "blocked"', block)
		self.assertIn('recently_released: "recently_released"', block)

	def test_visibility_toggles_every_group_section(self) -> None:
		fn = self._fn_block("function applyWorkbenchQueueTableVisibility(doc, activeUiQueue) {")
		self.assertIn("needsSection.hidden", fn)
		self.assertIn("packageSection.hidden", fn)
		self.assertIn("WORKBENCH_QUEUE_GROUP_SECTION_TESTIDS.forEach", fn)
		self.assertNotIn(".innerHTML", fn)
		self.assertNotIn("appendChild", fn)

	def test_row_template_capture_covers_every_distinct_section(self) -> None:
		fn = self._fn_block("function initializeWorkbenchPackageQueueList(root) {")
		self.assertIn("workbenchPackageQueueRowTemplateByRoot.has(root)", fn)
		self.assertIn("firstRow.cloneNode(true)", fn)
		self.assertIn("WORKBENCH_QUEUE_GROUP_SECTION_TESTIDS.forEach", fn)

	def test_pagination_binds_every_group_sections_own_footer(self) -> None:
		fn = self._fn_block("function bindWorkbenchPackageQueuePagination(root, doc) {")
		self.assertIn("WORKBENCH_QUEUE_GROUP_SECTION_TESTIDS.forEach", fn)
		self.assertIn("writeWorkbenchStateToUrl({ page:", fn)

	def test_render_dispatches_through_group_configs_own_row_builder(self) -> None:
		fn = self._fn_block("function renderWorkbenchPackageQueueRows(root, doc, uiQueue, payload) {")
		self.assertIn("WORKBENCH_QUEUE_GROUPS[uiQueue]", fn)
		self.assertIn("group.rowBuilder(template, doc, item, uiQueue)", fn)
		self.assertNotIn(".innerHTML", fn)

	def test_review_release_row_builder_clones_template_and_navigates_to_package_detail(self) -> None:
		"""UI-consistency pass: the title is now a real `<a>` (Needs-Planning
		style, no separate "Actions" column) — package rows route to the
		dedicated package-detail page (PD9)."""
		fn = self._fn_block("function buildWorkbenchReviewReleaseRow(template, doc, item) {")
		self.assertIn("template.cloneNode(true)", fn)
		self.assertNotIn(".innerHTML", fn)
		self.assertNotIn("document.createElement", fn)
		self.assertIn("workbenchPackageRouteCode(data)", fn)
		self.assertIn('cells[0].querySelector("a")', fn)
		self.assertIn('titleLink.setAttribute("href", href)', fn)
		self.assertIn("navigateToPackageDetailPage(packageCode)", fn)
		self.assertIn("applyWorkbenchCategoryChip(doc, categoryBadge,", fn)
		self.assertIn("applyWorkbenchStackedStatusPill(readinessWrap, data.readiness_tone,", fn)

	def test_blocked_row_builder_routes_demand_and_package_blockers_differently(self) -> None:
		"""Blocked rows can be a blocked demand or a blocked package
		(`underlying_object_type`); navigation must branch to the matching
		Desk surface for each, not assume every blocked row is a package.
		UI-consistency pass: the title is now a real `<a>` too, so its
		`href` must branch the same way the row-click handler does (demand
		vs. package Desk surface)."""
		fn = self._fn_block("function buildWorkbenchBlockedRow(template, doc, item) {")
		self.assertIn("template.cloneNode(true)", fn)
		self.assertNotIn(".innerHTML", fn)
		self.assertNotIn("document.createElement", fn)
		self.assertIn("data.underlying_object_id", fn)
		self.assertIn('data.underlying_object_type === "approved_demand"', fn)
		self.assertIn('cells[0].querySelectorAll("a")', fn)
		self.assertIn('titleLink.setAttribute("href", href)', fn)
		self.assertIn('"/desk/demand-detail/" + encodeURIComponent(targetId)', fn)
		self.assertIn("buildPackageDetailUrl(targetCode || targetId)", fn)
		self.assertIn('frappe.set_route("demand-detail", targetId)', fn)
		self.assertNotIn("demand-workbench", fn)
		self.assertNotIn('"/app/demand/"', fn)
		self.assertIn("navigateToPackageDetailPage(targetCode || targetId)", fn)
		self.assertIn("applyWorkbenchCategoryChip(doc, categoryBadge,", fn)
		self.assertIn('applyWorkbenchStackedStatusPill(blockerWrap, "error",', fn)

	def test_released_row_builder_clones_template_and_uses_a_real_link(self) -> None:
		"""Released's title has always been a real `<a>` (like In Creation);
		with the UI-consistency pass, Review-Release and Blocked's titles
		are now real `<a>`s too (see the two tests above) — Released is no
		longer the only row builder with this shape."""
		fn = self._fn_block("function buildWorkbenchReleasedRow(template, doc, item) {")
		self.assertIn("template.cloneNode(true)", fn)
		self.assertNotIn(".innerHTML", fn)
		self.assertNotIn("document.createElement", fn)
		self.assertIn("workbenchPackageRouteCode(data)", fn)
		self.assertIn("titleLink.setAttribute(\"href\", href)", fn)
		self.assertIn("navigateToPackageDetailPage(packageCode)", fn)
		self.assertIn("applyWorkbenchCategoryChip(doc, categoryBadge,", fn)
		self.assertIn("data.tender_status_label", fn)

	def test_readiness_pill_helpers_are_shared_not_duplicated_per_row_builder(self) -> None:
		"""Two distinct pill DOM shapes exist in the designs (In Creation's
		rounded-full pill vs. Awaiting-Review/Blocked's stacked icon+pill);
		each gets exactly one shared helper, reused by every row builder
		with that shape, rather than each row builder reimplementing it."""
		self.assertIn("function applyWorkbenchPackagePillReadiness(wrapEl, tone, label) {", self.source)
		self.assertIn("function applyWorkbenchStackedStatusPill(wrapEl, tone, label) {", self.source)
		package_fn = self._fn_block("function buildWorkbenchPackageQueueRow(template, doc, item, uiQueue) {")
		self.assertIn("applyWorkbenchPackagePillReadiness(readinessWrap,", package_fn)
		review_release_fn = self._fn_block("function buildWorkbenchReviewReleaseRow(template, doc, item) {")
		self.assertIn("applyWorkbenchStackedStatusPill(readinessWrap,", review_release_fn)
		blocked_fn = self._fn_block("function buildWorkbenchBlockedRow(template, doc, item) {")
		self.assertIn("applyWorkbenchStackedStatusPill(blockerWrap,", blocked_fn)

	def test_category_chip_helper_is_shared_not_duplicated_per_row_builder(self) -> None:
		"""UI-consistency pass: the dot+pill category chip (Needs Planning's
		style) is now used by every row builder via one shared helper,
		replacing what used to be 5 duplicated inline class-string blocks."""
		self.assertIn("function applyWorkbenchCategoryChip(doc, badgeEl, categoryValue) {", self.source)
		for fn_signature in (
			"function buildWorkbenchNeedsPlanningRow(template, doc, row) {",
			"function buildWorkbenchPackageQueueRow(template, doc, item, uiQueue) {",
			"function buildWorkbenchReviewReleaseRow(template, doc, item) {",
			"function buildWorkbenchBlockedRow(template, doc, item) {",
			"function buildWorkbenchReleasedRow(template, doc, item) {",
		):
			fn = self._fn_block(fn_signature)
			self.assertIn("applyWorkbenchCategoryChip(doc, categoryBadge,", fn)

	def test_empty_state_helper_is_shared_and_wired_into_both_render_functions(self) -> None:
		"""UI-consistency pass: an empty queue must show a graceful message
		instead of a bare header-over-footer; both render functions call the
		one shared `appendWorkbenchEmptyStateRow` helper rather than each
		fabricating their own empty-state markup."""
		self.assertIn("function appendWorkbenchEmptyStateRow(doc, tbody, message) {", self.source)
		needs_planning_fn = self._fn_block("function renderWorkbenchNeedsPlanningRows(root, doc, payload) {")
		self.assertIn("appendWorkbenchEmptyStateRow(doc, tbody,", needs_planning_fn)
		package_queue_fn = self._fn_block("function renderWorkbenchPackageQueueRows(root, doc, uiQueue, payload) {")
		self.assertIn("appendWorkbenchEmptyStateRow(doc, tbody,", package_queue_fn)

	def test_insights_variant_toggle_never_touches_the_static_heading(self) -> None:
		fn = self._fn_block("function applyWorkbenchInsightsVariant(doc, activeUiQueue) {")
		self.assertIn("WORKBENCH_INSIGHTS_DEFAULT_TESTID", fn)
		self.assertIn("WORKBENCH_INSIGHTS_RELEASED_TESTID", fn)
		self.assertIn('activeUiQueue === "recently_released"', fn)
		self.assertNotIn("textContent", fn)
		self.assertNotIn(".innerHTML", fn)
		self.assertNotIn("Workbench Insights", fn)
		self.assertNotIn("Released Insights", fn)

	def test_insights_variant_wired_into_tab_click_and_initial_load(self) -> None:
		tab_click_fn = self._fn_block("function bindWorkbenchQueueTabs(root, doc) {")
		self.assertIn("applyWorkbenchInsightsVariant(doc, tab.uiQueue)", tab_click_fn)
		init_fn = self._fn_block("function initializeWorkbenchQueueTabs(root) {")
		self.assertIn("applyWorkbenchInsightsVariant(doc, activeUiQueue)", init_fn)

	def test_blocked_tab_now_shows_a_real_count_badge(self) -> None:
		"""Pixel-fidelity fix: the "6. Blocked" design shows a count badge
		("Blocked (12)") on its own tab; the tab order config must render it
		using the existing count data, not the placeholder plain-text tab."""
		block = self.source.split("const WORKBENCH_QUEUE_TAB_ORDER = [", 1)[1].split("];", 1)[0]
		self.assertIn('{ uiQueue: "blocked", label: "Blocked", showCount: true }', block)
		self.assertIn('{ uiQueue: "recently_released", label: "Released", showCount: false }', block)

	def test_legacy_package_readiness_fake_map_stays_removed(self) -> None:
		self.assertNotIn("WORKBENCH_PACKAGE_READINESS_BY_UI_QUEUE", self.source)
