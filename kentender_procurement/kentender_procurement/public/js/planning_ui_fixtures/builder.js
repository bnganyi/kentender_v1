// PLN-UI-03 — literal Stitch <main> from docs/mvp-1/04_planning/ui_design/PLN-UI-03.html
// Fake top/side nav discarded; kt-stitch-canvas + testids/bind hooks only.
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_builder = function () {
	return `<div class="kt-pln-root kt-stitch-canvas" data-testid="kt-pln-ui03-root">
<main class="flex-1 max-w-7xl mx-auto w-full px-container-padding py-section-gap flex flex-col gap-section-gap">
<div class="flex flex-col md:flex-row justify-between items-start md:items-end gap-4" data-testid="kt-pln-ui03-header">
<div class="flex flex-col gap-stack-xs">
<nav class="flex items-center text-on-surface-variant font-body-sm text-body-sm gap-2" data-kt-pln-builder-context aria-label="Breadcrumb">
<a class="hover:text-primary transition-colors" href="/app/planning-workspace">Procurement Planning</a>
<span class="material-symbols-outlined text-sm" aria-hidden="true">chevron_right</span>
<span class="hover:text-primary transition-colors" data-kt-pln-builder-pe-crumb>Ministry of Health</span>
<span class="material-symbols-outlined text-sm" aria-hidden="true">chevron_right</span>
<span class="text-on-surface" data-kt-pln-builder-fy-crumb>2027/28</span>
</nav>
<h1 class="font-headline-lg text-headline-lg text-on-surface" data-kt-pln-builder-title>Ministry of Health Annual Procurement Plan 2027/28</h1>
<div class="flex items-center gap-2 text-on-surface-variant font-body-sm text-body-sm">
<span class="bg-surface-variant px-2 py-1 rounded-sm font-label-caps text-label-caps text-on-surface" data-kt-pln-builder-lifecycle data-testid="kt-pln-ui03-lifecycle">Draft</span>
<span>·</span>
<span data-kt-pln-builder-version>Version 1</span>
<span>·</span>
<span data-kt-pln-builder-period>Planning period 1 July 2027 to 30 June 2028</span>
</div>
</div>
<button type="button" class="bg-primary hover:bg-primary-container text-on-primary font-body-md text-body-md px-4 py-2 rounded flex items-center gap-2 transition-colors shadow-sm shrink-0" data-kt-pln-action="add-demand" data-testid="kt-pln-ui03-add-demand-header">
<span class="material-symbols-outlined text-sm" aria-hidden="true">add</span>
Add approved demand
</button>
</div>
<div class="bg-surface-container-lowest border border-border-subtle rounded-lg p-container-padding flex flex-wrap gap-6 items-center justify-between shadow-sm" data-testid="kt-pln-ui03-summary">
<div class="flex flex-col">
<span class="font-label-caps text-label-caps text-on-surface-variant">Plan Items</span>
<span class="font-headline-sm text-headline-sm text-on-surface" data-kt-pln-builder-items>0</span>
</div>
<div class="w-px h-10 bg-border-subtle hidden md:block"></div>
<div class="flex flex-col">
<span class="font-label-caps text-label-caps text-on-surface-variant">Planned Value</span>
<span class="font-data-lg text-data-lg text-on-surface" data-kt-pln-builder-total>KES 0</span>
</div>
<div class="w-px h-10 bg-border-subtle hidden md:block"></div>
<div class="flex flex-col">
<span class="font-label-caps text-label-caps text-on-surface-variant">Org Units</span>
<span class="font-headline-sm text-headline-sm text-on-surface" data-kt-pln-builder-org-units>0</span>
</div>
<div class="w-px h-10 bg-border-subtle hidden md:block"></div>
<div class="flex flex-col">
<span class="font-label-caps text-label-caps text-on-surface-variant">Dept. Contributions</span>
<span class="font-body-md text-body-md text-on-surface" data-kt-pln-builder-contributions>0 submitted</span>
</div>
<div class="w-px h-10 bg-border-subtle hidden md:block"></div>
<div class="flex flex-col">
<span class="font-label-caps text-label-caps text-on-surface-variant mb-1">Validation</span>
<div class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-surface-variant text-on-surface-variant font-label-caps text-label-caps border border-outline-variant" data-kt-pln-builder-validation>
<span class="material-symbols-outlined text-[14px]" aria-hidden="true">pending</span>
Not run
</div>
</div>
</div>
<div class="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
<div class="flex flex-wrap items-center gap-3 w-full sm:w-auto">
<div class="relative w-full sm:w-48">
<select class="w-full appearance-none bg-surface-container-lowest border border-border-subtle rounded py-2 pl-3 pr-8 font-body-sm text-on-surface focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-all" aria-label="Organisation Unit">
<option>Organisation Unit</option>
</select>
<span class="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-outline pointer-events-none text-[20px]" aria-hidden="true">arrow_drop_down</span>
</div>
<div class="relative w-full sm:w-40">
<select class="w-full appearance-none bg-surface-container-lowest border border-border-subtle rounded py-2 pl-3 pr-8 font-body-sm text-on-surface focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-all" aria-label="Category">
<option>Category</option>
</select>
<span class="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-outline pointer-events-none text-[20px]" aria-hidden="true">arrow_drop_down</span>
</div>
<div class="relative w-full sm:w-36">
<select class="w-full appearance-none bg-surface-container-lowest border border-border-subtle rounded py-2 pl-3 pr-8 font-body-sm text-on-surface focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-all" aria-label="Status">
<option>Status</option>
</select>
<span class="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-outline pointer-events-none text-[20px]" aria-hidden="true">arrow_drop_down</span>
</div>
</div>
<div class="relative w-full sm:w-64">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-[20px]" aria-hidden="true">search</span>
<input class="w-full pl-10 pr-4 py-2 bg-surface-container-lowest border border-border-subtle rounded font-body-sm text-on-surface focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-all" placeholder="Search plan items" type="text" aria-label="Search plan items"/>
</div>
</div>
<div class="bg-surface-container-lowest border border-border-subtle rounded-lg shadow-sm flex flex-col min-h-[400px]" data-testid="kt-pln-ui03-empty" data-kt-pln-empty-state>
<div class="px-5 py-4 border-b border-border-subtle bg-surface-container-low rounded-t-lg">
<h2 class="font-headline-sm text-headline-sm text-on-surface">Plan Items</h2>
</div>
<div class="flex-1 flex flex-col items-center justify-center p-8 text-center bg-surface-bright/50">
<div class="w-16 h-16 bg-surface-variant rounded-full flex items-center justify-center mb-4">
<span class="material-symbols-outlined text-[32px] text-outline" aria-hidden="true">inventory_2</span>
</div>
<h3 class="font-headline-sm text-headline-sm text-on-surface mb-2">No Plan Items yet</h3>
<p class="font-body-md text-body-md text-on-surface-variant max-w-md mb-6" data-kt-pln-empty-copy>Add an approved and funded Demand to begin building this annual plan.</p>
<div class="flex flex-col items-center gap-4">
<button type="button" class="bg-primary text-on-primary font-body-sm font-medium px-5 py-2.5 rounded hover:bg-primary-container transition-colors shadow-sm flex items-center justify-center gap-2" data-kt-pln-action="add-demand" data-testid="kt-pln-ui03-add-demand">
<span class="material-symbols-outlined text-[20px]" aria-hidden="true">add</span>
Add approved demand
</button>
<a class="font-body-sm text-primary hover:text-primary-container underline transition-colors" href="/app/planning-workspace" data-testid="kt-pln-ui03-add-pending">View eligible Demands</a>
</div>
</div>
</div>
<div class="bg-surface-container-lowest border border-border-subtle rounded-lg shadow-sm overflow-hidden hidden" data-testid="kt-pln-ui03-items" data-kt-pln-items-table hidden>
<div class="px-5 py-4 border-b border-border-subtle bg-surface-container-low">
<h2 class="font-headline-sm text-headline-sm text-on-surface">Plan Items</h2>
</div>
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse">
<thead>
<tr class="border-b border-border-subtle bg-surface-container-low/50">
<th class="font-label-caps text-label-caps text-on-surface-variant p-4 font-semibold uppercase">Demand</th>
<th class="font-label-caps text-label-caps text-on-surface-variant p-4 font-semibold uppercase">Category</th>
<th class="font-label-caps text-label-caps text-on-surface-variant p-4 font-semibold uppercase text-right">Estimated value</th>
<th class="font-label-caps text-label-caps text-on-surface-variant p-4 font-semibold uppercase">Status</th>
</tr>
</thead>
<tbody class="divide-y divide-subtle" data-kt-pln-items-body></tbody>
</table>
</div>
</div>
<div class="mt-auto pt-section-gap border-t border-border-subtle flex flex-col sm:flex-row items-center justify-between gap-4">
<a class="text-on-surface-variant hover:text-on-surface font-body-md text-body-md transition-colors flex items-center gap-2 px-4 py-2 rounded hover:bg-surface-variant" href="/app/planning-workspace" data-testid="kt-pln-ui03-back">
<span class="material-symbols-outlined text-sm" aria-hidden="true">arrow_back</span>
Back to Planning
</a>
<div class="flex items-center gap-4 w-full sm:w-auto">
<button type="button" class="flex-1 sm:flex-none bg-surface-container-highest hover:bg-surface-variant text-on-surface font-body-md text-body-md px-6 py-2 rounded border border-border-subtle transition-colors opacity-50 cursor-not-allowed" disabled="">
Run validation
</button>
<button type="button" class="flex-1 sm:flex-none bg-surface-variant text-on-surface-variant opacity-50 cursor-not-allowed font-body-md text-body-md px-6 py-2 rounded flex items-center justify-center gap-2" disabled="">
Submit for departmental sign-off
<span class="material-symbols-outlined text-sm" aria-hidden="true">lock</span>
</button>
</div>
</div>
</main>
</div>`;
};
