// Extracted from docs/mvp-1/01_strategy/ui_design/strategy_performance/code.html <main>
// Only surgical data-testid / data-kt-str-* hooks added — Stitch classes preserved (no BEM rewrite).
frappe.provide("kentender_strategy.ui_fixtures");
kentender_strategy.ui_fixtures.performance = function () {
	return `<div class="kt-str-root kt-str-performance" data-testid="kt-str-performance">
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-section-gap">
<!-- Header Section -->
<div class="flex flex-col md:flex-row md:items-start justify-between gap-4" data-testid="kt-str-perf-header">
<div>
<h1 class="font-headline-lg text-headline-lg text-on-surface mb-2">Strategy Performance</h1>
<p class="text-on-surface-variant text-body-lg">Monitor strategic results and the procurement activity supporting them.</p>
</div>
<div class="flex items-center gap-3">
<button type="button" class="text-primary hover:bg-surface-container px-4 py-2 rounded-lg font-label-caps text-label-caps transition-colors flex items-center gap-2 hidden" data-kt-str-action="open-portfolio" data-testid="kt-str-perf-open-portfolio">
<span class="material-symbols-outlined text-[18px]" aria-hidden="true">open_in_new</span>
Open Strategy Portfolio
</button>
<button type="button" class="bg-primary text-on-primary px-4 py-2 rounded-lg font-label-caps text-label-caps hover:opacity-90 transition-opacity flex items-center gap-2" data-kt-str-action="export-report" data-testid="kt-str-perf-export">
<span class="material-symbols-outlined text-[18px]" aria-hidden="true">download</span>
Export report
</button>
</div>
</div>
<!-- Context Strip & Filters -->
<div class="data-block p-card-padding" data-testid="kt-str-perf-filters">
<div class="grid grid-cols-1 md:grid-cols-4 gap-gutter mb-4">
<div class="col-span-1">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1" for="kt-str-perf-entity">Procuring Entity</label>
<div class="font-body-md text-on-surface bg-surface-container-low px-3 py-2 rounded border border-surface-variant cursor-not-allowed" data-kt-str-perf="entity_label">—</div>
<select id="kt-str-perf-entity" class="hidden w-full font-body-md border-outline-variant rounded bg-surface-container-lowest" data-kt-str-filter="procuring_entity" aria-label="Procuring entity"></select>
</div>
<div class="col-span-2">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1">Active Plan</label>
<div class="font-data-mono text-data-mono text-on-surface bg-surface-container-low px-3 py-2 rounded border border-surface-variant cursor-not-allowed truncate" data-kt-str-perf="plan_block" title=""><div class="font-body-md" data-kt-str-perf="plan_name">—</div><div class="text-[10px] text-on-surface-variant font-data-mono" data-kt-str-perf="plan_code">—</div></div>
<select class="hidden w-full font-body-md border-outline-variant rounded mt-2" data-kt-str-filter="plan_code" aria-label="Active plan"></select>
</div>
<div class="col-span-1">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1" for="kt-str-perf-period">Reporting Period</label>
<div class="relative">
<select id="kt-str-perf-period" class="w-full font-body-md border border-outline-variant rounded py-2 pl-3 pr-8 focus:ring-primary focus:border-primary bg-surface-container-lowest appearance-none" data-kt-str-filter="period" aria-label="Reporting period">
<option value="">All periods</option>
</select>
<span class="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm pointer-events-none" aria-hidden="true">expand_more</span>
</div>
</div>
</div>
<div class="flex flex-wrap items-end gap-gutter pt-4 border-t border-surface-variant">
<div class="flex-1 min-w-[200px]">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1" for="kt-str-perf-programme">Programme</label>
<div class="relative">
<select id="kt-str-perf-programme" class="w-full font-body-md border border-outline-variant rounded py-2 pl-3 pr-8 focus:ring-primary focus:border-primary bg-surface-container-lowest appearance-none" data-kt-str-filter="programme" aria-label="Programme">
<option value="">All Programmes</option>
</select>
<span class="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm pointer-events-none" aria-hidden="true">expand_more</span>
</div>
</div>
<div class="flex-1 min-w-[200px]">
<label class="block font-label-caps text-label-caps text-on-surface-variant mb-1" for="kt-str-perf-sub">Sub-programme</label>
<div class="relative">
<select id="kt-str-perf-sub" class="w-full font-body-md border border-outline-variant rounded py-2 pl-3 pr-8 focus:ring-primary focus:border-primary bg-surface-container-lowest appearance-none" data-kt-str-filter="sub_programme" aria-label="Sub-programme">
<option value="">All Sub-programmes</option>
</select>
<span class="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm pointer-events-none" aria-hidden="true">expand_more</span>
</div>
</div>
<div class="flex gap-2">
<button type="button" class="border border-outline-variant text-primary px-4 py-2 rounded-lg font-label-caps text-label-caps hover:bg-surface-container transition-colors" data-kt-str-action="clear-filters" data-testid="kt-str-perf-clear">Clear filters</button>
<button type="button" class="bg-primary text-on-primary px-4 py-2 rounded-lg font-label-caps text-label-caps hover:opacity-90 transition-opacity" data-kt-str-action="apply-filters" data-testid="kt-str-perf-apply">Apply filters</button>
</div>
</div>
<div class="mt-4 text-xs text-on-surface-variant flex items-center justify-between">
<span data-kt-str-perf="as_at">As at —</span>
<span data-kt-str-perf="sources">Sources available: —</span>
</div>
<div class="mt-2 text-xs text-error hidden" data-kt-str-perf="source_unavailable" data-testid="kt-str-perf-source-unavailable"></div>
</div>
<!-- Performance Strip -->
<div class="flex flex-wrap gap-2" data-testid="kt-str-perf-strip"><div class="flex-1 min-w-[140px] bg-surface-container-lowest border border-outline-variant rounded-lg p-3 flex flex-col justify-center items-center"><span class="font-headline-md text-headline-md text-on-surface" data-kt-str-strip="active_targets">—</span><span class="font-label-caps text-label-caps text-on-surface-variant text-center mt-1">Active targets</span></div><div class="flex-1 min-w-[140px] bg-[#f0fdf4] border border-[#bbf7d0] rounded-lg p-3 flex flex-col justify-center items-center"><span class="font-headline-md text-headline-md text-[#166534]" data-kt-str-strip="on_track">—</span><span class="font-label-caps text-label-caps text-[#166534] text-center mt-1">On track</span></div><div class="flex-1 min-w-[140px] bg-[#fffbeb] border border-[#fde68a] rounded-lg p-3 flex flex-col justify-center items-center"><span class="font-headline-md text-headline-md text-[#92400e]" data-kt-str-strip="at_risk">—</span><span class="font-label-caps text-label-caps text-[#92400e] text-center mt-1">At risk</span></div><div class="flex-1 min-w-[140px] bg-[#fef2f2] border border-[#fecaca] rounded-lg p-3 flex flex-col justify-center items-center"><span class="font-headline-md text-headline-md text-[#991b1b]" data-kt-str-strip="off_track">—</span><span class="font-label-caps text-label-caps text-[#991b1b] text-center mt-1">Off track</span></div><div class="flex-1 min-w-[140px] bg-surface-container border border-outline-variant rounded-lg p-3 flex flex-col justify-center items-center"><span class="font-headline-md text-headline-md text-on-surface-variant" data-kt-str-strip="no_data">—</span><span class="font-label-caps text-label-caps text-on-surface-variant text-center mt-1">No data</span></div><div class="flex-1 min-w-[140px] bg-[#fef2f2] border border-[#fecaca] rounded-lg p-3 flex flex-col justify-center items-center relative overflow-hidden"><div class="absolute top-0 left-0 w-1 h-full bg-[#ef4444]"></div><span class="font-headline-md text-headline-md text-[#991b1b]" data-kt-str-strip="ca_overdue">—</span><span class="font-label-caps text-label-caps text-[#991b1b] text-center mt-1">Corrective actions overdue</span></div></div>
<div class="hidden text-sm text-on-surface-variant p-4 border border-outline-variant rounded-lg bg-surface-container-low" data-testid="kt-str-perf-empty" data-kt-str-perf="empty">
No Verified measurements exist for this reporting period.
<button type="button" class="ml-2 text-primary hover:underline font-label-caps text-label-caps" data-kt-str-action="change-period">Change reporting period</button>
</div>
<!-- Bento Grid Layout for Tables to avoid standard stack -->
<div class="grid grid-cols-1 lg:grid-cols-2 gap-section-gap">
<!-- Section 1 — Exceptions Requiring Intervention (Full Width) -->
<div class="data-block overflow-hidden flex flex-col lg:col-span-2" data-testid="kt-str-perf-exceptions">
<div class="bg-surface-container-low px-card-padding py-4 border-b border-outline-variant flex justify-between items-center">
<h2 class="font-headline-sm text-headline-sm text-error flex items-center gap-2">
<span class="material-symbols-outlined text-[20px]">warning</span>
                            Exceptions Requiring Intervention
                        </h2>
</div>
<div class="overflow-x-auto flex-1">
<table class="w-full data-table">
<thead>
<tr>
<th class="">Exception</th>
<th class="">Affected record</th>
<th class="hidden xl:table-cell">Owner</th>
<th class="">Due or age</th>
<th class="text-right">Action</th>
</tr>
</thead>
<tbody data-kt-str-perf-tbody="exceptions">
<tr data-kt-str-empty="1"><td colspan="5" class="text-on-surface-variant text-sm py-6 text-center">Loading exceptions…</td></tr>
</tbody>
</table>
</div>
</div><div class="lg:col-span-2 data-block overflow-hidden flex flex-col" data-testid="kt-str-perf-outcomes">
<div class="bg-surface-container-low px-card-padding py-4 border-b border-outline-variant">
<h2 class="font-headline-sm text-headline-sm text-on-surface">Outcome Performance <span class="text-on-surface-variant font-body-md ml-2 font-normal" data-kt-str-perf="outcome_count"></span></h2>
</div>
<div class="overflow-x-auto">
<table class="w-full data-table whitespace-nowrap">
<thead><tr><th class="">STRATEGIC OUTCOME</th><th class="">TARGET STATUS</th><th class="">DIRECTION</th><th class="">SUPPORTING PROCUREMENT ACTIVITY</th><th class="">MANAGEMENT ATTENTION</th><th class="text-right">ACTION</th></tr></thead>
<tbody><tr><td class=""><div class="font-semibold">Reliable digital health infrastructure</div><div class="text-xs text-on-surface-variant font-data-mono">MOH-OUT-0001</div></td><td class=""><span class="status-pill status-on-track mr-1">2 ON TRACK</span><span class="status-pill status-at-risk">1 AT RISK</span></td><td class=""><div class="flex items-center gap-1 text-[#166534]"><span class="material-symbols-outlined text-[16px]">trending_up</span><span class="">Improving</span></div></td><td class="text-xs">2 approved demands, 1 tender, 1 active contract</td><td class="text-[#991b1b] text-xs font-semibold">Availability corrective action overdue</td><td class="text-right"><button class="text-primary hover:underline font-label-caps text-label-caps">Review performance</button></td></tr><tr><td class=""><div class="font-semibold">Responsive critical-service recovery</div><div class="text-xs text-on-surface-variant font-data-mono">MOH-OUT-02</div></td><td class=""><span class="status-pill status-on-track mr-1">1 ON TRACK</span><span class="status-pill status-no-data">1 NO DATA</span></td><td class=""><div class="flex items-center gap-1 text-on-surface-variant"><span class="material-symbols-outlined text-[16px]">trending_flat</span><span class="">Stable</span></div></td><td class="text-xs">1 approved demand, 1 procurement-plan item</td><td class="text-[#991b1b] text-xs font-semibold">Q2 recovery-time measurement overdue</td><td class="text-right"><button class="text-primary hover:underline font-label-caps text-label-caps">Review performance</button></td></tr><tr><td class=""><div class="font-semibold">Sustainable digital health capability</div><div class="text-xs text-on-surface-variant font-data-mono">MOH-OUT-03</div></td><td class=""><span class="status-pill status-on-track mr-1">1 ON TRACK</span><span class="status-pill status-off-track">1 OFF TRACK</span></td><td class=""><div class="flex items-center gap-1 text-[#991b1b]"><span class="material-symbols-outlined text-[16px]">trending_down</span><span class="">Declining</span></div></td><td class="text-xs">1 active contract</td><td class="text-[#991b1b] text-xs font-semibold">Skills-transfer milestone overdue</td><td class="text-right"><button class="text-primary hover:underline font-label-caps text-label-caps">Review performance</button></td></tr></tbody>
</table>
</div>
<div class="px-card-padding py-3 text-xs text-on-surface-variant bg-surface-container-low border-t border-outline-variant flex justify-between items-center"><span data-kt-str-perf="outcomes_footer">Showing 0 of 0 outcomes</span></div></div>
<!-- Section 2 — Exceptions Requiring Intervention -->
<!-- Section 3 — Procurement Contribution & Funding -->
<div class="data-block overflow-hidden flex flex-col lg:col-span-2" data-testid="kt-str-perf-procurement">
<div class="bg-surface-container-low px-card-padding py-4 border-b border-outline-variant">
<h2 class="font-headline-sm text-headline-sm text-on-surface">Procurement Contribution &amp; Funding Snapshot</h2>
</div>
<div class="p-4 bg-surface-container-lowest border-b border-outline-variant" data-kt-str-perf="funding">
<div class="flex items-center justify-between mb-4">
<span class="text-sm font-semibold text-on-surface">Funding Snapshot</span>
<div class="flex items-center gap-2">
<span class="text-xs text-on-surface-variant">Approved budget</span>
<span class="font-data-mono text-data-mono" data-kt-str-funding="budget">—</span>
</div>
</div>
<div class="w-full bg-surface-container-highest rounded-full h-3 mb-4 flex overflow-hidden" data-kt-str-funding="bar">
<div class="bg-status-committed h-full" data-kt-str-funding="committed_bar" style="width: 0%" title="Committed"></div>
<div class="bg-status-reserved h-full" data-kt-str-funding="reserved_bar" style="width: 0%" title="Reserved"></div>
<div class="bg-surface-container-highest h-full border-l border-outline-variant" data-kt-str-funding="available_bar" style="width: 0%" title="Available"></div>
</div>
<div class="flex justify-between items-start mb-6">
<div class="flex flex-col">
<div class="flex items-center gap-1.5 text-xs text-on-surface-variant mb-1">
<div class="w-2.5 h-2.5 rounded-full bg-status-committed"></div>
Committed
</div>
<span class="font-data-mono text-data-mono" data-kt-str-funding="committed">—</span>
</div>
<div class="flex flex-col items-center">
<div class="flex items-center gap-1.5 text-xs text-on-surface-variant mb-1">
<div class="w-2.5 h-2.5 rounded-full bg-status-reserved"></div>
Reserved
</div>
<span class="font-data-mono text-data-mono" data-kt-str-funding="reserved">—</span>
</div>
<div class="flex flex-col items-end">
<div class="flex items-center gap-1.5 text-xs text-on-surface-variant mb-1">
<div class="w-2.5 h-2.5 rounded-full bg-surface-container-highest border border-outline-variant"></div>
Available
</div>
<span class="font-data-mono text-data-mono text-status-available font-bold text-lg" data-kt-str-funding="available">—</span>
</div>
</div>
<div class="flex flex-wrap gap-4 pt-4 border-t border-surface-variant mb-4">
<div class="flex-1 bg-surface-container-low rounded p-3">
<div class="text-xs text-on-surface-variant mb-1">Actual expenditure</div>
<div class="font-data-mono text-data-mono" data-kt-str-funding="consumed">—</div>
</div>
<div class="flex-1 bg-surface-container-low rounded p-3">
<div class="text-xs text-on-surface-variant mb-1">Outstanding commitment</div>
<div class="font-data-mono text-data-mono" data-kt-str-funding="outstanding">—</div>
</div>
</div>
<div class="text-[10px] text-on-surface-variant bg-surface-container-low p-2 rounded flex items-start gap-2">
<span class="material-symbols-outlined text-[14px]">info</span>
<span data-kt-str-funding="basis">Available funding equals approved budget less active reservations and contract commitments. Actual expenditure is reported separately because it is already included within the committed contract obligation.</span>
</div>
</div>
<div class="bg-surface-container-low px-card-padding py-3 border-b border-outline-variant">
<h3 class="font-label-caps text-label-caps text-on-surface">Aligned Procurement Pipeline</h3>
</div>
<div class="overflow-x-auto flex-1 bg-surface-container-low/30">
<table class="w-full data-table">
<thead>
<tr>
<th class="">Lifecycle stage</th>
<th class="text-left">Aligned records</th>
<th class="text-right">Current value</th>
<th class="text-right">Action</th>
</tr>
</thead>
<tbody data-kt-str-perf-tbody="stages">
<tr data-kt-str-empty="1"><td colspan="4" class="text-on-surface-variant text-sm py-6 text-center">Loading pipeline…</td></tr>
</tbody>
</table>
<div class="px-4 py-3 text-[10px] text-on-surface-variant bg-surface-container-low border-t border-outline-variant flex items-center gap-2">
<span class="material-symbols-outlined text-[14px]">info</span>
                            Pipeline values represent overlapping procurement lifecycle stages and must not be added together.
                        </div>
</div>
</div>
<!-- Section 4 — Public-value Commitments (Full Width) -->
<div class="lg:col-span-2 data-block overflow-hidden flex flex-col" data-testid="kt-str-perf-commitments">
<div class="bg-surface-container-low px-card-padding py-4 border-b border-outline-variant flex justify-between items-center">
<h2 class="font-headline-sm text-headline-sm text-on-surface">Plan Value Commitments</h2>
</div>
<div class="overflow-x-auto">
<table class="w-full data-table whitespace-nowrap">
<thead><tr class=""><th class="">COMMITMENT</th><th class="">REQUIREMENT LEVEL</th><th class="">FUNDING TREATMENT</th><th class="">DOWNSTREAM ADOPTION</th><th class="">VERIFIED RESULT</th><th class="">ATTENTION</th><th class="text-right">ACTION</th></tr></thead>
<tbody><tr class=""><td class=""><div class="font-semibold">Improve infrastructure efficiency</div><div class="text-xs text-on-surface-variant font-data-mono">PVO-EFT-01</div></td><td class=""><span class="status-pill bg-surface-container-highest text-on-surface-variant">REQUIRED</span></td><td class="text-xs">Embedded in budget line</td><td class="text-xs"><span class="text-[#166534] font-semibold">4 of 4</span> applicable Value Cases addressed</td><td class="text-xs">Availability 99.6% against 99.9% target — Q2 FY 2027/28</td><td class="text-[#991b1b] text-xs font-semibold">Corrective action overdue</td><td class="text-right"><button class="text-primary hover:underline font-label-caps text-label-caps">Review commitment</button></td></tr><tr class=""><td class=""><div class="font-semibold">Reduce whole-life infrastructure cost</div><div class="text-xs text-on-surface-variant font-data-mono">PVO-ECO-01</div></td><td class=""><span class="status-pill bg-surface-container-highest text-on-surface-variant">REQUIRED</span></td><td class="text-xs">Dedicated allocation — KES 40M</td><td class="text-xs"><span class="text-[#92400e] font-semibold">3 of 4</span> applicable Value Cases addressed</td><td class="text-xs text-on-surface-variant">No verified Q2 measure</td><td class="text-[#92400e] text-xs font-semibold">1 treatment outstanding</td><td class="text-right"><button class="text-primary hover:underline font-label-caps text-label-caps">Review treatment</button></td></tr></tbody>
</table>
</div>
<div class="px-card-padding py-3 text-[10px] text-on-surface-variant bg-surface-container-low border-t border-outline-variant flex items-center gap-2"><span class="material-symbols-outlined text-[14px]">info</span>
                        “Addressed” means the commitment was considered and treated downstream; it does not prove achievement.</div>
</div>
</div>
</div>
</div>`;
};
