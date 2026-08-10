// PLN-UI-04 — literal Stitch modal from docs/mvp-1/04_planning/ui_design/PLN-UI-04.html
// Pack v1.3: single-select source; Plan Need Items separately is a secondary action.
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_add_demand_dialog = function () {
	return `<div class="fixed inset-0 z-[200] hidden kt-stitch-canvas" data-testid="kt-pln-ui04-dialog" data-kt-pln-add-demand-dialog data-kt-pln-dialog-mode="add" hidden>
<!-- Overlay for Modal focus (Stitch classes) -->
<div class="absolute inset-0 bg-on-surface/40 backdrop-blur-sm z-10 transition-opacity duration-300" aria-hidden="true"></div>
<!-- Modal Dialog -->
<div class="relative z-50 flex items-center justify-center w-full h-full p-4 sm:p-6 md:p-8">
<!-- Modal Container -->
<div aria-labelledby="kt-pln-ui04-modal-title" aria-modal="true" class="bg-surface-container-lowest rounded-xl border border-subtle shadow-[0_8px_30px_rgb(0,0,0,0.12)] w-full max-w-6xl max-h-[90vh] flex flex-col overflow-hidden ring-1 ring-black/5" role="dialog">
<!-- Header -->
<div class="flex items-center justify-between px-6 py-5 border-b border-subtle bg-surface-container-lowest">
<div>
<h2 class="font-headline-md text-headline-md text-on-surface m-0" id="kt-pln-ui04-modal-title" data-kt-pln-ui04-title>Add approved Demand</h2>
<p class="font-body-sm text-body-sm text-on-surface-variant mt-1" data-kt-pln-ui04-subtitle>Select one pre-approved Demand to create a Proposed Plan Item.</p>
</div>
<button type="button" class="text-on-surface-variant hover:text-on-surface hover:bg-surface-container-low rounded-full p-2 transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2" data-kt-pln-action="elig-close" aria-label="Close">
<span aria-hidden="true" class="material-symbols-outlined">close</span>
<span class="sr-only">Close</span>
</button>
</div>
<!-- Filter Bar -->
<div class="px-6 py-4 border-b border-subtle bg-surface-container flex flex-col md:flex-row gap-4 items-center justify-between">
<div class="flex flex-1 w-full gap-4 flex-wrap md:flex-nowrap">
<div class="relative flex-1 min-w-[200px]">
<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
<span class="material-symbols-outlined text-outline text-sm" aria-hidden="true">search</span>
</div>
<input class="block w-full pl-10 pr-3 py-2 border border-outline-variant rounded-lg bg-surface-container-lowest font-body-sm text-body-sm text-on-surface placeholder-on-surface-variant focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-shadow" placeholder="Search approved Demands" type="text" data-kt-pln-elig-search aria-label="Search approved Demands"/>
</div>
<div class="relative min-w-[180px]">
<select class="block w-full pl-3 pr-10 py-2 border border-outline-variant rounded-lg bg-surface-container-lowest font-body-sm text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary appearance-none transition-shadow" data-kt-pln-elig-ou aria-label="Organisation Unit">
<option value="">All permitted units</option>
</select>
<div class="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
<span class="material-symbols-outlined text-outline text-sm" aria-hidden="true">arrow_drop_down</span>
</div>
</div>
<div class="relative min-w-[150px]">
<select class="block w-full pl-3 pr-10 py-2 border border-outline-variant rounded-lg bg-surface-container-lowest font-body-sm text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary appearance-none transition-shadow" data-kt-pln-elig-category aria-label="Category">
<option value="">All categories</option>
</select>
<div class="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
<span class="material-symbols-outlined text-outline text-sm" aria-hidden="true">arrow_drop_down</span>
</div>
</div>
</div>
<div class="flex items-center gap-2 flex-shrink-0">
<input class="w-4 h-4 text-primary bg-surface border-outline-variant rounded focus:ring-primary focus:ring-2 transition-colors" id="kt-pln-elig-remaining" type="checkbox" data-kt-pln-elig-remaining checked/>
<label class="font-body-sm text-body-sm text-on-surface-variant cursor-pointer select-none" for="kt-pln-elig-remaining">Available to plan only</label>
</div>
</div>
<!-- Table Content -->
<div class="flex-1 overflow-x-auto overflow-y-auto bg-surface-container-lowest custom-scrollbar relative">
<table class="w-full text-left border-collapse min-w-[1000px]">
<thead class="sticky top-0 bg-surface-container-lowest shadow-[0_1px_0_theme('colors.border-subtle')] z-10">
<tr>
<th class="pl-6 pr-3 py-3 w-10" scope="col"><span class="sr-only">Select</span></th>
<th class="px-3 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider" scope="col">Demand</th>
<th class="px-3 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider" scope="col">Organisation Unit</th>
<th class="px-3 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider text-right" scope="col">Approved amount</th>
<th class="px-3 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider text-right" scope="col">Already planned</th>
<th class="px-3 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider text-right" scope="col">Available to plan</th>
<th class="px-3 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider" scope="col">Required by</th>
<th class="px-6 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider" scope="col">Funding status</th>
</tr>
</thead>
<tbody class="divide-y divide-subtle" data-kt-pln-elig-body></tbody>
</table>
</div>
<!-- Footer & Selection Summary (Stitch PLN-UI-04) -->
<div class="px-6 py-4 border-t border-subtle bg-surface-container-lowest flex items-center justify-between gap-4">
<div class="flex flex-col gap-3 flex-1 mr-8 min-w-0">
<div class="flex flex-wrap items-center gap-x-6 gap-y-2 p-3 bg-surface-container-low rounded-lg border border-subtle" data-kt-pln-elig-summary-bar data-testid="kt-pln-ui04-summary">
<div class="flex items-center gap-2 kt-pln-ui04-summary-chip">
<span class="material-symbols-outlined text-primary text-sm" aria-hidden="true">check_circle</span>
<span class="font-body-sm font-semibold" data-kt-pln-elig-count-label>0 Approved Demands selected</span>
</div>
<div class="flex items-center gap-2 kt-pln-ui04-summary-chip" data-kt-pln-elig-need-wrap>
<span class="material-symbols-outlined text-on-surface-variant text-sm" aria-hidden="true">list_alt</span>
<span class="font-body-sm" data-kt-pln-elig-need-count>0 Need Items</span>
</div>
<div class="flex items-center gap-2 kt-pln-ui04-summary-chip">
<span class="material-symbols-outlined text-on-surface-variant text-sm" aria-hidden="true">payments</span>
<span class="font-data-md text-sm" data-kt-pln-elig-amount>Total KES 0</span>
</div>
<div class="flex items-center gap-2 kt-pln-ui04-summary-chip hidden" data-kt-pln-elig-funding-wrap data-testid="kt-pln-ui04-funding-reserved" hidden>
<span class="material-symbols-outlined text-status-available text-sm" aria-hidden="true">verified</span>
<span class="font-body-sm" data-kt-pln-elig-funding-label>Funding reserved</span>
</div>
<button type="button" class="text-primary font-label-caps text-[11px] hover:underline ml-auto" data-kt-pln-action="view-source-breakdown" data-testid="kt-pln-ui04-view-source">View source breakdown</button>
</div>
<div class="flex items-center justify-between px-1 gap-4" data-kt-pln-add-mode-footer>
<p class="font-body-sm text-[13px] text-on-surface-variant max-w-2xl" data-kt-pln-ui04-helper>This Demand will be added as one new Plan Item. You will complete its procurement method, schedule and other planning details next.</p>
<button type="button" class="text-primary font-label-caps text-[11px] hover:underline italic whitespace-nowrap hidden" data-kt-pln-action="plan-separately" data-testid="kt-pln-ui04-plan-separately" hidden>Plan Need Items separately</button>
</div>
<div class="hidden px-1" data-kt-pln-separation-wrap data-testid="kt-pln-ui04-separation-panel" hidden>
<label class="block font-label-caps text-on-surface-variant mb-2" for="kt-pln-ui04-separation-reason">Separation reason</label>
<textarea id="kt-pln-ui04-separation-reason" class="block w-full pl-3 pr-3 py-2 border border-outline-variant rounded-lg bg-surface-container-lowest font-body-sm text-body-sm text-on-surface min-h-[72px]" name="separation_reason" data-kt-pln-separation-reason data-kt-field="separation_reason" data-testid="kt-pln-ui04-separation-reason"></textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="separation_reason" hidden></div>
</div>
<div class="hidden px-1" data-kt-pln-aggregate-reason-wrap data-testid="kt-pln-ui04-aggregate-panel" hidden>
<label class="block font-label-caps text-on-surface-variant mb-2" for="kt-pln-ui04-aggregate-reason">Reason for combining requirements</label>
<textarea id="kt-pln-ui04-aggregate-reason" class="block w-full pl-3 pr-3 py-2 border border-outline-variant rounded-lg bg-surface-container-lowest font-body-sm text-body-sm text-on-surface min-h-[72px]" name="aggregation_reason" data-kt-pln-aggregate-reason data-kt-field="aggregation_reason" data-testid="kt-pln-ui04-aggregate-reason"></textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="aggregation_reason" hidden></div>
</div>
</div>
<div class="flex items-center gap-3 flex-shrink-0">
<button class="px-4 py-2 border border-subtle rounded-lg font-label-caps text-label-caps text-primary hover:bg-surface-container-low focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1 transition-colors bg-surface-container-lowest" type="button" data-kt-pln-action="elig-cancel">
Cancel
</button>
<button class="px-4 py-2 rounded-lg font-label-caps text-label-caps bg-primary text-on-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1 shadow-sm flex items-center gap-2 transition-colors" type="button" data-kt-pln-action="elig-add" data-testid="kt-pln-ui04-add">
<span class="material-symbols-outlined text-[18px]" aria-hidden="true">add</span>
<span data-kt-pln-ui04-cta-label>Add Demand and continue</span>
</button>
</div>
</div>
</div>
</div>
</div>`;
};
