// BUD-UI-02 — Stitch Funding Performance (funding_performance_…/code.html).
// Fake sidenav / TopNav discarded; Desk + CL shell.
frappe.provide("kentender_budget.ui_fixtures");

kentender_budget.ui_fixtures.performance = function () {
	return `<div class="kt-bud-root kt-stitch-canvas" data-testid="kt-bud-performance">
<div class="flex-1 p-container-padding max-w-7xl mx-auto w-full flex flex-col gap-section-gap" data-testid="kt-bud-performance-canvas">
<div class="kt-bud-perf-header" data-testid="kt-bud-performance-header">
<div class="kt-bud-perf-header-main">
<h1 class="font-headline-lg text-headline-lg text-primary" data-testid="kt-bud-performance-title">Funding Performance</h1>
<p class="text-body-lg text-on-surface-variant mt-1" data-testid="kt-bud-performance-subtitle">Monitor procurement funding coverage, commitments and exceptions.</p>
<div class="kt-bud-perf-meta" data-testid="kt-bud-performance-meta">
<div class="kt-bud-perf-entity" data-testid="kt-bud-performance-entity">
<span class="material-symbols-outlined text-sm" aria-hidden="true">domain</span>
<span class="font-medium text-on-surface" data-kt-bud-perf-entity>—</span>
</div>
<div class="kt-bud-perf-as-at text-outline" data-testid="kt-bud-performance-as-at">
<span class="material-symbols-outlined text-sm" aria-hidden="true">schedule</span>
<span data-kt-bud-perf-as-at>—</span>
</div>
</div>
</div>
<div class="kt-bud-perf-header-actions">
<button type="button" class="kt-bud-perf-export border" data-testid="kt-bud-performance-export" data-kt-bud-perf-export>
<span class="material-symbols-outlined text-[20px]" aria-hidden="true">download</span>
Export report
</button>
</div>
</div>

<div class="kt-bud-perf-notice hidden" data-testid="kt-bud-performance-notice" data-kt-bud-perf-notice hidden role="status" aria-live="polite">
<span class="material-symbols-outlined" aria-hidden="true">info</span>
<div class="kt-bud-perf-notice-body">
<p class="kt-bud-perf-notice-title" data-kt-bud-perf-notice-title></p>
<p class="kt-bud-perf-notice-msg" data-kt-bud-perf-notice-msg></p>
</div>
<button type="button" class="kt-bud-perf-notice-dismiss" data-testid="kt-bud-performance-notice-dismiss" data-kt-bud-perf-notice-dismiss aria-label="Dismiss">
<span class="material-symbols-outlined" aria-hidden="true">close</span>
</button>
</div>

<div class="kt-bud-perf-filters" data-testid="kt-bud-performance-filters">
<span class="material-symbols-outlined text-outline" aria-hidden="true">filter_list</span>
<div class="kt-bud-perf-filter-field" data-kt-bud-perf-filter-field="fiscal_period">
<div class="kt-bud-perf-select-wrap">
<select aria-label="Fiscal period" data-testid="kt-bud-performance-filter-fiscal" data-kt-bud-perf-filter="fiscal_period">
<option value="">All fiscal periods</option>
</select>
<span class="material-symbols-outlined" aria-hidden="true">expand_more</span>
</div>
</div>
<div class="kt-bud-perf-filter-field" data-kt-bud-perf-filter-field="programme">
<div class="kt-bud-perf-select-wrap">
<select aria-label="Programme" data-testid="kt-bud-performance-filter-programme" data-kt-bud-perf-filter="programme">
<option value="">All programmes</option>
</select>
<span class="material-symbols-outlined" aria-hidden="true">expand_more</span>
</div>
</div>
<div class="kt-bud-perf-filter-field" data-kt-bud-perf-filter-field="primary_target">
<div class="kt-bud-perf-select-wrap">
<select aria-label="Strategic target" data-testid="kt-bud-performance-filter-target" data-kt-bud-perf-filter="primary_target">
<option value="">All strategic targets</option>
</select>
<span class="material-symbols-outlined" aria-hidden="true">expand_more</span>
</div>
</div>
<div class="kt-bud-perf-filter-field" data-kt-bud-perf-filter-field="funding_status">
<div class="kt-bud-perf-select-wrap">
<select aria-label="Funding status" data-testid="kt-bud-performance-filter-status" data-kt-bud-perf-filter="funding_status">
<option value="">All funding statuses</option>
</select>
<span class="material-symbols-outlined" aria-hidden="true">expand_more</span>
</div>
</div>
</div>

<div class="kt-bud-perf-kpi-strip" data-testid="kt-bud-performance-kpis">
<div class="kt-bud-perf-kpi" data-kt-bud-perf-kpi="approved">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Approved</span>
<span class="kt-bud-perf-kpi-value" data-kt-bud-perf-kpi-value="approved">—</span>
</div>
<div class="kt-bud-perf-kpi kt-bud-perf-kpi--reserved" data-kt-bud-perf-kpi="reserved">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Reserved</span>
<span class="kt-bud-perf-kpi-value" data-kt-bud-perf-kpi-value="reserved">—</span>
</div>
<div class="kt-bud-perf-kpi kt-bud-perf-kpi--committed" data-kt-bud-perf-kpi="committed">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Committed</span>
<span class="kt-bud-perf-kpi-value" data-kt-bud-perf-kpi-value="committed">—</span>
</div>
<div class="kt-bud-perf-kpi kt-bud-perf-kpi--available" data-kt-bud-perf-kpi="available">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Available</span>
<span class="kt-bud-perf-kpi-value" data-kt-bud-perf-kpi-value="available">—</span>
</div>
<div class="kt-bud-perf-kpi" data-kt-bud-perf-kpi="actual">
<span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Actual Expenditure</span>
<span class="kt-bud-perf-kpi-value" data-kt-bud-perf-kpi-value="actual">—</span>
</div>
<div class="kt-bud-perf-kpi kt-bud-perf-kpi--attention" data-kt-bud-perf-kpi="attention">
<span class="font-label-caps text-label-caps uppercase">Needs Attention</span>
<div class="kt-bud-perf-kpi-attention">
<span class="kt-bud-perf-kpi-value" data-kt-bud-perf-kpi-value="attention">—</span>
<span class="text-body-md">Line</span>
</div>
</div>
</div>

<div class="kt-bud-perf-table-card" data-testid="kt-bud-performance-coverage-card">
<div class="kt-bud-perf-table-card-head">
<h2 class="font-headline-sm text-headline-sm text-primary">Strategy Funding Coverage</h2>
</div>
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse" data-testid="kt-bud-performance-coverage-table">
<thead>
<tr class="font-label-caps text-label-caps text-on-surface-variant uppercase">
<th class="py-3 px-4">Strategic Target</th>
<th class="py-3 px-4 text-right">Budget Lines</th>
<th class="py-3 px-4 text-right">Approved</th>
<th class="py-3 px-4 text-right">Reserved</th>
<th class="py-3 px-4 text-right">Committed</th>
<th class="py-3 px-4 text-right">Available</th>
<th class="py-3 px-4">Value Treatment</th>
<th class="py-3 px-4 text-center">Attention</th>
<th class="py-3 px-4 text-right">Action</th>
</tr>
</thead>
<tbody data-testid="kt-bud-performance-coverage-tbody" data-kt-bud-perf-coverage-tbody>
<tr><td colspan="9" class="px-4 py-8 text-center text-on-surface-variant">Loading coverage…</td></tr>
</tbody>
</table>
</div>
</div>

<div class="kt-bud-perf-table-card kt-bud-perf-table-card--exceptions" data-testid="kt-bud-performance-exceptions-card">
<div class="kt-bud-perf-table-card-head kt-bud-perf-table-card-head--exceptions">
<span class="material-symbols-outlined" aria-hidden="true">warning</span>
<h2 class="font-headline-sm text-headline-sm">Funding Exceptions</h2>
</div>
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse" data-testid="kt-bud-performance-exceptions-table">
<thead>
<tr class="font-label-caps text-label-caps text-on-surface-variant uppercase">
<th class="py-3 px-4">Exception</th>
<th class="py-3 px-4">Budget Line</th>
<th class="py-3 px-4">Owner</th>
<th class="py-3 px-4">Age</th>
<th class="py-3 px-4 text-right">Action</th>
</tr>
</thead>
<tbody data-testid="kt-bud-performance-exceptions-tbody" data-kt-bud-perf-exceptions-tbody>
<tr><td colspan="5" class="px-4 py-8 text-center text-on-surface-variant">Loading exceptions…</td></tr>
</tbody>
</table>
</div>
</div>

<div class="kt-bud-perf-disclaimer" data-testid="kt-bud-performance-disclaimer" data-kt-bud-perf-disclaimer>
<span class="material-symbols-outlined text-base" aria-hidden="true">info</span>
<p data-kt-bud-perf-disclaimer-text>Strategy alignment shows intended support. It does not prove that procurement caused the strategic result.</p>
</div>
</div>
</div>`;
};
