// BUD-UI-07 — Stitch Funding Activity (funding_activity_…/code.html).
// Fake sidenav / partial tabs discarded; workspace chrome injected by shell.
frappe.provide("kentender_budget.ui_fixtures");

kentender_budget.ui_fixtures.activity = function () {
	var footerHtml =
		window.kentender_core &&
		kentender_core.ui_fixtures &&
		typeof kentender_core.ui_fixtures.tablePaginationFooterHtml === "function"
			? kentender_core.ui_fixtures.tablePaginationFooterHtml({
					ns: "kt",
					testid: "kt-bud-activity-table-footer",
			  })
			: "";

	return `<div class="kt-bud-root kt-stitch-canvas" data-testid="kt-bud-activity">
<!-- Workspace chrome injected by budget_workspace_shell -->
<div class="flex-1 p-container-padding max-w-[1400px] mx-auto w-full" data-testid="kt-bud-activity-canvas">
<!-- Balance strip -->
<div class="kt-bud-activity-strip" data-testid="kt-bud-activity-strip">
<div class="kt-bud-activity-strip-cell">
<p class="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">Reserved</p>
<p class="font-data-mono text-data-mono text-on-surface font-bold text-lg" data-kt-bud-activity-bal="reserved">—</p>
</div>
<div class="kt-bud-activity-strip-divider" aria-hidden="true"></div>
<div class="kt-bud-activity-strip-cell">
<p class="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">Committed</p>
<p class="font-data-mono text-data-mono text-status-committed font-bold text-lg" data-kt-bud-activity-bal="committed">—</p>
</div>
<div class="kt-bud-activity-strip-divider" aria-hidden="true"></div>
<div class="kt-bud-activity-strip-cell">
<p class="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">Actual</p>
<p class="font-data-mono text-data-mono text-status-available font-bold text-lg" data-kt-bud-activity-bal="actual">—</p>
</div>
<div class="kt-bud-activity-strip-divider" aria-hidden="true"></div>
<div class="kt-bud-activity-strip-cell">
<p class="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">Outstanding commitment</p>
<p class="font-data-mono text-data-mono text-status-reserved font-bold text-lg" data-kt-bud-activity-bal="outstanding">—</p>
</div>
</div>

<!-- Toolbar — search left, filters right (Lines pattern) -->
<div class="kt-bud-activity-toolbar" data-testid="kt-bud-activity-toolbar">
<div class="kt-bud-activity-toolbar-search" data-testid="kt-bud-activity-search-wrap">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">Search</label>
<div class="kt-bud-activity-search-field">
<span class="material-symbols-outlined" data-kt-bud-activity-search-icon aria-hidden="true">search</span>
<input type="text" placeholder="Search activity..." aria-label="Search activity" data-testid="kt-bud-activity-search" data-kt-bud-activity-search />
</div>
</div>
<div class="kt-bud-activity-toolbar-filters">
<div class="kt-bud-activity-filter-field" data-kt-bud-activity-filter-field="type">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">Activity type</label>
<div class="kt-bud-activity-select-wrap">
<select aria-label="Activity type" data-testid="kt-bud-activity-filter-type" data-kt-bud-activity-filter="activity_type">
<option value="">All types</option>
<option value="reservation">Reservation</option>
<option value="commitment">Commitment</option>
<option value="actual">Actual</option>
</select>
<span class="material-symbols-outlined" aria-hidden="true">expand_more</span>
</div>
</div>
<div class="kt-bud-activity-filter-field" data-kt-bud-activity-filter-field="status">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">Status</label>
<div class="kt-bud-activity-select-wrap">
<select aria-label="Status" data-testid="kt-bud-activity-filter-status" data-kt-bud-activity-filter="status">
<option value="">All statuses</option>
<option value="Partially converted">Partially converted</option>
<option value="Active">Active</option>
<option value="Matched">Matched</option>
<option value="Stale">Stale</option>
<option value="Reserved">Reserved</option>
</select>
<span class="material-symbols-outlined" aria-hidden="true">expand_more</span>
</div>
</div>
<div class="kt-bud-activity-filter-field" data-kt-bud-activity-filter-field="date">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">Date from</label>
<input type="date" class="kt-bud-activity-date" aria-label="Date from" data-testid="kt-bud-activity-filter-date" data-kt-bud-activity-filter="date_from" />
</div>
</div>
</div>

<!-- In-canvas notice / read-only detail -->
<div class="kt-bud-activity-notice hidden" data-testid="kt-bud-activity-notice" data-kt-bud-activity-notice hidden role="status" aria-live="polite">
<span class="material-symbols-outlined kt-bud-activity-notice-icon" aria-hidden="true">info</span>
<div class="kt-bud-activity-notice-body">
<p class="kt-bud-activity-notice-title" data-kt-bud-activity-notice-title></p>
<p class="kt-bud-activity-notice-msg" data-kt-bud-activity-notice-msg></p>
</div>
<button type="button" class="kt-bud-activity-notice-dismiss" data-testid="kt-bud-activity-notice-dismiss" data-kt-bud-activity-notice-dismiss aria-label="Dismiss">
<span class="material-symbols-outlined" aria-hidden="true">close</span>
</button>
</div>

<!-- Table -->
<div class="kt-bud-activity-table-card" data-testid="kt-bud-activity-table-card">
<div class="overflow-x-auto table-scroll" data-testid="kt-bud-activity-table-scroll">
<table class="w-full text-left border-collapse min-w-[1100px]" data-testid="kt-bud-activity-table">
<thead>
<tr class="bg-surface-container-low border-b border-outline-variant text-xs text-on-surface-variant uppercase tracking-wider font-semibold font-label-caps">
<th class="px-4 py-3">Activity</th>
<th class="px-4 py-3">Source record</th>
<th class="px-4 py-3 text-right">Amount</th>
<th class="px-4 py-3">Current status</th>
<th class="px-4 py-3">Event date</th>
<th class="px-4 py-3">Related record</th>
<th class="px-4 py-3 text-right">Action</th>
</tr>
</thead>
<tbody class="divide-y divide-outline-variant/60 font-body-md text-sm" data-testid="kt-bud-activity-tbody" data-kt-bud-activity-tbody>
<tr data-kt-bud-activity-empty>
<td colspan="7" class="px-4 py-8 text-center text-on-surface-variant">Loading funding activity…</td>
</tr>
</tbody>
</table>
</div>
${footerHtml}
</div>
</div>
</div>`;
};
