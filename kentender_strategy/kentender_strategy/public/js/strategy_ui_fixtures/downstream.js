// Auto-extracted Stitch canvas — downstream_usage_ministry_of_health_unified_plan
frappe.provide("kentender_strategy.ui_fixtures");
kentender_strategy.ui_fixtures.downstream = function () {
	return `<div class="kt-str-root" data-testid="kt-str-downstream">
<!-- Workspace Header -->
<div class="flex flex-col gap-gutter" data-testid="kt-str-plan-chrome">
<div class="flex items-center gap-2 text-on-surface-variant font-label-caps text-label-caps">
<span class="">MOH-SP-2026-2030</span>
<span class="w-1 h-1 rounded-full bg-outline-variant"></span>
<span class="text-status-reserved">DRAFT</span>
<span class="w-1 h-1 rounded-full bg-outline-variant"></span>
<span class="">v2</span>
</div>
<div class="flex items-center justify-between">
<h2 class="font-headline-lg text-headline-lg-mobile md:text-headline-lg text-on-surface">Ministry of Health Strategic Plan 2026–2030</h2>
</div>
</div>
<!-- Tabs -->
<div class="flex items-center gap-6 border-b border-outline-variant overflow-x-auto scrollbar-hide">
<button type="button" class="pb-3 text-body-md font-medium text-on-surface-variant hover:text-on-surface whitespace-nowrap transition-colors">Overview</button>
<button type="button" class="pb-3 text-body-md font-medium text-on-surface-variant hover:text-on-surface whitespace-nowrap transition-colors">Structure</button>
<button type="button" class="pb-3 text-body-md font-medium text-on-surface-variant hover:text-on-surface whitespace-nowrap transition-colors">Value Commitments</button>
<button type="button" class="pb-3 text-body-md font-medium text-on-surface-variant hover:text-on-surface whitespace-nowrap transition-colors">Measurement</button>
<button type="button" class="pb-3 text-body-md font-bold text-primary border-b-2 border-primary whitespace-nowrap">Downstream Usage</button>
<button type="button" class="pb-3 text-body-md font-medium text-on-surface-variant hover:text-on-surface whitespace-nowrap transition-colors">Review</button>
<button type="button" class="pb-3 text-body-md font-medium text-on-surface-variant hover:text-on-surface whitespace-nowrap transition-colors">Audit</button>
</div>
<!-- Tab Content Area -->
<div class="flex flex-col gap-section-gap">
<!-- Page Header -->
<section class="flex flex-col md:flex-row md:items-start justify-between gap-gutter">
<div>
<h3 class="font-headline-md text-headline-md text-on-surface">Downstream usage</h3>
<p class="font-body-md text-body-md text-on-surface-variant mt-1">See where this plan’s targets and value commitments are referenced across procurement.</p>
</div>
</section>
<!-- Summary Strip -->
<div class="flex flex-wrap gap-3">
<div class="bg-surface-container-lowest px-4 py-2 rounded-lg border border-outline-variant flex items-center gap-2 shadow-sm">
<span class="material-symbols-outlined text-primary text-[18px]">account_balance</span>
<span class="text-body-md font-medium text-on-surface">Budget</span>
<span class="bg-surface-container-highest px-2 py-0.5 rounded-full text-label-caps font-data-mono">3</span>
</div>
<div class="bg-surface-container-lowest px-4 py-2 rounded-lg border border-outline-variant flex items-center gap-2 shadow-sm">
<span class="material-symbols-outlined text-primary text-[18px]">inventory_2</span>
<span class="text-body-md font-medium text-on-surface">Demand</span>
<span class="bg-surface-container-highest px-2 py-0.5 rounded-full text-label-caps font-data-mono">5</span>
</div>
<div class="bg-surface-container-lowest px-4 py-2 rounded-lg border border-outline-variant flex items-center gap-2 shadow-sm">
<span class="material-symbols-outlined text-primary text-[18px]">event_note</span>
<span class="text-body-md font-medium text-on-surface">Planning</span>
<span class="bg-surface-container-highest px-2 py-0.5 rounded-full text-label-caps font-data-mono">4</span>
</div>
<div class="bg-surface-container-lowest px-4 py-2 rounded-lg border border-outline-variant flex items-center gap-2 shadow-sm">
<span class="material-symbols-outlined text-primary text-[18px]">gavel</span>
<span class="text-body-md font-medium text-on-surface">Tender</span>
<span class="bg-surface-container-highest px-2 py-0.5 rounded-full text-label-caps font-data-mono">2</span>
</div>
<div class="bg-surface-container-lowest px-4 py-2 rounded-lg border border-outline-variant flex items-center gap-2 shadow-sm">
<span class="material-symbols-outlined text-primary text-[18px]">history_edu</span>
<span class="text-body-md font-medium text-on-surface">Contract</span>
<span class="bg-surface-container-highest px-2 py-0.5 rounded-full text-label-caps font-data-mono">1</span>
</div>
<div class="bg-surface-container-lowest px-4 py-2 rounded-lg border border-outline-variant flex items-center gap-2 shadow-sm opacity-60">
<span class="material-symbols-outlined text-on-surface-variant text-[18px]">domain</span>
<span class="text-body-md font-medium text-on-surface-variant">Asset</span>
<span class="bg-surface-container-highest px-2 py-0.5 rounded-full text-label-caps font-data-mono">0</span>
</div>
<div class="bg-surface-container-lowest px-4 py-2 rounded-lg border border-outline-variant flex items-center gap-2 shadow-sm opacity-60">
<span class="material-symbols-outlined text-on-surface-variant text-[18px]">delete</span>
<span class="text-body-md font-medium text-on-surface-variant">Disposal</span>
<span class="bg-surface-container-highest px-2 py-0.5 rounded-full text-label-caps font-data-mono">0</span>
</div>
</div>
<!-- Data Container -->
<section class="bg-surface-container-lowest rounded-xl border border-subtle border-outline-variant shadow-sm overflow-hidden flex flex-col">
<!-- Filter Strip -->
<div class="bg-surface-container-low p-container-padding border-b border-outline-variant flex flex-col gap-gutter">
<div class="flex flex-wrap items-center gap-2">
<div class="relative flex-1 min-w-[200px] max-w-xs">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]" data-icon="search">search</span>
<input class="w-full pl-10 pr-3 py-1.5 bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all" placeholder="Search record reference..." type="text">
</div>
<select class="py-1.5 pl-3 pr-8 bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none appearance-none bg-no-repeat bg-[right_0.5rem_center] bg-[length:1.5em_1.5em] transition-all" style="background-image: url(&quot;data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23737781%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpolyline%20points%3D%226%209%2012%2015%2018%209%22%3E%3C%2Fpolyline%3E%3C%2Fsvg%3E&quot;);">
<option value="">Module: All</option>
</select>
<select class="py-1.5 pl-3 pr-8 bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none appearance-none bg-no-repeat bg-[right_0.5rem_center] bg-[length:1.5em_1.5em] transition-all" style="background-image: url(&quot;data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23737781%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpolyline%20points%3D%226%209%2012%2015%2018%209%22%3E%3C%2Fpolyline%3E%3C%2Fsvg%3E&quot;);">
<option value="">Strategy Target: All</option>
</select>
<select class="py-1.5 pl-3 pr-8 bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none appearance-none bg-no-repeat bg-[right_0.5rem_center] bg-[length:1.5em_1.5em] transition-all" style="background-image: url(&quot;data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23737781%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpolyline%20points%3D%226%209%2012%2015%2018%209%22%3E%3C%2Fpolyline%3E%3C%2Fsvg%3E&quot;);">
<option value="">Reference Type: All</option>
<option value="primary">Primary alignment</option>
<option value="supporting">Supporting alignment</option>
<option value="value">Value commitment</option>
</select>
<select class="py-1.5 pl-3 pr-8 bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none appearance-none bg-no-repeat bg-[right_0.5rem_center] bg-[length:1.5em_1.5em] transition-all" style="background-image: url(&quot;data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23737781%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpolyline%20points%3D%226%209%2012%2015%2018%209%22%3E%3C%2Fpolyline%3E%3C%2Fsvg%3E&quot;);">
<option value="">Status: All</option>
</select>
<button type="button" class="text-secondary font-medium text-body-md hover:underline px-2 py-1.5 ml-auto">
                        Clear filters
                    </button>
</div>
</div>
<!-- Data Table -->
<div class="overflow-x-auto w-full scrollbar-hide">
<table data-testid="kt-str-downstream-table" class="w-full text-left border-collapse min-w-[1000px]">
<thead class="bg-surface-container-low border-b border-outline-variant">
<tr>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider w-1/4">Downstream record</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider whitespace-nowrap">Module</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider w-1/4">Strategy reference</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider whitespace-nowrap">Reference type</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider whitespace-nowrap">Current status</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider whitespace-nowrap">Last updated</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider whitespace-nowrap text-right">Action</th>
</tr>
</thead>
<tbody class="divide-y divide-outline-variant bg-surface-container-lowest">
<!-- Row 1 -->
<tr class="hover:bg-surface-container transition-colors group">
<td class="py-4 px-4 align-top">
<div class="flex flex-col">
<span class="font-data-mono text-data-mono text-primary font-bold">DEM-MOH-2027-014</span>
<span class="text-body-md text-on-surface-variant mt-0.5 line-clamp-1">Clinical systems infrastructure refresh</span>
</div>
</td>
<td class="py-4 px-4 align-top text-body-md text-on-surface whitespace-nowrap">Demand</td>
<td class="py-4 px-4 align-top">
<div class="flex flex-col">
<span class="font-data-mono text-data-mono text-on-surface font-medium">MOH-TGT-01</span>
<span class="text-body-md text-on-surface-variant mt-0.5 line-clamp-1">At least 99.9% availability</span>
</div>
</td>
<td class="py-4 px-4 align-top whitespace-nowrap">
<span class="inline-flex items-center px-2.5 py-1 rounded-full bg-primary text-on-primary font-label-caps text-[11px] font-bold">Primary alignment</span>
</td>
<td class="py-4 px-4 align-top whitespace-nowrap">
<div class="inline-flex items-center gap-1.5 text-status-available text-body-md font-medium">
<span class="material-symbols-outlined text-[16px]" style="font-variation-settings: 'FILL' 1">check_circle</span> Approved
                                </div>
</td>
<td class="py-4 px-4 align-top font-data-mono text-data-mono text-on-surface whitespace-nowrap">12 Sep 2027</td>
<td class="py-4 px-4 align-top text-right whitespace-nowrap">
<button type="button" class="text-secondary hover:text-primary transition-colors p-1 rounded hover:bg-surface-container">
<span class="material-symbols-outlined">visibility</span>
</button>
</td>
</tr>
<!-- Row 2 -->
<tr class="hover:bg-surface-container transition-colors group">
<td class="py-4 px-4 align-top">
<div class="flex flex-col">
<span class="font-data-mono text-data-mono text-primary font-bold">BUD-MOH-2027-008</span>
<span class="text-body-md text-on-surface-variant mt-0.5 line-clamp-1">Digital health infrastructure allocation</span>
</div>
</td>
<td class="py-4 px-4 align-top text-body-md text-on-surface whitespace-nowrap">Budget</td>
<td class="py-4 px-4 align-top">
<div class="flex flex-col">
<span class="font-data-mono text-data-mono text-on-surface font-medium">MOH-TGT-01</span>
</div>
</td>
<td class="py-4 px-4 align-top whitespace-nowrap">
<span class="inline-flex items-center px-2.5 py-1 rounded-full bg-secondary-fixed text-on-secondary-fixed-variant font-label-caps text-[11px] font-bold">Supporting alignment</span>
</td>
<td class="py-4 px-4 align-top whitespace-nowrap">
<div class="inline-flex items-center gap-1.5 text-status-available text-body-md font-medium">
<span class="material-symbols-outlined text-[16px]" style="font-variation-settings: 'FILL' 1">check_circle</span> Approved
                                </div>
</td>
<td class="py-4 px-4 align-top font-data-mono text-data-mono text-on-surface whitespace-nowrap">28 Aug 2027</td>
<td class="py-4 px-4 align-top text-right whitespace-nowrap">
<button type="button" class="text-secondary hover:text-primary transition-colors p-1 rounded hover:bg-surface-container">
<span class="material-symbols-outlined">visibility</span>
</button>
</td>
</tr>
<!-- Row 3 -->
<tr class="hover:bg-surface-container transition-colors group">
<td class="py-4 px-4 align-top">
<div class="flex flex-col">
<span class="font-data-mono text-data-mono text-primary font-bold">TND-MOH-ICT-042</span>
<span class="text-body-md text-on-surface-variant mt-0.5 line-clamp-1">Supply and installation of resilient clinical systems infrastructure</span>
</div>
</td>
<td class="py-4 px-4 align-top text-body-md text-on-surface whitespace-nowrap">Tender</td>
<td class="py-4 px-4 align-top">
<div class="flex flex-col">
<span class="font-data-mono text-data-mono text-on-surface font-medium">PVO-RES-01</span>
<span class="text-body-md text-on-surface-variant mt-0.5 line-clamp-1">Improve continuity of critical services</span>
</div>
</td>
<td class="py-4 px-4 align-top whitespace-nowrap">
<span class="inline-flex items-center px-2.5 py-1 rounded-full bg-surface-container-high text-on-surface-variant font-label-caps text-[11px] font-bold">Value commitment</span>
</td>
<td class="py-4 px-4 align-top whitespace-nowrap">
<div class="inline-flex items-center gap-1.5 text-status-reserved text-body-md font-medium">
<span class="material-symbols-outlined text-[16px]">pending</span> Configuration
                                </div>
</td>
<td class="py-4 px-4 align-top font-data-mono text-data-mono text-on-surface whitespace-nowrap">20 Sep 2027</td>
<td class="py-4 px-4 align-top text-right whitespace-nowrap">
<button type="button" class="text-secondary hover:text-primary transition-colors p-1 rounded hover:bg-surface-container">
<span class="material-symbols-outlined">visibility</span>
</button>
</td>
</tr>
<!-- Row 4 -->
<tr class="hover:bg-surface-container transition-colors group">
<td class="py-4 px-4 align-top">
<div class="flex flex-col">
<span class="font-data-mono text-data-mono text-primary font-bold">CTR-MOH-ICT-018</span>
<span class="text-body-md text-on-surface-variant mt-0.5 line-clamp-1">Clinical systems infrastructure support</span>
</div>
</td>
<td class="py-4 px-4 align-top text-body-md text-on-surface whitespace-nowrap">Contract</td>
<td class="py-4 px-4 align-top">
<div class="flex flex-col">
<span class="font-data-mono text-data-mono text-on-surface font-medium">MOH-TGT-01</span>
</div>
</td>
<td class="py-4 px-4 align-top whitespace-nowrap">
<span class="inline-flex items-center px-2.5 py-1 rounded-full bg-secondary-fixed text-on-secondary-fixed-variant font-label-caps text-[11px] font-bold">Supporting alignment</span>
</td>
<td class="py-4 px-4 align-top whitespace-nowrap">
<div class="inline-flex items-center gap-1.5 text-status-committed text-body-md font-medium">
<span class="material-symbols-outlined text-[16px]" style="font-variation-settings: 'FILL' 1">bolt</span> Active
                                </div>
</td>
<td class="py-4 px-4 align-top font-data-mono text-data-mono text-on-surface whitespace-nowrap">15 Oct 2027</td>
<td class="py-4 px-4 align-top text-right whitespace-nowrap">
<button type="button" class="text-secondary hover:text-primary transition-colors p-1 rounded hover:bg-surface-container">
<span class="material-symbols-outlined">visibility</span>
</button>
</td>
</tr>
</tbody>
</table>
</div>
</section>
<!-- Footer Note -->
<div class="flex gap-2 items-start text-on-surface-variant bg-surface-container p-4 rounded-lg border border-outline-variant">
<span class="material-symbols-outlined text-[20px] shrink-0 mt-0.5">info</span>
<p class="text-body-md font-body-md">Historical references remain valid when a strategy version is superseded. Only references requiring remediation appear as issues.</p>
</div>
</div>
</div>`;
};
