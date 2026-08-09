// PLN-UI-02 — literal Stitch <main> from docs/mvp-1/04_planning/ui_design/PLN-UI-02.html
// Fake top/side nav discarded; kt-stitch-canvas + testids/bind hooks only.
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_register = function () {
	return `<div class="kt-pln-root kt-stitch-canvas" data-testid="kt-pln-ui02-root">
<main class="flex-grow flex flex-col overflow-y-auto w-full">
<div class="p-container-padding md:p-section-gap max-w-4xl mx-auto w-full flex-grow flex flex-col">
<div class="mb-section-gap" data-testid="kt-pln-ui02-header">
<div class="flex items-center gap-2 text-on-surface-variant font-body-sm text-body-sm mb-stack-sm">
<a class="hover:text-primary transition-colors" href="/app/planning-workspace">Procurement Planning</a>
<span class="material-symbols-outlined text-[16px]" aria-hidden="true">chevron_right</span>
<span class="text-on-surface font-medium">New annual plan</span>
</div>
<h1 class="font-headline-lg text-headline-lg text-on-surface mb-stack-xs">Create annual procurement plan</h1>
<p class="font-body-md text-body-md text-on-surface-variant max-w-2xl">Register the plan that will consolidate approved needs for one Procuring Entity and financial year.</p>
</div>
<div class="bg-status-exhausted/10 border border-status-exhausted/20 rounded-lg p-4 mb-section-gap hidden" data-testid="kt-pln-ui02-blocked" data-kt-pln-register-blocked hidden role="alert">
<p class="font-headline-sm text-headline-sm text-status-exhausted mb-1">Registration blocked</p>
<p class="font-body-md text-body-md text-on-surface mb-4" data-kt-pln-register-blocked-msg>An authorised Procuring Entity assignment is required before you can register a plan.</p>
<a class="inline-flex border border-subtle text-primary font-body-sm text-body-sm font-semibold px-4 py-2 rounded-lg hover:bg-surface-container-low transition-colors" href="/app/planning-workspace" data-testid="kt-pln-ui02-back-workspace">Back to workspace</a>
</div>
<form class="bg-surface-container-lowest border border-subtle rounded-lg flex flex-col overflow-hidden mb-section-gap flex-grow shadow-sm" data-testid="kt-pln-ui02-form" data-kt-pln-register-form novalidate>
<div class="p-section-gap border-b border-subtle flex flex-col gap-6">
<div>
<h2 class="font-label-caps text-label-caps text-on-surface-variant uppercase mb-4 tracking-wider">Plan ownership</h2>
<div class="grid grid-cols-1 md:grid-cols-2 gap-gutter-md">
<div class="flex flex-col gap-2" data-kt-pln-pe-field>
<label class="font-label-caps text-label-caps text-on-surface uppercase flex items-center gap-1" for="kt-pln-reg-pe">
Procuring Entity <span class="text-status-exhausted">*</span>
</label>
<div class="relative" data-kt-pln-pe-select-wrap>
<select class="w-full appearance-none bg-surface-container-lowest border border-outline-variant rounded-DEFAULT py-2 px-3 pr-10 font-body-md text-body-md text-on-surface focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-all" id="kt-pln-reg-pe" name="procuring_entity" data-kt-field="procuring_entity" data-testid="kt-pln-ui02-pe" aria-label="Procuring Entity">
<option disabled="" selected="" value="">Select Procuring Entity...</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none" data-kt-pln-pe-chevron aria-hidden="true">expand_more</span>
</div>
<p class="font-body-md text-body-md text-on-surface bg-surface-container-low border border-outline-variant rounded-DEFAULT py-2 px-3 hidden" data-kt-pln-pe-readonly data-testid="kt-pln-ui02-pe-readonly"></p>
<p class="font-body-sm text-body-sm text-on-surface-variant" data-kt-pln-pe-helper>Choose the entity that owns this plan. This cannot be changed after the plan is created.</p>
<div class="font-body-sm text-body-sm text-status-exhausted" data-kt-field-error="procuring_entity" hidden></div>
</div>
<div class="flex flex-col gap-2">
<label class="font-label-caps text-label-caps text-on-surface uppercase flex items-center gap-1" for="kt-pln-reg-fy">
Financial year <span class="text-status-exhausted">*</span>
</label>
<div class="relative">
<select class="w-full appearance-none bg-surface-container-lowest border border-outline-variant rounded-DEFAULT py-2 px-3 pr-10 font-body-md text-body-md text-on-surface focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-all" id="kt-pln-reg-fy" name="financial_year" data-kt-field="financial_year" data-testid="kt-pln-ui02-fy" aria-label="Financial year">
<option selected="" value="2027/28">2027/28</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none" aria-hidden="true">expand_more</span>
</div>
<div class="mt-1">
<p class="font-data-md text-data-md text-on-surface mb-1" data-kt-pln-period-label data-testid="kt-pln-ui02-period-label">Plan period: —</p>
<p class="font-body-sm text-body-sm text-on-surface-variant">Derived from the configured financial year.</p>
</div>
<div class="font-body-sm text-body-sm text-status-exhausted" data-kt-field-error="financial_year" hidden></div>
</div>
</div>
</div>
</div>
<div class="p-section-gap bg-surface-bright flex-grow">
<div>
<div class="flex items-center justify-between mb-4">
<h2 class="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider">Plan details</h2>
</div>
<div class="grid grid-cols-1 md:grid-cols-2 gap-gutter-md">
<div class="flex flex-col gap-2 md:col-span-2">
<label class="font-label-caps text-label-caps text-on-surface uppercase flex items-center gap-1" for="kt-pln-reg-title">
Plan title <span class="text-status-exhausted">*</span>
</label>
<input class="w-full bg-surface-container-lowest border border-outline-variant rounded-DEFAULT py-2 px-3 font-body-md text-body-md text-on-surface focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-all" id="kt-pln-reg-title" name="title" type="text" data-kt-field="title" data-kt-pln-title data-testid="kt-pln-ui02-title" value=""/>
<div class="font-body-sm text-body-sm text-status-exhausted" data-kt-field-error="title" hidden></div>
</div>
<div class="flex flex-col gap-2">
<label class="font-label-caps text-label-caps text-on-surface uppercase flex items-center gap-1" for="kt-pln-reg-currency">
Currency <span class="text-status-exhausted">*</span>
</label>
<div class="relative">
<select class="w-full appearance-none bg-surface-container-lowest border border-outline-variant rounded-DEFAULT py-2 px-3 pr-10 font-body-md text-body-md text-on-surface focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-all" id="kt-pln-reg-currency" name="currency" data-kt-field="currency" aria-label="Currency">
<option selected="" value="KES">KES</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none" aria-hidden="true">expand_more</span>
</div>
</div>
<div class="flex flex-col gap-2">
<label class="font-label-caps text-label-caps text-on-surface uppercase flex items-center gap-1" for="kt-pln-reg-ou">
Coordinating procurement unit <span class="text-status-exhausted">*</span>
</label>
<div class="relative">
<select class="w-full appearance-none bg-surface-container-lowest border border-outline-variant rounded-DEFAULT py-2 px-3 pr-10 font-body-md text-body-md text-on-surface focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-all" id="kt-pln-reg-ou" name="coordinating_org_unit" data-kt-field="coordinating_org_unit" data-testid="kt-pln-ui02-ou" aria-label="Coordinating Organisation Unit">
<option value="">Select unit...</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none" aria-hidden="true">expand_more</span>
</div>
<p class="font-body-sm text-body-sm text-on-surface-variant">Choose the unit authorised to coordinate procurement for this entity. It does not have to be the lowest organisation unit.</p>
<div class="font-body-sm text-body-sm text-status-exhausted" data-kt-field-error="coordinating_org_unit" hidden></div>
</div>
</div>
<p class="font-body-sm text-body-sm text-on-surface-variant mt-6 p-3 bg-surface-container-low rounded-DEFAULT border border-subtle" data-testid="kt-pln-ui02-no-budget">Budget is not captured on the plan header. Planned value is derived from plan items.</p>
</div>
</div>
<div class="p-4 border-t border-subtle bg-surface-container-lowest flex justify-end gap-3 mt-auto" data-testid="kt-pln-ui02-actions">
<a class="px-4 py-2 font-body-sm text-body-sm font-medium text-status-exhausted hover:bg-error-container/20 rounded-DEFAULT transition-colors" href="/app/planning-workspace">Cancel</a>
<button class="px-6 py-2 bg-primary text-on-primary font-body-sm text-body-sm font-medium rounded-DEFAULT hover:bg-primary/90 transition-colors shadow-sm" type="submit" data-testid="kt-pln-ui02-submit">
Create plan
</button>
</div>
</form>
</div>
</main>
</div>`;
};
