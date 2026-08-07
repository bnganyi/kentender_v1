// DEM-UI-02 / DEM-UI-03 — Stitch main canvas from docs/mvp-1/03_demands/ui_design/DEM-UI-02.html
// (+ returned banner region from DEM-UI-03). Fake top/side nav discarded.
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.demand_form = function () {
	// Select chevron: shared kt_stitch_desk_chrome.css data-URI (no sibling SVG / expand_more stack).
	return `<div class="kt-dem-root kt-dem-form kt-stitch-canvas" data-testid="kt-dem-ui02-root" data-kt-dem-live="0">
<input type="hidden" data-kt-dem-field="procuring_entity" value="">
<input type="hidden" data-kt-dem-field="owner_org_unit" value="">
<input type="hidden" data-kt-dem-field="demand_name" value="">
<div class="bg-surface-container-lowest border-b border-outline-variant px-6 py-8" data-testid="kt-dem-ui02-header">
<div class="max-w-4xl mx-auto">
<div class="flex items-center gap-2 text-on-surface-variant font-body-md mb-2" data-testid="kt-dem-ui02-context" data-kt-dem-scope-mode="single_readonly">
<span class="material-symbols-outlined text-sm" data-kt-dem-scope-ro>account_balance</span>
<span data-kt-dem-scope-ro data-kt-dem-label="procuring_entity">—</span>
<span data-kt-dem-scope-ro>·</span>
<span data-kt-dem-scope-ro data-kt-dem-label="owner_org_unit">—</span>
<span class="hidden" data-kt-dem-edit-only>·</span>
<span class="hidden font-data-mono" data-kt-dem-edit-only data-kt-dem-label="demand_code"></span>
<div class="hidden w-full max-w-xl" data-kt-dem-scope-multi data-testid="kt-dem-ui02-scope-select-wrap">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1" for="kt-dem-ui02-scope-pair">Owning entity and unit</label>
<select id="kt-dem-ui02-scope-pair" class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg pl-4 pr-10 py-2.5 text-on-surface font-body-md appearance-none outline-none" data-kt-dem-scope-pair data-testid="kt-dem-ui02-scope-pair">
<option value="" disabled selected>Select owning entity and unit</option>
</select>
</div>
</div>
<div class="hidden mb-4 p-4 border border-outline-variant bg-surface-container-low text-on-surface" data-kt-dem-scope-blocked data-testid="kt-dem-ui02-scope-blocked">
<div class="font-headline-sm text-headline-sm text-on-surface mb-1">Demand creation blocked</div>
<p class="font-body-md text-body-md text-on-surface-variant mb-0" data-kt-dem-label="blocked_reason">No operational Demand Requester assignment exists.</p>
</div>
<div class="flex items-center gap-4 mb-2">
<h1 class="font-headline-lg text-headline-lg text-on-surface" data-kt-dem-label="page_title">Create demand</h1>
<span class="hidden bg-status-reserved/20 text-status-reserved px-3 py-1 rounded-full text-label-caps font-bold" data-kt-dem-returned-only data-testid="kt-dem-ui02-status-pill">Returned</span>
</div>
<p class="font-body-lg text-body-lg text-on-surface-variant max-w-2xl" data-kt-dem-label="page_subtitle">Describe what is needed, why it is needed and when it is required.</p>
</div>
</div>
<div class="flex-1 p-6" data-testid="kt-dem-ui02-form-canvas">
<div class="max-w-4xl mx-auto space-y-section-gap pb-8">
<div class="hidden kt-dem-return-notice-card flex flex-col gap-4 p-4 bg-status-reserved/5 border border-status-reserved/20 rounded-xl" data-kt-dem-returned-only data-testid="kt-dem-ui02-return-notice">
<div class="flex justify-between items-start gap-4">
<div class="flex flex-col min-w-0">
<span class="text-label-caps font-bold text-status-reserved">Returned by</span>
<span class="text-body-md font-medium" data-kt-dem-label="returned_by">—</span>
</div>
<div class="text-right shrink-0">
<span class="text-label-caps font-bold text-status-reserved">Date</span>
<span class="text-body-md" data-kt-dem-label="returned_at">—</span>
</div>
</div>
<div class="p-4 bg-surface-container-lowest border border-status-reserved/30 rounded-lg">
<div class="font-label-caps text-status-reserved mb-1">Reason for return</div>
<p class="text-body-md mb-0" data-kt-dem-label="return_reason">—</p>
</div>
<div class="hidden" data-kt-dem-correction-wrap data-testid="kt-dem-ui02-correction-list">
<div class="font-label-caps text-status-reserved mb-2">What needs correction</div>
<ul class="list-disc pl-5 space-y-1 font-body-md text-body-md text-on-surface mb-0" data-kt-dem-correction-list></ul>
</div>
</div>
<section class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden" data-testid="kt-dem-ui02-section-need">
<div class="bg-surface-container-low px-card-padding py-3 border-b border-outline-variant flex items-center gap-2">
<span class="material-symbols-outlined text-primary">psychology</span>
<h2 class="font-headline-sm text-headline-sm text-on-surface">Need</h2>
</div>
<div class="p-card-padding space-y-6">
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-2">Demand title</label>
<input class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 text-on-surface font-body-md outline-none" type="text" data-kt-dem-field="title" data-testid="kt-dem-ui02-title" value="">
</div>
<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-2">What is needed?</label>
<textarea class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 text-on-surface font-body-md outline-none resize-none" rows="3" data-kt-dem-field="need_statement" data-testid="kt-dem-ui02-what"></textarea>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-2">Why is it needed?</label>
<textarea class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 text-on-surface font-body-md outline-none resize-none" rows="3" data-kt-dem-field="need_rationale" data-testid="kt-dem-ui02-why"></textarea>
</div>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-2">Expected outcome</label>
<textarea class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 text-on-surface font-body-md outline-none resize-none" rows="2" data-kt-dem-field="expected_outcome" data-kt-dem-highlight="expected_outcome" data-testid="kt-dem-ui02-outcome"></textarea>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-2">Beneficiaries</label>
<textarea class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 text-on-surface font-body-md outline-none resize-none" rows="2" data-kt-dem-field="beneficiaries" data-testid="kt-dem-ui02-beneficiaries"></textarea>
</div>
</div>
</section>
<section class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden" data-testid="kt-dem-ui02-section-delivery">
<div class="bg-surface-container-low px-card-padding py-3 border-b border-outline-variant flex items-center gap-2">
<span class="material-symbols-outlined text-primary">local_shipping</span>
<h2 class="font-headline-sm text-headline-sm text-on-surface">Delivery</h2>
</div>
<div class="p-card-padding grid grid-cols-1 md:grid-cols-2 gap-6">
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-2">Required by</label>
<div class="relative kt-dem-date-wrap" data-testid="kt-dem-ui02-date-wrap">
<!-- Stitch: text field + one calendar_month icon. Native date is an invisible overlay (no second glyph). -->
<input class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg pl-4 pr-10 py-2.5 text-on-surface font-body-md outline-none" type="text" readonly tabindex="-1" data-kt-dem-date-display data-testid="kt-dem-ui02-required-by" value="" placeholder="Select date" aria-label="Required by">
<input class="kt-dem-date-native" type="date" data-kt-dem-field="required_by_date" data-testid="kt-dem-ui02-required-by-native" value="" tabindex="0" aria-label="Required by date">
<span class="material-symbols-outlined kt-dem-date-icon" data-kt-dem-date-icon aria-hidden="true">calendar_month</span>
</div>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-2">Delivery location</label>
<input class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 text-on-surface font-body-md outline-none" type="text" data-kt-dem-field="delivery_location" data-testid="kt-dem-ui02-location" value="">
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-2">Demand route</label>
<div class="relative">
<select class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg pl-4 pr-10 py-2.5 text-on-surface font-body-md appearance-none outline-none" data-kt-dem-field="demand_route" data-testid="kt-dem-ui02-route">
<option value="Standard" selected>Standard</option>
<option value="Additional">Additional</option>
<option value="Emergency">Emergency</option>
</select>
</div>
<p class="mt-2 text-xs text-on-surface-variant">The route describes the need. Procurement Planning determines the procurement method later.</p>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-2">Technical contact <span class="font-normal normal-case text-on-surface-variant/70">(Optional)</span></label>
<div class="relative">
<select class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg pl-4 pr-10 py-2.5 text-on-surface font-body-md appearance-none outline-none text-on-surface-variant" data-kt-dem-field="technical_contact" data-testid="kt-dem-ui02-contact">
<option disabled selected value="">Select internal contact</option>
</select>
</div>
</div>
<div class="md:col-span-2 hidden" data-kt-dem-route-emergency data-testid="kt-dem-ui02-route-justification-wrap">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-2">Route justification</label>
<textarea class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 text-on-surface font-body-md outline-none resize-none" rows="2" data-kt-dem-field="route_justification" data-testid="kt-dem-ui02-route-justification"></textarea>
</div>
</div>
</section>
<section class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden" data-testid="kt-dem-ui02-section-items" data-kt-dem-highlight="items">
<div class="bg-surface-container-low px-card-padding py-3 border-b border-outline-variant flex items-center justify-between">
<div class="flex items-center gap-2">
<span class="material-symbols-outlined text-primary">list_alt</span>
<h2 class="font-headline-sm text-headline-sm text-on-surface">Need items</h2>
</div>
</div>
<div class="p-0 overflow-x-auto">
<table class="w-full text-left border-collapse">
<thead>
<tr class="border-b border-outline-variant bg-surface-container-low">
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant font-medium">Description</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant font-medium w-24">Quantity</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant font-medium w-32">Unit</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant font-medium w-48">Est. amount (Optional)</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant font-medium w-16 text-center">Action</th>
</tr>
</thead>
<tbody class="divide-y divide-outline-variant" data-kt-dem-items-tbody data-testid="kt-dem-ui02-items-tbody"></tbody>
</table>
</div>
<div class="p-3 border-t border-outline-variant bg-surface flex justify-center">
<button type="button" class="flex items-center gap-2 text-primary hover:bg-primary/5 px-4 py-2 rounded-lg font-body-md font-medium transition-colors" data-kt-dem-action="add-item" data-testid="kt-dem-ui02-add-item">
<span class="material-symbols-outlined text-[20px]">add</span>
Add item
</button>
</div>
</section>
<section class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden" data-testid="kt-dem-ui02-section-estimate" data-kt-dem-highlight="requester_estimate">
<div class="bg-surface-container-low px-card-padding py-3 border-b border-outline-variant flex items-center gap-2">
<span class="material-symbols-outlined text-primary">calculate</span>
<h2 class="font-headline-sm text-headline-sm text-on-surface">Estimate &amp; supporting info</h2>
</div>
<div class="p-card-padding grid grid-cols-1 md:grid-cols-2 gap-6">
<div class="md:col-span-2 flex flex-col md:flex-row md:items-end gap-6 pb-4 border-b border-outline-variant/50">
<div class="flex-1">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1">Requester estimate</label>
<div class="text-xs text-on-surface-variant mb-2">Calculated from items above</div>
<div class="flex items-baseline gap-2">
<span class="font-data-mono text-on-surface-variant" data-kt-dem-label="currency">KES</span>
<span class="font-headline-lg text-headline-lg text-on-surface font-data-mono" data-kt-dem-label="requester_estimate" data-testid="kt-dem-ui02-estimate-total">0</span>
</div>
</div>
<div class="hidden w-full md:w-64" data-kt-dem-available-funding data-testid="kt-dem-ui02-available-funding">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1">Available funding</label>
<div class="text-xs text-on-surface-variant mb-2">Read-only context from return</div>
<div class="flex items-baseline gap-2">
<span class="font-data-mono text-on-surface-variant" data-kt-dem-label="currency">KES</span>
<span class="font-headline-sm text-headline-sm text-on-surface font-data-mono" data-kt-dem-label="available_funding">—</span>
</div>
</div>
<div class="w-full md:w-64">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-2">Confidence</label>
<div class="relative">
<select class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg pl-4 pr-10 py-2.5 text-on-surface font-body-md appearance-none outline-none" data-kt-dem-field="estimate_confidence" data-testid="kt-dem-ui02-confidence">
<option value="High">High</option>
<option value="Medium" selected>Medium</option>
<option value="Low">Low</option>
</select>
</div>
</div>
</div>
<div class="md:col-span-2">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-2">Estimate basis</label>
<textarea class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 text-on-surface font-body-md outline-none resize-none" rows="2" data-kt-dem-field="estimate_basis" data-testid="kt-dem-ui02-estimate-basis"></textarea>
</div>
<div class="md:col-span-2">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-2">Supporting documents <span class="font-normal normal-case text-on-surface-variant/70">(Optional)</span></label>
<div class="border-2 border-dashed border-outline-variant rounded-lg p-6 flex flex-col items-center justify-center text-center hover:bg-surface-container-lowest transition-colors cursor-pointer bg-surface" data-testid="kt-dem-ui02-docs-dropzone" role="button" tabindex="0">
<span class="material-symbols-outlined text-outline text-3xl mb-2">upload_file</span>
<div class="font-body-md text-on-surface font-medium">Click to upload or drag and drop</div>
<div class="font-body-sm text-sm text-on-surface-variant mt-1">PDF, DOCX, XLSX (Max. 10MB)</div>
</div>
</div>
</div>
</section>
</div>
</div>
<div class="kt-dem-form-footer fixed bottom-0 left-0 md:left-64 right-0 bg-surface-container-lowest border-t border-outline-variant p-4 z-30 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]" data-testid="kt-dem-ui02-footer">
<div class="max-w-4xl mx-auto flex items-center justify-between">
<button type="button" class="px-5 py-2.5 rounded-lg border border-transparent hover:bg-surface-container text-on-surface-variant font-body-md font-medium transition-colors" data-kt-dem-action="cancel" data-kt-dem-cancel-create data-testid="kt-dem-ui02-cancel">Cancel</button>
<button type="button" class="hidden px-5 py-2.5 rounded-lg border border-transparent text-error hover:bg-error/5 font-body-md font-medium transition-colors" data-kt-dem-action="cancel-demand" data-kt-dem-returned-only data-testid="kt-dem-ui02-cancel-demand">Cancel demand</button>
<div class="flex gap-3">
<button type="button" class="px-5 py-2.5 rounded-lg border border-outline-variant hover:bg-surface-container text-on-surface font-body-md font-medium transition-colors" data-kt-dem-action="save" data-testid="kt-dem-ui02-save">Save draft</button>
<button type="button" class="px-5 py-2.5 rounded-lg bg-primary text-on-primary hover:bg-primary/90 font-body-md font-medium transition-colors flex items-center gap-2 shadow-sm" data-kt-dem-action="submit" data-testid="kt-dem-ui02-submit">
<span data-kt-dem-label="submit_label">Submit for business review</span>
<span class="material-symbols-outlined text-[18px]">send</span>
</button>
</div>
</div>
</div>
<div class="kt-dem-reason-modal hidden" data-testid="kt-dem-ui02-cancel-modal" data-kt-dem-cancel-modal hidden role="dialog" aria-modal="true" aria-labelledby="kt-dem-ui02-cancel-modal-title">
<div class="kt-dem-reason-modal-card">
<div class="kt-dem-reason-modal-header">
<h2 class="kt-dem-reason-modal-title" id="kt-dem-ui02-cancel-modal-title">Cancel demand</h2>
<button type="button" class="kt-dem-reason-modal-close" data-testid="kt-dem-ui02-cancel-modal-close" data-kt-dem-cancel-close aria-label="Close">
<span class="material-symbols-outlined" aria-hidden="true">close</span>
</button>
</div>
<div class="kt-dem-reason-modal-body">
<p class="kt-dem-reason-modal-lead">
This permanently cancels the demand. Provide a clear reason for the audit trail.
</p>
<label class="kt-dem-reason-modal-label" for="kt-dem-ui02-cancel-modal-comment">Reason for cancellation <span class="text-error" aria-hidden="true">*</span></label>
<textarea id="kt-dem-ui02-cancel-modal-comment" class="kt-dem-reason-modal-textarea" rows="4" data-testid="kt-dem-ui02-cancel-modal-comment" data-kt-dem-cancel-comment placeholder="e.g., Need withdrawn — funding no longer available for this financial year."></textarea>
<p class="kt-dem-reason-modal-error hidden" data-kt-dem-cancel-error data-testid="kt-dem-ui02-cancel-modal-error"></p>
</div>
<div class="kt-dem-reason-modal-footer">
<button type="button" class="kt-dem-reason-cancel" data-testid="kt-dem-ui02-cancel-modal-dismiss" data-kt-dem-cancel-dismiss>Keep demand</button>
<button type="button" class="kt-dem-reason-confirm is-reject" data-testid="kt-dem-ui02-cancel-modal-confirm" data-kt-dem-cancel-confirm>Cancel demand</button>
</div>
</div>
</div>
<template data-kt-dem-item-template>
<tr class="hover:bg-surface-container transition-colors group" data-kt-dem-item-row>
<td class="py-3 px-4">
<input class="w-full bg-surface-container-lowest border border-outline-variant rounded px-2 py-1.5 outline-none font-body-md text-on-surface" type="text" data-kt-dem-item="description" value="">
</td>
<td class="py-3 px-4">
<input class="w-full bg-surface-container-lowest border border-outline-variant rounded px-2 py-1.5 outline-none font-data-mono text-data-mono text-on-surface" type="number" data-kt-dem-item="quantity" value="1" min="0" step="any">
</td>
<td class="py-3 px-4">
<div class="relative"><select class="w-full bg-surface-container-lowest border border-outline-variant rounded px-2 py-1.5 pr-8 outline-none font-body-md text-on-surface appearance-none" data-kt-dem-item="uom"><option value="Lot">Lot</option><option value="Pieces">Pieces</option><option value="Months">Months</option></select></div>
</td>
<td class="py-3 px-4 relative">
<span class="absolute left-6 top-[21px] font-data-mono text-data-mono text-on-surface-variant text-sm z-10" data-kt-dem-currency-prefix>KES</span>
<input class="w-full bg-surface-container-lowest border border-outline-variant rounded pl-12 pr-2 py-1.5 outline-none font-data-mono text-data-mono text-on-surface text-right" type="text" data-kt-dem-item="requester_estimate" value="">
</td>
<td class="py-3 px-4 text-center">
<button type="button" class="text-on-surface-variant hover:text-error transition-colors p-1 rounded" data-kt-dem-action="remove-item" aria-label="Remove item">
<span class="material-symbols-outlined text-[20px]">delete</span>
</button>
</td>
</tr>
</template>
</div>`;
};
