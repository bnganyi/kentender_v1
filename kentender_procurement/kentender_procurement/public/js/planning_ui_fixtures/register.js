// PLN-UI-02 — hand-port of revision/PLN-UI-02.html.
// Desk owns navigation chrome and breadcrumbs; all five identity values are live/read-only.
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_register = function () {
	return `<div class="kt-pln-root kt-stitch-canvas kt-pln-register-revision" data-testid="kt-pln-ui02-root">
<main class="flex-1 overflow-y-auto p-container-padding md:p-section-gap lg:p-[40px] bg-background" data-testid="kt-pln-ui02-main">
<section class="mb-section-gap max-w-4xl" data-testid="kt-pln-ui02-header">
<h1 class="font-headline-lg text-headline-lg text-on-surface mb-stack-sm">Create annual procurement plan</h1>
<p class="font-body-lg text-body-lg text-on-surface-variant">Confirm the annual Plan that will contain approved needs for this Procuring Entity and financial year.</p>
</section>
<form class="max-w-4xl" data-kt-pln-register-form data-testid="kt-pln-ui02-form" novalidate>
<div class="bg-surface-container-lowest border border-subtle rounded-lg p-section-gap mb-section-gap shadow-sm" data-testid="kt-pln-ui02-identity">
<h2 class="font-label-caps text-label-caps text-on-surface-variant uppercase mb-section-gap pb-stack-sm border-b border-subtle">Plan identity</h2>
<dl class="flex flex-col gap-gutter-md" data-kt-pln-register-identity></dl>
</div>
<div class="mb-section-gap flex items-start gap-stack-sm bg-surface-container-low p-4 rounded border-l-4 border-primary" data-testid="kt-pln-ui02-supporting">
<span class="material-symbols-outlined text-primary mt-1 text-[20px]" aria-hidden="true">info</span>
<p class="font-body-md text-body-md text-on-surface-variant">Creating the Plan will open <strong class="text-on-surface font-medium">Draft Version 1</strong>. You can then add approved Demands as Plan Items.</p>
</div>
<div class="hidden mb-section-gap border border-status-exhausted/30 bg-status-exhausted/10 rounded p-4 font-body-sm" role="alert" data-kt-pln-register-error hidden></div>
<div class="flex items-center justify-end gap-gutter-md border-t border-subtle pt-section-gap mt-section-gap" data-testid="kt-pln-ui02-actions">
<button type="button" class="px-6 py-2 rounded font-label-caps text-label-caps text-primary border border-subtle hover:bg-surface-container-high transition-colors" data-kt-pln-register-cancel data-testid="kt-pln-ui02-cancel">Cancel</button>
<button type="submit" class="px-6 py-2 rounded font-label-caps text-label-caps text-on-primary bg-primary hover:bg-on-primary-fixed-variant transition-colors shadow-sm inline-flex items-center gap-2" data-testid="kt-pln-ui02-submit"><span class="material-symbols-outlined text-[18px]" aria-hidden="true">add_task</span><span data-kt-pln-register-submit-label>Create plan</span></button>
</div>
</form>
</main>
</div>`;
};
