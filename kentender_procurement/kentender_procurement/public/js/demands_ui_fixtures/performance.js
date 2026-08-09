// DEM-UI-10 — Demand performance (Stitch DEM-UI-10.html).
// Desk thead lock: primary-fixed #d7e2ff (not Stitch muted grey).
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.demand_performance = function () {
	return `
<div class="kt-dem-perf kt-stitch-canvas" data-testid="kt-dem-ui10-root" data-kt-dem-perf-root data-kt-dem-live="0">
<header class="kt-dem-ui10-header" data-testid="kt-dem-ui10-header">
<h1 class="kt-dem-ui10-title mb-0">Demand performance</h1>
<p class="kt-dem-ui10-subtitle mb-0">Monitor demand flow, funding confirmation and uptake into Procurement Planning.</p>
<p class="kt-dem-ui10-context mb-0" data-kt-dem-label="perf_context" data-testid="kt-dem-ui10-context">—</p>
</header>

<div class="kt-dem-ui10-filters" data-testid="kt-dem-ui10-filters">
<label class="sr-only" for="kt-dem-ui10-pe">Procuring entity</label>
<select id="kt-dem-ui10-pe" class="kt-dem-ui10-select" data-kt-dem-filter="procuring_entity" aria-label="Procuring entity">
<option value="">All entities</option>
</select>
<select class="kt-dem-ui10-select" data-kt-dem-filter="owner_org_unit" aria-label="Owning unit">
<option value="">Owning unit</option>
</select>
<select class="kt-dem-ui10-select" data-kt-dem-filter="demand_route" aria-label="Demand route">
<option value="">Demand route</option>
</select>
<select class="kt-dem-ui10-select" data-kt-dem-filter="status" aria-label="Status">
<option value="">Status</option>
</select>
<select class="kt-dem-ui10-select" data-kt-dem-filter="current_stage" aria-label="Current stage">
<option value="">Current stage</option>
</select>
<button type="button" class="kt-dem-ui10-btn kt-dem-ui10-btn--primary" data-kt-dem-action="perf-apply" data-testid="kt-dem-ui10-apply">Apply</button>
<button type="button" class="kt-dem-ui10-btn kt-dem-ui10-btn--ghost" data-kt-dem-action="perf-clear" data-testid="kt-dem-ui10-clear">Clear</button>
</div>

<div class="kt-dem-ui10-strip" data-testid="kt-dem-ui10-strip">
<div class="kt-dem-ui10-strip-item">
<span class="kt-dem-ui10-strip-label">Demands</span>
<span class="kt-dem-ui10-strip-value font-data-mono" data-kt-dem-label="strip_demands">0</span>
</div>
<div class="kt-dem-ui10-strip-item">
<span class="kt-dem-ui10-strip-label">Approved value</span>
<span class="kt-dem-ui10-strip-value font-data-mono" data-kt-dem-label="strip_approved_value">KES 0.00</span>
</div>
<div class="kt-dem-ui10-strip-item">
<span class="kt-dem-ui10-strip-label">Returned</span>
<span class="kt-dem-ui10-strip-value font-data-mono kt-dem-ui10-strip-value--warn" data-kt-dem-label="strip_returned">0</span>
</div>
<div class="kt-dem-ui10-strip-item">
<span class="kt-dem-ui10-strip-label">Awaiting action</span>
<span class="kt-dem-ui10-strip-value font-data-mono kt-dem-ui10-strip-value--warn" data-kt-dem-label="strip_awaiting">0</span>
</div>
<div class="kt-dem-ui10-strip-item">
<span class="kt-dem-ui10-strip-label">Approved taken into Planning</span>
<span class="kt-dem-ui10-strip-value font-data-mono kt-dem-ui10-strip-value--ok" data-kt-dem-label="strip_planning">0 of 0</span>
</div>
</div>

<div class="kt-dem-ui10-grid">
<section class="kt-dem-ui10-card" data-testid="kt-dem-ui10-flow">
<h2 class="kt-dem-ui10-card-title">Flow and ageing</h2>
<div class="kt-dem-ui10-table-wrap">
<table class="kt-dem-ui10-table">
<thead>
<tr>
<th>Stage</th>
<th class="text-right">Demands</th>
<th class="text-right">Oldest waiting</th>
<th>Current attention</th>
<th class="text-right">Action</th>
</tr>
</thead>
<tbody data-kt-dem-perf-flow></tbody>
</table>
</div>
</section>

<section class="kt-dem-ui10-card" data-testid="kt-dem-ui10-funding">
<h2 class="kt-dem-ui10-card-title">Funding control</h2>
<div class="kt-dem-ui10-funding-rows">
<div class="kt-dem-ui10-funding-row">
<span>Automatically recommended matches</span>
<span class="font-data-mono" data-kt-dem-label="fund_auto">0</span>
</div>
<div class="kt-dem-ui10-funding-row">
<span>Budget Officer confirmations</span>
<span class="font-data-mono" data-kt-dem-label="fund_bo">0</span>
</div>
<div class="kt-dem-ui10-funding-row">
<span>Recommendations adjusted</span>
<span class="font-data-mono" data-kt-dem-label="fund_adjusted">0</span>
</div>
<div class="kt-dem-ui10-funding-row">
<span class="font-semibold">Funding exceptions</span>
<span class="font-data-mono kt-dem-ui10-text-error" data-kt-dem-label="fund_exceptions">0</span>
</div>
<div class="kt-dem-ui10-funding-unfunded">
<span class="kt-dem-ui10-muted">Unfunded amount requiring resolution:</span>
<span class="font-data-mono kt-dem-ui10-text-error kt-dem-ui10-unfunded" data-kt-dem-label="fund_unfunded">KES 0.00</span>
</div>
<div class="kt-dem-ui10-funding-action">
<button type="button" class="kt-dem-ui10-link" data-kt-dem-action="view-funding-exception" data-testid="kt-dem-ui10-view-exception" hidden>
<span class="material-symbols-outlined text-sm" aria-hidden="true">chevron_right</span>
View funding exception
</button>
</div>
</div>
</section>
</div>

<section class="kt-dem-ui10-card kt-dem-ui10-card--full" data-testid="kt-dem-ui10-planning">
<h2 class="kt-dem-ui10-card-title">Planning uptake</h2>
<div class="kt-dem-ui10-table-wrap">
<table class="kt-dem-ui10-table kt-dem-ui10-table--planning">
<tbody data-kt-dem-perf-planning></tbody>
</table>
</div>
<p class="kt-dem-ui10-empty hidden" data-kt-dem-perf-planning-empty>No planning uptake in this scope.</p>
</section>

<section class="kt-dem-ui10-card kt-dem-ui10-card--full" data-testid="kt-dem-ui10-strategy">
<h2 class="kt-dem-ui10-card-title">Strategy &amp; public-value coverage</h2>
<div class="kt-dem-ui10-table-wrap">
<table class="kt-dem-ui10-table">
<thead>
<tr>
<th>Strategy outcome</th>
<th class="text-right">Approved Demand value</th>
<th class="text-center">Required commitments</th>
<th class="text-center">Addressed or carried forward</th>
<th class="text-right">Attention</th>
</tr>
</thead>
<tbody data-kt-dem-perf-strategy></tbody>
</table>
</div>
</section>

<footer class="kt-dem-ui10-methodology" data-testid="kt-dem-ui10-methodology">
<p class="mb-0">Demand value and Strategy alignment show planned support. They do not prove realised savings, benefits or outcomes.</p>
</footer>
</div>
`;
};
