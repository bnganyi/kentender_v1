// PLN-UI-03 empty (Stitch v1.9 literal) + PLN-UI-05 populated (Stitch v1.9 literal).
// Fake top/side nav and in-canvas breadcrumbs discarded (Desk chrome owns crumbs).
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_builder = function () {
	return `<div class="kt-pln-root kt-stitch-canvas relative" data-testid="kt-pln-ui03-root" data-kt-pln-builder-state="empty">
<main class="flex-1 overflow-y-auto bg-surface-bright pb-24 relative" data-testid="kt-pln-ui03-main">
<div class="max-w-7xl mx-auto p-container-padding lg:p-section-gap space-y-section-gap">
<div data-testid="kt-pln-ui03-header">
<div class="flex flex-col md:flex-row md:items-start justify-between gap-4">
<div>
<h1 class="font-headline-lg text-headline-lg text-on-surface mb-1" data-kt-pln-builder-title>Ministry of Health Annual Procurement Plan 2027/28</h1>
<p class="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-2">
<span class="inline-flex items-center rounded-full bg-status-reserved/10 px-2 py-0.5 text-xs font-medium text-status-reserved ring-1 ring-inset ring-status-reserved/20" data-kt-pln-builder-lifecycle data-testid="kt-pln-ui03-lifecycle">Open Plan</span>
<span aria-hidden="true">·</span>
<span data-kt-pln-builder-version>Draft Version 1</span>
<span data-kt-pln-builder-period-sep aria-hidden="true">·</span>
<span data-kt-pln-builder-period>1 July 2027 – 30 June 2028</span>
</p>
</div>
<div class="flex-shrink-0">
<button type="button" class="bg-primary hover:bg-on-primary-fixed-variant text-on-primary font-body-sm text-body-sm font-medium py-2 px-4 rounded-lg shadow-sm transition-colors flex items-center gap-2" data-kt-pln-action="add-demand" data-testid="kt-pln-ui03-add-demand-header">
<span class="material-symbols-outlined text-sm" aria-hidden="true" style="font-variation-settings: 'FILL' 1;">add</span>
Add approved Demand
</button>
</div>
</div>
</div>
<header class="hidden" data-testid="kt-pln-ui05-header" hidden>
<div class="flex flex-col md:flex-row md:justify-between md:items-end gap-4">
<div>
<h1 class="font-headline-lg text-headline-lg text-on-surface mb-stack-xs" data-kt-pln-builder-title>Ministry of Health Annual Procurement Plan 2027/28</h1>
<p class="font-body-md text-body-md text-on-surface-variant flex items-center gap-2">
<span class="inline-block w-2 h-2 rounded-full bg-status-reserved" aria-hidden="true"></span>
<span data-kt-pln-builder-lifecycle data-testid="kt-pln-ui05-lifecycle">Open Plan</span>
<span aria-hidden="true">·</span>
<span data-kt-pln-builder-version>Draft Version 1</span>
</p>
</div>
<button type="button" class="bg-primary text-on-primary px-6 py-2.5 rounded font-label-caps text-label-caps hover:bg-surface-tint transition-colors flex items-center shadow-sm" data-kt-pln-action="add-demand" data-testid="kt-pln-ui05-add-demand">
<span class="material-symbols-outlined mr-2" aria-hidden="true">add</span> Add approved demands
</button>
</div>
</header>
<div class="bg-surface-container-lowest border border-subtle rounded-lg p-4 flex flex-row items-center justify-between shadow-sm" data-testid="kt-pln-ui03-summary">
<div class="flex flex-col">
<span class="font-label-caps text-label-caps text-on-surface-variant mb-1">Plan Items</span>
<span class="font-data-md text-data-md text-on-surface" data-kt-pln-builder-items>0</span>
</div>
<div class="h-8 w-px bg-border-subtle hidden md:block" aria-hidden="true"></div>
<div class="flex flex-col">
<span class="font-label-caps text-label-caps text-on-surface-variant mb-1">Total Planned Value</span>
<span class="font-data-lg text-data-lg text-primary" data-kt-pln-builder-total>KES 0</span>
</div>
<div class="h-8 w-px bg-border-subtle hidden md:block" aria-hidden="true"></div>
<div class="flex flex-col">
<span class="font-label-caps text-label-caps text-on-surface-variant mb-1">Finance Confirmed</span>
<span class="font-data-md text-data-md text-on-surface" data-kt-pln-builder-finance data-testid="kt-pln-ui03-finance">0 of 0</span>
</div>
<div class="h-8 w-px bg-border-subtle hidden md:block" aria-hidden="true"></div>
<div class="flex flex-col">
<span class="font-label-caps text-label-caps text-on-surface-variant mb-1">Validation Status</span>
<span class="inline-flex items-center px-2 py-1 rounded bg-surface-container-high text-on-surface-variant font-label-caps text-label-caps w-fit border border-subtle" data-kt-pln-builder-validation data-testid="kt-pln-ui05-validation">
<span class="w-1.5 h-1.5 rounded-full bg-on-surface-variant/40 mr-1.5" aria-hidden="true"></span> Not run
</span>
</div>
</div>
<div class="bg-error-container/30 border border-error-container rounded-lg p-3 flex items-center justify-between hidden" data-kt-pln-issue-strip data-testid="kt-pln-ui05-issue-strip" hidden>
<div class="flex items-center text-on-error-container font-body-sm text-body-sm">
<span class="material-symbols-outlined mr-2 text-error" aria-hidden="true" data-kt-pln-issue-icon>info</span>
<span data-kt-pln-issue-copy>Complete the Plan Item before requesting Finance confirmation.</span>
</div>
<a class="text-primary font-body-sm text-body-sm font-medium hover:underline flex items-center" href="#" data-kt-pln-action="review-issue" data-kt-pln-issue-action>Review issue <span class="material-symbols-outlined ml-1 text-sm" aria-hidden="true">arrow_forward</span></a>
</div>
<div class="bg-surface-container-low border border-subtle rounded-lg p-3 flex items-center justify-between hidden" data-testid="kt-pln-ui05-no-changes" hidden>
<div class="flex items-center text-on-surface font-body-sm text-body-sm">
<span class="material-symbols-outlined mr-2 text-on-surface-variant" aria-hidden="true">info</span>
<span>No changes remain</span>
</div>
</div>
<div class="flex flex-col md:flex-row gap-3" data-testid="kt-pln-ui03-filters">
<div class="relative flex-1">
<div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
<span class="material-symbols-outlined text-on-surface-variant text-sm" aria-hidden="true">search</span>
</div>
<input class="w-full bg-surface-container-lowest border border-subtle rounded-lg py-2 pl-10 pr-3 font-body-sm text-body-sm text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary shadow-sm" placeholder="Search Plan Items" type="text" aria-label="Search Plan Items" data-kt-pln-builder-search/>
</div>
<div class="relative flex-1 md:max-w-xs">
<select class="w-full appearance-none bg-surface-container-lowest border border-subtle rounded-lg py-2 pl-3 pr-10 font-body-sm text-body-sm text-on-surface focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary shadow-sm" aria-label="Organisation Unit" data-kt-pln-builder-filter-ou>
<option value="">All permitted units</option>
</select>
<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-on-surface-variant">
<span class="material-symbols-outlined text-sm" aria-hidden="true">expand_more</span>
</div>
</div>
<div class="relative flex-1 md:max-w-xs">
<select class="w-full appearance-none bg-surface-container-lowest border border-subtle rounded-lg py-2 pl-3 pr-10 font-body-sm text-body-sm text-on-surface focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary shadow-sm" aria-label="Category" data-kt-pln-builder-filter-category>
<option value="">All categories</option>
</select>
<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-on-surface-variant">
<span class="material-symbols-outlined text-sm" aria-hidden="true">expand_more</span>
</div>
</div>
<div class="relative flex-1 md:max-w-xs">
<select class="w-full appearance-none bg-surface-container-lowest border border-subtle rounded-lg py-2 pl-3 pr-10 font-body-sm text-body-sm text-on-surface focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary shadow-sm" aria-label="Status" data-kt-pln-builder-filter-status>
<option value="">All statuses</option>
</select>
<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-on-surface-variant">
<span class="material-symbols-outlined text-sm" aria-hidden="true">expand_more</span>
</div>
</div>
</div>
<div class="bg-surface-container-lowest border border-subtle rounded-lg shadow-sm overflow-hidden flex flex-col h-[400px]" data-testid="kt-pln-ui03-empty" data-kt-pln-empty-state>
<div class="px-4 py-3 border-b border-subtle bg-surface-bright">
<h2 class="font-headline-sm text-headline-sm text-on-surface">Plan Items</h2>
</div>
<div class="flex-1 flex flex-col items-center justify-center p-8 text-center bg-surface-bright/50">
<div class="w-16 h-16 bg-surface-container rounded-full flex items-center justify-center mb-4 border border-subtle">
<span class="material-symbols-outlined text-4xl text-on-surface-variant" aria-hidden="true">assignment_late</span>
</div>
<h3 class="font-headline-sm text-headline-sm text-on-surface mb-2">No Plan Items yet</h3>
<p class="font-body-sm text-body-sm text-on-surface-variant max-w-sm mx-auto mb-6" data-kt-pln-empty-copy>Add an Approved Demand to begin building this annual Plan.</p>
<div class="flex flex-col gap-3 items-center">
<button type="button" class="bg-primary hover:bg-on-primary-fixed-variant text-on-primary font-body-sm text-body-sm font-medium py-2 px-6 rounded-lg shadow-sm transition-colors flex items-center gap-2" data-kt-pln-action="add-demand" data-testid="kt-pln-ui03-add-demand">
<span class="material-symbols-outlined text-sm" aria-hidden="true" style="font-variation-settings: 'FILL' 1;">add</span>
Add approved Demand
</button>
<a class="font-body-sm text-body-sm text-primary hover:text-on-primary-fixed-variant transition-colors underline" href="#" data-kt-pln-action="add-demand" data-testid="kt-pln-ui03-add-pending">View eligible Demands</a>
</div>
</div>
</div>
<div class="bg-surface-container-lowest border border-subtle rounded-lg shadow-sm flex-1 overflow-hidden flex flex-col mb-20 hidden" data-testid="kt-pln-ui03-items" data-kt-pln-items-table data-kt-pln-ui05-items hidden>
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse" data-testid="kt-pln-ui05-table">
<thead>
<tr class="border-b border-subtle bg-surface-bright">
<th class="p-4 font-label-caps text-label-caps text-on-surface-variant">Requirement</th>
<th class="p-4 font-label-caps text-label-caps text-on-surface-variant">Organisation Unit</th>
<th class="p-4 font-label-caps text-label-caps text-on-surface-variant text-right">Planned Value</th>
<th class="p-4 font-label-caps text-label-caps text-on-surface-variant">Method</th>
<th class="p-4 font-label-caps text-label-caps text-on-surface-variant">Schedule</th>
<th class="p-4 font-label-caps text-label-caps text-on-surface-variant" data-kt-pln-finance-empty="Not requested">Finance</th>
<th class="p-4 font-label-caps text-label-caps text-on-surface-variant">Validation</th>
<th class="p-4 font-label-caps text-label-caps text-on-surface-variant">Action</th>
</tr>
</thead>
<tbody class="divide-y divide-subtle" data-kt-pln-items-body>
<tr class="h-auto" data-kt-pln-items-filler>
<td class="p-8 text-center text-on-surface-variant font-body-sm text-body-sm border-t-0" colspan="8">
No further plan items added yet.
</td>
</tr>
</tbody>
</table>
</div>
</div>
</div>
</main>
<div class="absolute bottom-0 left-0 right-0 bg-surface-container-lowest border-t border-subtle p-4 px-container-padding md:px-section-gap flex justify-between items-center z-10 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]" data-testid="kt-pln-ui05-footer">
<button type="button" class="flex items-center text-on-surface-variant hover:text-on-surface font-body-md text-body-md transition-colors" data-testid="kt-pln-ui03-back" data-kt-pln-action="back">
<span class="material-symbols-outlined mr-2" aria-hidden="true">arrow_back</span> Back to Planning
</button>
<div class="flex gap-4">
<button type="button" class="px-6 py-2 border border-subtle text-primary bg-surface-bright rounded font-label-caps text-label-caps hover:bg-surface-container-low transition-colors shadow-sm hidden" data-kt-pln-action="cancel-update" data-testid="kt-pln-ui05-cancel-update" hidden>
Cancel update
</button>
<button type="button" class="px-6 py-2 border border-subtle text-primary bg-surface-bright rounded font-label-caps text-label-caps hover:bg-surface-container-low transition-colors shadow-sm" data-kt-pln-action="run-validation" data-testid="kt-pln-ui05-run-validation" disabled="">
Run validation
</button>
<button type="button" class="px-6 py-2 bg-surface-variant text-outline rounded font-label-caps text-label-caps cursor-not-allowed opacity-70" data-kt-pln-action="submit-for-review" data-testid="kt-pln-ui05-submit-review" disabled="">
Submit for review
</button>
</div>
</div>
<div data-kt-pln-dialog-host></div>
</div>`;
};
