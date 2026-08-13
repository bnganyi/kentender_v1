// PLN-UI-08 — literal Stitch <main> from docs/mvp-1/04_planning/ui_design/PLN-UI-08.html
// Fake top/side nav + in-canvas breadcrumbs discarded (Desk chrome); kt-stitch-canvas + testids/bind hooks only.
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_plan_review = function () {
	return `<div class="kt-pln-root kt-stitch-canvas" data-testid="kt-pln-ui08-root">
<main class="flex-1 overflow-y-auto p-container-padding space-y-section-gap no-scrollbar pb-24">
<div class="space-y-stack-sm" data-testid="kt-pln-ui08-header">
<div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
<div>
<h1 class="font-headline-lg text-headline-lg text-on-surface mb-1">Review and approve procurement plan<span class="inline-flex items-center px-3 py-1 rounded-full bg-status-reserved/10 text-status-reserved font-label-caps text-label-caps ml-3 align-middle" data-kt-pln-review-lifecycle data-testid="kt-pln-ui08-lifecycle">In review</span></h1>
<p class="font-body-lg text-body-lg text-on-surface-variant" data-kt-pln-review-secondary>Ministry of Health · FY 2027/28 · Version 1</p>
</div>
</div>
</div>
<div class="bg-surface-container-lowest border border-subtle rounded-lg p-4 flex flex-row items-center justify-between shadow-sm" data-testid="kt-pln-ui08-summary">
<div class="flex flex-col">
<span class="font-label-caps text-label-caps text-on-surface-variant mb-1">Plan Items</span>
<span class="font-data-md text-data-md text-on-surface" data-kt-pln-review-items>1</span>
</div>
<div class="h-8 w-px bg-border-subtle hidden md:block"></div>
<div class="flex flex-col">
<span class="font-label-caps text-label-caps text-on-surface-variant mb-1">Total Planned Value</span>
<span class="font-data-lg text-data-lg text-primary" data-kt-pln-review-total>KES 455,000,000</span>
</div>
<div class="h-8 w-px bg-border-subtle hidden md:block"></div>
<div class="flex flex-col">
<span class="font-label-caps text-label-caps text-on-surface-variant mb-1">Finance Confirmed</span>
<span class="font-data-md text-data-md text-on-surface" data-kt-pln-review-finance-confirmed>1 of 1</span>
</div>
<div class="h-8 w-px bg-border-subtle hidden md:block"></div>
<div class="flex flex-col">
<span class="font-label-caps text-label-caps text-on-surface-variant mb-1">Validation Status</span>
<span class="inline-flex items-center px-2 py-1 rounded bg-status-available/10 text-status-available font-label-caps text-label-caps w-fit" data-kt-pln-review-validation>
<span class="material-symbols-outlined text-[14px] mr-1">check_circle</span> Ready
</span>
</div>
</div>
<div class="grid grid-cols-1 lg:grid-cols-3 gap-section-gap items-start">
<div class="lg:col-span-2 space-y-section-gap">
<div class="bg-status-available/10 border border-status-available/20 rounded-lg p-gutter-md flex items-start gap-3" data-testid="kt-pln-ui08-issues" data-kt-pln-review-issues-banner>
<span class="material-symbols-outlined text-status-available">check_circle</span>
<p class="font-body-md text-body-md text-on-surface mt-0.5" data-kt-pln-review-issues-copy>All required planning and funding checks are ready for decision.</p>
</div>
<div class="bg-surface border border-subtle rounded-lg overflow-hidden" data-testid="kt-pln-ui08-items">
<div class="px-container-padding py-gutter-md border-b border-subtle bg-surface-bright">
<h3 class="font-headline-sm text-headline-sm text-on-surface">Plan Items</h3>
</div>
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse" data-testid="kt-pln-ui08-items-table">
<thead class="bg-surface-container-low border-b border-subtle">
<tr>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant whitespace-nowrap">Requirement</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant whitespace-nowrap">Organisation Unit</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant whitespace-nowrap text-right">Value</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant whitespace-nowrap">Method</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant whitespace-nowrap">Completion</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant whitespace-nowrap">Finance</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant whitespace-nowrap">Validation</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant whitespace-nowrap text-right">Action</th>
</tr>
</thead>
<tbody class="divide-y divide-subtle" data-kt-pln-review-items-body></tbody>
</table>
</div>
</div>
<div class="bg-surface border border-subtle rounded-lg overflow-hidden" data-testid="kt-pln-ui08-statutory">
<div class="px-container-padding py-gutter-md border-b border-subtle bg-surface-bright flex justify-between items-center">
<h3 class="font-headline-sm text-headline-sm text-on-surface">Preference &amp; Reservation Coverage</h3>
<span class="font-label-caps text-label-caps text-on-surface-variant bg-surface-container px-2 py-1 rounded">Derived automatically</span>
</div>
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse">
<thead class="bg-surface-container-low border-b border-subtle">
<tr>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant">Coverage requirement</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant text-right">Required value</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant text-right">Derived planned coverage</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant">Status</th>
</tr>
</thead>
<tbody class="divide-y divide-subtle" data-kt-pln-review-statutory-body></tbody>
</table>
</div>
</div>
</div>
<div class="lg:col-span-1" data-testid="kt-pln-ui08-rail">
<div class="sticky top-24 bg-surface border border-subtle rounded-lg shadow-sm flex flex-col overflow-hidden">
<div class="p-gutter-md border-b border-subtle bg-primary-fixed/30">
<h3 class="font-headline-sm text-headline-sm text-on-surface flex items-center gap-2">
<span class="material-symbols-outlined text-primary">gavel</span>
Professional approval
</h3>
</div>
<div class="p-gutter-md border-b border-subtle bg-surface-bright space-y-3">
<div class="flex justify-between items-center">
<span class="font-body-sm text-body-sm text-on-surface-variant">Prepared by</span>
<span class="font-body-sm text-body-sm text-on-surface font-medium text-right whitespace-normal" data-kt-pln-review-prepared-by>Supply Chain Mgt Services</span>
</div>
<div class="flex justify-between items-center">
<span class="font-body-sm text-body-sm text-on-surface-variant">Finance confirmation</span>
<span class="font-body-sm text-body-sm text-status-available font-medium flex items-center gap-1" data-kt-pln-review-finance-rail>
<span class="material-symbols-outlined text-[16px]">done</span> Complete
</span>
</div>
<div class="flex justify-between items-center">
<span class="font-body-sm text-body-sm text-on-surface-variant">Validation</span>
<span class="font-body-sm text-body-sm text-status-available font-medium" data-kt-pln-review-validation-run>Ready</span>
</div>
</div>
<div class="p-gutter-md space-y-gutter-md">
<div data-kt-pln-review-comment-block>
<label class="block font-label-caps text-label-caps text-on-surface mb-2" for="kt-pln-decision-comment">Decision comment</label>
<textarea class="w-full bg-surface-container-lowest border border-subtle rounded-lg px-3 py-2 font-body-sm text-body-sm text-on-surface focus:border-secondary focus:ring-2 focus:ring-secondary/20 outline-none transition-all resize-none" id="kt-pln-decision-comment" data-kt-field="decision_comment" data-testid="kt-pln-ui08-comment" placeholder="Enter comments here..." rows="4"></textarea>
<span class="font-body-sm text-body-sm text-on-surface-variant text-[13px]" data-kt-field-error="decision_comment"></span>
<p class="font-body-sm text-[12px] text-on-surface-variant mt-2">Optional when approving; required when returning.</p>
</div>
<div class="flex flex-col gap-3 pt-2" data-kt-pln-review-actions>
<button type="button" class="w-full bg-primary text-on-primary font-body-md font-medium py-2.5 rounded-lg hover:bg-on-primary-fixed-variant transition-colors shadow-sm flex justify-center items-center gap-2" data-kt-pln-action="primary-decision" data-testid="kt-pln-ui08-primary">
<span class="material-symbols-outlined text-[20px]">thumb_up</span>
<span data-kt-pln-review-primary-label>Approve plan</span>
</button>
<button type="button" class="w-full bg-transparent text-status-exhausted border border-transparent hover:border-status-exhausted/30 hover:bg-status-exhausted/5 font-body-md font-medium py-2 rounded-lg transition-colors flex justify-center items-center gap-2" data-kt-pln-action="return-plan" data-testid="kt-pln-ui08-return">
<span class="material-symbols-outlined text-[20px]">undo</span>
Return to planner
</button>
</div>
</div>
<div class="p-gutter-md border-t border-subtle bg-surface-bright" data-testid="kt-pln-ui08-trail">
<h4 class="font-label-caps text-label-caps text-on-surface-variant mb-4 uppercase">Prior-decision trail</h4>
<div class="relative pl-4 border-l-2 border-subtle space-y-6" data-kt-pln-review-trail></div>
</div>
</div>
</div>
</div>
</main>
</div>`;
};
