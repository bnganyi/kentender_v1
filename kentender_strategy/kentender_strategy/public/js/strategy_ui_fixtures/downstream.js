// STR-UI-12 Downstream Usage — live-bound hosts (canvas structure from design port).
frappe.provide("kentender_strategy.ui_fixtures");
kentender_strategy.ui_fixtures.downstream = function () {
	return `<div class="kt-str-root" data-testid="kt-str-downstream">
<!-- Plan chrome injected by strategy_alignment_shell.planChromeHtml -->
<!-- Tab Content Area -->
<div class="flex flex-col gap-section-gap">
<section class="flex flex-col md:flex-row md:items-start justify-between gap-gutter">
<div>
<h3 class="font-headline-md text-headline-md text-on-surface">Downstream usage</h3>
<p class="font-body-md text-body-md text-on-surface-variant mt-1">See where this plan’s targets and value commitments are referenced across procurement.</p>
</div>
</section>
<!-- Summary Strip -->
<div class="flex flex-wrap gap-3" data-kt-str-down-chips>
<div class="bg-surface-container-lowest px-4 py-2 rounded-lg border border-outline-variant flex items-center gap-2 shadow-sm" data-kt-str-down-chip="Budget">
<span class="material-symbols-outlined text-primary text-[18px]">account_balance</span>
<span class="text-body-md font-medium text-on-surface">Budget</span>
<span class="bg-surface-container-highest px-2 py-0.5 rounded-full text-label-caps font-data-mono" data-kt-str-down-count="Budget">0</span>
</div>
<div class="bg-surface-container-lowest px-4 py-2 rounded-lg border border-outline-variant flex items-center gap-2 shadow-sm" data-kt-str-down-chip="Demand">
<span class="material-symbols-outlined text-primary text-[18px]">inventory_2</span>
<span class="text-body-md font-medium text-on-surface">Demand</span>
<span class="bg-surface-container-highest px-2 py-0.5 rounded-full text-label-caps font-data-mono" data-kt-str-down-count="Demand">0</span>
</div>
<div class="bg-surface-container-lowest px-4 py-2 rounded-lg border border-outline-variant flex items-center gap-2 shadow-sm opacity-60" data-kt-str-down-chip="Planning">
<span class="material-symbols-outlined text-on-surface-variant text-[18px]">event_note</span>
<span class="text-body-md font-medium text-on-surface-variant">Planning</span>
<span class="bg-surface-container-highest px-2 py-0.5 rounded-full text-label-caps font-data-mono" data-kt-str-down-count="Planning">0</span>
</div>
<div class="bg-surface-container-lowest px-4 py-2 rounded-lg border border-outline-variant flex items-center gap-2 shadow-sm opacity-60" data-kt-str-down-chip="Tender">
<span class="material-symbols-outlined text-on-surface-variant text-[18px]">gavel</span>
<span class="text-body-md font-medium text-on-surface-variant">Tender</span>
<span class="bg-surface-container-highest px-2 py-0.5 rounded-full text-label-caps font-data-mono" data-kt-str-down-count="Tender">0</span>
</div>
<div class="bg-surface-container-lowest px-4 py-2 rounded-lg border border-outline-variant flex items-center gap-2 shadow-sm opacity-60" data-kt-str-down-chip="Contract">
<span class="material-symbols-outlined text-on-surface-variant text-[18px]">history_edu</span>
<span class="text-body-md font-medium text-on-surface-variant">Contract</span>
<span class="bg-surface-container-highest px-2 py-0.5 rounded-full text-label-caps font-data-mono" data-kt-str-down-count="Contract">0</span>
</div>
<div class="bg-surface-container-lowest px-4 py-2 rounded-lg border border-outline-variant flex items-center gap-2 shadow-sm opacity-60" data-kt-str-down-chip="Asset">
<span class="material-symbols-outlined text-on-surface-variant text-[18px]">domain</span>
<span class="text-body-md font-medium text-on-surface-variant">Asset</span>
<span class="bg-surface-container-highest px-2 py-0.5 rounded-full text-label-caps font-data-mono" data-kt-str-down-count="Asset">0</span>
</div>
<div class="bg-surface-container-lowest px-4 py-2 rounded-lg border border-outline-variant flex items-center gap-2 shadow-sm opacity-60" data-kt-str-down-chip="Disposal">
<span class="material-symbols-outlined text-on-surface-variant text-[18px]">delete</span>
<span class="text-body-md font-medium text-on-surface-variant">Disposal</span>
<span class="bg-surface-container-highest px-2 py-0.5 rounded-full text-label-caps font-data-mono" data-kt-str-down-count="Disposal">0</span>
</div>
</div>
<section class="bg-surface-container-lowest rounded-xl border border-subtle border-outline-variant shadow-sm overflow-hidden flex flex-col">
<div class="bg-surface-container-low p-container-padding border-b border-outline-variant flex flex-col gap-gutter" data-kt-str-down-filters>
<div class="flex flex-wrap items-center gap-2">
<div class="relative flex-1 min-w-[200px] max-w-xs">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]">search</span>
<input class="w-full pl-10 pr-3 py-1.5 bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md text-on-surface outline-none" placeholder="Search record reference..." type="text" data-kt-str-down-search/>
</div>
<div class="relative min-w-[140px]">
<select class="w-full py-1.5 pl-3 pr-8 bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md text-on-surface outline-none appearance-none" data-kt-str-down-filter-module aria-label="Module">
<option value="">Module: All</option>
<option value="Budget">Budget</option>
<option value="Demand">Demand</option>
<option value="Planning">Planning</option>
<option value="Tender">Tender</option>
<option value="Contract">Contract</option>
<option value="Asset">Asset</option>
<option value="Disposal">Disposal</option>
</select>
<span class="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm pointer-events-none" aria-hidden="true">expand_more</span>
</div>
<div class="relative min-w-[160px]">
<select class="w-full py-1.5 pl-3 pr-8 bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md text-on-surface outline-none appearance-none" data-kt-str-down-filter-target aria-label="Strategy Target">
<option value="">Strategy Target: All</option>
</select>
<span class="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm pointer-events-none" aria-hidden="true">expand_more</span>
</div>
<div class="relative min-w-[160px]">
<select class="w-full py-1.5 pl-3 pr-8 bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md text-on-surface outline-none appearance-none" data-kt-str-down-filter-reftype aria-label="Reference Type">
<option value="">Reference Type: All</option>
<option value="Primary alignment">Primary alignment</option>
<option value="Supporting alignment">Supporting alignment</option>
<option value="Value commitment">Value commitment</option>
</select>
<span class="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm pointer-events-none" aria-hidden="true">expand_more</span>
</div>
<div class="relative min-w-[130px]">
<select class="w-full py-1.5 pl-3 pr-8 bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md text-on-surface outline-none appearance-none" data-kt-str-down-filter-status aria-label="Status">
<option value="">Status: All</option>
</select>
<span class="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm pointer-events-none" aria-hidden="true">expand_more</span>
</div>
<button type="button" class="text-secondary font-medium text-body-md hover:underline px-2 py-1.5 ml-auto" data-kt-str-action="clear-down-filters">
                        Clear filters
                    </button>
</div>
</div>
<div class="overflow-x-auto w-full" data-testid="kt-str-downstream-scroll">
<table data-testid="kt-str-downstream-table" class="w-full text-left border-collapse min-w-[1000px]">
<thead class="bg-surface-container-low border-b border-outline-variant">
<tr>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider w-1/4">Downstream record</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider whitespace-nowrap">Module</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider w-1/4">Strategy reference</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider whitespace-nowrap">Reference type</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider whitespace-nowrap">Current status</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider whitespace-nowrap">Last updated</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider whitespace-nowrap text-right">Action</th>
</tr>
</thead>
<tbody class="divide-y divide-outline-variant bg-surface-container-lowest" data-kt-str-down-tbody>
<tr data-kt-str-down-empty>
<td colspan="7" class="py-8 px-4 text-center text-on-surface-variant text-body-md">No downstream references for this plan yet.</td>
</tr>
</tbody>
</table>
</div>
</section>
<p class="font-body-md text-body-md text-on-surface-variant" data-kt-str-down-footnote>
Superseded plan versions retain historical references for audit; new alignments use the Active plan only.
</p>
</div>
</div>`;
};
