// DEM-UIC-002 / DEM-UI-04 / DEM-UI-05 — Shared Demand review shell.
// Stitch: DEM-UI-04.html (Business) + DEM-UI-05.html / DEM-UI-05A.html (Enrichment).
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.demand_review = function () {
	var recordChrome =
		(kentender_procurement.ui_fixtures.demand_record_chrome &&
			kentender_procurement.ui_fixtures.demand_record_chrome()) ||
		"";
	return `<div class="kt-dem-root kt-dem-review kt-stitch-canvas" data-testid="kt-dem-ui04-root" data-kt-dem-live="0" data-kt-dem-review-stage="">
<div class="kt-dem-review-inner p-6 max-w-7xl mx-auto w-full">
${recordChrome}
<div data-kt-dem-business-host data-testid="kt-dem-business-host">
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

<div class="kt-dem-enrichment hidden" data-kt-dem-enrichment-host data-testid="kt-dem-ui05-root" hidden>
<div class="kt-dem-enrich-role-banner hidden" data-kt-dem-enrich-role-banner data-testid="kt-dem-ui05-role-banner" hidden>
<span class="material-symbols-outlined text-[18px] shrink-0" aria-hidden="true">lock</span>
<p class="text-sm mb-0"><span class="font-medium">Procurement Approval Authority required.</span> Save / Assign Strategy / Send stay disabled until you sign in as PAA (e.g. <span class="font-data-mono">moh.procurement.approver@example.test</span>).</p>
</div>
<div class="kt-dem-enrichment-stack flex flex-col gap-3 max-w-4xl mx-auto w-full" data-testid="kt-dem-ui05-main">
<section class="kt-dem-ui05-card bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden flex flex-col p-0" data-testid="kt-dem-ui05-section-business">
<div class="kt-dem-ui05-card-head bg-surface-container-low">
<h2 class="kt-dem-ui05-card-title font-headline-sm text-headline-sm text-on-surface mb-0">1. Business Request</h2>
</div>
<div class="kt-dem-ui05-card-body flex flex-col gap-3" data-kt-dem-business-summary-body data-testid="kt-dem-ui05-business-body">
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1">Summary of Need</span>
<p class="font-body-md text-body-md text-on-surface mb-0" data-kt-dem-label="need_statement">—</p>
</div>
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1">Beneficiaries</span>
<p class="font-body-md text-body-md text-on-surface mb-0" data-kt-dem-label="beneficiaries">—</p>
</div>
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1">Required By</span>
<p class="font-body-md text-body-md text-on-surface mb-0" data-kt-dem-label="required_by_display">—</p>
</div>
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1">Business Approver</span>
<p class="font-body-md text-body-md text-on-surface mb-0" data-kt-dem-label="business_approver_label">—</p>
</div>
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1">Delivery Location</span>
<p class="font-body-md text-body-md text-on-surface mb-0" data-kt-dem-label="delivery_location">—</p>
</div>
</div>
</div>
</section>

<section class="kt-dem-ui05-card bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden flex flex-col p-0" data-testid="kt-dem-ui05-section-classify">
<div class="kt-dem-ui05-card-head bg-surface-container-low">
<h2 class="kt-dem-ui05-card-title font-headline-sm text-headline-sm text-on-surface mb-0">2. Classification &amp; Estimate</h2>
</div>
<div class="kt-dem-ui05-card-body flex flex-col gap-3">
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
<div class="flex flex-col gap-1">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase" for="kt-dem-ui05-category">Category</label>
<select id="kt-dem-ui05-category" class="w-full border border-outline-variant rounded-lg px-3 py-2 font-body-md text-on-surface bg-surface-container-lowest" data-kt-dem-field="procurement_category" data-testid="kt-dem-ui05-category"></select>
</div>
<div class="flex flex-col gap-1">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase" for="kt-dem-ui05-route">Demand Route</label>
<select id="kt-dem-ui05-route" class="w-full border border-outline-variant rounded-lg px-3 py-2 font-body-md text-on-surface bg-surface-container-lowest" data-kt-dem-field="demand_route" data-testid="kt-dem-ui05-route"></select>
</div>
</div>
<div class="flex flex-col gap-1">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase" for="kt-dem-ui05-estimate-basis">Estimate Basis</label>
<textarea id="kt-dem-ui05-estimate-basis" class="w-full border border-outline-variant rounded-lg px-3 py-2 font-body-md text-on-surface bg-surface-container-lowest" rows="2" data-kt-dem-field="estimate_basis" data-testid="kt-dem-ui05-estimate-basis"></textarea>
</div>
<div class="kt-dem-ui05-estimate-band grid grid-cols-2 gap-4 bg-surface-container-low rounded-lg p-4 border border-outline-variant" data-testid="kt-dem-ui05-estimate-band">
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1">Requester Estimate</span>
<span class="kt-dem-ui05-requester-estimate font-data-mono text-data-mono text-on-surface text-lg" data-kt-dem-label="estimate_header_display" data-testid="kt-dem-ui05-requester-estimate">—</span>
</div>
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1">Confirmed Estimate</span>
<div class="kt-dem-ui05-confirmed-estimate flex items-center gap-2">
<span class="kt-dem-ui05-confirmed-currency font-data-mono text-data-mono text-primary font-bold" data-kt-dem-label="currency">KES</span>
<input class="kt-dem-ui05-confirmed-input font-data-mono text-data-mono text-primary font-bold text-lg w-full" type="text" data-kt-dem-field="confirmed_estimate" data-testid="kt-dem-ui05-confirmed-estimate" placeholder="0" autocomplete="off"/>
</div>
</div>
</div>
</div>
</section>

<section class="kt-dem-ui05-card bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden flex flex-col p-0" data-testid="kt-dem-ui05-section-items">
<div class="kt-dem-ui05-card-head bg-surface-container-low flex justify-between items-center">
<h2 class="kt-dem-ui05-card-title font-headline-sm text-headline-sm text-on-surface mb-0 flex items-center gap-2">3. Need Items</h2>
<button type="button" class="kt-dem-ui05-add-item text-primary font-body-md font-medium flex items-center gap-1 bg-transparent border-0 p-0" data-kt-dem-action="enrich-add-item" data-testid="kt-dem-ui05-add-item">
<span class="material-symbols-outlined text-sm" aria-hidden="true">add</span> Add Item
</button>
</div>
<div class="kt-dem-ui05-items-scroll">
<table class="kt-dem-ui05-items-table w-full text-left border-collapse" data-testid="kt-dem-ui05-items-table">
<thead>
<tr class="bg-surface-container-low border-b border-outline-variant">
<th class="p-3 font-label-caps text-label-caps text-on-surface-variant uppercase">Description</th>
<th class="p-3 font-label-caps text-label-caps text-on-surface-variant uppercase text-right">Qty</th>
<th class="p-3 font-label-caps text-label-caps text-on-surface-variant uppercase">Unit</th>
<th class="p-3 font-label-caps text-label-caps text-on-surface-variant uppercase text-right">Unit Est.</th>
<th class="p-3 font-label-caps text-label-caps text-on-surface-variant uppercase text-right">Total Est.</th>
<th class="p-3 font-label-caps text-label-caps text-on-surface-variant uppercase text-right">Action</th>
</tr>
</thead>
<tbody data-kt-dem-enrich-items-tbody data-testid="kt-dem-ui05-items-body"></tbody>
<tfoot>
<tr class="bg-surface-container-low">
<td class="p-3 text-right font-label-caps text-label-caps text-on-surface-variant uppercase" colspan="4">Total Estimated Value</td>
<td class="p-3 font-data-mono text-primary font-bold text-right text-lg" data-kt-dem-label="enrich_items_total" data-testid="kt-dem-ui05-items-total">KES 0</td>
<td></td>
</tr>
</tfoot>
</table>
</div>
</section>

<section class="kt-dem-ui05-card bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden flex flex-col p-0" data-testid="kt-dem-ui05-section-strategy">
<div class="kt-dem-ui05-card-head bg-surface-container-low flex justify-between items-center gap-3">
<h2 class="kt-dem-ui05-card-title font-headline-sm text-headline-sm text-on-surface mb-0">4. Strategy Alignment</h2>
<span class="px-2 py-0.5 rounded-full bg-surface-container-high text-on-surface-variant text-label-caps font-label-caps" data-kt-dem-label="strategy_alignment_pill" data-testid="kt-dem-ui05-strategy-pill">Not assigned</span>
</div>
<div class="kt-dem-ui05-card-body flex flex-col gap-3">
<div data-kt-dem-strategy-empty data-testid="kt-dem-ui05-strategy-empty">
<p class="font-body-md text-on-surface-variant mb-3">No Primary Strategy target assigned yet.</p>
<button type="button" class="text-primary font-body-md font-medium hover:underline bg-transparent border-0 p-0" data-kt-dem-action="assign-strategy" data-testid="kt-dem-ui05-assign-strategy">Assign strategy</button>
</div>
<div class="hidden" data-kt-dem-strategy-assigned data-testid="kt-dem-ui05-strategy-assigned" hidden>
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
<div class="md:col-span-2">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1">Primary Target</span>
<p class="font-body-lg text-on-surface font-semibold mb-0" data-kt-dem-label="primary_target_name">—</p>
<p class="font-data-mono text-data-mono text-on-surface-variant text-sm mb-0" data-kt-dem-label="primary_target_code"></p>
</div>
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1">Plan</span>
<p class="font-body-md text-on-surface mb-0" data-kt-dem-label="primary_plan_label" data-testid="kt-dem-ui05-primary-plan">—</p>
</div>
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1">Path</span>
<p class="font-body-md text-on-surface mb-0" data-kt-dem-label="primary_hierarchy_path" data-testid="kt-dem-ui05-primary-path">—</p>
</div>
</div>
<div class="flex items-center gap-4 pt-2 border-t border-outline-variant mt-2">
<button type="button" class="text-primary font-body-md text-sm font-medium hover:underline bg-transparent border-0 p-0" data-kt-dem-action="change-strategy" data-testid="kt-dem-ui05-change-strategy">Change</button>
<button type="button" class="text-on-surface-variant font-body-md text-sm font-medium hover:underline bg-transparent border-0 p-0" data-kt-dem-action="remove-strategy" data-testid="kt-dem-ui05-remove-strategy">Remove</button>
</div>
</div>
</div>
</section>

<section class="kt-dem-ui05-card bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden flex flex-col p-0" data-testid="kt-dem-ui05-section-pvc">
<div class="kt-dem-ui05-card-head bg-surface-container-low">
<h2 class="kt-dem-ui05-card-title font-headline-sm text-headline-sm text-on-surface mb-0">5. Public-value Commitments</h2>
</div>
<div class="kt-dem-ui05-card-body flex flex-col gap-3">
<p class="text-sm text-on-surface-variant mb-0" data-kt-dem-pvc-empty data-testid="kt-dem-ui05-pvc-empty">No applicable public-value commitments for the current Strategy selection.</p>
<div class="overflow-x-auto rounded-lg border border-outline-variant hidden" data-kt-dem-pvc-table hidden>
<table class="w-full text-left border-collapse text-sm">
<thead>
<tr class="bg-surface-container-low border-b border-outline-variant">
<th class="p-2 font-label-caps text-label-caps text-on-surface-variant uppercase">Commitment</th>
<th class="p-2 font-label-caps text-label-caps text-on-surface-variant uppercase">Treatment</th>
<th class="p-2 font-label-caps text-label-caps text-on-surface-variant uppercase">Rationale</th>
</tr>
</thead>
<tbody data-kt-dem-pvc-tbody data-testid="kt-dem-ui05-pvc-body"></tbody>
</table>
</div>
</div>
</section>

<section class="kt-dem-ui05-card bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden flex flex-col p-0" data-testid="kt-dem-ui05-section-duplication">
<div class="kt-dem-ui05-card-head bg-surface-container-low">
<h2 class="kt-dem-ui05-card-title font-headline-sm text-headline-sm text-on-surface mb-0">6. Duplication &amp; Aggregation</h2>
</div>
<div class="kt-dem-ui05-card-body flex flex-col gap-3">
<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-2">
<div class="flex items-start gap-3 p-3 bg-surface-container-low rounded-lg border border-outline-variant">
<span class="material-symbols-outlined text-status-available mt-0.5" aria-hidden="true">check_circle</span>
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1">Potential Duplicate</span>
<span class="font-body-md text-on-surface font-medium" data-kt-dem-label="duplicate_assessment">None found</span>
</div>
</div>
<div class="flex items-start gap-3 p-3 bg-surface-container-low rounded-lg border border-outline-variant">
<span class="material-symbols-outlined text-status-reserved mt-0.5" aria-hidden="true">link</span>
<div class="w-full">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1" for="kt-dem-ui05-related">Related Demands</label>
<input id="kt-dem-ui05-related" class="w-full border border-outline-variant rounded-lg px-3 py-2 font-body-md text-on-surface bg-surface-container-lowest" type="text" data-kt-dem-field="related_demands_note" data-testid="kt-dem-ui05-related-note" placeholder="Notes on related demands"/>
</div>
</div>
</div>
<div class="flex flex-col gap-1">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase" for="kt-dem-ui05-aggregation">Aggregation Treatment</label>
<select id="kt-dem-ui05-aggregation" class="w-full border border-outline-variant rounded-lg px-3 py-2 font-body-md text-on-surface bg-surface-container-lowest" data-kt-dem-field="aggregation_treatment" data-testid="kt-dem-ui05-aggregation"></select>
</div>
<div class="flex flex-col gap-1">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase" for="kt-dem-ui05-aggregation-rationale">Rationale</label>
<textarea id="kt-dem-ui05-aggregation-rationale" class="w-full border border-outline-variant rounded-lg px-3 py-2 font-body-md text-on-surface bg-surface-container-lowest" rows="3" data-kt-dem-field="aggregation_rationale" data-testid="kt-dem-ui05-aggregation-rationale" placeholder="Provide justification for the selected treatment..."></textarea>
</div>
</div>
</section>
</div>
</div>

<div class="kt-dem-budget hidden" data-kt-dem-budget-host data-testid="kt-dem-ui06-root" hidden>
<div class="kt-dem-budget-role-banner hidden" data-kt-dem-budget-role-banner data-testid="kt-dem-ui06-role-banner" hidden>
<span class="material-symbols-outlined text-[18px]" aria-hidden="true">info</span>
<span>You can view this Budget confirmation, but only a Budget Officer can confirm or return funding.</span>
</div>
<div class="kt-dem-budget-exception hidden" data-kt-dem-budget-exception data-testid="kt-dem-ui06-exception-banner" hidden>
<span class="material-symbols-outlined text-[18px]" aria-hidden="true">warning</span>
<span data-kt-dem-label="funding_exception_text">Funding exception — return to Procurement or resolve via exception flow.</span>
</div>
<!-- DEM-UI-06: left col sizes to content; Summary grows into leftover space (Stitch), Strategy never shrinks/clips. -->
<div class="kt-dem-budget-stack" data-testid="kt-dem-ui06-main">
<div class="kt-dem-budget-grid">
<div class="kt-dem-budget-col-left">
<section class="kt-dem-ui06-card kt-dem-ui06-summary bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden" data-testid="kt-dem-ui06-summary">
<div class="bg-surface-container-low px-4 py-3 border-b border-outline-variant flex items-center gap-2">
<span class="material-symbols-outlined text-primary text-[20px]" aria-hidden="true">summarize</span>
<h2 class="kt-dem-ui06-card-title font-headline-sm text-headline-sm text-on-surface mb-0">Funding Summary</h2>
</div>
<div class="kt-dem-ui06-card-body">
<div class="kt-dem-ui06-summary-rows">
<div class="kt-dem-ui06-summary-row">
<span class="text-on-surface-variant">Demand estimate</span>
<span class="text-on-surface font-data-mono" data-kt-dem-label="funding_estimate_display">—</span>
</div>
<div class="kt-dem-ui06-summary-row">
<span class="text-on-surface-variant">Proposed funding</span>
<span class="text-on-surface font-data-mono" data-kt-dem-label="funding_proposed_display">—</span>
</div>
<div class="kt-dem-ui06-summary-row">
<span class="text-on-surface-variant">Difference</span>
<span class="text-on-surface font-data-mono" data-kt-dem-label="funding_difference_display">—</span>
</div>
</div>
<div class="kt-dem-ui06-condition" data-testid="kt-dem-ui06-condition" data-kt-dem-funding-condition>
<span class="material-symbols-outlined" data-kt-dem-funding-condition-icon aria-hidden="true">check_circle</span>
<div>
<p class="font-body-md font-bold text-on-surface mb-0" data-kt-dem-label="funding_condition">—</p>
<p class="font-label-caps text-label-caps text-on-surface-variant mt-1 mb-0">Funding condition</p>
</div>
</div>
</div>
</section>
<section class="kt-dem-ui06-card kt-dem-ui06-strategy bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden" data-testid="kt-dem-ui06-strategy-check">
<div class="bg-surface-container-low px-4 py-3 border-b border-outline-variant flex items-center gap-2">
<span class="material-symbols-outlined text-primary text-[20px]" aria-hidden="true">fact_check</span>
<h2 class="kt-dem-ui06-card-title font-headline-sm text-headline-sm text-on-surface mb-0">Strategy Alignment</h2>
</div>
<div class="kt-dem-ui06-card-body">
<div class="kt-dem-ui06-strategy-box">
<div>
<span class="kt-dem-ui06-meta-label">Demand Target</span>
<p class="kt-dem-ui06-strategy-target" data-kt-dem-label="funding_demand_target">—</p>
</div>
<div class="kt-dem-ui06-strategy-swap" aria-hidden="true">
<span class="material-symbols-outlined text-[16px]">sync_alt</span>
</div>
<div>
<span class="kt-dem-ui06-meta-label">Budget Line Target</span>
<p class="kt-dem-ui06-strategy-target" data-kt-dem-label="funding_budget_line_target">—</p>
</div>
</div>
<div class="kt-dem-ui06-strategy-result" data-kt-dem-funding-strategy-result data-testid="kt-dem-ui06-strategy-result">
<span class="material-symbols-outlined text-[18px]" data-kt-dem-funding-strategy-icon aria-hidden="true">verified_user</span>
<span data-kt-dem-label="funding_strategy_result">—</span>
</div>
</div>
</section>
</div>
<div class="kt-dem-budget-col-right">
<section class="kt-dem-ui06-card bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden" data-testid="kt-dem-ui06-recommendation">
<!-- Content-sized — do not stretch with empty cavern for Adjust (Adjust is a sibling section). -->
<div class="kt-dem-ui06-recommend-head bg-surface-container-low px-4 py-3 border-b border-outline-variant flex justify-between items-center gap-3">
<h3 class="kt-dem-ui06-recommend-title kt-dem-ui06-card-title font-headline-sm text-headline-sm text-primary flex items-center gap-2 mb-0">
<span class="material-symbols-outlined text-primary text-[20px]" aria-hidden="true">memory</span>
System-recommended allocation
</h3>
<span class="kt-dem-ui06-alloc-badge px-2 py-1 rounded-full text-label-caps font-label-caps" data-kt-dem-label="funding_alloc_status" data-kt-dem-funding-alloc-badge>Pending</span>
</div>
<div class="kt-dem-ui06-card-body">
<div class="kt-dem-ui06-rec-stack" data-kt-dem-funding-rec-body>
<div class="kt-dem-ui06-rec-meta">
<div>
<p class="kt-dem-ui06-meta-label">Budget</p>
<p class="kt-dem-ui06-meta-value" data-kt-dem-label="funding_budget_display">—</p>
</div>
<div>
<p class="kt-dem-ui06-meta-label">Owning unit</p>
<p class="kt-dem-ui06-meta-value" data-kt-dem-label="funding_ou_display">—</p>
</div>
<div class="kt-dem-ui06-rec-meta-line">
<p class="kt-dem-ui06-meta-label">Budget line</p>
<p class="kt-dem-ui06-meta-value kt-dem-ui06-meta-value--line" data-kt-dem-label="funding_line_display">—</p>
</div>
</div>
<div class="kt-dem-ui06-progress" data-testid="kt-dem-ui06-progress">
<div class="kt-dem-ui06-progress-head">
<span class="kt-dem-ui06-progress-label">Allocation Progress</span>
<span class="kt-dem-ui06-progress-utilized" data-kt-dem-label="funding_utilized_display">—</span>
</div>
<div class="kt-dem-ui06-progress-track" data-kt-dem-funding-progress-track aria-hidden="true">
<div class="kt-dem-ui06-progress-committed bg-status-committed" data-kt-dem-funding-bar="committed" style="width:0%"></div>
<div class="kt-dem-ui06-progress-reserved bg-status-reserved" data-kt-dem-funding-bar="reserved" style="width:0%"></div>
<div class="kt-dem-ui06-progress-available bg-status-available" data-kt-dem-funding-bar="available" style="width:0%"></div>
</div>
<div class="kt-dem-ui06-progress-legend">
<div class="kt-dem-ui06-progress-legend-item"><span class="kt-dem-ui06-dot bg-status-committed"></span><span>Committed</span></div>
<div class="kt-dem-ui06-progress-legend-item"><span class="kt-dem-ui06-dot bg-status-reserved"></span><span>Reserved</span></div>
<div class="kt-dem-ui06-progress-legend-item"><span class="kt-dem-ui06-dot bg-status-available"></span><span>Available</span></div>
</div>
</div>
<div class="kt-dem-ui06-money-tiles" data-testid="kt-dem-ui06-money-tiles">
<div class="kt-dem-ui06-money-tile">
<p class="kt-dem-ui06-money-tile-label">Approved</p>
<p class="kt-dem-ui06-money-tile-value" data-kt-dem-label="funding_approved_display">—</p>
</div>
<div class="kt-dem-ui06-money-tile">
<p class="kt-dem-ui06-money-tile-label">Available before</p>
<p class="kt-dem-ui06-money-tile-value" data-kt-dem-label="funding_avail_before_display">—</p>
</div>
<div class="kt-dem-ui06-money-tile kt-dem-ui06-tile-allocate">
<p class="kt-dem-ui06-money-tile-label">Allocate</p>
<p class="kt-dem-ui06-money-tile-value" data-kt-dem-label="funding_allocate_display">—</p>
</div>
<div class="kt-dem-ui06-money-tile kt-dem-ui06-tile-after">
<p class="kt-dem-ui06-money-tile-label">Available after</p>
<p class="kt-dem-ui06-money-tile-value" data-kt-dem-label="funding_avail_after_display">—</p>
</div>
</div>
</div>
<p class="kt-dem-ui06-rec-empty hidden text-body-md text-on-surface-variant mb-0" data-kt-dem-funding-rec-empty data-testid="kt-dem-ui06-rec-empty" hidden>
No system recommendation is available. Use Adjust recommendation below, return to Procurement, or resolve via the exception flow.
</p>
</div>
</section>
<!-- Separate section — not nested under System-recommended allocation. -->
<section class="kt-dem-ui06-card kt-dem-ui06-adjust-section bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden" data-testid="kt-dem-ui06-adjust-panel" data-kt-dem-funding-adjust-panel>
<div class="bg-surface-container-low px-4 py-3 border-b border-outline-variant flex items-center gap-2">
<span class="material-symbols-outlined text-primary text-[20px]" aria-hidden="true">tune</span>
<h3 class="kt-dem-ui06-card-title font-headline-sm text-headline-sm text-on-surface mb-0">Adjust recommendation</h3>
</div>
<div class="kt-dem-ui06-card-body kt-dem-ui06-adjust-body">
<p class="kt-dem-ui06-adjust-help text-body-md text-on-surface-variant mb-0">
Choose an eligible Budget Line and allocation amount. Applying a sufficient allocation clears the funding exception.
</p>
<div class="kt-dem-ui06-adjust-fields">
<label class="kt-dem-ui06-adjust-field">
<span class="kt-dem-ui06-meta-label">Budget line</span>
<select class="kt-dem-ui06-adjust-select" data-kt-dem-field="funding_adjust_line" data-testid="kt-dem-ui06-adjust-line">
<option value="">Select budget line…</option>
</select>
</label>
<label class="kt-dem-ui06-adjust-field">
<span class="kt-dem-ui06-meta-label">Allocation amount</span>
<input class="kt-dem-ui06-adjust-input" type="text" inputmode="decimal" data-kt-dem-field="funding_adjust_amount" data-testid="kt-dem-ui06-adjust-amount" placeholder="0"/>
</label>
</div>
<button type="button" class="kt-dem-ui06-btn kt-dem-ui06-btn--primary" data-kt-dem-action="budget-apply-adjust" data-testid="kt-dem-ui06-apply-adjust">
Apply adjustment
</button>
</div>
</section>
</div>
</div>
<section class="kt-dem-ui06-card kt-dem-ui06-signoff bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden" data-testid="kt-dem-ui06-signoff">
<label class="flex items-start gap-3 cursor-pointer mb-6" data-testid="kt-dem-ui06-confirm-checkbox-label">
<span class="kt-dem-ui06-checkbox-wrap relative flex items-center justify-center shrink-0 mt-1">
<input class="kt-dem-ui06-checkbox peer" type="checkbox" data-kt-dem-field="funding_confirm_checkbox" data-testid="kt-dem-ui06-confirm-checkbox"/>
<span class="material-symbols-outlined kt-dem-ui06-checkbox-check" aria-hidden="true">check</span>
</span>
<span class="font-body-lg text-on-surface">I confirm that the selected active Budget allocation is appropriate and sufficient for this Demand.</span>
</label>
<p class="font-label-caps text-label-caps text-on-surface-variant mt-0 mb-0 pl-8 flex items-center gap-1" data-testid="kt-dem-ui06-no-reserve-note">
<span class="material-symbols-outlined text-[14px] shrink-0" aria-hidden="true">info</span>
<span data-kt-dem-label="funding_no_reserve_note">Confirmation does not reserve funds or approve the Demand. Funding is rechecked and reserved during Final approval.</span>
</p>
<!-- Stitch DEM-UI-06: actions live in the sign-off card (not a separate sticky bar). -->
<div class="kt-dem-ui06-actions flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-outline-variant pt-4 mt-6" data-testid="kt-dem-ui06-footer">
<button type="button" class="kt-dem-ui06-btn kt-dem-ui06-btn--ghost flex items-center gap-2 order-3 sm:order-1" data-kt-dem-action="budget-return" data-testid="kt-dem-ui06-return">
<span class="material-symbols-outlined text-[18px]" aria-hidden="true">arrow_back</span>
Return to Procurement
</button>
<div class="kt-dem-budget-footer-actions flex flex-col sm:flex-row gap-3 w-full sm:w-auto order-1 sm:order-2">
<button type="button" class="kt-dem-ui06-btn kt-dem-ui06-btn--secondary" data-kt-dem-action="budget-adjust" data-testid="kt-dem-ui06-adjust">Adjust allocation</button>
<button type="button" class="kt-dem-ui06-btn kt-dem-ui06-btn--primary" data-kt-dem-action="budget-confirm" data-testid="kt-dem-ui06-confirm" disabled>
<span class="material-symbols-outlined text-[18px]" aria-hidden="true">check_circle</span>
Confirm funding
</button>
</div>
</div>
</section>
</div>
</div>

<footer class="kt-dem-enrichment-footer hidden" data-kt-dem-enrichment-footer data-testid="kt-dem-ui05-footer" hidden>
<div class="kt-dem-enrichment-footer-inner max-w-4xl mx-auto flex items-center justify-between gap-4">
<button type="button" class="kt-dem-enrich-btn kt-dem-enrich-btn--ghost px-5 py-2.5 rounded-lg border border-transparent text-on-surface-variant font-body-md font-medium" data-kt-dem-action="enrich-return" data-testid="kt-dem-ui05-return">Return for correction</button>
<div class="kt-dem-enrichment-footer-actions flex gap-3">
<button type="button" class="kt-dem-enrich-btn kt-dem-enrich-btn--secondary px-5 py-2.5 rounded-lg border border-outline-variant text-on-surface font-body-md font-medium" data-kt-dem-action="enrich-save" data-testid="kt-dem-ui05-save">Save enrichment</button>
<button type="button" class="kt-dem-enrich-btn kt-dem-enrich-btn--primary px-5 py-2.5 rounded-lg bg-primary text-on-primary font-body-md font-medium flex items-center justify-center gap-2" data-kt-dem-action="enrich-send" data-testid="kt-dem-ui05-send" disabled>Send for Budget confirmation <span class="material-symbols-outlined text-[18px]" aria-hidden="true">send</span></button>
</div>
</div>
</footer>

<!-- Read-only Demand details drawer (Budget confirmation — View Details). Stitch right-drawer pattern. -->
<div class="kt-dem-details-drawer hidden" data-kt-dem-details-drawer data-testid="kt-dem-details-drawer" hidden role="dialog" aria-modal="true" aria-labelledby="kt-dem-details-drawer-title">
<div class="kt-dem-details-drawer-panel">
<div class="kt-dem-details-drawer-header">
<div class="flex justify-between items-start gap-3">
<div>
<h2 class="font-headline-md text-headline-md text-on-surface mb-1" id="kt-dem-details-drawer-title">Demand details</h2>
<p class="text-body-md text-on-surface-variant mb-0">Read-only summary for Budget confirmation.</p>
</div>
<button type="button" class="kt-dem-details-drawer-close" data-kt-dem-action="close-details-drawer" data-testid="kt-dem-details-close" aria-label="Close">
<span class="material-symbols-outlined" aria-hidden="true">close</span>
</button>
</div>
</div>
<div class="kt-dem-details-drawer-body" data-testid="kt-dem-details-body">
<section class="kt-dem-details-section" data-testid="kt-dem-details-business">
<div class="kt-dem-details-section-head">
<span>1. Business Request</span>
</div>
<div class="kt-dem-details-section-body">
<div class="kt-dem-details-field kt-dem-details-field--full">
<span class="kt-dem-details-label">Summary of need</span>
<p class="kt-dem-details-value" data-kt-dem-label="details_need_summary">—</p>
</div>
<div class="kt-dem-details-grid">
<div class="kt-dem-details-field">
<span class="kt-dem-details-label">Beneficiaries</span>
<p class="kt-dem-details-value" data-kt-dem-label="details_beneficiaries">—</p>
</div>
<div class="kt-dem-details-field">
<span class="kt-dem-details-label">Required by</span>
<p class="kt-dem-details-value" data-kt-dem-label="details_required_by">—</p>
</div>
<div class="kt-dem-details-field">
<span class="kt-dem-details-label">Business approver</span>
<p class="kt-dem-details-value" data-kt-dem-label="details_business_approver">—</p>
</div>
<div class="kt-dem-details-field">
<span class="kt-dem-details-label">Delivery location</span>
<p class="kt-dem-details-value" data-kt-dem-label="details_delivery_location">—</p>
</div>
</div>
</div>
</section>
<section class="kt-dem-details-section" data-testid="kt-dem-details-classify">
<div class="kt-dem-details-section-head">
<span>2. Classification &amp; Estimate</span>
</div>
<div class="kt-dem-details-section-body">
<div class="kt-dem-details-grid">
<div class="kt-dem-details-field">
<span class="kt-dem-details-label">Category</span>
<p class="kt-dem-details-value" data-kt-dem-label="details_category">—</p>
</div>
<div class="kt-dem-details-field">
<span class="kt-dem-details-label">Demand route</span>
<p class="kt-dem-details-value" data-kt-dem-label="details_demand_route">—</p>
</div>
</div>
<div class="kt-dem-details-field kt-dem-details-field--full">
<span class="kt-dem-details-label">Estimate basis</span>
<p class="kt-dem-details-value" data-kt-dem-label="details_estimate_basis">—</p>
</div>
<div class="kt-dem-details-field kt-dem-details-field--full">
<span class="kt-dem-details-label">Confirmed estimate</span>
<p class="kt-dem-details-value font-data-mono" data-kt-dem-label="details_confirmed_estimate">—</p>
</div>
</div>
</section>
<section class="kt-dem-details-section" data-testid="kt-dem-details-items">
<div class="kt-dem-details-section-head">
<span>3. Need Items</span>
<span class="kt-dem-details-count" data-kt-dem-label="details_items_count">0 items</span>
</div>
<div class="kt-dem-details-section-body">
<ul class="kt-dem-details-items-list" data-kt-dem-details-items data-testid="kt-dem-details-items-list"></ul>
<p class="kt-dem-details-empty hidden mb-0" data-kt-dem-details-items-empty hidden>No need items recorded.</p>
</div>
</section>
<section class="kt-dem-details-section" data-testid="kt-dem-details-strategy">
<div class="kt-dem-details-section-head">
<span>4. Strategy Alignment</span>
<span class="kt-dem-details-pill" data-kt-dem-label="details_strategy_pill">—</span>
</div>
<div class="kt-dem-details-section-body">
<p class="kt-dem-details-value mb-0" data-kt-dem-label="details_strategy_summary">—</p>
<p class="kt-dem-details-meta mb-0" data-kt-dem-label="details_strategy_path"></p>
</div>
</section>
<section class="kt-dem-details-section" data-testid="kt-dem-details-pvc">
<div class="kt-dem-details-section-head">
<span>5. Public-value Commitments</span>
</div>
<div class="kt-dem-details-section-body">
<ul class="kt-dem-details-pvc-list" data-kt-dem-details-pvc data-testid="kt-dem-details-pvc-list"></ul>
<p class="kt-dem-details-empty mb-0" data-kt-dem-details-pvc-empty>No applicable public-value commitments for the current Strategy selection.</p>
</div>
</section>
</div>
</div>
</div>

<div class="kt-dem-strategy-drawer hidden" data-kt-dem-strategy-drawer data-testid="kt-dem-ui05a-drawer" hidden role="dialog" aria-modal="true" aria-labelledby="kt-dem-ui05a-title">
<div class="kt-dem-strategy-drawer-panel">
<div class="kt-dem-strategy-drawer-header">
<div class="flex justify-between items-start mb-2">
<h2 class="font-headline-md text-headline-md text-on-surface mb-0" id="kt-dem-ui05a-title">Assign Strategy target</h2>
<button type="button" class="p-1 rounded-full border-0 bg-transparent" data-kt-dem-action="close-strategy-drawer" data-testid="kt-dem-ui05a-close" aria-label="Close">
<span class="material-symbols-outlined" aria-hidden="true">close</span>
</button>
</div>
<p class="text-body-md text-on-surface-variant mb-0">Select the primary active target this Demand directly supports.</p>
</div>
<div class="kt-dem-strategy-drawer-filters">
<div class="relative">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]" aria-hidden="true">search</span>
<input class="w-full pl-10 pr-4 py-2 border border-outline-variant rounded-lg text-body-md bg-surface-container-lowest" type="search" placeholder="Search target or outcome" data-kt-dem-field="strategy_search" data-testid="kt-dem-ui05a-search"/>
</div>
<div class="kt-dem-strategy-drawer-filter-row grid grid-cols-2 gap-2">
<select class="w-full pl-3 pr-8 py-1.5 border border-outline-variant rounded-lg text-xs bg-surface-container-lowest" data-kt-dem-field="strategy_plan_filter" data-testid="kt-dem-ui05a-plan-filter" aria-label="Strategic plan">
<option value="">Strategic plan</option>
</select>
<select class="w-full pl-3 pr-8 py-1.5 border border-outline-variant rounded-lg text-xs bg-surface-container-lowest" data-kt-dem-field="strategy_period_filter" data-testid="kt-dem-ui05a-period-filter" aria-label="Effective period">
<option value="">Effective period</option>
</select>
</div>
</div>
<div class="kt-dem-strategy-drawer-list" data-kt-dem-strategy-suggestions data-testid="kt-dem-ui05a-suggestions"></div>
<div class="kt-dem-strategy-drawer-reason" data-kt-dem-strategy-reason-host data-testid="kt-dem-ui05a-reason-host">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1" for="kt-dem-ui05a-reason" data-kt-dem-strategy-reason-label>Confirmation reason <span class="text-error">*</span></label>
<textarea id="kt-dem-ui05a-reason" class="w-full border border-outline-variant rounded-lg p-2 text-sm" rows="2" data-kt-dem-field="strategy_reason" data-testid="kt-dem-ui05a-reason" placeholder="Why this Primary target fits the Demand"></textarea>
</div>
<div class="kt-dem-strategy-drawer-footer">
<button type="button" class="flex-1 px-4 py-2.5 border border-outline text-on-surface rounded-lg font-medium" data-kt-dem-action="close-strategy-drawer" data-testid="kt-dem-ui05a-cancel">Cancel</button>
<button type="button" class="flex-1 px-4 py-2.5 bg-primary text-on-primary rounded-lg font-medium" data-kt-dem-action="confirm-strategy" data-testid="kt-dem-ui05a-assign">Assign target</button>
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
</div>
</div>`;
};
