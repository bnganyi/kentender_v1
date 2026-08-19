// BUD-UI-04 / BUD-UI-05 — Stitch Budget Lines table + Edit drawer
// (budget_lines_…/code.html + edit_budget_line_…/code.html).
// Fake sidenav / Stitch reference-label chrome discarded; workspace chrome injected by shell.
frappe.provide("kentender_budget.ui_fixtures");

kentender_budget.ui_fixtures.lines = function () {
	var footerHtml =
		window.kentender_core &&
		kentender_core.ui_fixtures &&
		typeof kentender_core.ui_fixtures.tablePaginationFooterHtml === "function"
			? kentender_core.ui_fixtures.tablePaginationFooterHtml({
					ns: "kt",
					testid: "kt-bud-lines-table-footer",
			  })
			: "";

	return `<div class="kt-bud-root kt-stitch-canvas" data-testid="kt-bud-lines">
<!-- Workspace chrome injected by budget_workspace_shell -->
<div class="flex-1 p-container-padding max-w-[1400px] mx-auto w-full" data-testid="kt-bud-lines-canvas">
<!-- Toolbar — search + Budget Source + Strategic Target + New Line -->
<div class="kt-bud-lines-toolbar" data-testid="kt-bud-lines-toolbar">
<div class="kt-bud-lines-toolbar-search" data-testid="kt-bud-lines-search-wrap">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">Search</label>
<div class="kt-bud-lines-search-field">
<span class="material-symbols-outlined" data-kt-bud-lines-search-icon aria-hidden="true">search</span>
<input type="text" placeholder="Search budget lines..." aria-label="Search budget lines" data-testid="kt-bud-lines-search" data-kt-bud-lines-search />
</div>
</div>
<div class="kt-bud-lines-toolbar-controls">
<div class="kt-bud-lines-filter-field" data-kt-bud-lines-filter-field="source">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">Budget Source</label>
<div class="kt-bud-lines-select-wrap">
<select aria-label="Budget Source" data-testid="kt-bud-lines-filter-source" data-kt-bud-lines-filter="funding_source">
<option value="">All sources</option>
<option value="Exchequer">Exchequer</option>
<option value="Own source">Own source</option>
<option value="Donor or grant">Donor or grant</option>
<option value="Other">Other</option>
</select>
<span class="material-symbols-outlined" aria-hidden="true">expand_more</span>
</div>
</div>
<div class="kt-bud-lines-filter-field" data-kt-bud-lines-filter-field="target">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">Strategic Target</label>
<div class="kt-bud-lines-select-wrap">
<select aria-label="Strategic Target" data-testid="kt-bud-lines-filter-target" data-kt-bud-lines-filter="primary_target">
<option value="">All targets</option>
</select>
<span class="material-symbols-outlined" aria-hidden="true">expand_more</span>
</div>
</div>
<button type="button" class="kt-bud-lines-new-btn" data-testid="kt-bud-lines-new" data-kt-bud-lines-new>
<span class="material-symbols-outlined" aria-hidden="true">add</span>
New Line
</button>
</div>
</div>
<!-- In-canvas governance notice (no Frappe Message dialog) -->
<div class="kt-bud-lines-notice hidden" data-testid="kt-bud-lines-notice" data-kt-bud-lines-notice hidden role="status" aria-live="polite">
<span class="material-symbols-outlined kt-bud-lines-notice-icon" aria-hidden="true">lock</span>
<div class="kt-bud-lines-notice-body">
<p class="kt-bud-lines-notice-title" data-kt-bud-lines-notice-title>Revision required</p>
<p class="kt-bud-lines-notice-msg" data-kt-bud-lines-notice-msg>Active budgets cannot add lines directly. Request a revision to change the baseline.</p>
</div>
<button type="button" class="kt-bud-lines-notice-cta" data-testid="kt-bud-lines-notice-cta" data-kt-bud-lines-notice-cta>Request revision</button>
<button type="button" class="kt-bud-lines-notice-dismiss" data-testid="kt-bud-lines-notice-dismiss" data-kt-bud-lines-notice-dismiss aria-label="Dismiss">
<span class="material-symbols-outlined" aria-hidden="true">close</span>
</button>
</div>
<!-- Table -->
<div class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden shadow-sm" data-testid="kt-bud-lines-table-card">
<div class="overflow-x-auto table-scroll" data-testid="kt-bud-lines-table-scroll">
<table class="w-full text-left border-collapse min-w-[1200px]" data-testid="kt-bud-lines-table">
<thead>
<tr class="bg-surface-container-low border-b border-outline-variant text-xs text-on-surface-variant uppercase tracking-wider font-semibold font-label-caps">
<th class="px-4 py-3 w-72">Budget line &amp; Source</th>
<th class="px-4 py-3">Strategic Target</th>
<th class="px-4 py-3 text-right">Approved</th>
<th class="px-4 py-3 text-right">Reserved</th>
<th class="px-4 py-3 text-right">Committed</th>
<th class="px-4 py-3 text-right">Available</th>
<th class="px-4 py-3 text-right">Actual</th>
<th class="px-4 py-3 w-48">Status / Notes</th>
<th class="px-4 py-3 w-36 text-right">Action</th>
</tr>
</thead>
<tbody class="divide-y divide-outline-variant/60 font-body-md text-sm" data-testid="kt-bud-lines-tbody" data-kt-bud-lines-tbody>
<tr data-kt-bud-lines-empty>
<td colspan="9" class="px-4 py-8 text-center text-on-surface-variant">Loading budget lines…</td>
</tr>
</tbody>
</table>
</div>
${footerHtml}
</div>
</div>

<!-- Edit drawer (Stitch 680px right panel) -->
<div class="kt-bud-lines-scrim" data-testid="kt-bud-line-drawer-scrim" data-kt-bud-line-drawer-scrim hidden></div>
<aside class="kt-bud-line-drawer" data-testid="kt-bud-line-drawer" data-kt-bud-line-drawer hidden aria-hidden="true">
<div class="flex items-center justify-between px-6 py-4 border-b border-outline-variant bg-surface-container-lowest" data-testid="kt-bud-line-drawer-header">
<h2 class="font-headline-md text-headline-md font-bold text-primary" data-kt-bud-line-drawer-title>Edit Budget Line</h2>
<button type="button" aria-label="Close panel" class="p-2 rounded-full text-on-surface-variant hover:bg-surface-container-low transition-colors cursor-pointer" data-testid="kt-bud-line-drawer-close" data-kt-bud-line-drawer-close>
<span class="material-symbols-outlined">close</span>
</button>
</div>
<div class="flex-1 overflow-y-auto px-6 py-6 custom-scrollbar space-y-section-gap" data-testid="kt-bud-line-drawer-body">
<!-- Funding -->
<section data-testid="kt-bud-line-section-funding">
<div class="flex items-center gap-2 mb-4 pb-2 border-b border-outline-variant">
<span class="material-symbols-outlined text-primary text-[20px]">account_balance</span>
<h3 class="font-headline-sm text-headline-sm font-semibold text-primary">Funding details</h3>
</div>
<div class="mb-6 space-y-2">
<div class="bg-surface-container-low border border-outline-variant rounded-lg p-3 flex items-center gap-2 text-on-surface-variant">
<span class="material-symbols-outlined text-[18px]">info</span>
<span class="text-body-md">Funding details imported from the authoritative financial system.</span>
</div>
<div class="text-on-surface-variant text-[12px] font-data-mono px-1">Generated reference: <span data-kt-bud-line-field="code">—</span></div>
</div>
<div class="grid grid-cols-1 md:grid-cols-2 gap-y-6 gap-x-8">
<div class="space-y-4">
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Budget line title</label>
<input type="text" class="w-full font-body-lg text-body-lg text-on-surface font-medium bg-surface-container-low py-2 px-3 rounded border border-outline-variant" data-kt-bud-line-input="title" data-testid="kt-bud-line-title" />
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Approved amount</label>
<input type="text" class="w-full font-data-mono text-data-mono text-primary font-bold bg-primary-fixed/20 py-2 px-3 rounded border border-outline-variant" data-kt-bud-line-input="approved_amount" data-testid="kt-bud-line-approved" />
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Funding source</label>
<div class="relative">
<select class="w-full bg-surface border border-outline-variant rounded-lg py-2 px-3 text-body-md text-on-surface focus:ring-2 focus:ring-primary focus:outline-none appearance-none" data-kt-bud-line-input="funding_source_type" data-testid="kt-bud-line-funding-type">
<option value="Exchequer">Exchequer</option>
<option value="Own source">Own source</option>
<option value="Donor or grant">Donor or grant</option>
<option value="Other">Other</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-on-surface-variant">expand_more</span>
</div>
</div>
</div>
<div class="space-y-4">
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">External financial line reference</label>
<input type="text" class="w-full font-data-mono text-data-mono text-on-surface bg-surface-container-low py-2 px-3 rounded border border-outline-variant" data-kt-bud-line-input="external_financial_line_reference" data-testid="kt-bud-line-external-ref" />
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Financial classification</label>
<div class="relative">
<select class="w-full bg-surface border border-outline-variant rounded-lg py-2 px-3 text-body-md text-on-surface focus:ring-2 focus:ring-primary focus:outline-none appearance-none" data-kt-bud-line-input="classification" data-testid="kt-bud-line-classification">
<option value="Capital expenditure">Capital expenditure</option>
<option value="Goods">Goods</option>
<option value="Works">Works</option>
<option value="Services">Services</option>
<option value="Consultancy">Consultancy</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-on-surface-variant">expand_more</span>
</div>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Responsible owner</label>
<input type="text" class="w-full bg-surface border border-outline-variant rounded-lg py-2 px-3 text-body-md text-on-surface" data-kt-bud-line-input="organisational_owner" data-testid="kt-bud-line-owner" />
<p class="mt-1 text-body-sm text-on-surface-variant" data-kt-bud-line-ownership-path data-testid="kt-bud-line-ownership-path"></p>
</div>
</div>
</div>
</section>
<!-- Strategy -->
<section data-testid="kt-bud-line-section-strategy">
<div class="flex items-center gap-2 mb-4 pb-2 border-b border-outline-variant">
<span class="material-symbols-outlined text-primary text-[20px]">track_changes</span>
<h3 class="font-headline-sm text-headline-sm font-semibold text-primary">Strategy alignment</h3>
</div>
<div class="space-y-4">
<div class="space-y-1">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Primary strategic target</label>
<div class="relative">
<select class="w-full bg-surface border border-outline-variant rounded-lg py-2 px-3 text-body-lg text-on-surface font-medium focus:ring-2 focus:ring-primary focus:outline-none appearance-none" data-kt-bud-line-input="primary_target" data-testid="kt-bud-line-primary-target" data-kt-bud-field="primary_target">
<option value="">Select Active target…</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-on-surface-variant">expand_more</span>
</div>
<div class="font-data-mono text-[12px] text-on-surface-variant px-1" data-kt-bud-line-field="primary_target_code">—</div>
<p class="hidden text-body-sm text-error px-1" data-kt-bud-error="primary_target" data-testid="kt-bud-line-primary-target-error" role="alert"></p>
</div>
<div data-testid="kt-bud-line-supporting-list" data-kt-bud-line-supporting-list class="space-y-3"></div>
<button type="button" class="flex items-center gap-2 px-4 py-2 rounded-lg border border-outline-variant font-label-caps text-label-caps text-primary hover:bg-surface-container transition-colors" data-testid="kt-bud-line-add-supporting" data-kt-bud-line-add-supporting>
<span class="material-symbols-outlined text-[18px]">add</span>
Add supporting target
</button>
</div>
</section>
<!-- PVC -->
<section data-testid="kt-bud-line-section-pvc">
<div class="flex items-center gap-2 mb-4 pb-2 border-b border-outline-variant">
<span class="material-symbols-outlined text-primary text-[20px]">fact_check</span>
<h3 class="font-headline-sm text-headline-sm font-semibold text-primary">Strategy Value Commitment treatment</h3>
</div>
<div class="space-y-4" data-testid="kt-bud-line-pvc-list" data-kt-bud-line-pvc-list></div>
</section>
<div class="h-8"></div>
</div>
<div class="kt-bud-line-drawer-footer sticky bottom-0 bg-surface-container-lowest border-t border-outline-variant px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4 z-10" data-testid="kt-bud-line-drawer-footer">
<div class="flex flex-col gap-2 w-full md:w-auto" data-testid="kt-bud-line-validation">
<div class="flex items-center gap-6 bg-surface p-3 rounded-lg border border-outline-variant">
<div class="flex flex-col">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase text-[10px]">Approved amount</span>
<span class="font-data-mono text-data-mono text-on-surface text-[13px]" data-kt-bud-line-field="approved_compact">—</span>
</div>
<div class="text-outline-variant font-light">-</div>
<div class="flex flex-col">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase text-[10px]">Dedicated treatments</span>
<span class="font-data-mono text-data-mono text-status-committed text-[13px]" data-kt-bud-line-field="dedicated_compact">—</span>
</div>
<div class="text-outline-variant font-light">=</div>
<div class="flex flex-col border-l border-outline-variant pl-4">
<span class="font-label-caps text-label-caps text-primary uppercase text-[10px] font-bold">Not dedicated</span>
<span class="font-data-mono text-data-mono text-primary font-bold text-[14px]" data-kt-bud-line-field="not_dedicated_compact">—</span>
</div>
</div>
<p class="text-[12px] text-on-surface-variant italic px-1">Dedicated treatment is a designation within this budget line; it is not the line’s Available funding balance.</p>
</div>
<div class="flex items-center gap-3 w-full md:w-auto justify-end">
<button type="button" class="px-5 py-2.5 rounded-lg border border-transparent font-label-caps text-label-caps text-on-surface-variant hover:bg-surface-container transition-colors" data-testid="kt-bud-line-cancel" data-kt-bud-line-cancel>Cancel</button>
<button type="button" class="px-5 py-2.5 rounded-lg bg-primary text-on-primary font-label-caps text-label-caps hover:bg-primary/90 transition-colors shadow-sm flex items-center gap-2" data-testid="kt-bud-line-save" data-kt-bud-line-save>
<span class="material-symbols-outlined text-[18px]">save</span>
Save budget line
</button>
<button type="button" class="px-5 py-2.5 rounded-lg border border-outline text-primary font-label-caps text-label-caps hover:bg-surface-container-low transition-colors hidden" data-testid="kt-bud-line-request-revision" data-kt-bud-line-request-revision>Request revision</button>
</div>
</div>
</aside>
</div>`;
};
