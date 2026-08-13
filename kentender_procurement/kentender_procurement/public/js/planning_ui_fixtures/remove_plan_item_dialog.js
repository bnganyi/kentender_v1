// PLN-UI-05A — literal Stitch confirmation (Draft / Finance / Active variants).
// Source: docs/mvp-1/04_planning/ui_design/PLN-UI-05A_Draft.html, _Finance.html, _Active.html
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_remove_item_dialog = function () {
	return `<div class="absolute inset-0 z-[200] hidden kt-stitch-canvas" data-testid="kt-pln-ui05a-dialog" data-kt-pln-remove-item-dialog hidden>
<div class="absolute inset-0 bg-on-surface/30 backdrop-blur-[2px] z-10" aria-hidden="true" data-kt-pln-action="keep-item"></div>
<div class="relative z-20 flex items-center justify-center w-full h-full p-4">
<div data-kt-pln-05a-variant="draft" data-testid="kt-pln-ui05a-draft">
<div class="relative z-20 w-full max-w-[560px] bg-surface-container-lowest border border-subtle rounded-lg shadow-xl overflow-hidden mx-4" role="dialog" aria-modal="true" aria-labelledby="kt-pln-ui05a-draft-title">
<div class="px-section-gap py-section-gap border-b border-subtle flex items-start justify-between">
<div class="flex items-center gap-stack-sm">
<div class="flex-shrink-0 w-10 h-10 rounded-full bg-status-exhausted/10 flex items-center justify-center"><span aria-hidden="true" class="material-symbols-outlined text-error" style="font-variation-settings: 'FILL' 1;">delete_forever</span></div>
<h2 class="font-headline-sm text-headline-sm text-on-surface" id="kt-pln-ui05a-draft-title" data-testid="kt-pln-ui05a-title">Remove Plan Item from draft?</h2>
</div>
<button type="button" class="text-on-surface-variant hover:text-on-surface transition-colors" data-kt-pln-action="keep-item" aria-label="Close dialog">
<span class="material-symbols-outlined">close</span>
</button>
</div>
<div class="p-section-gap space-y-section-gap">
<p class="font-body-md text-body-md text-on-surface-variant" data-kt-pln-05a-intro>
This removes the item from the current Draft Plan. The Approved Demand will be available for planning again.
</p>
<div class="bg-surface p-container-padding rounded border border-subtle space-y-stack-sm">
<div class="flex flex-col gap-stack-xs pb-stack-sm border-b border-subtle border-opacity-50">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Item</span>
<span class="font-body-md text-body-md font-medium" data-kt-pln-05a-item>Digital health technical staff certification programme</span>
</div>
<div class="grid grid-cols-2 gap-container-padding pb-stack-sm border-b border-subtle border-opacity-50 pt-stack-sm">
<div class="flex flex-col gap-stack-xs">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Organisation Unit</span>
<span class="font-body-sm text-body-sm text-on-surface" data-kt-pln-05a-ou>Human Resources Management and Development</span>
</div>
<div class="flex flex-col gap-stack-xs">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Planned Value</span>
<span class="font-data-md text-data-md text-primary" data-kt-pln-05a-value>KES 80,000,000</span>
</div>
</div>
<div class="grid grid-cols-2 gap-container-padding pt-stack-sm">
<div class="flex flex-col gap-stack-xs">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Approved Sources</span>
<span class="font-body-sm text-body-sm text-on-surface" data-kt-pln-05a-sources>1 Demand · 1 Need Item</span>
</div>
<div class="flex flex-col gap-stack-xs">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Finance Effect</span>
<span class="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-1" data-kt-pln-05a-finance>
<span class="material-symbols-outlined text-[16px]">info</span>
<span data-kt-pln-05a-finance-copy>No funding confirmed; no reservation to release</span>
</span>
</div>
</div>
</div>
<div class="space-y-stack-sm">
<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase" for="kt-pln-ui05a-reason-draft">Reason for removal <span class="text-error">*</span></label>
<textarea class="w-full bg-surface border border-subtle rounded px-3 py-2 font-body-sm text-body-sm text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-secondary/50 focus:border-secondary transition-all" id="kt-pln-ui05a-reason-draft" data-kt-field="reason" placeholder="Briefly explain why this item should be removed from the draft." rows="3"></textarea>
<p class="hidden font-body-sm text-body-sm text-error mt-stack-xs" data-kt-field-error="reason" hidden></p>
</div>
</div>
<div class="px-section-gap py-container-padding bg-surface-bright border-t border-subtle flex justify-end gap-stack-sm">
<button class="px-4 py-2 rounded border border-subtle font-body-sm text-body-sm font-medium text-primary hover:bg-surface-container-low transition-colors" type="button" data-kt-pln-action="keep-item" data-testid="kt-pln-ui05a-keep">
Keep item
</button>
<button class="px-4 py-2 rounded bg-error font-body-sm text-body-sm font-medium text-on-error hover:opacity-90 transition-colors shadow-sm" type="button" data-kt-pln-action="confirm-remove" data-testid="kt-pln-ui05a-confirm">Remove from draft</button>
</div>
</div>
</div>
<div data-kt-pln-05a-variant="finance" data-testid="kt-pln-ui05a-finance" hidden>
<div aria-labelledby="kt-pln-ui05a-finance-title" aria-modal="true" class="relative z-50 w-full max-w-lg mx-container-padding bg-surface-container-lowest rounded-xl shadow-[0_10px_25px_-5px_rgba(0,61,155,0.1),0_8px_10px_-6px_rgba(0,61,155,0.1)] border border-border-subtle flex flex-col overflow-hidden" role="dialog">
<div class="px-section-gap py-section-gap pb-4 border-b border-border-subtle">
<div class="flex items-start gap-4">
<div class="flex-shrink-0 w-10 h-10 rounded-full bg-status-exhausted/10 flex items-center justify-center">
<span aria-hidden="true" class="material-symbols-outlined text-status-exhausted" data-icon="delete_forever" data-weight="fill" style="font-variation-settings: 'FILL' 1;">delete_forever</span>
</div>
<div>
<h2 class="font-headline-sm text-headline-sm text-on-surface mb-stack-xs" id="kt-pln-ui05a-finance-title">Remove Plan Item from draft?</h2>
<p class="font-body-md text-body-md text-on-surface-variant" data-kt-pln-05a-intro>This removes the item from the current Draft Plan. The Approved Demand will be available for planning again.</p>
</div>
</div>
</div>
<div class="px-section-gap py-section-gap flex flex-col gap-section-gap bg-surface-bright">
<div class="bg-surface-container-lowest border border-border-subtle rounded-lg p-container-padding flex flex-col gap-stack-sm relative overflow-hidden">
<div class="absolute left-0 top-0 bottom-0 w-1 bg-status-reserved"></div>
<div class="grid grid-cols-1 gap-4">
<div>
<dt class="font-label-caps text-label-caps text-on-surface-variant uppercase">Item</dt>
<dd class="font-body-sm text-body-sm text-on-surface mt-1" data-kt-pln-05a-item>National digital health infrastructure upgrade</dd>
</div>
<div>
<dt class="font-label-caps text-label-caps text-on-surface-variant uppercase">Organisation Unit</dt>
<dd class="font-body-sm text-body-sm text-on-surface mt-1" data-kt-pln-05a-ou>Directorate of Digital Health and Policy</dd>
</div>
<div>
<dt class="font-label-caps text-label-caps text-on-surface-variant uppercase">Planned value</dt>
<dd class="font-data-md text-data-md text-on-surface mt-1" data-kt-pln-05a-value>KES 455,000,000</dd>
</div>
</div>
<div class="mt-2 bg-status-available/10 border border-status-available/20 rounded p-stack-sm flex items-start gap-2">
<span aria-hidden="true" class="material-symbols-outlined text-status-available text-sm mt-0.5" data-icon="info" data-weight="fill" style="font-variation-settings: 'FILL' 1;">info</span>
<p class="font-body-sm text-body-sm text-on-secondary-fixed-variant m-0 leading-tight" data-kt-pln-05a-finance-copy>Funding confirmation will be cancelled and <span class="font-data-md font-semibold" data-kt-pln-05a-release-amount>KES 455,000,000</span> will be released.</p>
</div>
</div>
<div class="flex flex-col gap-stack-xs">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase flex items-center gap-1" for="kt-pln-ui05a-reason-finance">
Reason for removal <span aria-hidden="true" class="text-status-exhausted">*</span>
</label>
<textarea class="w-full bg-surface-container-lowest border border-border-subtle rounded-DEFAULT px-3 py-2 font-body-sm text-body-sm text-on-surface placeholder-on-surface-variant/50 focus:border-secondary focus:ring-2 focus:ring-secondary/20 transition-all outline-none resize-none" id="kt-pln-ui05a-reason-finance" data-kt-field="reason" name="removal-reason" placeholder="Briefly explain why this item should be removed from the draft." required="" rows="3"></textarea>
<p class="hidden font-body-sm text-body-sm text-error mt-stack-xs" data-kt-field-error="reason" hidden></p>
</div>
</div>
<div class="px-section-gap py-container-padding border-t border-border-subtle bg-surface-container-lowest flex justify-end gap-3">
<button class="px-4 py-2 font-body-md text-body-md font-medium text-primary border border-border-subtle rounded-DEFAULT hover:bg-surface-container-low transition-colors" type="button" data-kt-pln-action="keep-item" data-testid="kt-pln-ui05a-keep">
Keep item
</button>
<button class="px-4 py-2 font-body-md text-body-md font-medium text-on-error bg-status-exhausted rounded-DEFAULT hover:bg-status-exhausted/90 transition-colors shadow-sm" type="button" data-kt-pln-action="confirm-remove" data-testid="kt-pln-ui05a-confirm">
Remove from draft
</button>
</div>
</div>
</div>
<div data-kt-pln-05a-variant="active" data-testid="kt-pln-ui05a-active" hidden>
<div aria-labelledby="kt-pln-ui05a-active-title" aria-modal="true" class="bg-surface-container-lowest w-full max-w-md rounded-xl shadow-lg border border-border-subtle flex flex-col overflow-hidden" role="dialog">
<div class="px-container-padding py-gutter-md border-b border-border-subtle flex items-start justify-between bg-surface-bright">
<div class="flex items-center gap-3">
<div class="bg-status-exhausted/10 p-2 rounded-full flex items-center justify-center">
<span class="material-symbols-outlined text-status-exhausted" style="font-variation-settings: 'FILL' 1;">warning</span>
</div>
<div>
<h2 class="font-headline-sm text-headline-sm text-on-surface" id="kt-pln-ui05a-active-title">Propose Plan Item removal?</h2>
</div>
</div>
<button aria-label="Close dialog" class="text-on-surface-variant hover:text-on-surface transition-colors" type="button" data-kt-pln-action="keep-item">
<span class="material-symbols-outlined">close</span>
</button>
</div>
<div class="px-container-padding py-gutter-md flex flex-col gap-section-gap overflow-y-auto">
<div class="flex flex-col gap-stack-sm">
<p class="font-body-md text-body-md text-on-surface-variant" data-kt-pln-05a-intro>
The item remains active in the current Approved Plan until this update is approved.
</p>
<div class="flex items-start gap-2 bg-surface-container-low p-3 rounded-lg border border-border-subtle">
<span class="material-symbols-outlined text-on-surface-variant text-[20px] mt-0.5">info</span>
<p class="font-body-sm text-body-sm text-on-surface-variant">
If approved, the item will be removed and its uncommitted reservation released.
</p>
</div>
</div>
<div class="bg-surface border border-border-subtle rounded-lg p-4 flex flex-col gap-3">
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1">Item</span>
<p class="font-body-md text-body-md text-on-surface font-medium" data-kt-pln-05a-item>National digital health infrastructure upgrade</p>
</div>
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1">Organisation Unit</span>
<p class="font-body-md text-body-md text-on-surface" data-kt-pln-05a-ou>Directorate of Digital Health and Policy</p>
</div>
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-1">Planned value</span>
<p class="font-data-md text-data-md text-on-surface" data-kt-pln-05a-value>KES 455,000,000</p>
</div>
</div>
<div class="flex flex-col gap-stack-xs">
<label class="font-label-caps text-label-caps text-on-surface uppercase" for="kt-pln-ui05a-reason-active">Reason for removal <span class="text-status-exhausted">*</span></label>
<textarea class="w-full rounded border-border-subtle bg-surface-container-lowest font-body-md text-body-md text-on-surface placeholder:text-on-surface-variant/50 focus:border-secondary focus:ring-1 focus:ring-secondary transition-shadow resize-none" id="kt-pln-ui05a-reason-active" data-kt-field="reason" name="removal-reason" placeholder="Briefly explain why this item should be removed from the draft." required="" rows="3"></textarea>
<p class="hidden font-body-sm text-body-sm text-error mt-stack-xs" data-kt-field-error="reason" hidden></p>
</div>
</div>
<div class="px-container-padding py-gutter-md border-t border-border-subtle bg-surface-bright flex items-center justify-end gap-3 mt-auto">
<button class="px-4 py-2 rounded font-body-md text-body-md font-medium text-primary border border-border-subtle hover:bg-surface-container-low transition-colors" type="button" data-kt-pln-action="keep-item">
Keep item
</button>
<button class="px-4 py-2 rounded font-body-md text-body-md font-medium text-on-error bg-status-exhausted hover:bg-status-exhausted/90 transition-colors shadow-sm flex items-center gap-2" type="button" data-kt-pln-action="confirm-remove" data-testid="kt-pln-ui05a-propose">
Propose removal
</button>
</div>
</div>
</div>
</div>
</div>`;
};
