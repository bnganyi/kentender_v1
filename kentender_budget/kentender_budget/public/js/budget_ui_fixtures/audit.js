// BUD-UI-12 — Stitch Audit History (audit_history_…/code.html).
// Fake sidenav / duplicate H1 discarded. Export lives in workspace chrome (Stitch header).
frappe.provide("kentender_budget.ui_fixtures");

kentender_budget.ui_fixtures.audit = function () {
	var footerHtml =
		window.kentender_core &&
		kentender_core.ui_fixtures &&
		typeof kentender_core.ui_fixtures.tablePaginationFooterHtml === "function"
			? kentender_core.ui_fixtures.tablePaginationFooterHtml({
					ns: "kt",
					testid: "kt-bud-audit-table-footer",
			  })
			: "";

	return `<div class="kt-bud-root kt-stitch-canvas" data-testid="kt-bud-audit">
<!-- Workspace chrome injected by budget_workspace_shell (Export in header per Stitch) -->
<div class="flex-1 p-container-padding max-w-[1600px] mx-auto w-full" data-testid="kt-bud-audit-canvas">
<div class="kt-bud-audit-toolbar" data-testid="kt-bud-audit-toolbar">
<div class="kt-bud-audit-toolbar-filters">
<div class="kt-bud-audit-filter-field" data-kt-bud-audit-filter-field="event_type">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">Event Type</label>
<div class="kt-bud-audit-select-wrap">
<select aria-label="Event type" data-testid="kt-bud-audit-filter-event" data-kt-bud-audit-filter="event_type">
<option value="">All Events</option>
</select>
<span class="material-symbols-outlined" aria-hidden="true">expand_more</span>
</div>
</div>
<div class="kt-bud-audit-filter-field" data-kt-bud-audit-filter-field="actor">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">User or Integration</label>
<div class="kt-bud-audit-select-wrap">
<select aria-label="User or integration" data-testid="kt-bud-audit-filter-actor" data-kt-bud-audit-filter="actor">
<option value="">All Sources</option>
</select>
<span class="material-symbols-outlined" aria-hidden="true">expand_more</span>
</div>
</div>
<div class="kt-bud-audit-filter-field" data-kt-bud-audit-filter-field="date_range">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">Date Range</label>
<div class="kt-bud-audit-date-range">
<input type="date" class="kt-bud-audit-date" aria-label="Date from" data-testid="kt-bud-audit-filter-date-from" data-kt-bud-audit-filter="date_from" />
<span class="kt-bud-audit-date-range-sep" aria-hidden="true">–</span>
<input type="date" class="kt-bud-audit-date" aria-label="Date to" data-testid="kt-bud-audit-filter-date-to" data-kt-bud-audit-filter="date_to" />
</div>
</div>
</div>
</div>

<div class="kt-bud-audit-notice hidden" data-testid="kt-bud-audit-notice" data-kt-bud-audit-notice hidden role="status" aria-live="polite">
<span class="material-symbols-outlined kt-bud-audit-notice-icon" aria-hidden="true">info</span>
<div class="kt-bud-audit-notice-body">
<p class="kt-bud-audit-notice-title" data-kt-bud-audit-notice-title></p>
<p class="kt-bud-audit-notice-msg" data-kt-bud-audit-notice-msg></p>
</div>
<button type="button" class="kt-bud-audit-notice-dismiss" data-testid="kt-bud-audit-notice-dismiss" data-kt-bud-audit-notice-dismiss aria-label="Dismiss">
<span class="material-symbols-outlined" aria-hidden="true">close</span>
</button>
</div>

<div class="kt-bud-audit-table-card" data-testid="kt-bud-audit-table-card">
<div class="overflow-x-auto table-scroll" data-testid="kt-bud-audit-table-scroll">
<table class="w-full text-left border-collapse min-w-[1200px]" data-testid="kt-bud-audit-table">
<thead>
<tr class="bg-surface-container-low border-b border-outline-variant text-xs text-on-surface-variant uppercase tracking-wider font-semibold font-label-caps">
<th class="px-4 py-3">Date and time</th>
<th class="px-4 py-3">Event</th>
<th class="px-4 py-3">Record</th>
<th class="px-4 py-3">User or integration</th>
<th class="px-4 py-3">Before and after summary</th>
<th class="px-4 py-3">Source reference</th>
<th class="px-4 py-3 text-right">Action</th>
</tr>
</thead>
<tbody class="divide-y divide-outline-variant/60 font-body-md text-sm" data-testid="kt-bud-audit-tbody" data-kt-bud-audit-tbody>
<tr data-kt-bud-audit-empty>
<td colspan="7" class="px-4 py-8 text-center text-on-surface-variant">Loading audit history…</td>
</tr>
</tbody>
</table>
</div>
${footerHtml}
</div>
</div>
</div>`;
};
