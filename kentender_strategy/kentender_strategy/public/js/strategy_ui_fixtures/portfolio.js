// Extracted from docs/mvp-1/01_strategy/ui_design/strategy_portfolio_strategy_alignment/code.html <main>
// Only surgical data-testid / data-kt-str-action hooks added — Stitch classes preserved.
// Table / My Work / summary counts are live-bound (seed plan MOH-SP-2026-2030 via API).
frappe.provide("kentender_strategy.ui_fixtures");
kentender_strategy.ui_fixtures.portfolio = function () {
	return `<div class="kt-str-root kt-stitch-canvas" data-testid="kt-str-portfolio">
<!-- Header Section -->
<div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4" data-testid="kt-str-pf-header">
<div class="min-w-0 flex-1">
<h1 class="font-headline-lg text-headline-lg text-primary">Strategy Alignment</h1>
<p class="font-body-md text-body-md text-on-surface-variant mt-1">Govern strategic outcomes, public-value commitments and performance targets used across procurement.</p>
</div>
<div class="flex items-center gap-3 shrink-0">
<button type="button" data-kt-str-action="open-performance" data-testid="kt-str-open-performance" class="text-primary hover:bg-surface-container px-4 py-2 rounded-lg font-label-caps text-label-caps transition-colors flex items-center gap-2">
<span class="material-symbols-outlined text-[18px]" aria-hidden="true">analytics</span>
Open Strategy Performance
</button>
<button type="button" data-kt-str-action="create-plan" data-testid="kt-str-create-plan" class="bg-primary text-on-primary px-5 py-2.5 rounded-lg flex items-center gap-2 font-semibold text-body-md shadow-sm hover:opacity-90 transition-all">
<span class="material-symbols-outlined text-lg">add</span>
        Create strategic plan
      </button>
</div>
</div>
<!-- Summary Strip -->
<div class="grid grid-cols-4 gap-gutter mb-6" data-testid="kt-str-summary-strip">
<div class="bg-surface-container-lowest border border-outline-variant p-4 rounded-lg flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-status-available/10 flex items-center justify-center text-status-available">
<span class="material-symbols-outlined">check_circle</span>
</div>
<div>
<span class="block font-headline-sm text-headline-sm text-primary" data-kt-str-count="active">—</span>
<span class="text-label-caps text-on-surface-variant opacity-70">Active plans</span>
</div>
</div>
<div class="bg-surface-container-lowest border border-outline-variant p-4 rounded-lg flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-status-reserved/10 flex items-center justify-center text-status-reserved">
<span class="material-symbols-outlined">pending_actions</span>
</div>
<div>
<span class="block font-headline-sm text-headline-sm text-primary" data-kt-str-count="submitted">—</span>
<span class="text-label-caps text-on-surface-variant opacity-70">Awaiting review</span>
</div>
</div>
<div class="bg-surface-container-lowest border border-outline-variant p-4 rounded-lg flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-status-committed/10 flex items-center justify-center text-status-committed">
<span class="material-symbols-outlined">timer</span>
</div>
<div>
<span class="block font-headline-sm text-headline-sm text-primary" data-kt-str-count="measurements_due">—</span>
<span class="text-label-caps text-on-surface-variant opacity-70">Measurements due</span>
</div>
</div>
<div class="bg-surface-container-lowest border border-outline-variant p-4 rounded-lg flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-status-exhausted/10 flex items-center justify-center text-status-exhausted">
<span class="material-symbols-outlined">error</span>
</div>
<div>
<span class="block font-headline-sm text-headline-sm text-primary" data-kt-str-count="measurement_attention">—</span>
<span class="text-label-caps text-on-surface-variant opacity-70">Needs attention</span>
</div>
</div>
</div>
<!-- Layout Grid (Bento Style) -->
<div class="grid grid-cols-12 gap-6" data-testid="kt-str-bento">
<!-- Filters and Table Container -->
<div class="col-span-12 lg:col-span-9 space-y-6" data-kt-str-bento-main="1">
<!-- Filter Row: search + | + dropdowns (single panel) -->
<div class="bg-surface-container-low p-3 rounded-lg border border-outline-variant flex flex-wrap items-center gap-3" data-testid="kt-str-pf-filters">
<div class="relative flex-1 min-w-[200px] max-w-xs">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm">search</span>
<input class="w-full pl-9 pr-4 py-1.5 bg-surface-container-lowest border border-outline-variant rounded text-body-md" placeholder="Search by plan code or title..." type="text" aria-label="Search plans" data-kt-str-filter="search">
</div>
<span class="kt-str-filter-sep text-on-surface-variant select-none" aria-hidden="true" data-testid="kt-str-pf-filter-sep">|</span>
<div class="relative min-w-[140px]">
<select class="w-full bg-surface-container-lowest border border-outline-variant rounded py-1.5 pl-3 pr-8 text-body-md appearance-none" aria-label="Plan type" data-kt-str-filter="plan_type">
<option value="">Plan type</option>
<option value="Entity Strategic Plan">Entity Strategic Plan</option>
<option value="Programme Strategy">Programme Strategy</option>
<option value="Thematic Plan">Thematic Plan</option>
<option value="Annual Implementation Plan">Annual Implementation Plan</option>
</select>
<span class="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm pointer-events-none" aria-hidden="true">expand_more</span>
</div>
<div class="relative min-w-[120px]">
<select class="w-full bg-surface-container-lowest border border-outline-variant rounded py-1.5 pl-3 pr-8 text-body-md appearance-none" aria-label="Period" data-kt-str-filter="period">
<option value="">Period</option>
<option value="2026–2030">2026–2030</option>
<option value="2030–2034">2030–2034</option>
</select>
<span class="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm pointer-events-none" aria-hidden="true">expand_more</span>
</div>
<div class="relative min-w-[120px]">
<select class="w-full bg-surface-container-lowest border border-outline-variant rounded py-1.5 pl-3 pr-8 text-body-md appearance-none" aria-label="Status" data-kt-str-filter="status">
<option value="">Status</option>
<option value="Draft">Draft</option>
<option value="Active">Active</option>
<option value="Submitted">Submitted</option>
</select>
<span class="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm pointer-events-none" aria-hidden="true">expand_more</span>
</div>
<div class="relative min-w-[160px]">
<select class="w-full bg-surface-container-lowest border border-outline-variant rounded py-1.5 pl-3 pr-8 text-body-md appearance-none" aria-label="Entity" data-kt-str-filter="procuring_entity">
<option value="">Entity</option>
</select>
<span class="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm pointer-events-none" aria-hidden="true">expand_more</span>
</div>
<button type="button" class="text-secondary font-semibold text-body-md hover:underline px-2" data-kt-str-action="clear-filters">Clear filters</button>
</div>
<!-- Compact Table -->
<div class="bg-surface-container-lowest border border-outline-variant rounded-lg overflow-hidden shadow-sm">
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse" data-testid="kt-str-plans-table">
<thead class="bg-surface-container-low border-b border-outline-variant">
<tr>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant kt-str-plans-col-plan">Plan</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant kt-str-plans-col-type">Type</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant kt-str-plans-col-period" title="Effective period">Period</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant text-center kt-str-plans-col-ver">Ver.</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant kt-str-plans-col-status">Status</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant kt-str-plans-col-attention">Attention</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant text-right kt-str-plans-col-action">Action</th>
</tr>
</thead>
<tbody class="divide-y divide-surface-container-high" data-kt-str-plans-tbody="1">
<tr data-kt-str-loading="1">
<td class="py-6 px-4 text-body-md text-on-surface-variant" colspan="7">Loading strategic plans…</td>
</tr>
</tbody>
</table>
</div>
` +
		kentender_strategy.ui_fixtures.tablePaginationFooterHtml() +
		`

</div>
</div>
<!-- My Work Sidebar Section -->
<div class="col-span-12 lg:col-span-3 space-y-6" data-kt-str-bento-aside="1" data-testid="kt-str-pf-my-work-col">
<div class="bg-white border border-outline-variant rounded-lg p-card-padding shadow-sm" data-testid="kt-str-pf-my-work">
<div class="flex items-center gap-2 mb-4">
<span class="material-symbols-outlined text-primary">assignment_turned_in</span>
<h3 class="font-headline-sm text-headline-sm text-primary">My Work</h3>
</div>
<div class="space-y-1" data-kt-str-my-work-list="1">
<p class="text-body-md text-on-surface-variant px-1 py-2" data-kt-str-my-work-empty="1">Loading work items…</p>
</div>
</div>
<div class="bg-surface-container-low border border-outline-variant rounded-lg p-card-padding" data-testid="kt-str-pf-quick-help">
<h4 class="font-label-caps text-label-caps text-on-surface-variant mb-2">QUICK HELP</h4>
<p class="text-body-md text-on-surface-variant leading-relaxed">
            Strategic alignment ensures all procurement activities map back to national priorities. 
            <a class="text-secondary font-semibold hover:underline" href="#" data-kt-str-action="pvo-catalogue">Learn about Strategic Pillars →</a>
</p>
</div>
</div>
</div>
</div>`;
};
