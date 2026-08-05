// BUD-UI-08 — Revisions tab list only (create is budget-revision-create page).
frappe.provide("kentender_budget.ui_fixtures");

kentender_budget.ui_fixtures.revisions = function () {
	var footerHtml =
		window.kentender_core &&
		kentender_core.ui_fixtures &&
		typeof kentender_core.ui_fixtures.tablePaginationFooterHtml === "function"
			? kentender_core.ui_fixtures.tablePaginationFooterHtml({
					ns: "kt",
					testid: "kt-bud-revisions-table-footer",
			  })
			: "";

	return `<div class="kt-bud-root kt-stitch-canvas" data-testid="kt-bud-revisions" data-kt-bud-rev-mode="list">
<!-- Workspace chrome injected by budget_workspace_shell -->
<div class="flex-1 p-container-padding max-w-[1400px] mx-auto w-full" data-testid="kt-bud-revisions-list" data-kt-bud-revisions-list>
<div class="kt-bud-rev-notice hidden" data-testid="kt-bud-rev-notice" data-kt-bud-rev-notice hidden role="status" aria-live="polite">
<span class="material-symbols-outlined kt-bud-rev-notice-icon" aria-hidden="true">info</span>
<div class="kt-bud-rev-notice-body">
<p class="kt-bud-rev-notice-title" data-kt-bud-rev-notice-title></p>
<p class="kt-bud-rev-notice-msg" data-kt-bud-rev-notice-msg></p>
</div>
<button type="button" class="kt-bud-rev-notice-dismiss" data-testid="kt-bud-rev-notice-dismiss" data-kt-bud-rev-notice-dismiss aria-label="Dismiss">
<span class="material-symbols-outlined" aria-hidden="true">close</span>
</button>
</div>

<div class="kt-bud-rev-table-card" data-testid="kt-bud-revisions-table-card">
<div class="overflow-x-auto table-scroll">
<table class="w-full text-left border-collapse min-w-[960px]" data-testid="kt-bud-revisions-table">
<thead>
<tr class="bg-surface-container-low border-b border-outline-variant text-xs text-on-surface-variant uppercase tracking-wider font-semibold font-label-caps">
<th class="px-4 py-3">Revision</th>
<th class="px-4 py-3">External reference</th>
<th class="px-4 py-3">Status</th>
<th class="px-4 py-3 text-right">Net change</th>
<th class="px-4 py-3">Effective date</th>
<th class="px-4 py-3">Reason</th>
<th class="px-4 py-3 text-right">Action</th>
</tr>
</thead>
<tbody class="divide-y divide-outline-variant/60 font-body-md text-sm" data-testid="kt-bud-revisions-tbody" data-kt-bud-revisions-tbody>
<tr data-kt-bud-rev-empty>
<td colspan="7" class="px-4 py-8 text-center text-on-surface-variant">Loading revisions…</td>
</tr>
</tbody>
</table>
</div>
${footerHtml}
</div>
</div>
</div>`;
};
