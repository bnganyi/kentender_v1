// Register Approved Budget — Stitch main from ui_design/register_approved_budget/code.html
// Fake top nav discarded; surgical data-kt-bud-* hooks only. No Budget code input.
frappe.provide("kentender_budget.ui_fixtures");

kentender_budget.ui_fixtures.register = function () {
	return `<div class="kt-bud-root kt-stitch-canvas" data-testid="kt-bud-register" data-kt-bud-live="0">
<main class="flex-1 flex flex-col items-center py-section-gap px-container-padding w-full max-w-4xl mx-auto" data-testid="kt-bud-register-main">
<div class="w-full mb-section-gap" data-testid="kt-bud-register-header">
<h1 class="font-headline-lg text-headline-lg text-primary mb-2">Register approved budget</h1>
<p class="font-body-lg text-body-lg text-on-surface-variant">Register an approved financial baseline for procurement use in KenTender.</p>
</div>
<div class="w-full bg-data-block-bg rounded-lg border border-border-subtle p-card-padding shadow-sm flex flex-col gap-section-gap" data-testid="kt-bud-register-form">
<section class="flex flex-col gap-4" data-testid="kt-bud-register-identity">
<h2 class="font-headline-sm text-headline-sm text-on-surface border-b border-border-subtle pb-2">Budget identity</h2>
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
<div class="flex flex-col gap-1">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase">Procuring Entity</label>
<input class="w-full bg-surface-container-low border-outline-variant text-on-surface-variant font-body-md text-body-md rounded-lg p-2 cursor-not-allowed" disabled="" type="text" value="" data-kt-bud-field="procuring_entity_label" aria-readonly="true">
</div>
<div class="flex flex-col gap-1">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase" for="kt-bud-fiscal-period">Fiscal period</label>
<select id="kt-bud-fiscal-period" class="w-full border-outline-variant text-on-surface font-body-md text-body-md rounded-lg p-2 focus:border-primary focus:ring-1 focus:ring-primary appearance-none" data-kt-bud-field="fiscal_period" aria-label="Fiscal period">
<option value="2028/29">FY 2028/29</option>
<option value="2027/28">FY 2027/28</option>
</select>
<p class="text-xs text-error hidden" data-kt-bud-error="fiscal_period"></p>
</div>
<div class="flex flex-col gap-1 md:col-span-2">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase" for="kt-bud-title">Budget title</label>
<input id="kt-bud-title" class="w-full border-outline-variant text-on-surface font-body-md text-body-md rounded-lg p-2 focus:border-primary focus:ring-1 focus:ring-primary" type="text" value="" data-kt-bud-field="title" autocomplete="off">
<p class="text-xs text-error hidden" data-kt-bud-error="title"></p>
</div>
<div class="flex flex-col gap-1">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase" for="kt-bud-currency">Currency</label>
<select id="kt-bud-currency" class="w-full border-outline-variant text-on-surface font-body-md text-body-md rounded-lg p-2 focus:border-primary focus:ring-1 focus:ring-primary appearance-none" data-kt-bud-field="currency" aria-label="Currency">
<option value="KES">KES</option>
<option value="USD">USD</option>
</select>
<p class="text-xs text-error hidden" data-kt-bud-error="currency"></p>
</div>
<div class="flex flex-col gap-1">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase" for="kt-bud-owner">Budget owner</label>
<input id="kt-bud-owner" class="w-full border-outline-variant text-on-surface font-body-md text-body-md rounded-lg p-2 focus:border-primary focus:ring-1 focus:ring-primary" type="text" value="" data-kt-bud-field="budget_owner" autocomplete="organization">
<p class="text-xs text-error hidden" data-kt-bud-error="budget_owner"></p>
</div>
</div>
</section>
<section class="flex flex-col gap-4" data-testid="kt-bud-register-approval">
<h2 class="font-headline-sm text-headline-sm text-on-surface border-b border-border-subtle pb-2">Approval details</h2>
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
<div class="flex flex-col gap-1">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase" for="kt-bud-auth-ref">External approval reference</label>
<input id="kt-bud-auth-ref" class="w-full border-outline-variant text-on-surface font-body-md text-body-md rounded-lg p-2 focus:border-primary focus:ring-1 focus:ring-primary" type="text" value="" data-kt-bud-field="authoritative_reference" autocomplete="off">
<p class="text-xs text-error hidden" data-kt-bud-error="authoritative_reference"></p>
</div>
<div class="flex flex-col gap-1">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase" for="kt-bud-approval-date">Approval date</label>
<div class="relative">
<input id="kt-bud-approval-date" class="w-full border-outline-variant text-on-surface font-body-md text-body-md rounded-lg p-2 pl-10 focus:border-primary focus:ring-1 focus:ring-primary appearance-none" type="date" value="" data-kt-bud-field="approval_date">
<span class="material-symbols-outlined absolute left-3 top-2 text-on-surface-variant pointer-events-none" data-icon="calendar_today">calendar_today</span>
</div>
<p class="text-xs text-error hidden" data-kt-bud-error="approval_date"></p>
</div>
<div class="flex flex-col gap-1 md:col-span-2">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase" for="kt-bud-approved-total">Approved total</label>
<div class="relative">
<span class="absolute left-3 top-3 font-data-mono text-data-mono text-on-surface-variant" data-kt-bud-currency-prefix>KES</span>
<input id="kt-bud-approved-total" class="w-full border-outline-variant text-on-surface font-data-mono text-data-mono text-lg rounded-lg p-3 pl-14 focus:border-primary focus:ring-1 focus:ring-primary font-bold bg-surface-bright" type="text" inputmode="decimal" value="" data-kt-bud-field="external_approved_total" autocomplete="off" placeholder="0.00">
</div>
<p class="text-xs text-error hidden" data-kt-bud-error="external_approved_total"></p>
</div>
<div class="flex flex-col gap-1 md:col-span-2" data-testid="kt-bud-register-evidence">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase">Approval evidence <span class="normal-case tracking-normal font-normal">(optional)</span></label>
<div class="flex flex-col gap-3">
<div class="hidden items-center gap-3 border border-outline-variant rounded-lg p-3 bg-surface-container-low" data-kt-bud-evidence-chip>
<span class="material-symbols-outlined text-primary">description</span>
<span class="font-body-md text-body-md text-on-surface flex-1" data-kt-bud-evidence-name></span>
<button class="text-error hover:text-on-error-container transition-colors" type="button" data-kt-bud-action="clear-evidence" aria-label="Remove evidence">
<span class="material-symbols-outlined">delete</span>
</button>
</div>
<div class="border-2 border-dashed border-outline-variant rounded-lg p-6 flex flex-col items-center justify-center gap-2 bg-surface-container-lowest hover:bg-surface-container-low transition-colors cursor-pointer" data-kt-bud-action="pick-evidence" data-testid="kt-bud-evidence-dropzone" role="button" tabindex="0">
<span class="material-symbols-outlined text-on-surface-variant text-headline-lg">cloud_upload</span>
<div class="text-center">
<p class="font-body-md text-body-md text-on-surface">Click to upload or drag and drop</p>
<p class="font-label-caps text-label-caps text-on-surface-variant">PDF, PNG, or JPG (max. 10MB)</p>
</div>
<input type="file" class="hidden" accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg" data-kt-bud-field="approval_evidence_file">
</div>
<input type="hidden" data-kt-bud-field="approval_evidence" value="">
<p class="text-xs text-error hidden" data-kt-bud-error="approval_evidence"></p>
</div>
</div>
</div>
<div class="mt-2 bg-surface-container-low border border-surface-variant rounded-lg p-4 flex gap-3 items-start" data-testid="kt-bud-register-info-note">
<span class="material-symbols-outlined text-on-surface-variant mt-0.5" data-icon="info">info</span>
<p class="font-body-md text-body-md text-on-surface-variant">KenTender records the approved baseline for procurement control. Budget formulation, appropriation and financial approval remain in the authoritative financial process. Future financial-system integration will use an API.</p>
</div>
</section>
</div>
<div class="w-full mt-section-gap flex justify-end items-center gap-4 pb-8" data-testid="kt-bud-register-actions">
<button class="px-6 py-2 rounded-lg border border-outline text-primary font-body-md text-body-md hover:bg-surface-container transition-colors focus:ring-2 focus:ring-primary focus:outline-none" type="button" data-kt-bud-action="cancel" data-testid="kt-bud-register-cancel">
Cancel
</button>
<button class="px-6 py-2 rounded-lg bg-primary text-on-primary font-body-md text-body-md hover:bg-primary-container transition-colors focus:ring-2 focus:ring-primary focus:outline-none shadow-sm" type="button" data-kt-bud-action="create-draft" data-testid="kt-bud-create-draft">
Create draft budget
</button>
</div>
</main>
</div>`;
};
