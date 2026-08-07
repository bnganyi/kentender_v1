// DEM-UI-01 — Stitch main canvas from docs/mvp-1/03_demands/ui_design/DEM-UI-01.html
// Fake top/side nav discarded; surgical data-kt-dem-* hooks only.
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.demands_workspace = function () {
	var footerHtml =
		window.kentender_core &&
		kentender_core.ui_fixtures &&
		typeof kentender_core.ui_fixtures.tablePaginationFooterHtml === "function"
			? kentender_core.ui_fixtures.tablePaginationFooterHtml({
					ns: "kt",
					testid: "kt-dem-ui01-table-footer",
			  })
			: "";

	return `<div class="kt-dem-root kt-stitch-canvas" data-testid="kt-dem-ui01-root">
<div class="max-w-[1400px] mx-auto p-container-padding md:p-section-gap flex flex-col gap-6 w-full">
<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4" data-testid="kt-dem-ui01-header">
<div>
<h1 class="font-headline-lg-mobile md:font-headline-lg text-headline-lg-mobile md:text-headline-lg text-on-surface mb-1">Demands</h1>
<p class="font-body-md text-body-md text-on-surface-variant">Capture, review and fund business needs before Procurement Planning.</p>
</div>
<button type="button" class="bg-primary text-on-primary font-body-md text-body-md font-medium py-2.5 px-5 rounded-lg flex items-center gap-2 hover:bg-primary/90 transition-colors shrink-0 shadow-sm whitespace-nowrap" data-kt-dem-action="create" data-testid="kt-dem-ui01-create">
<span class="material-symbols-outlined text-[20px]">add</span>
Create demand
</button>
</div>
<div class="flex flex-wrap items-center gap-x-8 gap-y-3 py-3 border-b border-outline-variant w-full overflow-x-auto pb-4" data-testid="kt-dem-ui01-summary">
<button type="button" class="flex items-center gap-2 group cursor-pointer" data-kt-dem-queue="my_drafts" data-testid="kt-dem-ui01-queue-my_drafts">
<span class="w-2 h-2 rounded-full bg-outline" aria-hidden="true"></span>
<span class="font-label-caps text-label-caps text-on-surface-variant group-hover:text-primary transition-colors">My drafts — <span data-kt-dem-count="my_drafts">0</span></span>
</button>
<button type="button" class="flex items-center gap-2 group cursor-pointer" data-kt-dem-queue="returned_to_me" data-testid="kt-dem-ui01-queue-returned_to_me">
<span class="w-2 h-2 rounded-full bg-status-exhausted" aria-hidden="true"></span>
<span class="font-label-caps text-label-caps text-on-surface-variant group-hover:text-primary transition-colors">Returned to me — <span data-kt-dem-count="returned_to_me">0</span></span>
</button>
<button type="button" class="flex items-center gap-2 group cursor-pointer" data-kt-dem-queue="my_approvals" data-testid="kt-dem-ui01-queue-my_approvals">
<span class="w-2 h-2 rounded-full bg-status-reserved" aria-hidden="true"></span>
<span class="font-label-caps text-label-caps text-on-surface-variant group-hover:text-primary transition-colors">My approvals — <span data-kt-dem-count="my_approvals">0</span></span>
</button>
<button type="button" class="flex items-center gap-2 group cursor-pointer" data-kt-dem-queue="budget_confirmations" data-testid="kt-dem-ui01-queue-budget_confirmations">
<span class="w-2 h-2 rounded-full bg-status-available" aria-hidden="true"></span>
<span class="font-label-caps text-label-caps text-on-surface-variant group-hover:text-primary transition-colors">Budget confirmations — <span data-kt-dem-count="budget_confirmations">0</span></span>
</button>
</div>
<div class="flex flex-wrap items-end gap-3 w-full bg-surface-container-lowest p-4 rounded-xl border border-outline-variant shadow-sm" data-testid="kt-dem-ui01-filters">
<div class="flex-1 min-w-[200px]">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1.5 ml-1">Search</label>
<div class="relative">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[18px]">search</span>
<input class="w-full bg-surface border border-outline-variant rounded-lg py-2 pl-9 pr-3 font-body-md text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary h-10 transition-colors" placeholder="Reference or Title" type="text" data-kt-dem-filter="search" aria-label="Search demands">
</div>
</div>
<div class="w-full sm:w-auto min-w-[160px]">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1.5 ml-1">Entity</label>
<select class="w-full bg-surface border border-outline-variant rounded-lg py-2 pl-3 pr-8 font-body-md text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary h-10 appearance-none transition-colors" data-kt-dem-filter="entity" aria-label="Entity">
<option value="">All entities</option>
</select>
</div>
<div class="w-full sm:w-auto min-w-[140px]">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1.5 ml-1">Status</label>
<select class="w-full bg-surface border border-outline-variant rounded-lg py-2 pl-3 pr-8 font-body-md text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary h-10 appearance-none transition-colors" data-kt-dem-filter="status" aria-label="Status">
<option value="">All Statuses</option>
<option value="Draft">Draft</option>
<option value="In Review">In review</option>
<option value="Returned">Returned</option>
<option value="Approved">Approved</option>
<option value="Cancelled">Cancelled</option>
</select>
</div>
<div class="w-full sm:w-auto min-w-[150px]">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1.5 ml-1">Stage</label>
<select class="w-full bg-surface border border-outline-variant rounded-lg py-2 pl-3 pr-8 font-body-md text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary h-10 appearance-none transition-colors" data-kt-dem-filter="stage" aria-label="Stage">
<option value="">All Stages</option>
<option value="Request Preparation">Request preparation</option>
<option value="Business Review">Business review</option>
<option value="Procurement Enrichment">Procurement enrichment</option>
<option value="Budget Confirmation">Budget confirmation</option>
<option value="Final Approval">Final approval</option>
<option value="Approved">Approved</option>
<option value="Complete">Complete</option>
</select>
</div>
<button type="button" class="h-10 px-4 font-label-caps text-label-caps text-primary hover:bg-surface-container-low rounded-lg transition-colors ml-auto sm:ml-0 flex items-center justify-center whitespace-nowrap" data-kt-dem-action="clear-filters" data-testid="kt-dem-ui01-clear-filters">
Clear filters
</button>
</div>
<div data-kt-dem-table-wrap="1" data-testid="kt-dem-ui01-table-wrap" class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden shadow-sm">
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse min-w-[1000px]" data-testid="kt-dem-ui01-table">
<thead>
<tr class="bg-surface-container-low border-b border-outline-variant">
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant font-semibold min-w-[300px]">Demand</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant font-semibold min-w-[200px]">Owning unit</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant font-semibold">Required by</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant font-semibold text-right">Estimate</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant font-semibold">Status</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant font-semibold">Current stage</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant font-semibold">Current owner</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant font-semibold text-right">Action</th>
</tr>
</thead>
<tbody class="divide-y divide-outline-variant" data-kt-dem-tbody="1">
<tr data-kt-dem-loading="1"><td class="py-6 px-4 font-body-md text-body-md text-on-surface-variant" colspan="8">Loading demands…</td></tr>
</tbody>
</table>
</div>
${footerHtml}
</div>
<div data-kt-dem-empty="1" data-testid="kt-dem-ui01-empty" class="hidden bg-surface-container-lowest border border-outline-variant rounded-xl p-12 flex-col items-center justify-center text-center shadow-sm">
<div class="w-16 h-16 bg-surface-container-low rounded-full flex items-center justify-center mb-4">
<span class="material-symbols-outlined text-outline text-[32px]">filter_list_off</span>
</div>
<h3 class="font-headline-sm text-headline-sm text-on-surface mb-2">No Demands match these filters</h3>
<p class="font-body-md text-body-md text-on-surface-variant mb-6 max-w-md">Try adjusting your search criteria, selecting a different entity, or clearing active filters to see more results.</p>
<button type="button" class="bg-surface-container-low text-on-surface font-label-caps text-label-caps py-2 px-4 rounded-lg border border-outline-variant hover:bg-surface-container-high transition-colors" data-kt-dem-action="clear-filters" data-testid="kt-dem-ui01-empty-clear">
Clear filters
</button>
</div>
</div>
</div>`;
};
