// BUD-UI-10 — Stitch Downstream Usage (downstream_usage_…/code.html).
// Fake sidenav / duplicate H1 / Export discarded; workspace chrome from shell.
frappe.provide("kentender_budget.ui_fixtures");

kentender_budget.ui_fixtures.downstream = function () {
	var footerHtml =
		window.kentender_core &&
		kentender_core.ui_fixtures &&
		typeof kentender_core.ui_fixtures.tablePaginationFooterHtml === "function"
			? kentender_core.ui_fixtures.tablePaginationFooterHtml({
					ns: "kt",
					testid: "kt-bud-downstream-table-footer",
			  })
			: "";

	return `<div class="kt-bud-root kt-stitch-canvas" data-testid="kt-bud-downstream">
<!-- Workspace chrome injected by budget_workspace_shell -->
<div class="flex-1 p-container-padding max-w-[1600px] mx-auto w-full" data-testid="kt-bud-downstream-canvas">
<div class="kt-bud-downstream-toolbar" data-testid="kt-bud-downstream-toolbar">
<div class="kt-bud-downstream-toolbar-search" data-testid="kt-bud-downstream-search-wrap">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">Search</label>
<div class="kt-bud-downstream-search-field">
<span class="material-symbols-outlined" aria-hidden="true">search</span>
<input type="text" placeholder="Filter by Requirement..." aria-label="Filter by requirement" data-testid="kt-bud-downstream-search" data-kt-bud-downstream-search />
</div>
</div>
<div class="kt-bud-downstream-toolbar-filters">
<div class="kt-bud-downstream-filter-field" data-kt-bud-downstream-filter-field="status">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">Status</label>
<div class="kt-bud-downstream-select-wrap">
<select aria-label="Status" data-testid="kt-bud-downstream-filter-status" data-kt-bud-downstream-filter="status">
<option value="">All statuses</option>
<option value="Partially converted">Partially converted</option>
<option value="Reserved">Reserved</option>
<option value="Converted">Converted</option>
<option value="Released">Released</option>
</select>
<span class="material-symbols-outlined" aria-hidden="true">expand_more</span>
</div>
</div>
</div>
</div>

<div class="kt-bud-downstream-notice hidden" data-testid="kt-bud-downstream-notice" data-kt-bud-downstream-notice hidden role="status" aria-live="polite">
<span class="material-symbols-outlined kt-bud-downstream-notice-icon" aria-hidden="true">info</span>
<div class="kt-bud-downstream-notice-body">
<p class="kt-bud-downstream-notice-title" data-kt-bud-downstream-notice-title></p>
<p class="kt-bud-downstream-notice-msg" data-kt-bud-downstream-notice-msg></p>
</div>
<button type="button" class="kt-bud-downstream-notice-dismiss" data-testid="kt-bud-downstream-notice-dismiss" data-kt-bud-downstream-notice-dismiss aria-label="Dismiss">
<span class="material-symbols-outlined" aria-hidden="true">close</span>
</button>
</div>

<div class="kt-bud-downstream-table-card" data-testid="kt-bud-downstream-table-card">
<div class="overflow-x-auto table-scroll" data-testid="kt-bud-downstream-table-scroll">
<table class="w-full text-left border-collapse min-w-[1200px]" data-testid="kt-bud-downstream-table">
<thead>
<tr class="bg-surface-container-low border-b border-outline-variant text-xs text-on-surface-variant uppercase tracking-wider font-semibold font-label-caps">
<th class="px-4 py-3">Requirement</th>
<th class="px-4 py-3 kt-bud-down-phase">Demand</th>
<th class="px-4 py-3">Procurement plan item</th>
<th class="px-4 py-3 kt-bud-down-phase">Tender</th>
<th class="px-4 py-3">Contract</th>
<th class="px-4 py-3 text-right kt-bud-down-phase">Reserved balance</th>
<th class="px-4 py-3 text-right">Commitment</th>
<th class="px-4 py-3 kt-bud-down-phase">Status</th>
<th class="px-4 py-3 text-right">Action</th>
</tr>
</thead>
<tbody class="divide-y divide-outline-variant/60 font-body-md text-sm" data-testid="kt-bud-downstream-tbody" data-kt-bud-downstream-tbody>
<tr data-kt-bud-downstream-empty>
<td colspan="9" class="px-4 py-8 text-center text-on-surface-variant">Loading downstream usage…</td>
</tr>
</tbody>
</table>
</div>
${footerHtml}
</div>
</div>
</div>`;
};
