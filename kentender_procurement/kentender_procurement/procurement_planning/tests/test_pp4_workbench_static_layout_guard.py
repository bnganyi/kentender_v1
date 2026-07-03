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


def _in_creation_design_source_path() -> Path:
	return (
		Path(__file__).resolve().parents[4]
		/ "docs"
		/ "prompts"
		/ "procurement planning v4"
		/ "workbench"
		/ "3. In creation"
		/ "code.html"
	)


def _remaining_queue_design_source_path(folder: str) -> Path:
	return (
		Path(__file__).resolve().parents[4]
		/ "docs"
		/ "prompts"
		/ "procurement planning v4"
		/ "workbench"
		/ folder
		/ "code.html"
	)


_TABLE_REGION_START_MARKER = "<!-- Table (Restored Columns from SCREEN_16) -->"
_BOTTOM_PANELS_MARKER = '<div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6 pb-12">'
_NEEDS_PLANNING_TABLE_SECTION_TESTID = "pp4-workbench-needs-planning-table-section"
_PACKAGE_TABLE_SECTION_TESTID = "pp4-workbench-package-table-section"
_REVIEW_RELEASE_TABLE_SECTION_TESTID = "pp4-workbench-review-release-table-section"
_BLOCKED_TABLE_SECTION_TESTID = "pp4-workbench-blocked-table-section"
_RELEASED_TABLE_SECTION_TESTID = "pp4-workbench-released-table-section"
_INSIGHTS_CARD_START_MARKER = "<!-- Workbench Insights Card -->"
_INSIGHTS_DEFAULT_TESTID = "pp4-workbench-insights-default"
_INSIGHTS_RELEASED_TESTID = "pp4-workbench-insights-released"
_INSIGHTS_CARD_CLOSE_MARKER = "\n  </div>\n</div>"


def _extract_section_by_testid(html: str, testid: str) -> str:
	"""Return the inner content of the `<div data-testid="{testid}"...>`
	in `html`, using balanced `<div>`/`</div>` counting since the section's
	own children (table's `overflow-x-auto` wrapper, footer's nested divs)
	contain closing `</div>` tags of their own before the section ends."""
	open_marker = f'data-testid="{testid}"'
	before, _, after = html.partition(open_marker)
	if not after:
		raise AssertionError(f"section with {open_marker} not found")
	after_open_tag = after.split(">", 1)[1]
	depth = 1
	cursor = 0
	while depth > 0:
		next_open = after_open_tag.find("<div", cursor)
		next_close = after_open_tag.find("</div>", cursor)
		if next_close == -1:
			raise AssertionError(f"unbalanced <div> for section {open_marker}")
		if next_open != -1 and next_open < next_close:
			depth += 1
			cursor = next_open + len("<div")
		else:
			depth -= 1
			cursor = next_close + len("</div>")
	return after_open_tag[: cursor - len("</div>")]


