// PLN-UI-08 — literal Stitch <main> from docs/mvp-1/04_planning/ui_design/PLN-UI-08.html
// Fake top/side nav + in-canvas breadcrumbs discarded (Desk chrome); kt-stitch-canvas + testids/bind hooks only.
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_plan_review = function () {
	return `<div class="kt-pln-root kt-stitch-canvas" data-testid="kt-pln-ui08-root">
<main class="flex-1 overflow-y-auto w-full p-container-padding lg:p-section-gap flex flex-col gap-section-gap">
<div class="flex flex-col gap-stack-sm" data-testid="kt-pln-ui08-header">
<div class="flex flex-col md:flex-row md:justify-between md:items-end gap-4 mt-2">
<div>
<h1 class="font-headline-lg text-headline-lg text-on-surface">Review annual procurement plan</h1>
<p class="font-body-md text-body-md text-on-surface-variant mt-1" data-kt-pln-review-secondary>Ministry of Health · <span class="font-data-md text-data-md">FY 2027/28</span> · Version 1</p>
</div>
<div class="flex gap-2">
<span class="inline-flex items-center px-3 py-1 rounded-full font-label-caps text-label-caps bg-status-reserved/10 text-status-reserved border border-status-reserved/20" data-kt-pln-review-lifecycle data-testid="kt-pln-ui08-lifecycle">
<span class="material-symbols-outlined text-[14px] mr-1" aria-hidden="true">pending</span> In review
</span>
<span class="inline-flex items-center px-3 py-1 rounded-full font-label-caps text-label-caps bg-status-available/10 text-status-available border border-status-available/20" data-kt-pln-review-validation-chip data-testid="kt-pln-ui08-validation-chip">
<span class="material-symbols-outlined text-[14px] mr-1" aria-hidden="true">check_circle</span> Ready
</span>
</div>
</div>
</div>
<div class="grid grid-cols-2 md:grid-cols-5 gap-4 bg-surface-container-lowest border border-subtle rounded-lg p-container-padding" data-testid="kt-pln-ui08-summary">
<div class="flex flex-col border-l-4 border-primary pl-3">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Plan Items</span>
<span class="font-data-lg text-data-lg text-on-surface mt-1 text-primary" data-kt-pln-review-items>1</span>
</div>
<div class="flex flex-col border-l border-subtle pl-4">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Total Planned</span>
<span class="font-data-md text-data-md text-on-surface mt-2 text-primary" data-kt-pln-review-total>KES 455,000,000</span>
</div>
<div class="flex flex-col border-l border-subtle pl-4">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Contributions</span>
<span class="font-body-md text-body-md text-on-surface mt-2" data-kt-pln-review-contributions>1 of 1 submitted</span>
</div>
<div class="flex flex-col border-l border-subtle pl-4">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Open Tender</span>
<span class="font-data-md text-data-md text-on-surface mt-2 text-primary" data-kt-pln-review-open-tender>KES 455,000,000</span>
</div>
<div class="flex flex-col border-l border-subtle pl-4">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Validation</span>
<span class="inline-flex items-center mt-2 px-2 py-0.5 rounded-full font-label-caps text-label-caps bg-status-available/10 text-status-available w-max" data-kt-pln-review-validation>Ready</span>
</div>
</div>
<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
<div class="lg:col-span-2 flex flex-col gap-8">
<section class="flex flex-col gap-4" data-testid="kt-pln-ui08-items">
<h2 class="font-headline-sm text-headline-sm text-on-surface">Plan Items</h2>
<div class="overflow-x-auto bg-surface-container-lowest border border-subtle rounded-lg">
<table class="w-full text-left border-collapse" data-testid="kt-pln-ui08-items-table">
<thead>
<tr class="border-b border-subtle bg-surface">
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant">Requirement</th>
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant">Organisation Unit</th>
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant">Value</th>
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant">Method</th>
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant">Completion</th>
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant">Status</th>
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant text-right">Action</th>
</tr>
</thead>
<tbody class="divide-y divide-subtle" data-kt-pln-review-items-body></tbody>
</table>
</div>
</section>
<section class="flex flex-col gap-4" data-testid="kt-pln-ui08-statutory">
<h2 class="font-headline-sm text-headline-sm text-on-surface">Statutory allocation coverage</h2>
<div class="overflow-x-auto bg-surface-container-lowest border border-subtle rounded-lg">
<table class="w-full text-left border-collapse">
<thead>
<tr class="border-b border-subtle bg-surface">
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant w-1/3">Obligation</th>
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant w-1/4">Required treatment</th>
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant">Planned treatment</th>
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant">Status</th>
</tr>
</thead>
<tbody class="divide-y divide-subtle" data-kt-pln-review-statutory-body></tbody>
</table>
</div>
</section>
<section class="flex flex-col gap-4" data-testid="kt-pln-ui08-issues">
<h2 class="font-headline-sm text-headline-sm text-on-surface">Review issues</h2>
<div class="bg-status-available/10 border border-status-available/20 rounded-lg p-4 flex items-start gap-3 text-status-available" data-kt-pln-review-issues-banner>
<span class="material-symbols-outlined mt-0.5" aria-hidden="true">check_circle</span>
<p class="font-body-md text-body-md" data-kt-pln-review-issues-copy>All required planning checks are ready for this decision.</p>
</div>
</section>
</div>
<div class="lg:col-span-1" data-testid="kt-pln-ui08-rail">
<div class="bg-surface-container-lowest border border-subtle rounded-lg p-container-padding flex flex-col gap-6 sticky top-[5.5rem]">
<h2 class="font-headline-sm text-headline-sm text-on-surface border-b border-subtle pb-4">Review decision</h2>
<div class="flex flex-col gap-4">
<div class="flex flex-col gap-1">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Current decision</span>
<span class="font-body-sm text-body-sm text-on-surface font-medium" data-kt-pln-review-current-decision>Professional review</span>
</div>
<div class="flex flex-col gap-1">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Prepared by</span>
<span class="font-body-sm text-body-sm text-on-surface" data-kt-pln-review-prepared-by>Supply Chain Management Services</span>
</div>
<div class="flex flex-col gap-1">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Departmental submission</span>
<span class="font-body-sm text-body-sm text-on-surface" data-kt-pln-review-dept>Submitted</span>
</div>
<div class="flex flex-col gap-1">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Validation run</span>
<span class="font-body-sm text-body-sm text-status-available flex items-center gap-1" data-kt-pln-review-validation-run>
<span class="material-symbols-outlined text-[16px]" aria-hidden="true">check_circle</span> Ready
</span>
</div>
</div>
<div class="flex flex-col gap-2" data-kt-pln-review-comment-block>
<label class="font-body-sm text-body-sm text-on-surface font-medium" for="kt-pln-decision-comment">Decision comment</label>
<textarea class="w-full rounded-md border-subtle bg-surface-bright focus:border-primary focus:ring-primary font-body-sm text-on-surface resize-none" id="kt-pln-decision-comment" data-kt-field="decision_comment" data-testid="kt-pln-ui08-comment" placeholder="Enter comments here..." rows="4"></textarea>
<span class="font-body-sm text-body-sm text-on-surface-variant text-[13px]" data-kt-field-error="decision_comment"></span>
<span class="font-body-sm text-body-sm text-on-surface-variant text-[13px]">Optional when recommending approval; required when returning the Plan.</span>
</div>
<div class="flex flex-col gap-3 pt-2" data-kt-pln-review-actions>
<button type="button" class="w-full py-2.5 px-4 bg-primary text-on-primary rounded font-body-md font-medium hover:bg-primary/90 transition-colors" data-kt-pln-action="primary-decision" data-testid="kt-pln-ui08-primary">
Recommend approval
</button>
<button type="button" class="w-full py-2.5 px-4 border border-outline text-primary rounded font-body-md font-medium hover:bg-surface-container-low transition-colors" data-kt-pln-action="return-plan" data-testid="kt-pln-ui08-return">
Return plan
</button>
</div>
<div class="mt-4 pt-6 border-t border-subtle flex flex-col gap-3" data-testid="kt-pln-ui08-trail">
<h3 class="font-label-caps text-label-caps text-on-surface-variant uppercase mb-1">Prior-decision trail</h3>
<div class="relative pl-4 border-l-2 border-subtle flex flex-col gap-4" data-kt-pln-review-trail></div>
</div>
</div>
</div>
</div>
</main>
</div>`;
};
