// PLN-UI-07 — literal structural port of docs/mvp-1/04_planning/ui_design/PLN-UI-07.html drawer.
// Stitch utility classes retained. Only kt-stitch-canvas / testids / bind hooks added.
// Item titles wrap (no ellipsis) per legal-data rule.
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_contribution_drawer = function () {
	return `<div class="kt-pln-ui07-root kt-stitch-canvas fixed inset-0 z-40 drawer-overlay flex justify-end hidden" data-testid="kt-pln-ui07-root" data-kt-pln-contribution-drawer hidden aria-modal="true" role="dialog" aria-labelledby="kt-pln-ui07-title">
<div class="w-full max-w-[400px] md:w-1/3 bg-surface-container-lowest h-full flex flex-col shadow-2xl animate-[slideInRight_0.3s_ease-out]" data-testid="kt-pln-ui07-panel">
<header class="flex items-center justify-between px-container-padding py-4 border-b border-subtle bg-surface-container-lowest">
<h2 id="kt-pln-ui07-title" class="font-headline-md text-headline-md text-on-surface">Submit departmental contribution</h2>
<button type="button" aria-label="Close drawer" class="p-2 text-on-surface-variant hover:bg-surface-container hover:text-on-surface rounded-DEFAULT transition-colors bg-transparent border-0 cursor-pointer" data-kt-pln-action="contrib-close" data-testid="kt-pln-ui07-close">
<span class="material-symbols-outlined" aria-hidden="true">close</span>
</button>
</header>
<div class="flex-1 overflow-y-auto px-container-padding py-section-gap space-y-section-gap">
<section class="bg-surface-container-low rounded-lg p-4 border border-subtle">
<div class="grid grid-cols-1 gap-stack-sm mb-4">
<div>
<p class="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Organisation Unit</p>
<p class="font-body-md text-body-md text-on-surface" data-kt-pln-contrib-ou>Directorate of Digital Health and Policy</p>
</div>
<div>
<p class="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Financial year</p>
<p class="font-body-md text-body-md text-on-surface" data-kt-pln-contrib-fy>2027/28</p>
</div>
</div>
<div class="border-t border-subtle pt-4 grid grid-cols-2 gap-4">
<div>
<p class="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Plan Items</p>
<p class="font-data-md text-data-md text-on-surface" data-kt-pln-contrib-item-count>1</p>
</div>
<div>
<p class="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Total planned value</p>
<p class="font-data-md text-data-md text-on-surface" data-kt-pln-contrib-total>KES 455,000,000</p>
</div>
<div class="col-span-2">
<p class="font-label-caps text-label-caps text-on-surface-variant mb-2 uppercase">Validation</p>
<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-status-available/10 text-status-available font-body-sm text-body-sm" data-kt-pln-contrib-validation data-testid="kt-pln-ui07-validation">
<span class="material-symbols-outlined text-[16px]" aria-hidden="true">check_circle</span>
<span data-kt-pln-contrib-validation-label>Ready</span>
</span>
</div>
</div>
<p class="font-body-sm text-body-sm text-status-exhausted mt-3 hidden" data-kt-pln-contrib-return-reason hidden></p>
</section>
<section>
<h3 class="font-label-caps text-label-caps text-on-surface-variant mb-3 uppercase">Included Items</h3>
<div class="bg-surface-container-lowest border border-subtle rounded-lg divide-y divide-subtle" data-kt-pln-contrib-items data-testid="kt-pln-ui07-items">
</div>
</section>
<section class="space-y-4">
<div>
<label class="block font-label-caps text-label-caps text-on-surface mb-2 uppercase" for="kt-pln-ui07-note">Submission note (Optional)</label>
<textarea class="w-full rounded-DEFAULT border-subtle bg-surface-container-lowest text-on-surface font-body-md text-body-md focus:border-secondary focus:ring-1 focus:ring-secondary/50 placeholder:text-outline" id="kt-pln-ui07-note" name="submission_note" data-kt-pln-field="submission_note" data-kt-field="submission_note" data-testid="kt-pln-ui07-note" placeholder="Add context for Procurement, if needed" rows="3"></textarea>
</div>
<div class="flex items-start gap-3 mt-6 bg-surface-bright p-4 rounded-lg border border-subtle">
<div class="flex items-center h-5 mt-0.5">
<input class="w-4 h-4 rounded border-subtle text-primary focus:ring-primary/50 bg-surface-container-lowest cursor-pointer" id="kt-pln-ui07-declaration" name="declaration" type="checkbox" data-kt-pln-field="declaration" data-kt-field="declaration" data-testid="kt-pln-ui07-declaration" value="1"/>
</div>
<label class="font-body-sm text-body-sm text-on-surface cursor-pointer leading-relaxed" for="kt-pln-ui07-declaration" data-kt-pln-contrib-declaration-label>
I confirm that these requirements represent this Organisation Unit’s planned procurement needs for the stated financial year.
</label>
</div>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="declaration" hidden></div>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="form" hidden></div>
</section>
</div>
<footer class="p-container-padding border-t border-subtle bg-surface-container-lowest flex justify-end gap-3 mt-auto shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]" data-testid="kt-pln-ui07-footer">
<button type="button" class="px-4 py-2 font-body-md text-body-md text-primary border border-subtle rounded-DEFAULT hover:bg-surface-container transition-colors cursor-pointer bg-surface-container-lowest" data-kt-pln-action="contrib-cancel" data-testid="kt-pln-ui07-cancel">
Cancel
</button>
<button type="button" class="px-4 py-2 font-body-md text-body-md bg-primary text-on-primary rounded-DEFAULT hover:bg-primary/90 transition-colors shadow-sm border-0 cursor-pointer" data-kt-pln-action="contrib-confirm" data-testid="kt-pln-ui07-confirm">
Confirm contribution
</button>
</footer>
</div>
</div>`;
};
