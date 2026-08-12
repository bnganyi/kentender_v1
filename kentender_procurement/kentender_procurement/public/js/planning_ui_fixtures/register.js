// PLN-UI-02 — literal Stitch <main> form + sticky footer from
// docs/mvp-1/04_planning/ui_design/PLN-UI-02.html
// Fake top/side nav + in-canvas crumbs discarded; kt-stitch-canvas + testids/bind hooks only.
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_register = function () {
	return `<div class="kt-pln-root kt-stitch-canvas" data-testid="kt-pln-ui02-root">
<main class="flex-1 flex flex-col h-full overflow-hidden relative" data-testid="kt-pln-ui02-main">
<div class="bg-status-exhausted/10 border border-status-exhausted/20 rounded-lg p-4 mx-container-padding mt-container-padding hidden" data-testid="kt-pln-ui02-blocked" data-kt-pln-register-blocked hidden role="alert">
<p class="font-headline-sm text-headline-sm text-status-exhausted mb-1">Registration blocked</p>
<p class="font-body-md text-body-md text-on-surface mb-4" data-kt-pln-register-blocked-msg>An authorised Procuring Entity assignment is required before you can register a plan.</p>
<a class="inline-flex border border-subtle text-primary font-body-sm text-body-sm font-semibold px-4 py-2 rounded-lg hover:bg-surface-container-low transition-colors" href="/app/planning-workspace" data-testid="kt-pln-ui02-back-workspace">Back to workspace</a>
</div>
<form class="flex-1 flex flex-col h-full overflow-hidden relative" data-testid="kt-pln-ui02-form" data-kt-pln-register-form novalidate>
<div class="flex-1 overflow-y-auto bg-surface-bright pb-24">
<div class="max-w-4xl mx-auto px-container-padding py-section-gap flex flex-col gap-section-gap">
<div class="flex flex-col gap-stack-sm" data-testid="kt-pln-ui02-header">
<h1 class="font-headline-lg text-headline-lg text-on-surface">Create annual procurement plan</h1>
<p class="font-body-md text-body-md text-on-surface-variant">Register the plan that will contain approved needs for one Procuring Entity and financial year.</p>
</div>
<div class="bg-surface-container-lowest rounded-lg border border-subtle overflow-hidden">
<div class="p-section-gap border-b border-subtle">
<h2 class="font-headline-sm text-headline-sm text-on-surface mb-6">1. Plan ownership</h2>
<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
<div class="flex flex-col gap-stack-xs md:col-span-2" data-kt-pln-pe-field>
<label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-reg-pe">Procuring Entity <span class="text-status-exhausted">*</span></label>
<div class="relative input-glow rounded border border-subtle bg-surface-container-lowest transition-all" data-kt-pln-pe-select-wrap>
<select class="w-full appearance-none bg-transparent py-2 pl-3 pr-10 font-body-md text-body-md text-on-surface focus:outline-none border-none" id="kt-pln-reg-pe" name="procuring_entity" data-kt-field="procuring_entity" data-testid="kt-pln-ui02-pe" aria-label="Procuring Entity">
<option disabled="" selected="" value="">Select an entity...</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none" data-kt-pln-pe-chevron aria-hidden="true">arrow_drop_down</span>
</div>
<p class="font-body-md text-body-md text-on-surface bg-surface-container-low border border-subtle rounded py-2 px-3 hidden" data-kt-pln-pe-readonly data-testid="kt-pln-ui02-pe-readonly"></p>
<p class="font-body-sm text-body-sm text-on-surface-variant mt-1" data-kt-pln-pe-helper>Choose the entity that owns this Plan. It cannot be changed after creation.</p>
<div class="font-body-sm text-body-sm text-status-exhausted" data-kt-field-error="procuring_entity" hidden></div>
</div>
<div class="flex flex-col gap-stack-xs">
<label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-reg-fy">Financial year <span class="text-status-exhausted">*</span></label>
<div class="relative input-glow rounded border border-subtle bg-surface-container-lowest transition-all">
<select class="w-full appearance-none bg-transparent py-2 pl-3 pr-10 font-data-md text-data-md text-on-surface focus:outline-none border-none" id="kt-pln-reg-fy" name="financial_year" data-kt-field="financial_year" data-testid="kt-pln-ui02-fy" aria-label="Financial year">
<option selected="" value="2027/28">2027/28</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none" aria-hidden="true">arrow_drop_down</span>
</div>
<div class="mt-2 bg-surface-container-low p-3 rounded flex items-start gap-2 border border-subtle" data-testid="kt-pln-ui02-period" data-kt-pln-period>
<span class="material-symbols-outlined text-on-surface-variant text-[20px] shrink-0" aria-hidden="true">calendar_month</span>
<p class="font-body-sm text-body-sm text-on-surface-variant">Plan period: <strong class="text-on-surface font-medium" data-kt-pln-period-label data-testid="kt-pln-ui02-period-label">—</strong></p>
</div>
<div class="font-body-sm text-body-sm text-status-exhausted" data-kt-field-error="financial_year" hidden></div>
</div>
</div>
</div>
<div class="p-section-gap">
<h2 class="font-headline-sm text-headline-sm text-on-surface mb-6">2. Plan details</h2>
<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
<div class="flex flex-col gap-stack-xs md:col-span-2">
<label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-reg-title">Plan title <span class="text-status-exhausted">*</span></label>
<div class="input-glow rounded border border-subtle bg-surface-container-lowest transition-all">
<input class="w-full bg-transparent py-2 px-3 font-body-md text-body-md text-on-surface focus:outline-none border-none" id="kt-pln-reg-title" name="title" type="text" data-kt-field="title" data-kt-pln-title data-testid="kt-pln-ui02-title" value=""/>
</div>
<div class="font-body-sm text-body-sm text-status-exhausted" data-kt-field-error="title" hidden></div>
</div>
<div class="flex flex-col gap-stack-xs">
<label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-reg-currency">Currency <span class="text-status-exhausted">*</span></label>
<div class="relative input-glow rounded border border-subtle bg-surface-container-lowest transition-all">
<select class="w-full appearance-none bg-transparent py-2 pl-3 pr-10 font-data-md text-data-md text-on-surface focus:outline-none border-none" id="kt-pln-reg-currency" name="currency" data-kt-field="currency" data-testid="kt-pln-ui02-currency" aria-label="Currency">
<option selected="" value="KES">KES - Kenyan Shilling</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none" aria-hidden="true">arrow_drop_down</span>
</div>
</div>
<div class="flex flex-col gap-stack-xs md:col-span-2">
<label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-reg-ou">Coordinating procurement unit <span class="text-status-exhausted">*</span></label>
<div class="relative input-glow rounded border border-subtle bg-surface-container-lowest transition-all flex items-center">
<span class="material-symbols-outlined pl-3 text-on-surface-variant" aria-hidden="true">search</span>
<select class="w-full appearance-none bg-transparent py-2 pl-2 pr-10 font-body-md text-body-md text-on-surface focus:outline-none border-none" id="kt-pln-reg-ou" name="coordinating_org_unit" data-kt-field="coordinating_org_unit" data-testid="kt-pln-ui02-ou" aria-label="Coordinating Organisation Unit">
<option value="">Select unit...</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none" aria-hidden="true">arrow_drop_down</span>
</div>
<p class="font-body-sm text-body-sm text-on-surface-variant mt-1">This is the unit authorised to coordinate procurement for the entity. It need not be the lowest Organisation Unit.</p>
<div class="font-body-sm text-body-sm text-status-exhausted" data-kt-field-error="coordinating_org_unit" hidden></div>
</div>
</div>
</div>
</div>
</div>
</div>
<div class="absolute bottom-0 left-0 w-full bg-surface border-t border-subtle p-4 flex justify-end gap-4 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-20" data-testid="kt-pln-ui02-actions">
<a class="px-6 py-2 rounded border border-subtle bg-transparent text-primary font-label-caps text-label-caps hover:bg-surface-container-low transition-colors" href="/app/planning-workspace" data-testid="kt-pln-ui02-cancel">Cancel</a>
<button class="px-6 py-2 rounded bg-primary text-on-primary font-label-caps text-label-caps shadow-sm hover:bg-on-primary-fixed-variant transition-colors flex items-center gap-2" type="submit" data-testid="kt-pln-ui02-submit">
<span class="material-symbols-outlined text-[18px]" aria-hidden="true">add_task</span>
Create plan
</button>
</div>
</form>
</main>
</div>`;
};
