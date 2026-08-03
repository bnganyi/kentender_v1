// Extracted from performance_measurements_ministry_of_health_strategic_plan_v2/code.html
// Table/counts are live-bound (STR-UI-08). Fixture rows are shell only.
frappe.provide("kentender_strategy.ui_fixtures");
kentender_strategy.ui_fixtures.measurements = function () {
	return `<div class="kt-str-root kt-str-meas-root" data-testid="kt-str-measurements">
<!-- Workspace Header -->
<div class="bg-surface-container-lowest px-8 pt-6 border-b border-outline-variant" data-testid="kt-str-plan-chrome">
<div class="flex items-start justify-between">
<div>
<div class="flex items-center gap-3 mb-1">
<span class="font-data-mono text-data-mono text-on-surface-variant bg-surface-container px-2 py-1 rounded text-xs" data-kt-str-plan-code>—</span>
<span class="bg-status-reserved text-on-surface px-2 py-0.5 rounded font-label-caps text-[10px] uppercase font-bold tracking-wide" data-kt-str-plan-status>—</span>
<span class="text-on-surface-variant text-sm" data-kt-str-plan-version></span>
</div>
<h1 class="font-headline-lg text-headline-lg text-primary mt-2" data-kt-str-plan-title>—</h1>
<p class="text-on-surface-variant mt-1 text-sm" data-kt-str-plan-period></p>
</div>
</div>
<div class="flex gap-6 mt-6 border-b border-surface-variant" data-testid="kt-str-plan-tabs">
<button type="button" class="kt-str-tab pb-3 text-on-surface-variant hover:text-primary font-medium text-sm transition-colors" data-kt-str-tab="strategy-plan-overview">Overview</button>
<button type="button" class="kt-str-tab pb-3 text-on-surface-variant hover:text-primary font-medium text-sm transition-colors" data-kt-str-tab="strategy-plan-structure">Structure</button>
<button type="button" class="kt-str-tab pb-3 text-on-surface-variant hover:text-primary font-medium text-sm transition-colors" data-kt-str-tab="strategy-plan-value-commitments">Value Commitments</button>
<button type="button" class="kt-str-tab pb-3 text-primary border-b-2 border-primary font-medium text-sm is-active" data-kt-str-tab="strategy-plan-measurements">Measurement</button>
<button type="button" class="kt-str-tab pb-3 text-on-surface-variant hover:text-primary font-medium text-sm transition-colors" data-kt-str-tab="strategy-plan-downstream-usage">Downstream Usage</button>
<button type="button" class="kt-str-tab pb-3 text-on-surface-variant hover:text-primary font-medium text-sm transition-colors" data-kt-str-tab="strategy-plan-review">Review</button>
<button type="button" class="kt-str-tab pb-3 text-on-surface-variant hover:text-primary font-medium text-sm transition-colors" data-kt-str-tab="strategy-plan-audit">Audit</button>
</div>
</div>
<!-- Tab Content Area -->
<div class="flex flex-col gap-section-gap px-8 pt-6 pb-8">
<section class="flex flex-col md:flex-row md:items-start justify-between gap-gutter" data-testid="kt-str-meas-header">
<div>
<h3 class="font-headline-md text-headline-md text-on-surface">Performance measurements</h3>
<p class="font-body-md text-body-md text-on-surface-variant mt-1">Submit and verify period results against approved performance targets.</p>
</div>
<div class="shrink-0 mt-4 md:mt-0">
<button type="button" class="w-full md:w-auto bg-primary text-on-primary py-2 px-6 rounded-lg font-body-md font-medium hover:bg-on-primary-fixed-variant transition-colors shadow-sm" data-kt-str-action="submit-measurement" data-kt-str-meas-submit>
                    Submit measurement
                </button>
</div>
</section>
<section class="bg-surface-container-lowest rounded-xl border border-subtle border-outline-variant shadow-sm overflow-hidden flex flex-col">
<div class="bg-surface-container-low p-container-padding border-b border-outline-variant flex flex-col gap-gutter p-4">
<div class="flex flex-wrap gap-gutter text-body-md gap-3" data-kt-str-meas-counts>
<div class="flex items-center gap-2 bg-surface-container-lowest border border-outline-variant rounded-full px-3 py-1 shadow-sm">
<span class="w-2 h-2 rounded-full bg-status-reserved"></span>
<span class="text-on-surface-variant">Due:</span>
<span class="font-data-mono font-medium text-on-surface" data-kt-str-meas-count="due">0</span>
</div>
<div class="flex items-center gap-2 bg-surface-container-lowest border border-outline-variant rounded-full px-3 py-1 shadow-sm">
<span class="w-2 h-2 rounded-full bg-status-committed"></span>
<span class="text-on-surface-variant">Submitted:</span>
<span class="font-data-mono font-medium text-on-surface" data-kt-str-meas-count="submitted">0</span>
</div>
<div class="flex items-center gap-2 bg-surface-container-lowest border border-outline-variant rounded-full px-3 py-1 shadow-sm">
<span class="w-2 h-2 rounded-full bg-status-available"></span>
<span class="text-on-surface-variant">Verified:</span>
<span class="font-data-mono font-medium text-on-surface" data-kt-str-meas-count="verified">0</span>
</div>
<div class="flex items-center gap-2 bg-error-container border border-error/20 rounded-full px-3 py-1 shadow-sm">
<span class="w-2 h-2 rounded-full bg-error"></span>
<span class="text-error font-medium">Needs attention:</span>
<span class="font-data-mono font-bold text-error" data-kt-str-meas-count="needs_attention">0</span>
</div>
</div>
<div class="flex flex-wrap items-center gap-2 mt-2" data-kt-str-meas-filters>
<div class="relative flex-1 min-w-[200px] max-w-xs">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]">search</span>
<input class="w-full pl-10 pr-3 py-1.5 bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md text-on-surface outline-none" placeholder="Search target..." type="text" data-kt-str-meas-search/>
</div>
<select class="py-1.5 pl-3 pr-8 bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md text-on-surface outline-none" data-kt-str-meas-filter-period>
<option value="">Measurement period</option>
</select>
<select class="py-1.5 pl-3 pr-8 bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md text-on-surface outline-none" data-kt-str-meas-filter-workflow>
<option value="">Workflow status</option>
<option value="Draft">Draft</option>
<option value="Submitted">Submitted</option>
<option value="Returned">Returned</option>
<option value="Verified">Verified</option>
<option value="Rejected">Rejected</option>
</select>
<select class="py-1.5 pl-3 pr-8 bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md text-on-surface outline-none" data-kt-str-meas-filter-result>
<option value="">Result status</option>
<option value="On track">On track</option>
<option value="At risk">At risk</option>
<option value="Off track">Off track</option>
<option value="No data">No data</option>
</select>
<button type="button" class="text-secondary font-medium text-body-md hover:underline px-2 py-1.5 ml-auto" data-kt-str-action="clear-meas-filters">
                        Clear filters
                    </button>
</div>
</div>
<div class="overflow-x-auto w-full border-t border-outline-variant">
<table data-testid="kt-str-measurements-table" class="w-full text-left border-collapse min-w-[1000px]">
<thead class="bg-surface-container-low border-b border-outline-variant">
<tr>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider w-1/3">Target</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider whitespace-nowrap w-32">Period</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider whitespace-nowrap text-right w-32">Target value</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider whitespace-nowrap text-right w-32">Actual</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider whitespace-nowrap w-32">Result</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider whitespace-nowrap w-32">Workflow</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider whitespace-nowrap w-40">Corrective action</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider whitespace-nowrap text-right">Action</th>
</tr>
</thead>
<tbody class="divide-y divide-outline-variant bg-surface-container-lowest" data-kt-str-meas-tbody>
</tbody>
</table>
</div>
<div class="bg-surface-container-low p-4 border-t border-outline-variant flex items-center justify-between text-body-md text-on-surface-variant">
<span data-kt-str-meas-footer>Showing 0 entries</span>
</div>
</section>
</div>
</div>`;
};
