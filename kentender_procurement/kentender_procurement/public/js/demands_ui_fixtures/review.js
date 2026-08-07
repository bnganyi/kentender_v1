// DEM-UIC-002 / DEM-UI-04 — Shared Demand review shell + Business review stage.
// Stitch: docs/mvp-1/03_demands/ui_design/DEM-UI-04.html (nav discarded).
// Prompt 04: review prompts are statements (not HTML checkboxes).
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.demand_review = function () {
	return `<div class="kt-dem-root kt-dem-review kt-stitch-canvas" data-testid="kt-dem-ui04-root" data-kt-dem-live="0" data-kt-dem-review-stage="">
<div class="kt-dem-review-inner p-6 max-w-7xl mx-auto w-full">
<div class="mb-6" data-testid="kt-dem-ui04-header">
<div class="flex flex-col md:flex-row md:items-start justify-between gap-4">
<div>
<div class="flex items-center gap-3 mb-1 flex-wrap">
<h1 class="font-headline-lg text-headline-lg text-on-surface mb-0" data-kt-dem-label="title">—</h1>
<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-status-reserved/10 text-status-reserved border border-status-reserved/20" data-kt-dem-label="status_display" data-testid="kt-dem-ui04-status-pill">—</span>
</div>
<div class="flex flex-wrap items-center gap-x-6 gap-y-2 mt-2">
<div class="flex items-center gap-1.5">
<span class="material-symbols-outlined text-[18px] text-on-surface-variant">tag</span>
<span class="font-data-mono text-data-mono text-on-surface-variant" data-kt-dem-label="demand_code" data-testid="kt-dem-ui04-code">—</span>
</div>
<div class="flex items-center gap-1.5">
<span class="material-symbols-outlined text-[18px] text-on-surface-variant">payments</span>
<span class="font-data-mono text-data-mono text-on-surface-variant" data-testid="kt-dem-ui04-estimate">
<span data-kt-dem-label="estimate_header_display">—</span>
<span class="text-outline text-xs"> est.</span>
</span>
</div>
<div class="flex items-center gap-1.5">
<span class="material-symbols-outlined text-[18px] text-on-surface-variant">calendar_today</span>
<span class="text-on-surface-variant text-sm">Req: <span data-kt-dem-label="required_by_display">—</span></span>
</div>
<div class="flex items-center gap-1.5">
<span class="material-symbols-outlined text-[18px] text-on-surface-variant">route</span>
<span class="text-on-surface-variant text-sm"><span data-kt-dem-label="demand_route">—</span> Route</span>
</div>
</div>
</div>
</div>
</div>
<div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4 mb-6" data-testid="kt-dem-ui04-stage">
<div class="flex flex-col md:flex-row justify-between gap-4" data-kt-dem-stage-list></div>
</div>
<div class="kt-dem-review-grid grid grid-cols-1 lg:grid-cols-3 gap-6">
<div class="lg:col-span-2 space-y-4" data-testid="kt-dem-ui04-main">
<section class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden" data-testid="kt-dem-ui04-section-need">
<div class="bg-surface-container-low px-4 py-3 border-b border-outline-variant flex items-center gap-2">
<span class="material-symbols-outlined text-primary">corporate_fare</span>
<h2 class="font-headline-sm text-headline-sm text-on-surface mb-0">Business need</h2>
</div>
<div class="p-4 space-y-4">
<p class="text-on-surface font-body-lg mb-0" data-kt-dem-label="need_statement">—</p>
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
<div>
<div class="font-label-caps text-label-caps text-on-surface-variant mb-1">Why</div>
<p class="font-body-md text-on-surface mb-0" data-kt-dem-label="need_rationale">—</p>
</div>
<div>
<div class="font-label-caps text-label-caps text-on-surface-variant mb-1">Expected outcome</div>
<p class="font-body-md text-on-surface mb-0" data-kt-dem-label="expected_outcome">—</p>
</div>
</div>
<div class="bg-surface border border-outline-variant rounded-lg p-4">
<div class="font-label-caps text-label-caps text-on-surface-variant mb-2">Beneficiaries</div>
<p class="font-body-md text-on-surface mb-0" data-kt-dem-label="beneficiaries">—</p>
</div>
</div>
</section>
<section class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden" data-testid="kt-dem-ui04-section-items">
<div class="bg-surface-container-low px-4 py-3 border-b border-outline-variant flex items-center justify-between">
<div class="flex items-center gap-2">
<span class="material-symbols-outlined text-primary">inventory_2</span>
<h2 class="font-headline-sm text-headline-sm text-on-surface mb-0">Need items</h2>
</div>
<span class="text-xs bg-surface-container-high px-2 py-1 rounded text-on-surface-variant font-medium" data-kt-dem-label="items_count">0 Items</span>
</div>
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse">
<thead>
<tr class="border-b border-outline-variant">
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant">Description</th>
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant text-right">Quantity</th>
<th class="px-4 py-3 font-label-caps text-label-caps text-on-surface-variant text-right">Estimate</th>
</tr>
</thead>
<tbody data-kt-dem-items-tbody data-testid="kt-dem-ui04-items-body"></tbody>
</table>
</div>
</section>
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
<section class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden" data-testid="kt-dem-ui04-section-delivery">
<div class="bg-surface-container-low px-4 py-3 border-b border-outline-variant flex items-center gap-2">
<span class="material-symbols-outlined text-primary">local_shipping</span>
<h2 class="font-headline-sm text-headline-sm text-on-surface mb-0">Delivery details</h2>
</div>
<div class="p-4 space-y-4">
<div>
<div class="text-xs text-on-surface-variant mb-1">Owning unit</div>
<div class="font-medium text-on-surface" data-kt-dem-label="owner_org_unit_label">—</div>
</div>
<div>
<div class="text-xs text-on-surface-variant mb-1">Delivery location</div>
<div class="font-medium text-on-surface" data-kt-dem-label="delivery_location">—</div>
</div>
<div>
<div class="text-xs text-on-surface-variant mb-1">Required by</div>
<div class="font-medium text-on-surface" data-kt-dem-label="required_by_display">—</div>
</div>
<div>
<div class="text-xs text-on-surface-variant mb-1">Route</div>
<div class="font-medium text-on-surface" data-kt-dem-label="demand_route">—</div>
</div>
<div>
<div class="text-xs text-on-surface-variant mb-1">Technical contact</div>
<div class="font-medium text-on-surface" data-kt-dem-label="technical_contact_label">—</div>
</div>
</div>
</section>
<section class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden" data-testid="kt-dem-ui04-section-supporting">
<div class="bg-surface-container-low px-4 py-3 border-b border-outline-variant flex items-center gap-2">
<span class="material-symbols-outlined text-primary">info</span>
<h2 class="font-headline-sm text-headline-sm text-on-surface mb-0">Supporting info</h2>
</div>
<div class="p-4 space-y-4">
<div>
<div class="text-xs text-on-surface-variant mb-1">Estimate basis</div>
<div class="font-medium text-sm p-3 bg-surface rounded border border-outline-variant text-on-surface" data-kt-dem-label="estimate_basis">—</div>
</div>
<div>
<div class="text-xs text-on-surface-variant mb-2">Attachments</div>
<p class="text-sm text-on-surface-variant mb-0" data-testid="kt-dem-ui04-attachments-empty">No supporting documents attached.</p>
</div>
</div>
</section>
</div>
</div>
<div class="lg:col-span-1" data-testid="kt-dem-ui04-decision" data-kt-dem-business-decision>
<div class="kt-dem-ui04-decision-card bg-surface-container-lowest border border-outline-variant sticky top-24 overflow-hidden">
<div class="border-b border-outline-variant" data-kt-dem-decision-pad>
<h2 class="font-headline-md text-headline-md text-primary flex items-center gap-2 mb-0">
<span class="material-symbols-outlined">gavel</span>
Business review
</h2>
<p class="text-sm text-on-surface-variant mt-2 mb-0">Evaluate the strategic alignment and necessity of this demand.</p>
</div>
<div class="space-y-6" data-kt-dem-decision-pad>
<div data-testid="kt-dem-ui04-prompts">
<div class="font-label-caps text-label-caps text-on-surface-variant mb-3">Review Criteria</div>
<div class="space-y-3" data-kt-dem-review-prompts></div>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-2" for="kt-dem-ui04-comment">Review comments <span class="font-normal normal-case text-outline text-xs">(Optional)</span></label>
<textarea id="kt-dem-ui04-comment" class="w-full rounded-lg border border-outline-variant bg-surface-container-lowest text-body-md px-3 py-2 outline-none resize-none" data-kt-dem-field="comment" data-testid="kt-dem-ui04-comment" placeholder="Add rationale or notes for the procurement team..." rows="3"></textarea>
</div>
<div class="kt-dem-ui04-disclaimer bg-surface-container-low p-3 rounded border border-outline-variant flex gap-3 items-start" data-testid="kt-dem-ui04-disclaimer">
<span class="material-symbols-outlined text-outline text-[20px] shrink-0 mt-0.5">lightbulb</span>
<p class="text-xs text-on-surface-variant leading-relaxed mb-0" data-kt-dem-label="non_final_disclaimer">Business support does not confirm funding or constitute final procurement approval.</p>
</div>
</div>
<div class="kt-dem-ui04-actions-bar bg-surface-container-low border-t border-outline-variant flex flex-col gap-3" data-testid="kt-dem-ui04-actions">
<button type="button" class="w-full bg-primary hover:bg-primary/90 text-on-primary font-medium py-2.5 px-4 rounded-lg flex justify-center items-center gap-2 transition-colors" data-kt-dem-action="support" data-testid="kt-dem-ui04-support">
<span class="material-symbols-outlined text-[20px]">thumb_up</span>
Support demand
</button>
<div class="flex gap-3">
<button type="button" class="flex-1 bg-transparent border border-outline-variant hover:border-on-surface text-on-surface font-medium py-2 px-3 rounded-lg flex justify-center items-center gap-2 transition-colors text-sm" data-kt-dem-action="return" data-testid="kt-dem-ui04-return">
<span class="material-symbols-outlined text-[18px]">assignment_return</span>
Return for correction
</button>
<button type="button" class="flex-1 bg-transparent text-error hover:bg-error/10 font-medium py-2 px-3 rounded-lg flex justify-center items-center gap-2 transition-colors text-sm" data-kt-dem-action="reject" data-testid="kt-dem-ui04-reject">
<span class="material-symbols-outlined text-[18px]">cancel</span>
Reject demand
</button>
</div>
</div>
</div>
</div>
</div>
</div>

<div class="kt-dem-reason-modal hidden" data-testid="kt-dem-ui04-reason-modal" data-kt-dem-reason-modal hidden role="dialog" aria-modal="true" aria-labelledby="kt-dem-ui04-reason-modal-title">
<div class="kt-dem-reason-modal-card">
<div class="kt-dem-reason-modal-header">
<h2 class="kt-dem-reason-modal-title" id="kt-dem-ui04-reason-modal-title" data-kt-dem-reason-title>Return for correction</h2>
<button type="button" class="kt-dem-reason-modal-close" data-testid="kt-dem-ui04-reason-close" data-kt-dem-reason-close aria-label="Close">
<span class="material-symbols-outlined" aria-hidden="true">close</span>
</button>
</div>
<div class="kt-dem-reason-modal-body">
<p class="kt-dem-reason-modal-lead" data-kt-dem-reason-lead>
Provide a clear reason so the requester knows what to correct before resubmitting.
</p>
<label class="kt-dem-reason-modal-label" for="kt-dem-ui04-reason-comment">Reason <span class="text-error" aria-hidden="true">*</span></label>
<textarea id="kt-dem-ui04-reason-comment" class="kt-dem-reason-modal-textarea" rows="4" data-testid="kt-dem-ui04-reason-comment" data-kt-dem-reason-comment data-kt-field="reason" placeholder="e.g., Revise participant quantities and clarify the expected outcome for the revised scope."></textarea>
<p class="kt-dem-reason-modal-error hidden" data-kt-field-error="reason" data-testid="kt-dem-ui04-reason-error"></p>
<div class="kt-dem-reason-hints" data-kt-dem-reason-hints data-testid="kt-dem-ui04-reason-hints" hidden>
<div class="kt-dem-reason-hints-label">What needs correction</div>
<label class="kt-dem-reason-hint">
<span class="kt-dem-ui04-criterion-box relative flex items-center justify-center shrink-0">
<input class="kt-dem-ui04-criterion-input peer" type="checkbox" data-kt-dem-reason-hint="items" data-testid="kt-dem-ui04-hint-items"/>
<span class="material-symbols-outlined kt-dem-ui04-criterion-check" aria-hidden="true">check</span>
</span>
<span>Need items and participant quantities</span>
</label>
<label class="kt-dem-reason-hint">
<span class="kt-dem-ui04-criterion-box relative flex items-center justify-center shrink-0">
<input class="kt-dem-ui04-criterion-input peer" type="checkbox" data-kt-dem-reason-hint="expected_outcome" data-testid="kt-dem-ui04-hint-outcome"/>
<span class="material-symbols-outlined kt-dem-ui04-criterion-check" aria-hidden="true">check</span>
</span>
<span>Expected outcome for the revised scope</span>
</label>
<label class="kt-dem-reason-hint">
<span class="kt-dem-ui04-criterion-box relative flex items-center justify-center shrink-0">
<input class="kt-dem-ui04-criterion-input peer" type="checkbox" data-kt-dem-reason-hint="requester_estimate" data-testid="kt-dem-ui04-hint-estimate"/>
<span class="material-symbols-outlined kt-dem-ui04-criterion-check" aria-hidden="true">check</span>
</span>
<span>Requester estimate</span>
</label>
</div>
</div>
<div class="kt-dem-reason-modal-footer">
<button type="button" class="kt-dem-reason-cancel" data-testid="kt-dem-ui04-reason-cancel" data-kt-dem-reason-cancel>Cancel</button>
<button type="button" class="kt-dem-reason-confirm is-return" data-testid="kt-dem-ui04-reason-confirm" data-kt-dem-reason-confirm>Confirm return</button>
</div>
</div>
</div>
</div>`;
};
