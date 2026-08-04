// BUD-UI-01 — Stitch main canvas from ui_design/budget_funding/code.html
// Fake top/side nav discarded; surgical data-kt-bud-* hooks only.
frappe.provide("kentender_budget.ui_fixtures");

kentender_budget.ui_fixtures.portfolio = function () {
	var footerHtml =
		window.kentender_core &&
		kentender_core.ui_fixtures &&
		typeof kentender_core.ui_fixtures.tablePaginationFooterHtml === "function"
			? kentender_core.ui_fixtures.tablePaginationFooterHtml({
					ns: "kt",
					testid: "kt-bud-table-footer",
			  })
			: "";

	return `<div class="kt-bud-root kt-stitch-canvas" data-testid="kt-bud-portfolio">
<div class="max-w-7xl mx-auto p-container-padding md:p-section-gap space-y-section-gap">
<div class="flex flex-col md:flex-row md:items-start justify-between gap-4" data-testid="kt-bud-pf-header">
<div class="max-w-2xl">
<h1 class="font-headline-lg text-headline-lg-mobile md:text-headline-lg text-on-surface mb-2">Budget &amp; Funding</h1>
<p class="font-body-lg text-body-lg text-on-surface-variant">Manage approved procurement funding and monitor its use across the procurement lifecycle.</p>
</div>
<div class="flex flex-col sm:flex-row gap-3 shrink-0">
<button type="button" data-kt-bud-action="open-performance" data-testid="kt-bud-open-performance" class="px-4 py-2 rounded-lg border border-outline text-on-surface font-body-md text-body-md hover:bg-surface-container-highest transition-colors flex items-center justify-center gap-2">
<span class="material-symbols-outlined text-sm">monitoring</span>
View funding performance
</button>
<button type="button" data-kt-bud-action="register-budget" data-testid="kt-bud-register-budget" class="px-4 py-2 rounded-lg bg-primary text-on-primary font-body-md text-body-md hover:bg-primary-container hover:text-on-primary-container transition-colors shadow-sm flex items-center justify-center gap-2">
<span class="material-symbols-outlined text-sm">add</span>
Register approved budget
</button>
</div>
</div>
<div class="grid grid-cols-2 md:grid-cols-4 gap-gutter" data-testid="kt-bud-summary-strip">
<div class="bg-status-available/10 border border-status-available/20 border-l-[3px] border-l-status-available p-3 flex items-center justify-between">
<span class="font-body-md text-body-md text-on-surface-variant">Active budgets</span>
<span class="font-headline-sm text-headline-sm text-status-available" data-kt-bud-count="active">—</span>
</div>
<div class="bg-status-reserved/10 border border-status-reserved/20 border-l-[3px] border-l-status-reserved p-3 flex items-center justify-between">
<span class="font-body-md text-body-md text-on-surface-variant">Awaiting review</span>
<span class="font-headline-sm text-headline-sm text-status-reserved" data-kt-bud-count="awaiting_review">—</span>
</div>
<div class="bg-surface-container-lowest border border-outline-variant p-3 flex items-center justify-between opacity-70">
<span class="font-body-md text-body-md text-on-surface-variant">Returned</span>
<span class="font-headline-sm text-headline-sm text-on-surface" data-kt-bud-count="returned">—</span>
</div>
<div class="bg-status-exhausted/10 border border-status-exhausted/20 border-l-[3px] border-l-status-exhausted p-3 flex items-center justify-between">
<span class="font-body-md text-body-md text-status-exhausted font-medium">Funding exceptions</span>
<span class="font-headline-md text-headline-md text-status-exhausted font-bold" data-kt-bud-count="funding_exceptions">—</span>
</div>
</div>
<div class="bg-surface-container-lowest border border-outline-variant rounded-lg p-card-padding flex flex-col md:flex-row gap-4 items-end shadow-sm" data-testid="kt-bud-pf-filters">
<div class="flex-1 w-full relative">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">Search</label>
<div class="relative">
<span class="material-symbols-outlined absolute left-3 top-2 text-on-surface-variant">search</span>
<input class="w-full pl-10 pr-4 py-2 bg-surface border border-outline-variant rounded-lg text-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none" placeholder="Search by budget title or external approval reference" type="text" aria-label="Search budgets" data-kt-bud-filter="search">
</div>
</div>
<div class="flex flex-wrap gap-4 w-full md:w-auto">
<div class="w-full sm:w-auto">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">Fiscal Period</label>
<select class="w-full sm:w-40 px-3 py-2 bg-surface border border-outline-variant rounded-lg text-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none appearance-none" aria-label="Fiscal period" data-kt-bud-filter="fiscal_period">
<option value="">All Periods</option>
<option value="2027/28">FY 2027/28</option>
<option value="2028/29">FY 2028/29</option>
<option value="2026/27">FY 2026/27</option>
</select>
</div>
<div class="w-full sm:w-auto">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">Status</label>
<select class="w-full sm:w-32 px-3 py-2 bg-surface border border-outline-variant rounded-lg text-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none appearance-none" aria-label="Status" data-kt-bud-filter="status">
<option value="">All Statuses</option>
<option value="Active">Active</option>
<option value="Under review">Under review</option>
<option value="Returned">Returned</option>
<option value="Draft">Draft</option>
<option value="Closed">Closed</option>
</select>
</div>
<div class="w-full sm:w-auto">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase tracking-wider">Source</label>
<select class="w-full sm:w-40 px-3 py-2 bg-surface border border-outline-variant rounded-lg text-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none appearance-none" aria-label="Source" data-kt-bud-filter="registration_source">
<option value="">All Sources</option>
<option value="Direct capture">Direct capture</option>
</select>
</div>
</div>
</div>
<div data-kt-bud-table-wrap="1" data-testid="kt-bud-table-wrap" class="bg-surface-container-lowest border border-outline-variant rounded-lg overflow-hidden shadow-sm">
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse" data-testid="kt-bud-budgets-table">
<thead>
<tr class="bg-surface-container-low border-b border-outline-variant">
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase whitespace-nowrap w-80">Budget</th>
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase whitespace-nowrap w-24">Fiscal Period</th>
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase whitespace-nowrap w-40">Source</th>
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase whitespace-nowrap text-right w-32">Approved</th>
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase whitespace-nowrap text-right w-32">Available</th>
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase whitespace-nowrap w-32">Status</th>
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase whitespace-nowrap w-64">Attention</th>
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase whitespace-nowrap text-right">Action</th>
</tr>
</thead>
<tbody class="font-body-md text-body-md divide-y divide-outline-variant/50" data-kt-bud-budgets-tbody="1">
<tr data-kt-bud-loading="1"><td class="px-4 py-6 text-on-surface-variant" colspan="8">Loading budgets…</td></tr>
</tbody>
</table>
</div>
${footerHtml}
</div>
<div data-kt-bud-empty="1" data-testid="kt-bud-empty" class="hidden bg-surface-container-lowest border border-outline-variant border-dashed rounded-lg p-section-gap flex flex-col items-center justify-center text-center py-16">
<div class="w-16 h-16 bg-surface-container rounded-full flex items-center justify-center text-on-surface-variant mb-4">
<span class="material-symbols-outlined text-3xl">account_balance_wallet</span>
</div>
<h3 class="font-headline-sm text-headline-sm text-on-surface mb-2">No budgets found</h3>
<p class="font-body-md text-body-md text-on-surface-variant max-w-md mb-6">No procurement budget has been registered for this fiscal period or matches your search criteria.</p>
<button type="button" data-kt-bud-action="register-budget" data-testid="kt-bud-empty-register" class="px-4 py-2 rounded-lg bg-primary text-on-primary font-body-md text-body-md hover:bg-primary-container hover:text-on-primary-container transition-colors shadow-sm flex items-center gap-2">
<span class="material-symbols-outlined text-sm">add</span>
Register approved budget
</button>
</div>
</div>
</div>`;
};
