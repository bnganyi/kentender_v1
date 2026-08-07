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
</div>

<div class="kt-dem-enrichment hidden" data-kt-dem-enrichment-host data-testid="kt-dem-ui05-root" hidden>
<div class="kt-dem-enrichment-stack flex flex-col gap-6 max-w-4xl mx-auto w-full" data-testid="kt-dem-ui05-main">
<section class="bg-surface-container-lowest border border-outline-variant rounded-xl p-5 flex flex-col gap-4" data-testid="kt-dem-ui05-section-business">
<h2 class="font-headline-sm text-headline-sm text-on-surface border-b border-outline-variant pb-2 mb-0">1. Business Request</h2>
<div class="flex flex-col gap-4">
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1">Summary of Need</span>
<p class="font-body-md text-body-md text-on-surface mb-0" data-kt-dem-label="need_statement">—</p>
</div>
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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

<section class="bg-surface-container-lowest border border-outline-variant rounded-xl p-5 flex flex-col gap-4" data-testid="kt-dem-ui05-section-classify">
<h2 class="font-headline-sm text-headline-sm text-on-surface border-b border-outline-variant pb-2 mb-0">2. Classification &amp; Estimate</h2>
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
<div class="grid grid-cols-2 gap-4 bg-surface-container-low rounded-lg p-4 border border-outline-variant">
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1">Requester Estimate</span>
<span class="font-data-mono text-data-mono text-on-surface text-lg" data-kt-dem-label="estimate_header_display">—</span>
</div>
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1">Confirmed Estimate</span>
<div class="flex items-center gap-2 border-b-2 border-primary pb-1">
<span class="font-data-mono text-data-mono text-primary font-bold" data-kt-dem-label="currency">KES</span>
<input class="bg-transparent border-none p-0 font-data-mono text-data-mono text-primary font-bold text-lg w-full" type="text" data-kt-dem-field="confirmed_estimate" data-testid="kt-dem-ui05-confirmed-estimate" placeholder="0"/>
</div>
</div>
</div>
</section>

<section class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden flex flex-col" data-testid="kt-dem-ui05-section-items">
<div class="p-5 bg-surface-container-low border-b border-outline-variant flex justify-between items-center">
<h2 class="font-headline-sm text-headline-sm text-on-surface mb-0 flex items-center gap-2">3. Need Items</h2>
<button type="button" class="text-primary font-body-md font-medium hover:underline flex items-center gap-1 bg-transparent border-0 p-0" data-kt-dem-action="enrich-add-item" data-testid="kt-dem-ui05-add-item">
<span class="material-symbols-outlined text-sm" aria-hidden="true">add</span> Add Item
</button>
</div>
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse">
<thead>
<tr class="bg-surface-container-low border-b border-outline-variant">
<th class="p-3 font-label-caps text-label-caps text-on-surface-variant uppercase">Description</th>
<th class="p-3 font-label-caps text-label-caps text-on-surface-variant uppercase text-right">Qty</th>
<th class="p-3 font-label-caps text-label-caps text-on-surface-variant uppercase">Unit</th>
<th class="p-3 font-label-caps text-label-caps text-on-surface-variant uppercase text-right">Confirmed Est.</th>
<th class="p-3 font-label-caps text-label-caps text-on-surface-variant uppercase text-right">Action</th>
</tr>
</thead>
<tbody data-kt-dem-enrich-items-tbody data-testid="kt-dem-ui05-items-body"></tbody>
</table>
</div>
</section>

<section class="bg-surface-container-lowest border border-outline-variant rounded-xl p-5 flex flex-col gap-4" data-testid="kt-dem-ui05-section-strategy">
<div class="flex justify-between items-center border-b border-outline-variant pb-2">
<h2 class="font-headline-sm text-headline-sm text-on-surface mb-0">4. Strategy Alignment</h2>
<span class="px-2 py-0.5 rounded-full bg-surface-container-high text-on-surface-variant text-label-caps font-label-caps" data-kt-dem-label="strategy_alignment_pill" data-testid="kt-dem-ui05-strategy-pill">Not assigned</span>
</div>
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
<p class="font-body-md text-on-surface mb-0" data-kt-dem-label="primary_plan_label">—</p>
</div>
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1">Path</span>
<p class="font-body-md text-on-surface mb-0" data-kt-dem-label="primary_hierarchy_path">—</p>
</div>
</div>
<div class="flex items-center gap-4 pt-2 border-t border-outline-variant mt-2">
<button type="button" class="text-primary font-body-md text-sm font-medium hover:underline bg-transparent border-0 p-0" data-kt-dem-action="change-strategy" data-testid="kt-dem-ui05-change-strategy">Change</button>
<button type="button" class="text-on-surface-variant font-body-md text-sm font-medium hover:underline bg-transparent border-0 p-0" data-kt-dem-action="remove-strategy" data-testid="kt-dem-ui05-remove-strategy">Remove</button>
</div>
</div>
</section>

<section class="bg-surface-container-lowest border border-outline-variant rounded-xl p-5 flex flex-col gap-4" data-testid="kt-dem-ui05-section-pvc">
<h2 class="font-headline-sm text-headline-sm text-on-surface border-b border-outline-variant pb-2 mb-0">5. Public-value Commitments</h2>
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
</section>

<section class="bg-surface-container-lowest border border-outline-variant rounded-xl p-5 flex flex-col gap-4" data-testid="kt-dem-ui05-section-duplication">
<h2 class="font-headline-sm text-headline-sm text-on-surface border-b border-outline-variant pb-2 mb-0">6. Duplication &amp; Aggregation</h2>
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
</section>
</div>
</div>

<footer class="kt-dem-enrichment-footer hidden" data-kt-dem-enrichment-footer data-testid="kt-dem-ui05-footer" hidden>
<div class="kt-dem-enrichment-footer-inner max-w-4xl mx-auto flex flex-col sm:flex-row items-center gap-4 justify-end">
<div class="flex gap-3 w-full sm:w-auto">
<button type="button" class="flex-1 sm:flex-none px-4 py-2 border border-outline text-on-surface-variant rounded-lg font-body-md font-medium" data-kt-dem-action="enrich-return" data-testid="kt-dem-ui05-return">Return for correction</button>
<button type="button" class="flex-1 sm:flex-none px-4 py-2 bg-surface-container-high text-on-surface rounded-lg font-body-md font-medium" data-kt-dem-action="enrich-save" data-testid="kt-dem-ui05-save">Save enrichment</button>
<button type="button" class="flex-1 sm:flex-none px-4 py-2 bg-primary text-on-primary rounded-lg font-body-md font-medium flex items-center justify-center gap-2" data-kt-dem-action="enrich-send" data-testid="kt-dem-ui05-send" disabled>Send for Budget confirmation <span class="material-symbols-outlined text-sm" aria-hidden="true">send</span></button>
</div>
</div>
</footer>

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
<input class="w-full pl-10 pr-4 py-2 border border-outline-variant rounded-lg text-body-md" type="search" placeholder="Search target or outcome" data-kt-dem-field="strategy_search" data-testid="kt-dem-ui05a-search"/>
</div>
</div>
<div class="kt-dem-strategy-drawer-list" data-kt-dem-strategy-suggestions data-testid="kt-dem-ui05a-suggestions"></div>
<div class="kt-dem-strategy-drawer-reason hidden" data-kt-dem-strategy-reason-host hidden>
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1" for="kt-dem-ui05a-reason">Confirmation reason <span class="text-error">*</span></label>
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
</div>`;
};
