// PLN-UI-04 — literal Stitch modal from docs/mvp-1/04_planning/ui_design/PLN-UI-04.html
// Corrected: no absolute selection <td>; Proposed Funding wraps (no truncate).
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_add_demand_dialog = function () {
	return `<div class="fixed inset-0 z-[200] hidden kt-stitch-canvas" data-testid="kt-pln-ui04-dialog" data-kt-pln-add-demand-dialog data-kt-pln-dialog-mode="add" hidden>
<div class="absolute inset-0 bg-on-surface/40 backdrop-blur-sm z-10" aria-hidden="true"></div>
<div class="relative z-50 flex items-center justify-center w-full h-full p-4 sm:p-6 md:p-8">
<div aria-labelledby="kt-pln-ui04-modal-title" aria-modal="true" class="bg-surface-container-lowest w-full max-w-6xl max-h-[921px] flex flex-col rounded-xl shadow-[0_8px_30px_rgb(0,61,155,0.1)] border border-subtle overflow-hidden" role="dialog">
<div class="px-section-gap py-gutter-md border-b border-subtle bg-surface-container-lowest flex justify-between items-start shrink-0">
<div>
<h2 class="font-headline-md text-headline-md text-on-surface m-0" id="kt-pln-ui04-modal-title" data-kt-pln-ui04-title>Add approved Demands</h2>
<p class="font-body-sm text-body-sm text-on-surface-variant mt-stack-xs" data-kt-pln-ui04-subtitle>Select from pre-approved strategic demands to allocate to this procurement plan.</p>
</div>
<button type="button" class="text-on-surface-variant hover:bg-surface-container-low p-2 rounded-full transition-colors duration-200" data-kt-pln-action="elig-close" aria-label="Close dialog">
<span class="material-symbols-outlined" aria-hidden="true" style="font-variation-settings: 'FILL' 0;">close</span>
</button>
</div>
<div class="px-section-gap py-gutter-md bg-surface-bright border-b border-subtle shrink-0">
<div class="flex flex-wrap gap-gutter-md items-end">
<div class="flex-1 min-w-[250px]">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-stack-xs uppercase" for="kt-pln-elig-search">Search approved Demands</label>
<div class="relative">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline pointer-events-none" aria-hidden="true" style="font-variation-settings: 'FILL' 0;">search</span>
<input id="kt-pln-elig-search" class="w-full pl-10 pr-3 py-2 bg-surface-container-lowest border border-subtle rounded text-body-sm font-body-sm text-on-surface focus:border-secondary focus:ring-2 focus:ring-secondary/20 transition-all outline-none" placeholder="Search by name or reference..." type="text" data-kt-pln-elig-search aria-label="Search approved Demands"/>
</div>
</div>
<div class="w-full md:w-auto min-w-[200px]">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-stack-xs uppercase" for="kt-pln-elig-ou">Organisation Unit</label>
<div class="relative">
<select id="kt-pln-elig-ou" class="w-full appearance-none bg-surface-container-lowest border border-subtle rounded py-2 pl-3 pr-10 text-body-sm font-body-sm text-on-surface focus:border-secondary focus:ring-2 focus:ring-secondary/20 transition-all outline-none" data-kt-pln-elig-ou aria-label="Organisation Unit">
<option value="">All permitted units</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-outline pointer-events-none" aria-hidden="true" style="font-variation-settings: 'FILL' 0;">arrow_drop_down</span>
</div>
</div>
<div class="w-full md:w-auto min-w-[180px]">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-stack-xs uppercase" for="kt-pln-elig-category">Category</label>
<div class="relative">
<select id="kt-pln-elig-category" class="w-full appearance-none bg-surface-container-lowest border border-subtle rounded py-2 pl-3 pr-10 text-body-sm font-body-sm text-on-surface focus:border-secondary focus:ring-2 focus:ring-secondary/20 transition-all outline-none" data-kt-pln-elig-category aria-label="Category">
<option value="">All categories</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-outline pointer-events-none" aria-hidden="true" style="font-variation-settings: 'FILL' 0;">arrow_drop_down</span>
</div>
</div>
<div class="flex items-center gap-2 pb-2 pl-2">
<input checked class="w-4 h-4 text-primary bg-surface-container-lowest border-outline rounded focus:ring-primary focus:ring-offset-0" id="kt-pln-elig-remaining" type="checkbox" data-kt-pln-elig-remaining/>
<label class="font-body-sm text-body-sm text-on-surface cursor-pointer" for="kt-pln-elig-remaining">Available to plan only</label>
</div>
</div>
</div>
<div class="flex-1 overflow-auto bg-surface-container-lowest min-h-0">
<table class="w-full text-left border-collapse min-w-[1000px]">
<thead class="sticky top-0 bg-surface-bright border-b border-subtle z-10">
<tr>
<th class="w-12 px-container-padding py-3" scope="col"><span class="sr-only">Select</span></th>
<th class="font-label-caps text-label-caps text-on-surface-variant px-container-padding py-3 uppercase" scope="col">Demand</th>
<th class="font-label-caps text-label-caps text-on-surface-variant px-container-padding py-3 uppercase" scope="col">Organisation Unit</th>
<th class="font-label-caps text-label-caps text-on-surface-variant px-container-padding py-3 uppercase text-right" scope="col">Approved Value</th>
<th class="font-label-caps text-label-caps text-on-surface-variant px-container-padding py-3 uppercase" scope="col">Required By</th>
<th class="font-label-caps text-label-caps text-on-surface-variant px-container-padding py-3 uppercase" scope="col">Proposed Funding</th>
<th class="font-label-caps text-label-caps text-on-surface-variant px-container-padding py-3 uppercase" scope="col">Status</th>
</tr>
</thead>
<tbody class="divide-y divide-subtle" data-kt-pln-elig-body></tbody>
</table>
</div>
<div class="bg-surface-bright border-t border-subtle p-section-gap shrink-0 shadow-[0_-4px_10px_rgb(0,0,0,0.02)]" data-kt-pln-elig-summary-panel>
<div class="flex flex-col gap-section-gap">
<div class="flex flex-col md:flex-row gap-gutter-md justify-between items-start md:items-center" data-testid="kt-pln-ui04-summary" data-kt-pln-elig-summary-bar>
<div class="flex items-center gap-stack-sm flex-wrap">
<span class="material-symbols-outlined text-primary" style="font-variation-settings: 'FILL' 1;" aria-hidden="true">check_circle</span>
<h3 class="font-headline-sm text-headline-sm text-on-surface m-0" data-kt-pln-elig-count-label>0 Approved Demands selected</h3>
<span class="text-outline" data-kt-pln-elig-meta-sep aria-hidden="true">·</span>
<p class="font-body-md text-on-surface-variant m-0" data-kt-pln-elig-ou-count>0 Organisation Units</p>
<span class="text-outline" data-kt-pln-elig-meta-sep2 aria-hidden="true">·</span>
<p class="font-data-md text-primary font-semibold m-0" data-kt-pln-elig-amount>KES 0</p>
</div>
<a class="font-body-sm text-primary hover:underline flex items-center gap-1" href="#" data-kt-pln-action="view-source-breakdown" data-testid="kt-pln-ui04-view-source">View source breakdown<span class="material-symbols-outlined text-[16px]" aria-hidden="true">open_in_new</span></a>
</div>
<div class="hidden grid grid-cols-1 md:grid-cols-2 gap-section-gap pt-section-gap border-t border-subtle" data-kt-pln-formation-wrap data-testid="kt-pln-ui04-formation" hidden>
<div class="space-y-stack-sm">
<p class="font-label-caps text-label-caps text-on-surface-variant uppercase">Plan Item formation</p>
<div class="flex flex-col gap-2">
<label class="flex items-center gap-2 cursor-pointer">
<input class="w-4 h-4 text-primary border-outline focus:ring-primary" name="kt-pln-formation" type="radio" value="separate" data-kt-pln-formation-mode checked/>
<span class="font-body-md text-on-surface">Create separate Plan Items</span>
</label>
<label class="flex items-center gap-2" data-kt-pln-formation-combine-label>
<input class="w-4 h-4 text-primary border-outline focus:ring-primary" name="kt-pln-formation" type="radio" value="combined" data-kt-pln-formation-mode data-testid="kt-pln-ui04-formation-combine"/>
<span class="font-body-md text-on-surface">Combine into one Plan Item</span>
</label>
</div>
<div class="hidden" data-kt-pln-formation-reason-wrap data-testid="kt-pln-ui04-formation-reason-wrap" hidden>
<label class="block font-label-caps text-on-surface-variant mb-2" for="kt-pln-ui04-formation-reason">Reason for combining</label>
<textarea id="kt-pln-ui04-formation-reason" class="block w-full pl-3 pr-3 py-2 border border-subtle rounded bg-surface-container-lowest font-body-sm text-body-sm text-on-surface min-h-[72px]" name="formation_reason" data-kt-pln-formation-reason data-kt-field="formation_reason" data-testid="kt-pln-ui04-formation-reason"></textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="formation_reason" hidden></div>
</div>
</div>
<div class="bg-surface-container-low p-4 rounded-lg flex flex-col justify-center" data-kt-pln-formation-callout>
<p class="font-body-sm text-on-surface-variant italic mb-2" data-kt-pln-formation-callout-copy></p>
<div class="flex items-center gap-2 text-primary font-semibold">
<span class="material-symbols-outlined" aria-hidden="true">inventory_2</span>
<span class="font-body-md" data-kt-pln-formation-preview>1 Plan Item will be created.</span>
</div>
</div>
</div>
<p class="font-body-sm text-body-sm text-on-surface-variant m-0" data-kt-pln-ui04-helper data-kt-pln-add-mode-footer>Select an Approved Demand to begin.</p>
</div>
</div>
<div class="px-section-gap py-gutter-md bg-surface-container-lowest border-t border-subtle flex justify-end gap-gutter-md shrink-0">
<button class="px-4 py-2 font-body-sm text-body-sm font-medium text-error hover:bg-error-container/20 rounded transition-colors" type="button" data-kt-pln-action="elig-cancel">Cancel</button>
<button class="px-4 py-2 bg-primary text-on-primary font-body-sm text-body-sm font-medium rounded hover:bg-primary-container hover:text-on-primary-container transition-colors shadow-sm" type="button" data-kt-pln-action="elig-add" data-testid="kt-pln-ui04-add" disabled>
<span data-kt-pln-ui04-cta-label>Create Plan Item</span>
</button>
</div>
</div>
</div>
</div>`;
};
