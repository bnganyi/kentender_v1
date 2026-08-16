// PLN-UI-09 — high-fidelity application canvas port of revision/PLN-UI-09.html.
// Export and historical-version actions are omitted where the approved ledger overrides the artifact.
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_plan_approved = function () {
	return `<div class="kt-pln-root kt-stitch-canvas" data-testid="kt-pln-ui09-root">
<main class="kt-pln-ui09-canvas">
<header class="kt-pln-approved-heading" data-testid="kt-pln-ui09-header"><div><h1 class="font-headline-lg text-headline-lg text-on-surface" data-kt-pln-ui09-title>Annual Procurement Plan</h1><div class="kt-pln-approved-badges"><span class="kt-pln-chip kt-pln-chip-secondary"><span class="kt-pln-dot"></span>Open Plan</span><span class="kt-pln-chip kt-pln-chip-success"><span class="kt-pln-dot"></span><span data-kt-pln-ui09-version>Approved Version</span></span></div><p class="kt-pln-approved-evidence"><span class="material-symbols-outlined">verified</span><span data-kt-pln-ui09-approved-evidence></span></p></div><button class="kt-pln-button-primary" data-testid="kt-pln-ui09-add-item" data-kt-pln-action="add-demand"><span class="material-symbols-outlined">add</span>Add Plan Item</button></header>

<section data-testid="kt-pln-ui09-successor-notice" class="kt-pln-successor hidden" data-kt-pln-ui09-successor hidden><p data-kt-pln-ui09-successor-copy></p><button class="kt-pln-button-secondary" data-testid="kt-pln-ui09-continue" data-kt-pln-action="continue-update">Continue update</button></section>

<section class="kt-pln-approved-summary" data-testid="kt-pln-ui09-summary">
<article><span class="kt-pln-summary-hover kt-pln-summary-primary"></span><p class="kt-pln-metric-label">Approved plan value</p><strong class="font-data-lg text-data-lg" data-kt-pln-ui09-total>KES 0</strong></article>
<article><span class="kt-pln-summary-hover kt-pln-summary-secondary"></span><p class="kt-pln-metric-label">Active Plan Items</p><strong class="font-headline-md text-headline-md" data-kt-pln-ui09-items>0</strong></article>
<article><span class="kt-pln-summary-hover kt-pln-summary-success"></span><p class="kt-pln-metric-label">Finance confirmed</p><strong class="font-headline-md text-headline-md" data-kt-pln-ui09-finance>0 of 0</strong><span class="kt-pln-progress"><i class="kt-pln-progress-success"></i></span></article>
<article><span class="kt-pln-summary-hover kt-pln-summary-committed"></span><p class="kt-pln-metric-label">Tender take-up</p><strong class="font-headline-md text-headline-md" data-kt-pln-ui09-takeup>0 of 0</strong><span class="kt-pln-progress"><i class="kt-pln-progress-committed"></i></span></article>
</section>

<section class="kt-pln-approved-implementation"><div class="kt-pln-approved-filters" data-testid="kt-pln-ui09-filters"><div class="kt-pln-approved-section-title"><span class="material-symbols-outlined">monitoring</span><h2 class="font-headline-sm text-headline-sm">Plan implementation</h2></div><div class="kt-pln-filter-row"><div class="relative"><select data-kt-pln-ui09-filter="period" aria-label="Reporting period"><option></option></select></div><span class="font-body-sm text-body-sm text-on-surface-variant" data-kt-pln-ui09-as-at></span><div class="relative"><select data-kt-pln-ui09-filter="ou" aria-label="Organisation Unit"><option value="">All permitted units</option></select></div><div class="relative"><select data-kt-pln-ui09-filter="status" aria-label="Implementation status"><option value="">All statuses</option></select></div></div></div><div class="overflow-x-auto custom-scrollbar"><table data-testid="kt-pln-ui09-implementation-table" class="kt-pln-approved-table"><thead><tr><th>Requirement</th><th>Organisation Unit</th><th class="text-right">Approved value</th><th>Tender take-up</th><th>Next planned milestone</th><th>Actual progress</th><th>Variance</th><th class="text-right">Action</th></tr></thead><tbody data-kt-pln-ui09-body></tbody></table></div></section>

<section class="kt-pln-approved-history"><h2 class="font-headline-sm text-headline-sm"><span class="material-symbols-outlined">history</span>Version history</h2><div class="kt-pln-timeline" data-kt-pln-ui09-history></div></section>
</main><div data-kt-pln-dialog-host></div></div>`;
};
