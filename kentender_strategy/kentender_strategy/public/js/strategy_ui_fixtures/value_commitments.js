// Extracted from plan_value_commitments_ministry_of_health_draft_v2/code.html
// Canvas + add-commitment drawer. Table/drawer bodies are live-bound (STR-UI-07).
frappe.provide("kentender_strategy.ui_fixtures");
kentender_strategy.ui_fixtures.value_commitments = function () {
	return `<div class="kt-str-root kt-str-vc-root" data-testid="kt-str-value-commitments">
<!-- Canvas -->
<div class="flex-1 px-8 pt-4 pb-8 max-w-[1400px] transition-all duration-300" id="main-canvas" data-testid="kt-str-vc-canvas">
<header class="mb-section-gap flex justify-between items-start gap-4" data-testid="kt-str-vc-header">
<div class="min-w-0 flex-1">
<h3 class="font-headline-md text-headline-md text-on-surface">Plan value commitments</h3>
<p class="font-body-md text-body-md text-on-surface-variant leading-relaxed mt-1">Select the public-value objectives this plan will carry forward and connect each commitment to a strategic outcome or target.</p>
<div class="mt-4 flex items-center gap-3" data-kt-str-vc-progress>
<div class="w-48 h-2 bg-surface-container-highest rounded-full overflow-hidden">
<div class="h-full bg-status-available" data-kt-str-vc-progress-bar style="width:0%"></div>
</div>
<span class="font-label-caps text-label-caps text-on-surface-variant" data-kt-str-vc-progress-label>0 OF 0 COMMITMENTS COMPLETE</span>
</div>
</div>
<button type="button" class="bg-primary text-on-primary px-5 py-2.5 rounded-lg font-body-md font-medium hover:bg-on-primary-fixed-variant transition-colors flex items-center gap-2 shadow-sm shrink-0" data-kt-str-action="add-vc" data-kt-str-vc-add>
<span class="material-symbols-outlined text-[18px]">add</span>
                        Add commitment
                    </button>
</header>
<div class="bg-surface-bright border border-outline-variant/50 rounded-lg p-4 mb-section-gap flex gap-3 items-start shadow-sm">
<span class="material-symbols-outlined text-secondary mt-0.5">info</span>
<div>
<span class="font-body-md text-on-surface font-medium block mb-1">Required consideration</span>
<p class="font-body-md text-on-surface-variant text-sm">A downstream value case must include this objective or record an approved not-applicable reason.</p>
</div>
</div>
<div class="bg-surface-container-lowest rounded-xl border border-surface-container-high shadow-sm overflow-hidden">
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse" data-testid="kt-str-vc-table">
<thead>
<tr class="bg-surface-container-low border-b border-surface-container-high">
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant">COMMITMENT</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant">LEVEL</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant">PLAN RATIONALE</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant">LINKED STRATEGY</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant">OWNER</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant">STATUS</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant text-right">ACTION</th>
</tr>
</thead>
<tbody class="divide-y divide-surface-container-high font-body-md text-on-surface" data-kt-str-vc-tbody>
</tbody>
</table>
</div>
</div>
</div>
<!-- Drawer (Right Side) -->
<div class="w-[450px] bg-surface-container-lowest border-l border-surface-container-high shadow-2xl flex flex-col transform translate-x-full transition-transform duration-300 ease-in-out absolute right-0 top-0 bottom-0 z-30" id="add-commitment-drawer" data-testid="kt-str-vc-drawer" data-dismiss="explicit-only">
<div class="px-6 py-5 border-b border-surface-container-high flex justify-between items-center bg-surface-bright">
<div>
<h2 class="font-headline-sm text-headline-sm text-on-surface" data-kt-str-vc-drawer-title>Add Commitment</h2>
<p class="text-sm text-on-surface-variant mt-1" data-kt-str-vc-drawer-subtitle>Select and configure an objective</p>
</div>
<button type="button" class="p-2 text-on-surface-variant hover:bg-surface-container rounded-full transition-colors" data-kt-str-action="close-vc-drawer" aria-label="Close">
<span class="material-symbols-outlined">close</span>
</button>
</div>
<div class="flex-1 overflow-y-auto" data-testid="kt-str-vc-drawer-scroll">
<div class="p-6 border-b border-surface-container-high bg-surface-container-low/50" data-kt-str-vc-drawer-library>
<div class="relative mb-4">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]">search</span>
<input class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg py-2 pl-9 pr-4 text-sm focus:ring-2 focus:ring-primary focus:border-primary transition-all outline-none" placeholder="Search objectives library..." type="text" data-kt-str-vc-drawer-search/>
</div>
<div class="grid grid-cols-2 gap-2" data-testid="kt-str-vc-drawer-filters">
<select class="text-sm bg-surface-container-lowest border border-outline-variant rounded-md py-1.5 px-3 focus:ring-primary focus:border-primary min-w-0 w-full text-on-surface-variant outline-none" data-kt-str-vc-drawer-pillar>
<option value="">Pillar: All</option>
</select>
<select class="text-sm bg-surface-container-lowest border border-outline-variant rounded-md py-1.5 px-3 focus:ring-primary focus:border-primary min-w-0 w-full text-on-surface-variant outline-none" data-kt-str-vc-drawer-source>
<option value="">Source: All</option>
</select>
</div>
<div class="mt-4 max-h-40 overflow-y-auto space-y-1" data-kt-str-vc-drawer-pvo-list></div>
</div>
<div class="p-6">
<div class="bg-primary/5 border border-primary/20 rounded-xl p-5 mb-6 hidden" data-kt-str-vc-drawer-preview>
<div class="flex items-start justify-between mb-2">
<span class="font-data-mono text-data-mono text-primary font-bold" data-kt-str-vc-drawer-pvo-code></span>
<span class="text-[11px] font-semibold tracking-wider uppercase text-on-surface-variant bg-surface-container-highest px-2 py-0.5 rounded" data-kt-str-vc-drawer-pvo-pillar></span>
</div>
<h3 class="font-headline-sm text-[16px] leading-tight text-on-surface mb-3" data-kt-str-vc-drawer-pvo-title></h3>
</div>
<form class="space-y-5" data-kt-str-vc-drawer-form>
<div>
<label class="block text-sm font-semibold text-on-surface mb-1.5">Plan Rationale <span class="text-error">*</span></label>
<textarea class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg p-3 text-sm focus:ring-2 focus:ring-primary focus:border-primary transition-all placeholder:text-outline outline-none" placeholder="Explain how this commitment applies to the current strategic plan..." rows="3" data-kt-str-vc-drawer-rationale name="rationale"></textarea>
</div>
<div class="grid grid-cols-2 gap-4">
<div>
<label class="block text-sm font-semibold text-on-surface mb-1.5">Consideration Level</label>
<select class="w-full text-sm bg-surface-container-lowest border border-outline-variant rounded-lg p-2.5 focus:ring-primary focus:border-primary outline-none" data-kt-str-vc-drawer-level name="consideration_level">
<option value="Required consideration">Required</option>
<option value="Recommended consideration">Recommended</option>
<option value="Available">Available</option>
</select>
</div>
<div>
<label class="block text-sm font-semibold text-on-surface mb-1.5">Owner <span class="text-error">*</span></label>
<input type="text" class="w-full text-sm bg-surface-container-lowest border border-outline-variant rounded-lg p-2.5 focus:ring-primary focus:border-primary outline-none" placeholder="Responsible owner" data-kt-str-vc-drawer-owner name="responsible_owner"/>
</div>
</div>
<div>
<label class="block text-sm font-semibold text-on-surface mb-1.5">Strategic Links <span class="text-error">*</span></label>
<div class="border border-outline-variant rounded-lg p-3 bg-surface-container-lowest min-h-[80px] max-h-48 overflow-y-auto space-y-2" data-kt-str-vc-drawer-links>
</div>
</div>
</form>
</div>
</div>
<div class="p-6 border-t border-surface-container-high bg-surface-bright flex justify-end gap-3">
<button type="button" class="px-4 py-2 rounded-lg text-sm font-medium text-on-surface hover:bg-surface-container-high transition-colors border border-outline-variant" data-kt-str-action="close-vc-drawer">Cancel</button>
<button type="button" class="px-5 py-2 rounded-lg text-sm font-medium bg-primary text-on-primary hover:bg-on-primary-fixed-variant transition-colors shadow-sm" data-kt-str-action="save-vc" data-kt-str-vc-drawer-save>Save Commitment</button>
</div>
</div>
</div>`;
};
