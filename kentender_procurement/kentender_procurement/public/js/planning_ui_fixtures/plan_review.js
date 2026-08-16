// PLN-UI-08 — high-fidelity application canvas port of revision/PLN-UI-08-1/2.html.
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_plan_review = function () {
	return `<div class="kt-pln-root kt-stitch-canvas" data-testid="kt-pln-ui08-root">
<main class="kt-pln-ui08-canvas">
<div class="kt-pln-review-layout">
<div class="kt-pln-review-canvas">
<header class="kt-pln-review-heading" data-testid="kt-pln-ui08-header">
<h1 class="font-headline-lg text-headline-lg text-on-surface">Review procurement plan update</h1>
<p class="font-body-lg text-body-lg text-on-surface-variant" data-kt-pln-review-secondary></p>
<div class="kt-pln-review-badges"><span class="kt-pln-chip kt-pln-chip-primary"><span class="material-symbols-outlined">pending</span>In review</span><span class="kt-pln-chip kt-pln-chip-success"><span class="material-symbols-outlined">check_circle</span>Ready</span></div>
<div class="kt-pln-review-notice"><span class="material-symbols-outlined">info</span><p>Approved Version remains active until this review is completed.</p></div>
</header>

<section class="kt-pln-review-summary" data-testid="kt-pln-ui08-summary">
<div><span class="kt-pln-metric-label">Submitted value</span><strong class="font-data-md" data-kt-pln-review-total></strong></div>
<div><span class="kt-pln-metric-label">Plan Items</span><strong class="font-data-md" data-kt-pln-review-items></strong></div>
<div><span class="kt-pln-metric-label">Finance confirmed</span><strong class="font-data-md" data-kt-pln-review-finance-confirmed></strong></div>
<div><span class="kt-pln-metric-label">Validation</span><strong class="font-data-md text-status-available" data-kt-pln-review-validation></strong></div>
</section>

<section class="kt-pln-review-items">
<div class="kt-pln-review-section-head"><h2 class="font-headline-sm text-headline-sm">Plan Items in submitted version</h2></div>
<div class="overflow-x-auto"><table class="kt-pln-review-table"><thead><tr><th>Change</th><th>Plan Item</th><th>Organisation Unit</th><th class="text-right">Planned value</th><th>Method</th><th>Contract completion</th><th class="text-center">Finance</th><th class="text-center">Validation</th><th>Action</th></tr></thead><tbody data-kt-pln-review-items-body></tbody></table></div>
</section>

<section class="kt-pln-review-checks"><span class="material-symbols-outlined">task_alt</span><div><h3>Review checks passed</h3><p data-kt-pln-review-issues-copy>All required Planning validation and Finance confirmations are ready for decision.</p></div></section>

<section class="kt-pln-review-history"><h2 class="font-headline-sm text-headline-sm">Decision history</h2><div class="kt-pln-timeline" data-kt-pln-review-history></div></section>
</div>

<aside class="kt-pln-review-rail">
<div class="kt-pln-review-decision">
<h2 class="font-headline-sm text-headline-sm">Decision</h2>
<dl><div><dt>Task</dt><dd>Professional Plan review</dd></div><div><dt>Finance confirmation</dt><dd class="text-status-available"><span class="material-symbols-outlined">check_circle</span><span data-kt-pln-review-finance-confirmed></span></dd></div><div><dt>Validation</dt><dd class="text-status-available"><span class="material-symbols-outlined">check_circle</span><span data-kt-pln-review-validation></span></dd></div></dl>
<label for="kt-pln-review-note">Approval note</label><textarea id="kt-pln-review-note" data-kt-pln-review-note placeholder="Add optional comments..."></textarea>
<p class="hidden kt-pln-field-error" data-kt-pln-review-error role="alert"></p>
<div class="kt-pln-review-actions"><button class="kt-pln-button-primary" data-testid="kt-pln-ui08-primary" data-kt-pln-action="approve-review"><span class="material-symbols-outlined">thumb_up</span>Approve update</button><button class="kt-pln-button-secondary" data-testid="kt-pln-ui08-return" data-kt-pln-action="return-review"><span class="material-symbols-outlined">reply</span>Return to planner</button></div>
</div>
</aside>
</div>
</main>
</div>`;
};
