// PLN-UI-01 — literal Stitch <main> from docs/mvp-1/04_planning/ui_design/PLN-UI-01.html
// Fake top/side nav discarded; kt-stitch-canvas + testids/bind hooks only.
// PE/FY filter band uses Stitch utility classes (live bind; not in static Stitch mock).
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
<main class="flex-1 overflow-y-auto bg-background p-container-padding md:p-section-gap relative z-0">
<div class="flex flex-col md:flex-row md:justify-between md:items-start gap-4 mb-section-gap" data-testid="kt-pln-ui01-header">
<div>
<p class="font-label-caps text-label-caps text-on-surface-variant uppercase mb-1" data-kt-pln-context-label>Ministry of Health | 2027/28</p>
<h1 class="font-headline-lg text-headline-lg text-on-surface mb-2">Procurement Planning</h1>
<p class="font-body-md text-body-md text-on-surface-variant">Turn approved and funded needs into an approved annual procurement plan.</p>
</div>
<div class="flex flex-col sm:flex-row items-start sm:items-center gap-4" data-testid="kt-pln-ui01-header-actions">
<button type="button" class="bg-primary text-on-primary font-body-sm text-body-sm font-semibold px-4 py-2 rounded-lg hover:bg-primary-container transition-colors whitespace-nowrap shadow-sm shadow-primary/10" data-kt-pln-action="open-plan" data-testid="kt-pln-ui01-open-plan">
Open current plan
</button>
</div>
</div>
<div class="flex flex-wrap items-end gap-3 w-full bg-surface-container-lowest p-4 rounded-lg border border-subtle shadow-sm mb-section-gap" data-testid="kt-pln-ui01-filters">
<div class="w-full sm:w-auto min-w-[200px]">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1.5" for="kt-pln-filter-pe">Procuring Entity</label>
<div class="relative">
<select id="kt-pln-filter-pe" class="w-full appearance-none bg-surface-container-lowest border border-outline-variant rounded-lg py-2 pl-3 pr-10 font-body-md text-body-md text-on-surface focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-all h-10" data-kt-pln-filter="procuring_entity" aria-label="Procuring Entity"></select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none" aria-hidden="true">expand_more</span>
</div>
</div>
<div class="w-full sm:w-auto min-w-[160px]">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1.5" for="kt-pln-filter-fy">Financial year</label>
<div class="relative">
<select id="kt-pln-filter-fy" class="w-full appearance-none bg-surface-container-lowest border border-outline-variant rounded-lg py-2 pl-3 pr-10 font-body-md text-body-md text-on-surface focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-all h-10" data-kt-pln-filter="financial_year" aria-label="Financial year"></select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none" aria-hidden="true">expand_more</span>
</div>
</div>
</div>
<div class="bg-status-exhausted/10 border border-status-exhausted/20 rounded-lg p-4 mb-section-gap hidden" data-testid="kt-pln-ui01-blocked" data-kt-pln-blocked hidden role="alert">
<p class="font-headline-sm text-headline-sm text-status-exhausted mb-1">Planning workspace blocked</p>
<p class="font-body-md text-body-md text-on-surface" data-kt-pln-blocked-msg>An authorised Procuring Entity assignment is required.</p>
</div>
<div class="bg-surface-container-lowest border border-subtle rounded-lg p-6 mb-section-gap shadow-sm" data-testid="kt-pln-ui01-plan-panel" data-kt-pln-plan-panel>
<div class="flex justify-between items-start mb-6 border-b border-subtle pb-4">
<div class="flex items-center gap-3 flex-wrap">
<h2 class="font-headline-md text-headline-md text-on-surface" data-kt-pln-plan-title>Ministry of Health Annual Procurement Plan 2027/28</h2>
<span class="bg-surface-container text-on-surface font-label-caps text-label-caps px-2 py-1 rounded-full border border-subtle" data-kt-pln-plan-lifecycle>Draft</span>
</div>
<button type="button" class="border border-subtle text-primary font-body-sm text-body-sm font-semibold px-4 py-2 rounded-lg hover:bg-surface-container-low transition-colors" data-kt-pln-action="continue-plan" data-testid="kt-pln-ui01-continue">
Continue planning
</button>
</div>
<div class="grid grid-cols-1 md:grid-cols-4 gap-6">
<div>
<p class="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Plan Items</p>
<p class="font-data-lg text-data-lg text-primary" data-kt-pln-plan-items>0</p>
</div>
<div>
<p class="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Planned Total</p>
<p class="font-data-lg text-data-lg text-primary" data-kt-pln-plan-total>KES 0</p>
</div>
<div>
<p class="font-label-caps text-label-caps mb-1 uppercase text-status-reserved">Validation</p>
<div class="flex items-center gap-2 mt-2">
<span class="material-symbols-outlined text-outline text-[18px]" aria-hidden="true">rule</span>
<p class="font-body-sm text-body-sm text-status-reserved" data-kt-pln-plan-validation>Not run</p>
</div>
</div>
<div>
<p class="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Contributions</p>
<p class="font-body-md text-body-md mt-1 text-secondary" data-kt-pln-plan-contributions data-kt-pln-plan-version>0 of 1 submitted</p>
</div>
</div>
<p class="font-body-md text-body-md text-on-surface-variant mt-4 hidden" data-kt-pln-no-plan data-testid="kt-pln-ui01-no-plan">
<span data-kt-pln-no-plan-msg>No plan registered for this Procuring Entity and financial year.</span>
<button type="button" class="font-body-sm text-body-sm text-primary font-medium no-underline ml-1" data-kt-pln-action="register" data-testid="kt-pln-ui01-register">Create annual plan</button>
</p>
</div>
<div class="bg-surface-container-lowest border border-subtle rounded-lg shadow-sm overflow-hidden" data-testid="kt-pln-ui01-queue">
<div class="p-4 border-b border-subtle flex flex-col gap-4 bg-surface-container-low/30">
<h3 class="font-headline-sm text-headline-sm text-on-surface">Work Requiring Action</h3>
<div class="flex gap-4 flex-wrap" role="tablist" aria-label="Work filters">
<a class="font-label-caps text-label-caps text-primary border-b-2 border-primary pb-1" href="#" data-kt-pln-work-filter="all" data-testid="kt-pln-ui01-filter-all">All work</a>
<a class="font-label-caps text-label-caps text-on-surface-variant hover:text-on-surface transition-colors pb-1" href="#" data-kt-pln-work-filter="approved_demands" data-testid="kt-pln-ui01-filter-approved">Approved Demands</a>
<a class="font-label-caps text-label-caps text-on-surface-variant hover:text-on-surface transition-colors pb-1" href="#" data-kt-pln-work-filter="returned" data-testid="kt-pln-ui01-filter-returned">Returned</a>
<a class="font-label-caps text-label-caps text-on-surface-variant hover:text-on-surface transition-colors pb-1" href="#" data-kt-pln-work-filter="needs_attention" data-testid="kt-pln-ui01-filter-attention">Needs attention</a>
<a class="font-label-caps text-label-caps text-on-surface-variant hover:text-on-surface transition-colors pb-1" href="#" data-kt-pln-work-filter="approved_not_started" data-testid="kt-pln-ui01-filter-not-started">Approved not started</a>
</div>
</div>
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse" data-testid="kt-pln-ui01-table">
<thead>
<tr class="border-b border-subtle bg-surface-container-low/50">
<th class="font-label-caps text-label-caps text-on-surface-variant p-4 font-semibold uppercase tracking-wider">Work item</th>
<th class="font-label-caps text-label-caps text-on-surface-variant p-4 font-semibold uppercase tracking-wider">Organisation Unit</th>
<th class="font-label-caps text-label-caps text-on-surface-variant p-4 font-semibold uppercase tracking-wider text-right">Amount</th>
<th class="font-label-caps text-label-caps text-on-surface-variant p-4 font-semibold uppercase tracking-wider">Reason</th>
<th class="font-label-caps text-label-caps text-on-surface-variant p-4 font-semibold uppercase tracking-wider">Status</th>
<th class="font-label-caps text-label-caps text-on-surface-variant p-4 font-semibold uppercase tracking-wider text-right">Action</th>
</tr>
</thead>
<tbody class="divide-y divide-subtle" data-kt-pln-queue-body></tbody>
</table>
${footerHtml}
</div>
</div>
</main>
</div>`;
};
