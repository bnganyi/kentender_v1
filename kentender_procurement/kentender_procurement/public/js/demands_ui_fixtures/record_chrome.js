// DEM-UIC-002 — Shared Demand record header + five-stage indicator.
// Layout: ID + status + route (top) → title → PE · OU under title → stage strip.
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.demand_record_chrome = function () {
	return `
<div class="kt-dem-record-chrome mb-6" data-testid="kt-dem-record-chrome">
<div class="mb-6" data-testid="kt-dem-record-header" data-kt-dem-record-header>
<div class="flex flex-wrap items-center gap-2 mb-3" data-testid="kt-dem-record-meta-top">
<span class="font-data-mono text-data-mono text-on-surface-variant" data-kt-dem-label="demand_code" data-testid="kt-dem-code">—</span>
<span class="kt-dem-status-pill" data-kt-dem-label="status_display" data-testid="kt-dem-status-pill" role="status" aria-live="polite">—</span>
<span class="kt-dem-route-pill" data-kt-dem-label="demand_route_display" data-testid="kt-dem-route-pill">—</span>
</div>
<div class="kt-dem-record-title-row" data-testid="kt-dem-record-title-row">
<h1 class="font-headline-lg text-headline-lg text-on-surface mb-0" data-kt-dem-label="title" data-testid="kt-dem-record-title">—</h1>
<button type="button" class="kt-dem-view-details hidden" data-kt-dem-action="open-details-drawer" data-testid="kt-dem-view-details" hidden>
<span class="kt-dem-view-details-text">View Details</span>
<span class="material-symbols-outlined" aria-hidden="true">chevron_right</span>
</button>
</div>
<p class="font-body-lg text-body-lg text-on-surface-variant mb-2 hidden" data-kt-dem-create-lead data-testid="kt-dem-create-lead">
Describe what is needed, why it is needed and when it is required.
</p>
<div class="flex items-center gap-2 text-on-surface-variant font-body-md" data-testid="kt-dem-record-pe" data-kt-dem-record-pe>
<span class="material-symbols-outlined text-[18px]" aria-hidden="true">account_balance</span>
<span data-kt-dem-label="pe_ou_display">—</span>
</div>
</div>
<div class="kt-dem-stage-card bg-surface-container-lowest border border-outline-variant rounded-xl p-3" data-testid="kt-dem-stage" data-kt-dem-stage role="navigation" aria-label="Demand stage">
<div class="flex flex-col md:flex-row justify-between gap-4" data-kt-dem-stage-list></div>
</div>
</div>`;
};
