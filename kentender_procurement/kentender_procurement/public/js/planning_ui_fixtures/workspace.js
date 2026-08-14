// PLN-UI-01 — literal Stitch <main> from docs/mvp-1/04_planning/ui_design/PLN-UI-01.html
// Fake top/side nav discarded; kt-stitch-canvas + testids/bind hooks only.
// Shared Desk table footer appended (kentender-stitch-desk-table-footer).
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_workspace = function () {
	var footerHtml =
		window.kentender_core &&
		kentender_core.ui_fixtures &&
		typeof kentender_core.ui_fixtures.tablePaginationFooterHtml === "function"
			? kentender_core.ui_fixtures.tablePaginationFooterHtml({
					ns: "kt",
					testid: "kt-pln-ui01-table-footer",
			  })
			: "";

	return `<div class="kt-pln-root kt-stitch-canvas" data-testid="kt-pln-ui01-root">
<main class="flex-1 p-container-padding md:p-section-gap flex flex-col gap-section-gap max-w-[1400px] mx-auto w-full">
<div class="flex flex-col md:flex-row md:items-start justify-between gap-gutter-md" data-testid="kt-pln-ui01-header">
<div class="flex-1 max-w-2xl">
<h1 class="font-headline-lg text-headline-lg text-on-surface mb-stack-xs">Procurement Planning</h1>
<p class="font-body-md text-body-md text-on-surface-variant">Turn approved needs into funded, approved Plan Items ready for tendering.</p>
</div>
<div class="flex-shrink-0 flex items-start gap-4 flex-col sm:flex-row w-full md:w-auto" data-testid="kt-pln-ui01-header-actions">
<button type="button" class="w-full sm:w-auto bg-primary text-on-primary font-body-md px-6 py-2.5 rounded-lg hover:bg-primary-container-low shadow-sm transition-colors flex justify-center items-center gap-2 whitespace-nowrap" data-kt-pln-action="open-plan" data-testid="kt-pln-ui01-open-plan">
Open current plan <span class="material-symbols-outlined text-[20px]" aria-hidden="true">arrow_forward</span>
</button>
</div>
</div>
<div class="bg-surface-container-lowest border border-border-subtle rounded-lg p-container-padding flex flex-col gap-stack-sm" data-testid="kt-pln-ui01-filters">
<div class="flex flex-col md:flex-row gap-gutter-md items-end">
<div class="flex-1 w-full flex flex-col gap-1">
<label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-filter-pe">Procuring Entity</label>
<div class="relative">
<select id="kt-pln-filter-pe" class="w-full appearance-none bg-surface border border-border-subtle rounded-DEFAULT px-3 py-2 pr-10 font-body-md text-on-surface focus:outline-none focus:border-secondary focus:ring-2 focus:ring-secondary/20 transition-all" data-kt-pln-filter="procuring_entity" aria-label="Procuring Entity"></select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none" aria-hidden="true">expand_more</span>
</div>
</div>
<div class="w-full md:w-64 flex flex-col gap-1">
<label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-filter-fy">Financial Year</label>
<div class="relative">
<select id="kt-pln-filter-fy" class="w-full appearance-none bg-surface border border-border-subtle rounded-DEFAULT px-3 py-2 pr-10 font-body-md text-on-surface focus:outline-none focus:border-secondary focus:ring-2 focus:ring-secondary/20 transition-all" data-kt-pln-filter="financial_year" aria-label="Financial Year"></select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none" aria-hidden="true">expand_more</span>
</div>
</div>
</div>
<p class="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-1.5 mt-1" data-testid="kt-pln-ui01-scope-helper" data-kt-pln-scope-helper>
<span class="material-symbols-outlined text-[16px]" aria-hidden="true">info</span>
<span data-kt-pln-helper-text>These controls define the workspace scope; they do not assign ownership to records.</span>
</p>
</div>
<div class="bg-status-exhausted/10 border border-status-exhausted/20 rounded-lg p-4 hidden" data-testid="kt-pln-ui01-blocked" data-kt-pln-blocked hidden role="alert">
<p class="font-headline-sm text-headline-sm text-status-exhausted mb-1">Planning workspace blocked</p>
<p class="font-body-md text-body-md text-on-surface" data-kt-pln-blocked-msg>An authorised Procuring Entity assignment is required.</p>
</div>
<div class="bg-surface-container-lowest border border-border-subtle rounded-lg p-container-padding flex flex-col md:flex-row items-start md:items-center justify-between gap-gutter-md border-l-4 border-l-primary" data-testid="kt-pln-ui01-plan-panel" data-kt-pln-plan-panel>
<div class="min-w-0 flex-1">
<h2 class="font-headline-sm text-headline-sm text-on-surface mb-2 whitespace-normal" data-kt-pln-plan-title>Ministry of Health Annual Procurement Plan 2027/28</h2>
<div class="flex flex-wrap items-center gap-x-4 gap-y-2 font-body-sm text-body-sm text-on-surface-variant" data-kt-pln-plan-meta>
<span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-status-available" data-kt-pln-plan-lifecycle-dot aria-hidden="true"></span><span data-kt-pln-plan-lifecycle>Open</span></span>
<span class="text-outline-variant" aria-hidden="true">•</span>
<span data-kt-pln-plan-version>Draft Version 1</span>
<span class="text-outline-variant" aria-hidden="true">•</span>
<span><span class="font-data-md text-data-md text-on-surface" data-kt-pln-plan-items>0</span> Plan Items</span>
<span class="text-outline-variant" aria-hidden="true">•</span>
<span data-kt-pln-plan-money><span class="font-data-md text-data-md text-on-surface" data-kt-pln-plan-total-amount>KES 0</span> planned</span>
<span class="text-outline-variant" aria-hidden="true">•</span>
<span class="flex items-center gap-1"><span class="material-symbols-outlined text-[16px]" data-kt-pln-plan-validation-icon aria-hidden="true">warning</span> Validation: <span data-kt-pln-plan-validation>Not run</span></span>
</div>
<p class="font-body-md text-body-md text-on-surface-variant mt-3 hidden" data-kt-pln-no-plan data-testid="kt-pln-ui01-no-plan">
<span data-kt-pln-no-plan-msg>No plan registered for this Procuring Entity and financial year.</span>
<button type="button" class="font-body-sm text-body-sm text-primary font-medium no-underline ml-1" data-kt-pln-action="register" data-testid="kt-pln-ui01-register">Create annual plan</button>
</p>
</div>
<button type="button" class="shrink-0 border border-border-subtle text-primary bg-surface hover:bg-surface-container-low font-body-md px-4 py-2 rounded-DEFAULT transition-colors whitespace-nowrap" data-kt-pln-action="continue-plan" data-testid="kt-pln-ui01-continue">
Continue planning
</button>
</div>
<div class="bg-surface-container-lowest border border-border-subtle rounded-lg flex flex-col overflow-hidden" data-testid="kt-pln-ui01-queue">
<div class="p-container-padding border-b border-border-subtle bg-surface-bright flex flex-col sm:flex-row items-center justify-between gap-gutter-md">
<h3 class="font-headline-sm text-headline-sm text-on-surface m-0">Work Requiring Action</h3>
<div class="flex items-center gap-3 w-full sm:w-auto">
<div class="relative w-full sm:w-64">
<select class="w-full appearance-none bg-surface border border-border-subtle rounded-DEFAULT px-3 py-1.5 pr-8 font-body-sm text-on-surface focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/50 transition-all" data-kt-pln-filter="work_type" data-testid="kt-pln-ui01-work-filter" aria-label="Work type">
<option value="all">All work</option>
<option value="approved_demands">Approved Demands</option>
<option value="returned_by_finance">Plan Items returned by Finance</option>
<!-- PLN-FR-040 / PLN-GAP-UI-003: REQ queue filter (Stitch UI-01 omits this option). -->
<option value="awaiting_finance">Awaiting Finance confirmation</option>
<option value="needs_attention">Plan Items needing attention</option>
</select>
<span class="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none text-[18px]" aria-hidden="true">arrow_drop_down</span>
</div>
<div class="relative w-full sm:w-64">
<span class="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-[18px] text-on-surface-variant" aria-hidden="true">search</span>
<input class="w-full pl-9 pr-3 py-1.5 bg-surface border border-border-subtle rounded-DEFAULT font-body-sm text-on-surface focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/50 transition-all" placeholder="Search work..." type="text" data-kt-pln-work-search data-testid="kt-pln-ui01-work-search" aria-label="Search work"/>
</div>
</div>
</div>
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse" data-testid="kt-pln-ui01-table">
<thead>
<tr class="border-b border-border-subtle bg-surface-container-low font-label-caps text-label-caps text-on-surface-variant">
<th class="p-3 whitespace-nowrap font-medium">Work Item</th>
<th class="p-3 whitespace-nowrap font-medium">Organisation Unit</th>
<th class="p-3 whitespace-nowrap font-medium text-right">Amount</th>
<th class="p-3 whitespace-nowrap font-medium">Reason</th>
<th class="p-3 whitespace-nowrap font-medium">Status</th>
<th class="p-3 whitespace-nowrap font-medium text-right">Action</th>
</tr>
</thead>
<tbody class="font-body-sm text-on-surface divide-y divide-border-subtle" data-kt-pln-queue-body></tbody>
</table>
${footerHtml}
</div>
</div>
</main>
</div>`;
};