def _extract_div_inner_by_start(html: str, div_start: int) -> str:
	"""Like `_extract_section_by_testid`, but starting from a known `<div`
	index rather than a `data-testid` marker — returns the inner content of
	that div using balanced `<div>`/`</div>` counting."""
	after_open_tag_index = html.index(">", div_start) + 1
	after_open_tag = html[after_open_tag_index:]
	depth = 1
	cursor = 0
	while depth > 0:
		next_open = after_open_tag.find("<div", cursor)
		next_close = after_open_tag.find("</div>", cursor)
		if next_close == -1:
			raise AssertionError("unbalanced <div> starting from the given index")
		if next_open != -1 and next_open < next_close:
			depth += 1
			cursor = next_open + len("<div")
		else:
			depth -= 1
			cursor = next_close + len("</div>")
	return after_open_tag[: cursor - len("</div>")]


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

		# Header, KPI cards, tabs, filter bar, table, and bottom panels
		# (everything up to the floating toolbar placeholder) must remain
		# byte-identical to the design — except the table region itself,
		# which W6 wraps in two toggleable sections (see the dedicated
		# package-table test below); that region is carved out and
		# verified separately instead of via one giant byte comparison.
		main_marker = '<main class="'
		toolbar_marker = "<!-- FLOATING SELECTION TOOLBAR"
		source_main = source_html.split(main_marker, 1)[1]
		deployed_main = deployed_html.split(main_marker, 1)[1]
		# Strip only the leading class attribute value (ml-64 vs not) before comparing.
		source_main_body = source_main.split(">", 1)[1]
		deployed_main_body = deployed_main.split(">", 1)[1]
		source_before_toolbar = source_main_body.split(toolbar_marker, 1)[0]
		deployed_before_toolbar = deployed_main_body.split(toolbar_marker, 1)[0]

		source_pre_table, source_after_table_marker = source_before_toolbar.split(
			_TABLE_REGION_START_MARKER, 1
		)
		deployed_pre_table, deployed_after_table_marker = deployed_before_toolbar.split(
			_TABLE_REGION_START_MARKER, 1
		)
		self.assertEqual(
			source_pre_table,
			deployed_pre_table,
			"Content before the table region (header/KPI/tabs/filter bar) must stay pixel-identical to the design.",
		)

		source_table_region, source_post_table = source_after_table_marker.split(
			_BOTTOM_PANELS_MARKER, 1
		)
		deployed_table_region, deployed_post_table = deployed_after_table_marker.split(
			_BOTTOM_PANELS_MARKER, 1
		)

		# Everything through the Strategic Alignment card (i.e. up to the
		# Workbench Insights card) must stay pixel-identical. Past that
		# point, only the Insights card's insight-*items* content is allowed
		# to differ (heading stays static; items became two hidden-toggled
		# variants) — verified separately by the dedicated insights test
		# below, along with confirming the heading itself never changes.
		source_before_insights, source_after_insights_marker = source_post_table.split(
			_INSIGHTS_CARD_START_MARKER, 1
		)
		deployed_before_insights, deployed_after_insights_marker = deployed_post_table.split(
			_INSIGHTS_CARD_START_MARKER, 1
		)
		self.assertEqual(
			_BOTTOM_PANELS_MARKER + source_before_insights,
			_BOTTOM_PANELS_MARKER + deployed_before_insights,
			"Bottom panels through the Strategic Alignment card must stay pixel-identical to the design.",
		)

		source_heading_end = source_after_insights_marker.index("</h3>") + len("</h3>")
		deployed_heading_end = deployed_after_insights_marker.index("</h3>") + len("</h3>")
		self.assertEqual(
			source_after_insights_marker[:source_heading_end],
			deployed_after_insights_marker[:deployed_heading_end],
			"Workbench Insights heading (icon + text) must stay pixel-identical and queue-static.",
		)

		source_items_and_after = source_after_insights_marker[source_heading_end:].split(
			_INSIGHTS_CARD_CLOSE_MARKER, 1
		)
		self.assertEqual(
			len(source_items_and_after),
			2,
			"Could not locate the Insights card's closing tags in the source design.",
		)
		deployed_items_and_after = deployed_after_insights_marker[deployed_heading_end:].split(
			_INSIGHTS_CARD_CLOSE_MARKER, 1
		)
		self.assertEqual(
			len(deployed_items_and_after),
			2,
			"Could not locate the Insights card's closing tags in the deployed asset.",
		)
		self.assertEqual(
			_INSIGHTS_CARD_CLOSE_MARKER + source_items_and_after[1],
			_INSIGHTS_CARD_CLOSE_MARKER + deployed_items_and_after[1],
			"Everything from the Insights card's closing tags through the floating toolbar placeholder "
			"must stay pixel-identical to the design.",
		)

		# The needs-planning table+footer (source's only table region) must
		# be reproduced byte-identically inside its own toggle wrapper.
		# `source_table_region` still carries the design's own trailing
		# card-closing `</div>` (immediately after `</footer>`, since the
		# design has no toggle wrapper); strip it before comparing since the
		# wrapper's own surrounding whitespace/close-tag is this port's only
		# (invisible, block-level) structural addition.
		source_table_content = source_table_region.rsplit("</div>", 1)[0].strip("\n")
		deployed_needs_planning_section = _extract_section_by_testid(
			deployed_table_region, _NEEDS_PLANNING_TABLE_SECTION_TESTID
		).strip("\n")
		self.assertEqual(
			source_table_content,
			deployed_needs_planning_section,
			"Needs Planning table+footer must stay pixel-identical to the design once unwrapped from its toggle section.",
		)

		# Past the marker: source is still just the placeholder comment + the
		# design's own dead inline script (four hardcoded mock rows only);
		# deployed has the real, hidden-by-default toolbar markup and no
		# inline script (W5 drives it from pp2_planning_router.js instead).
		self.assertNotIn('id="selection-toolbar"', source_main_body)
		self.assertIn("Selection toolbar logic", source_main_body)
		self.assertIn('id="selection-toolbar"', deployed_main_body)
		self.assertNotIn("Selection toolbar logic", deployed_main_body)

	def test_deployed_package_table_section_matches_in_creation_design_verbatim(self) -> None:
		"""W6, then the UI-consistency pass — the package-row table (In
		Creation / Awaiting Review / Ready for Release share one table) is
		ported from the "3. In creation" design, hidden by default so the
		Needs Planning table (the default active tab) is the only one shown
		until the router toggles between them. The UI-consistency pass
		intentionally harmonizes the title-link color/weight, category-chip
		style, and rows-per-page control to the Needs-Planning canonical
		style instead of keeping them byte-identical to this one screen's
		own mockup (see WORKBENCH_WIRING_TRACKER.md); the column headers and
		the Linked-Demands/Est-Value/Readiness cells, which this pass does
		not touch, must still match the design verbatim."""
		in_creation_source = _in_creation_design_source_path()
		deployed = _deployed_design_path()
		self.assertTrue(in_creation_source.exists(), msg=f"missing {in_creation_source}")

		source_html = in_creation_source.read_text(encoding="utf-8")
		deployed_html = deployed.read_text(encoding="utf-8")

		source_table_start = source_html.index('<table class="workbench-table')
		source_thead_end = source_html.index("</thead>", source_table_start) + len("</thead>")
		source_thead = source_html[source_table_start:source_thead_end]

		deployed_package_section = _extract_section_by_testid(
			deployed_html, _PACKAGE_TABLE_SECTION_TESTID
		).strip("\n")
		self.assertIn(
			source_thead,
			deployed_package_section,
			"Column headers must stay pixel-identical to the design.",
		)

		# Cells this pass does not touch (Linked Demands / Est. Value /
		# Readiness) must remain byte-identical to the design, per sample row.
		unchanged_cell_snippets = (
			'<td class="py-4 px-4 text-center"><span class="font-body-sm font-bold">3</span></td>',
			'<td class="py-4 px-4"><div class="flex flex-col"><span class="text-[10px] text-on-surface-variant '
			'font-bold uppercase">KES</span><span class="font-headline-md text-primary">1.4B</span></div></td>',
			'<td class="py-4 px-6"><div class="flex items-center gap-2 px-3 py-1 bg-status-warning/10 '
			'text-status-warning rounded-full w-fit"><span class="material-symbols-outlined text-sm">'
			"hourglass_empty</span><span class=\"font-label-md font-bold text-xs\">In Progress</span></div></td>",
		)
		for snippet in unchanged_cell_snippets:
			self.assertIn(snippet, source_html, msg=f"fixture drifted from design: {snippet!r}")
			self.assertIn(snippet, deployed_package_section)

		# Title link: harmonized to the Needs-Planning canonical style (dark,
		# bold, only turns blue on hover) instead of the design's own
		# permanently-blue `text-secondary` anchor.
		self.assertIn(
			'<a class="font-body-md font-bold text-secondary hover:underline block truncate max-w-[300px]" '
			'href="#">MOH/GDS/001 - Diagnostic Tools</a>',
			source_html,
		)
		self.assertNotIn('font-bold text-secondary hover:underline block truncate', deployed_package_section)
		self.assertIn(
			'<a class="font-body-md font-bold text-primary hover:text-secondary hover:underline transition-colors '
			'block truncate max-w-[300px]" href="#">MOH/GDS/001 - Diagnostic Tools</a>',
			deployed_package_section,
		)

		# Category chip: harmonized dot+pill signature (Needs Planning style)
		# instead of the design's own dot-less uppercase-bold pill.
		self.assertIn(
			'<span class="px-3 py-1 bg-cat-goods/10 text-cat-goods rounded-full font-label-sm uppercase '
			'font-bold">Goods</span>',
			source_html,
		)
		self.assertIn(
			'<span class="px-2.5 py-1 rounded-full bg-cat-goods/10 text-cat-goods font-label-sm font-semibold '
			'flex items-center gap-1 w-fit"><span class="w-1.5 h-1.5 rounded-full bg-cat-goods"></span> Goods</span>',
			deployed_package_section,
		)

		# Rows-per-page control: harmonized to Needs Planning's
		# non-interactive div+arrow_drop_down, replacing the design's own
		# <select>+expand_more (confirmed decorative-only in the router).
		self.assertIn("<select", source_html)
		self.assertNotIn("<select", deployed_package_section)
		self.assertIn("arrow_drop_down", deployed_package_section)

		# Must be hidden by default (Needs Planning is the initial active tab).
		open_marker = f'data-testid="{_PACKAGE_TABLE_SECTION_TESTID}"'
		section_open_tag = deployed_html.split(open_marker, 1)[1].split(">", 1)[0]
		self.assertIn("hidden", section_open_tag)

	def _assert_review_release_or_blocked_section_matches_design(
		self,
		*,
		design_folder: str,
		section_testid: str,
		unchanged_cell_snippets: tuple[str, ...],
		sample_title: str,
		sample_category_tone: str,
		sample_category_label: str,
	) -> None:
		"""Remaining-queues pass (W7/W8), then the UI-consistency pass —
		Awaiting Review/Ready for Release and Blocked both originally ported
		a 7-column table (including a separate "Actions" column with an
		"Open" button) verbatim from their own design. The UI-consistency
		pass removes that Actions column (the title itself becomes the click
		target, Needs-Planning-style) and harmonizes the title/category-chip
		styling; the column headers (Actions aside) and the cells this pass
		does not touch (Linked/Est-Value/Review-Status/Readiness-or-Blocker
		-Reason) must still match the design verbatim."""
		design_source = _remaining_queue_design_source_path(design_folder)
		deployed = _deployed_design_path()
		self.assertTrue(design_source.exists(), msg=f"missing {design_source}")

		source_html = design_source.read_text(encoding="utf-8")
		deployed_html = deployed.read_text(encoding="utf-8")

		source_table_start = source_html.index('<table class="w-full text-left border-collapse min-w-[1100px]">')
		source_thead_end = source_html.index("</thead>", source_table_start) + len("</thead>")
		source_thead = source_html[source_table_start:source_thead_end]
		self.assertIn(
			'<th class="px-6 py-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider '
			'text-right pr-8">Actions</th>',
			source_thead,
		)
		source_thead_sans_actions = source_thead.replace(
			'\n<th class="px-6 py-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider '
			'text-right pr-8">Actions</th>',
			"",
		)

		deployed_section = _extract_section_by_testid(deployed_html, section_testid).strip("\n")
		self.assertIn(
			source_thead_sans_actions,
			deployed_section,
			f"{section_testid}'s column headers (Actions column aside) must stay pixel-identical to the design.",
		)
		self.assertNotIn(">Actions<", deployed_section)
		self.assertNotIn(">Open <", deployed_section)
		self.assertNotIn("group-hover:underline\">Open", deployed_section)

		for snippet in unchanged_cell_snippets:
			self.assertIn(snippet, source_html, msg=f"fixture drifted from design: {snippet!r}")
			self.assertIn(snippet, deployed_section)

		# Title: harmonized from a plain `<span>` (the design's own click
		# target was the row's "Open" button) into a real Needs-Planning
		# -style `<a>` — the title itself is now the click target.
		self.assertIn(
			f'<span class="font-bold text-primary group-hover:text-secondary transition-colors">{sample_title}</span>',
			source_html,
		)
		self.assertNotIn("group-hover:text-secondary transition-colors\">", deployed_section)
		self.assertIn(
			f'<a class="font-body-md font-bold text-primary hover:text-secondary hover:underline '
			f'transition-colors" href="#">{sample_title}</a>',
			deployed_section,
		)

		# Category chip: harmonized dot+pill signature (Needs Planning style)
		# instead of the design's own dot-less, non-rounded-full,
		# tracking-tighter uppercase chip.
		self.assertIn(
			f'<span class="bg-{sample_category_tone}/10 text-{sample_category_tone} font-label-md text-label-md '
			f'px-3 py-1 rounded uppercase tracking-tighter">{sample_category_label.upper()}</span>',
			source_html,
		)
		self.assertIn(
			f'<span class="px-2.5 py-1 rounded-full bg-{sample_category_tone}/10 text-{sample_category_tone} '
			f'font-label-sm font-semibold flex items-center gap-1 w-fit"><span class="w-1.5 h-1.5 rounded-full '
			f'bg-{sample_category_tone}"></span> {sample_category_label}</span>',
			deployed_section,
		)

		# The section must still carry a footer (reused shared markup, not a
		# second verbatim port), harmonized to the div+arrow_drop_down
		# rows-per-page control, and be hidden by default.
		self.assertIn("<footer", deployed_section)
		self.assertNotIn("<select", deployed_section)
		self.assertIn("arrow_drop_down", deployed_section)
		open_marker = f'data-testid="{section_testid}"'
		section_open_tag = deployed_html.split(open_marker, 1)[1].split(">", 1)[0]
		self.assertIn("hidden", section_open_tag)

	def test_deployed_review_release_table_section_matches_awaiting_review_design_verbatim(self) -> None:
		"""W7/W8 — Awaiting Review + Ready for Release share one table
		(confirmed byte-identical in their own source designs); this section
		is ported from "4. Awaiting review"."""
		self._assert_review_release_or_blocked_section_matches_design(
			design_folder="4. Awaiting review",
			section_testid=_REVIEW_RELEASE_TABLE_SECTION_TESTID,
			unchanged_cell_snippets=(
				'<td class="px-6 py-6 text-center">\n<div class="inline-flex items-center gap-2 '
				'text-on-surface-variant bg-surface-container-low px-3 py-1 rounded-full">\n<span '
				'class="material-symbols-outlined text-[16px]">link</span>\n<span class="font-label-md '
				'text-label-md">5</span>\n</div>\n</td>',
				'<td class="px-6 py-6 text-center">\n<span class="font-bold text-primary">KES 850M</span>\n</td>',
				'<td class="px-6 py-6 text-center"><span class="bg-secondary-container/10 text-secondary '
				'font-label-md text-label-md px-3 py-1 rounded uppercase tracking-tighter">Technical Review</span></td>',
				'<td class="px-6 py-6">\n<div class="flex flex-col items-center gap-1">\n<span '
				'class="material-symbols-outlined text-status-success text-[20px]">check_circle</span>\n<span '
				'class="bg-status-success/10 text-status-success font-label-md text-label-md px-2 py-0.5 '
				"rounded\">Passed</span>\n</div>\n</td>",
			),
			sample_title="MOH/GDS/010 - Medical Supplies",
			sample_category_tone="cat-goods",
			sample_category_label="Goods",
		)

	def test_review_release_table_column_structure_matches_across_its_two_source_designs(self) -> None:
		"""Confirms the sharing assumption above: "4. Awaiting review" and
		"5. Ready for release" ship the exact same table *column structure*
		(`<thead>`), which is what justifies one shared section/row-builder
		for both uiQueues — their sample `<tbody>` rows differ (different
		mock data per screen), which is expected and irrelevant since real
		rows are always rendered from live backend data, never these
		samples."""
		awaiting_review = _remaining_queue_design_source_path("4. Awaiting review").read_text(encoding="utf-8")
		ready_for_release = _remaining_queue_design_source_path("5. Ready for release").read_text(encoding="utf-8")
		prefix = '<table class="w-full text-left border-collapse min-w-[1100px]">'
		ar_start = awaiting_review.index(prefix)
		ar_thead = awaiting_review[ar_start : awaiting_review.index("</thead>", ar_start) + len("</thead>")]
		rr_start = ready_for_release.index(prefix)
		rr_thead = ready_for_release[rr_start : ready_for_release.index("</thead>", rr_start) + len("</thead>")]
		self.assertEqual(ar_thead, rr_thead)

	def test_deployed_blocked_table_section_matches_design_verbatim(self) -> None:
		self._assert_review_release_or_blocked_section_matches_design(
			design_folder="6. Blocked",
			section_testid=_BLOCKED_TABLE_SECTION_TESTID,
			unchanged_cell_snippets=(
				'<td class="px-6 py-6 text-center">\n<div class="inline-flex items-center gap-2 '
				'text-on-surface-variant bg-surface-container-low px-3 py-1 rounded-full">\n<span '
				'class="material-symbols-outlined text-[16px]">link</span>\n<span class="font-label-md '
				'text-label-md">5</span>\n</div>\n</td>',
				'<td class="px-6 py-6 text-center">\n<span class="font-bold text-primary">KES 850M</span>\n</td>',
				'<td class="px-6 py-6 text-center"><span class="bg-secondary-container/10 text-secondary '
				'font-label-md text-label-md px-3 py-1 rounded uppercase tracking-tighter">Technical Review</span></td>',
				'<td class="px-6 py-6"><div class="flex flex-col items-center gap-1"><span '
				'class="material-symbols-outlined text-status-error text-[20px]">error</span><span '
				'class="bg-status-error/10 text-status-error font-label-md text-label-md px-2 py-0.5 '
				'rounded">Insufficient Funding</span></div></td>',
			),
			sample_title="MOH/GDS/010 - Medical Supplies",
			sample_category_tone="cat-goods",
			sample_category_label="Goods",
		)

	def test_deployed_released_table_section_matches_design_verbatim(self) -> None:
		"""W8, then the UI-consistency pass — Released's table (5 columns:
		Title & Ref, Linked, Category, Est. Value, Tender Status) never had
		an "Actions" column (the title was already a real `<a>`), so this
		pass only harmonizes the title-link typography and category chip;
		the column headers and the Linked/Est-Value/Tender-Status cells,
		which this pass does not touch, must still match the design
		verbatim."""
		released_source = _remaining_queue_design_source_path("7. Released")
		deployed = _deployed_design_path()
		self.assertTrue(released_source.exists(), msg=f"missing {released_source}")

		source_html = released_source.read_text(encoding="utf-8")
		deployed_html = deployed.read_text(encoding="utf-8")

		source_table_start = source_html.index('<table class="w-full text-left border-collapse">')
		source_thead_end = source_html.index("</thead>", source_table_start) + len("</thead>")
		source_thead = source_html[source_table_start:source_thead_end]

		deployed_section = _extract_section_by_testid(deployed_html, _RELEASED_TABLE_SECTION_TESTID).strip("\n")
		self.assertIn(source_thead, deployed_section, "Column headers must stay pixel-identical to the design.")

		unchanged_cell_snippets = (
			'<div class="inline-flex items-center gap-2 text-on-surface-variant bg-surface-container-low px-3 '
			'py-1 rounded-full"><span class="material-symbols-outlined text-[16px]">link</span><span '
			'class="font-label-md text-label-md">5</span></div>',
			'<td class="px-6 py-6 text-center"><span class="font-bold text-primary">KES 850M</span></td>',
			'<td class="px-6 py-6 text-center"><span class="bg-status-success/10 text-status-success '
			'font-label-md text-label-md px-3 py-1 rounded uppercase tracking-tighter">Tender Created</span></td>',
		)
		for snippet in unchanged_cell_snippets:
			self.assertIn(snippet, source_html, msg=f"fixture drifted from design: {snippet!r}")
			self.assertIn(snippet, deployed_section)

		# Title: harmonized typography (adds `font-body-md` + `hover:underline`,
		# matching Needs Planning) on top of the design's already-real `<a>`.
		self.assertIn(
			'<a class="font-bold text-primary hover:text-secondary transition-colors" href="#">'
			"MOH/GDS/010 - Medical Supplies</a>",
			source_html,
		)
		self.assertIn(
			'<a class="font-body-md font-bold text-primary hover:text-secondary hover:underline '
			'transition-colors" href="#">MOH/GDS/010 - Medical Supplies</a>',
			deployed_section,
		)

		# Category chip: harmonized dot+pill signature (Needs Planning style).
		self.assertIn(
			'<span class="bg-cat-goods/10 text-cat-goods font-label-md text-label-md px-3 py-1 rounded '
			'uppercase tracking-tighter">GOODS</span>',
			source_html,
		)
		self.assertIn(
			'<span class="px-2.5 py-1 rounded-full bg-cat-goods/10 text-cat-goods font-label-sm font-semibold '
			'flex items-center gap-1 w-fit"><span class="w-1.5 h-1.5 rounded-full bg-cat-goods"></span> Goods</span>',
			deployed_section,
		)

		# The section must still carry a footer (reused shared markup, not a
		# second verbatim port), harmonized to the div+arrow_drop_down
		# rows-per-page control, and be hidden by default.
		self.assertIn("<footer", deployed_section)
		self.assertNotIn("<select", deployed_section)
		self.assertIn("arrow_drop_down", deployed_section)
		open_marker = f'data-testid="{_RELEASED_TABLE_SECTION_TESTID}"'
		section_open_tag = deployed_html.split(open_marker, 1)[1].split(">", 1)[0]
		self.assertIn("hidden", section_open_tag)

	def test_deployed_insights_variants_match_designs_verbatim(self) -> None:
		"""W7/W8 — the "Workbench Insights" heading stays static text for
		every queue (per direction); only the two insight-items blocks
		(default vs. Released's own copy) are hidden-toggled."""
		design_source = _design_source_path()
		released_source = _remaining_queue_design_source_path("7. Released")
		deployed = _deployed_design_path()

		source_html = design_source.read_text(encoding="utf-8")
		released_html = released_source.read_text(encoding="utf-8")
		deployed_html = deployed.read_text(encoding="utf-8")

		# Default variant must be a byte-identical port of the pristine
		# default design's own (only ever) insight-items block. Both sides
		# compare inner content only (the `<div ...>`/`</div>` wrapper tags
		# themselves differ: the source has no `data-testid`).
		source_items_div_start = source_html.index(
			'<div class="space-y-4">', source_html.index(_INSIGHTS_CARD_START_MARKER)
		)
		source_items_inner = _extract_div_inner_by_start(source_html, source_items_div_start)
		deployed_default_inner = _extract_section_by_testid(deployed_html, _INSIGHTS_DEFAULT_TESTID)
		self.assertEqual(
			source_items_inner,
			deployed_default_inner,
			"Default insight-items must be byte-identical (data-testid wrapper attribute aside).",
		)

		# Released variant must be a byte-identical port of "7. Released"'s
		# own insight-items block (heading excluded from the port).
		released_heading_marker = (
			'<h3 class="font-headline-md text-headline-md text-primary flex items-center gap-2 mb-4">'
			'<span class="material-symbols-outlined text-secondary">trending_up</span> Released Insights</h3>\n'
		)
		released_items_div_start = released_html.index(
			'<div class="space-y-4">', released_html.index(released_heading_marker)
		)
		released_items_inner = _extract_div_inner_by_start(released_html, released_items_div_start)
		released_items_full = released_html[
			released_items_div_start : released_items_div_start
			+ len('<div class="space-y-4">')
			+ len(released_items_inner)
			+ len("</div>")
		]

		deployed_released_inner = _extract_section_by_testid(deployed_html, _INSIGHTS_RELEASED_TESTID)
		# The deployed Released variant wraps its ported content in its own
		# `<div class="space-y-4">...</div>` (matching the source's own
		# structure verbatim, one level deeper than the `data-testid` div).
		self.assertEqual(
			released_items_full,
			deployed_released_inner,
			"Released insight-items must be a byte-identical port of the '7. Released' design.",
		)

		# Released variant must be hidden by default (every queue except
		# Released shows the default variant on initial load).
		open_marker = f'data-testid="{_INSIGHTS_RELEASED_TESTID}"'
		section_open_tag = deployed_html.split(open_marker, 1)[1].split(">", 1)[0]
		self.assertIn("hidden", section_open_tag)

		# The heading itself must never change: only the literal "Workbench
		# Insights" text appears in the deployed asset, never "Released
		# Insights" or any other per-queue variant.
		self.assertIn("Workbench Insights", deployed_html)
		self.assertNotIn("Released Insights", deployed_html)
