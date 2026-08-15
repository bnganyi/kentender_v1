// PLN-UI-01 — high-fidelity hand-port of revision/PLN-UI-01.html.
// The existing KenTender shell owns navigation; this fixture owns the live main canvas.
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_workspace = function () {
	return `<div class="kt-pln-root kt-stitch-canvas" data-testid="kt-pln-ui01-root">
<main class="kt-pln-workspace-canvas max-w-7xl mx-auto w-full">
<div class="kt-pln-loading" data-kt-pln-loading role="status" aria-live="polite">
<span class="kt-pln-spinner" aria-hidden="true"></span><span>Loading Procurement Planning workspace…</span>
</div>
<div class="kt-pln-alert kt-pln-alert-error hidden" data-kt-pln-error hidden role="alert" tabindex="-1">
<strong>Planning workspace could not be loaded.</strong><span data-kt-pln-error-message>Try again.</span>
<button type="button" class="text-primary" data-kt-pln-action="retry">Retry</button>
</div>
<div class="kt-pln-alert kt-pln-alert-error hidden" data-kt-pln-blocked hidden role="alert" tabindex="-1" data-testid="kt-pln-ui01-blocked">
<strong>Planning workspace unavailable</strong><span data-kt-pln-blocked-msg>An authorised Procuring Entity assignment is required.</span>
</div>
	<div data-kt-pln-content hidden>
	<div class="kt-pln-heading-group mb-section-gap">
	<header class="kt-pln-page-header" data-testid="kt-pln-ui01-header">
	<div>
	<h1 class="font-headline-lg text-headline-lg text-on-surface mb-2">Procurement Planning</h1>
	<p class="font-body-md text-body-md text-on-surface-variant max-w-2xl">Turn approved needs into funded, approved Plan Items ready for tendering.</p>
	</div>
	<div class="kt-pln-primary-action-wrap">
	<button type="button" class="bg-primary" data-kt-pln-primary-action data-testid="kt-pln-ui01-primary-action" hidden>
	<span data-kt-pln-primary-label>View approved plan</span><span class="material-symbols-outlined text-sm" aria-hidden="true">arrow_forward</span>
	</button>
	</div>
	</header>
	</div>

	<section class="kt-pln-context font-body-sm text-body-sm text-on-surface-variant" data-testid="kt-pln-ui01-filters" aria-label="Workspace context">
	<div class="kt-pln-context-summary" data-kt-pln-context-summary>
	<div class="kt-pln-context-item">
	<span class="font-label-caps text-label-caps">Procuring Entity:</span><strong data-kt-pln-pe-readonly></strong>
	</div>
	<span class="kt-pln-context-separator" aria-hidden="true">|</span>
	<div class="kt-pln-context-item">
	<span class="font-label-caps text-label-caps">Financial year:</span><strong data-kt-pln-fy-readonly></strong>
	</div>
	<span class="kt-pln-context-separator" aria-hidden="true">|</span>
	<button type="button" class="kt-pln-context-change" data-kt-pln-action="change-context">Change</button>
	</div>
	<div class="kt-pln-context-controls" data-kt-pln-context-controls hidden>
	<label class="sr-only" for="kt-pln-filter-pe">Procuring Entity</label>
	<select id="kt-pln-filter-pe" data-kt-pln-pe-select data-kt-pln-filter="procuring_entity" aria-label="Procuring Entity"></select>
	<label class="sr-only" for="kt-pln-filter-fy">Financial year</label>
	<select id="kt-pln-filter-fy" data-kt-pln-filter="financial_year" aria-label="Financial year"></select>
	</div>
	<p class="kt-pln-context-helper" data-kt-pln-context-helper></p>
	</section>

<section class="kt-pln-plan-block mb-section-gap" data-kt-pln-plan-panel data-testid="kt-pln-ui01-plan-panel">
	<div data-kt-pln-current-plan>
	<div class="kt-pln-plan-heading">
	<div>
	<p class="font-data-md kt-pln-reference" data-kt-pln-plan-reference></p>
	<h2 class="font-headline-md text-headline-md" data-kt-pln-plan-title></h2>
<div class="kt-pln-status-line" data-kt-pln-plan-status-line></div>
</div>
</div>
<div class="kt-pln-summary-grid" data-kt-pln-summary-grid></div>
</div>
<div class="kt-pln-purposeful-empty" data-kt-pln-no-plan hidden>
<span class="material-symbols-outlined" aria-hidden="true">event_busy</span>
<div><h2 class="font-headline-sm" data-kt-pln-no-plan-heading>No annual Procurement Plan</h2><p data-kt-pln-no-plan-msg></p><p class="kt-pln-empty-supporting" data-kt-pln-no-plan-supporting></p></div>
</div>
</section>

<section class="mb-section-gap" data-testid="kt-pln-ui01-work-section">
<div class="kt-pln-section-title"><span class="material-symbols-outlined kt-pln-reserved" aria-hidden="true">assignment_late</span><h3 class="font-headline-sm text-headline-sm">Work requiring action</h3></div>
<div class="kt-pln-work-controls" data-kt-pln-work-controls hidden>
<label class="sr-only" for="kt-pln-work-filter">Work type</label>
<select id="kt-pln-work-filter" data-kt-pln-filter="work_type" data-testid="kt-pln-ui01-work-filter" aria-label="Work type"></select>
	<div class="kt-pln-search-wrap"><span class="material-symbols-outlined" aria-hidden="true">search</span><label class="sr-only" for="kt-pln-work-search">Search work</label><input id="kt-pln-work-search" type="text" placeholder="Search work" data-kt-pln-work-search data-testid="kt-pln-ui01-work-search"></div>
</div>
<div class="kt-pln-table-block" data-kt-pln-work-table>
<div class="overflow-x-auto"><table data-testid="kt-pln-ui01-table">
<thead><tr><th>Work item</th><th>Type</th><th>Organisation Unit</th><th class="text-right">Amount</th><th>Why it needs action</th><th>Status</th><th>Action</th></tr></thead>
<tbody data-kt-pln-work-body></tbody>
</table></div>
</div>
<div class="kt-pln-purposeful-empty" data-kt-pln-work-empty hidden><span class="material-symbols-outlined" aria-hidden="true">task_alt</span><p data-kt-pln-work-empty-text>Nothing currently requires your planning action.</p></div>
</section>

<section data-testid="kt-pln-ui01-waiting-section">
<div class="kt-pln-section-title"><span class="material-symbols-outlined text-on-surface-variant" aria-hidden="true">hourglass_empty</span><h3 class="font-headline-sm text-headline-sm">Waiting on others</h3></div>
<div class="kt-pln-table-block" data-kt-pln-waiting-table hidden>
<div class="overflow-x-auto"><table data-testid="kt-pln-ui01-waiting-table">
<thead><tr><th>Work item</th><th>Stage</th><th>Status</th><th>With</th></tr></thead>
<tbody data-kt-pln-waiting-body></tbody>
</table></div>
</div>
	<div class="kt-pln-purposeful-empty kt-pln-waiting-empty" data-kt-pln-waiting-empty>
	<span class="material-symbols-outlined" aria-hidden="true">inventory_2</span>
	<p class="font-body-md text-body-md text-on-surface-variant" data-kt-pln-waiting-empty-text>Nothing is currently waiting on another reviewer.</p>
	</div>
</section>
</div>
</main>
</div>`;
};
