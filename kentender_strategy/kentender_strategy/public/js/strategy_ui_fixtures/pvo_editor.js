// Auto-extracted Stitch canvas — create_public_value_objective_draft_state
frappe.provide("kentender_strategy.ui_fixtures");
kentender_strategy.ui_fixtures.pvo_editor = function () {
	return `<div class="kt-str-root" data-testid="kt-str-pvo-editor">
<div class="flex-1 px-container-padding md:px-8 py-8 max-w-[1200px] w-full mx-auto pb-32">
<!-- Page Header -->
<div class="mb-section-gap flex flex-col md:flex-row md:items-start justify-between gap-4">
<div>
<div class="flex items-center gap-3 mb-2">
<h1 class="font-headline-lg md:font-headline-lg text-headline-lg-mobile md:text-headline-lg text-on-surface">Create public value objective</h1>
<span class="bg-status-reserved text-white font-label-caps text-label-caps px-3 py-1 rounded-full uppercase tracking-wider flex items-center self-center mt-1">Draft</span>
</div>
<p class="font-body-lg text-body-lg text-on-surface-variant max-w-2xl">Define a reusable objective and the conditions under which it may be considered.</p>
</div>
</div>
<div class="flex flex-col gap-section-gap">
<!-- Section 1: Objective -->
<section class="bg-surface-container-lowest border border-border-subtle rounded-xl overflow-hidden flex flex-col">
<div class="bg-surface-container-low px-card-padding py-4 border-b border-border-subtle">
<h3 class="font-headline-sm text-headline-sm text-on-surface">Objective Details</h3>
</div>
<div class="p-card-padding grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-5">
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Objective code</label>
<input class="w-full bg-surface border-outline-variant rounded-lg px-3 py-2 font-data-mono text-data-mono text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors" type="text" value="PVO-SUS-02"/>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Version</label>
<input class="w-full bg-surface-container opacity-70 border-outline-variant rounded-lg px-3 py-2 font-data-mono text-data-mono text-on-surface-variant cursor-not-allowed" disabled="" type="text" value="1"/>
</div>
<div class="md:col-span-2">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Title</label>
<input class="w-full bg-surface border-outline-variant rounded-lg px-3 py-2 font-body-md text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors" type="text" value="Ensure compliant handling of replaced ICT equipment"/>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Pillar</label>
<select class="w-full bg-surface border-outline-variant rounded-lg px-3 py-2 font-body-md text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors appearance-none">
<option>Sustainability and asset stewardship</option>
<option>Economic development</option>
<option>Social value</option>
</select>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Scope</label>
<select class="w-full bg-surface border-outline-variant rounded-lg px-3 py-2 font-body-md text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors appearance-none">
<option>Procuring entity</option>
<option>National</option>
<option>County</option>
</select>
</div>
<div class="md:col-span-2">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Procuring entity</label>
<div class="relative">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]">account_balance</span>
<input class="w-full bg-surface border-outline-variant rounded-lg pl-10 pr-3 py-2 font-body-md text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors" type="text" value="Ministry of Health"/>
</div>
</div>
<div class="md:col-span-2">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Description</label>
<textarea class="w-full bg-surface border-outline-variant rounded-lg px-3 py-2 font-body-md text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors resize-none" placeholder="Enter detailed description..." rows="3"></textarea>
</div>
</div>
</section>
<!-- Section 2: Authority and ownership -->
<section class="bg-surface-container-lowest border border-border-subtle rounded-xl overflow-hidden flex flex-col">
<div class="bg-surface-container-low px-card-padding py-4 border-b border-border-subtle flex justify-between items-center">
<h3 class="font-headline-sm text-headline-sm text-on-surface">Authority and ownership</h3>
</div>
<div class="p-card-padding grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-5">
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Source type</label>
<select class="w-full bg-surface border-outline-variant rounded-lg px-3 py-2 font-body-md text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors appearance-none">
<option>Act</option>
<option>Policy</option>
<option>Directive</option>
</select>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Responsible function</label>
<input class="w-full bg-surface border-outline-variant rounded-lg px-3 py-2 font-body-md text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors" type="text" value="Supply Chain Management Services"/>
</div>
<div class="md:col-span-2">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Source reference</label>
<input class="w-full bg-surface border-outline-variant rounded-lg px-3 py-2 font-body-md text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors" type="text" value="Public Procurement and Asset Disposal Act — applicable asset-disposal provisions"/>
<p class="text-xs text-on-surface-variant mt-1.5 flex items-center gap-1 opacity-80"><span class="material-symbols-outlined text-[14px]">info</span>The reference supports auditability and does not replace the authoritative legal source.</p>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Effective from</label>
<div class="relative">
<input class="w-full bg-surface border-outline-variant rounded-lg px-3 py-2 font-data-mono text-data-mono text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors" type="text" value="1 July 2026"/>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none text-[20px]">calendar_today</span>
</div>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Effective to</label>
<div class="relative">
<input class="w-full bg-surface border-outline-variant rounded-lg px-3 py-2 font-data-mono text-data-mono text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors" type="text" value="30 June 2030"/>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none text-[20px]">calendar_today</span>
</div>
</div>
</div>
</section>
<!-- Section 3: Applicability -->
<section class="bg-surface-container-lowest border border-border-subtle rounded-xl overflow-hidden flex flex-col">
<div class="bg-surface-container-low px-card-padding py-4 border-b border-border-subtle flex justify-between items-center">
<h3 class="font-headline-sm text-headline-sm text-on-surface">Applicability</h3>
</div>
<div class="p-card-padding flex flex-col gap-5">
<div class="w-full md:w-1/2">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Applicability mode</label>
<select class="w-full bg-surface border-outline-variant rounded-lg px-3 py-2 font-body-md text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors appearance-none">
<option>Asset-triggered</option>
<option>Value-based</option>
<option>Category-based</option>
</select>
</div>
<div class="border border-border-subtle rounded-lg overflow-hidden">
<table class="w-full text-left border-collapse">
<thead>
<tr class="bg-surface-container-low border-b border-border-subtle">
<th class="py-2.5 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase w-1/3">Trigger type</th>
<th class="py-2.5 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase">Trigger value</th>
<th class="py-2.5 px-4 w-12"></th>
</tr>
</thead>
<tbody class="font-body-md text-body-md text-on-surface">
<tr class="border-b border-border-subtle hover:bg-surface-container transition-colors group">
<td class="py-3 px-4 font-medium">Asset condition</td>
<td class="py-3 px-4">Replacement or end of useful life</td>
<td class="py-3 px-4 text-right">
<button type="button" class="text-on-surface-variant hover:text-error opacity-0 group-hover:opacity-100 transition-all p-1">
<span class="material-symbols-outlined text-[20px]">delete</span>
</button>
</td>
</tr>
</tbody>
</table>
<div class="bg-surface-bright py-3 px-4">
<button type="button" class="text-primary hover:text-primary-container font-headline-sm text-body-md flex items-center gap-1.5 transition-colors">
<span class="material-symbols-outlined text-[18px]">add</span>
                                        Add trigger
                                    </button>
</div>
</div>
</div>
</section>
<!-- Section 4: Guidance -->
<section class="bg-surface-container-lowest border border-border-subtle rounded-xl overflow-hidden flex flex-col">
<div class="bg-surface-container-low px-card-padding py-4 border-b border-border-subtle">
<h3 class="font-headline-sm text-headline-sm text-on-surface">Guidance</h3>
</div>
<div class="p-card-padding grid grid-cols-1 gap-y-5">
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Measure guidance</label>
<textarea class="w-full bg-surface border-outline-variant rounded-lg px-3 py-2 font-body-md text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors resize-none" rows="2">Track the proportion of replaced ICT equipment transferred, reused or disposed through an authorised route</textarea>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Evidence guidance</label>
<textarea class="w-full bg-surface border-outline-variant rounded-lg px-3 py-2 font-body-md text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors resize-none" rows="2">Asset register update, inspection record, transfer or disposal approval and completion record</textarea>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Default enforcement guidance</label>
<input class="w-full bg-surface border-outline-variant rounded-lg px-3 py-2 font-body-md text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors" type="text" value="Asset or disposal control"/>
</div>
</div>
</section>
</div>
</div>
<!-- Sticky Footer Actions -->
<div class="fixed bottom-0 right-0 left-0 md:left-64 bg-surface-container-lowest border-t border-border-subtle p-4 px-container-padding md:px-8 z-30 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]">
<div class="max-w-[1200px] mx-auto flex justify-end gap-3">
<button type="button" class="border border-outline px-6 py-2 rounded-lg font-headline-sm text-body-md text-on-surface hover:bg-surface-container-lowest transition-colors" data-kt-str-action="cancel">
                        Cancel
                    </button>
<button type="button" class="bg-primary text-on-primary px-6 py-2 rounded-lg font-headline-sm text-body-md hover:bg-primary-container transition-colors shadow-sm" data-kt-str-action="save-draft">
                        Save objective
                    </button>
</div>
</div>
</div>
</div>`;
};
