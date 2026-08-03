// Auto-extracted Stitch canvas — public_value_objective_catalogue_separated_pillar_and_source
frappe.provide("kentender_strategy.ui_fixtures");
kentender_strategy.ui_fixtures.pvo_catalogue = function () {
	return `<div class="kt-str-root" data-testid="kt-str-pvo-catalogue">
<div class="max-w-7xl mx-auto space-y-section-gap">
<div class="flex flex-col md:flex-row md:items-start justify-between gap-4">
<div class="max-w-3xl">
<h1 class="font-headline-lg text-headline-lg text-on-surface mb-2">Public Value Objective Catalogue</h1>
<p class="font-body-lg text-body-lg text-on-surface-variant">Maintain approved objectives that strategic plans may adopt and downstream value cases may consider.</p>
</div>
<button type="button" class="bg-primary text-on-primary px-5 py-2.5 rounded-lg font-body-md font-medium hover:bg-primary/90 transition-colors flex items-center gap-2 shrink-0" data-kt-str-action="create-pvo">
<span class="material-symbols-outlined text-[20px]">add_circle</span>
                        Create objective
                    </button>
</div>
<div class="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-sm">
<div class="p-4 border-b border-outline-variant bg-surface-container-low/50 rounded-t-xl flex flex-wrap gap-3 items-center">
<div class="relative min-w-[240px] flex-1 md:flex-none">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[18px]">search</span>
<input class="w-full h-9 pl-9 pr-3 bg-surface-container-lowest border border-outline-variant rounded-md font-body-md text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none" placeholder="Search by code or title..." type="text">
</div>
<select class="h-9 px-3 py-0 bg-surface-container-lowest border border-outline-variant rounded-md font-body-md text-sm text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none cursor-pointer">
<option value="">Pillar</option>
<option value="strategic">Strategic Outcomes</option>
<option value="economy">Economy</option>
</select>
<select class="h-9 px-3 py-0 bg-surface-container-lowest border border-outline-variant rounded-md font-body-md text-sm text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none cursor-pointer">
<option value="">Source type</option>
<option value="strategy">Entity Strategy</option>
<option value="policy">Policy</option>
</select>
<select class="h-9 px-3 py-0 bg-surface-container-lowest border border-outline-variant rounded-md font-body-md text-sm text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none cursor-pointer">
<option value="">Applicability</option>
</select>
<select class="h-9 px-3 py-0 bg-surface-container-lowest border border-outline-variant rounded-md font-body-md text-sm text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none cursor-pointer">
<option value="">Status</option>
<option value="active">Active</option>
<option value="submitted">Submitted</option>
</select>
<button type="button" class="h-9 px-4 text-on-surface-variant hover:text-primary hover:bg-surface-container rounded-md font-body-md text-sm transition-colors ml-auto">
                            Clear filters
                        </button>
</div>
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse">
<thead>
<tr class="border-b border-outline-variant bg-surface-container-lowest">
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant w-1/3">Objective</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant w-48">Pillar</th><th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant">Source</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant">Applicability</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant">
<div class="flex items-center gap-1 group relative">
                                            Default Guidance
                                            
<span class="material-symbols-outlined text-[16px] text-outline cursor-pointer hover:text-primary transition-colors">info</span></div>
</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant w-24">Version</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant w-32">Status</th>
<th class="py-3 px-4 font-label-caps text-label-caps text-on-surface-variant text-right w-24">Action</th>
</tr>
</thead>
<tbody class="divide-y divide-outline-variant bg-surface-container-lowest">
<tr class="hover:bg-surface-container/50 transition-colors group">
<td class="py-3 px-4">
<div class="flex flex-col">
<span class="font-data-mono text-data-mono text-primary font-bold">PVO-EFT-01</span>
<span class="font-body-md text-on-surface font-medium mt-1">Improve availability of critical health services</span>
</div>
</td>
<td class="py-3 px-4"><span class="font-body-md text-[13px] text-on-surface">Strategic and service outcomes</span></td><td class="py-3 px-4 font-body-md text-[13px] text-on-surface-variant">Entity Strategy</td>
<td class="py-3 px-4 font-body-md text-[13px] text-on-surface">Demand-selected</td>
<td class="py-3 px-4 font-body-md text-[13px] text-on-surface-variant">Strategic outcome</td>
<td class="py-3 px-4 font-data-mono text-data-mono text-on-surface-variant">v1</td>
<td class="py-3 px-4">
<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-status-available/10 text-status-available border border-status-available/20 font-body-md text-xs font-medium">
<span class="w-1.5 h-1.5 rounded-full bg-status-available"></span>
                                            Active
                                        </span>
</td>
<td class="py-3 px-4 text-right">
<button type="button" class="text-primary hover:text-primary-container font-body-md text-sm font-medium transition-colors">View</button>
</td>
</tr>
<tr class="hover:bg-surface-container/50 transition-colors group">
<td class="py-3 px-4">
<div class="flex flex-col">
<span class="font-data-mono text-data-mono text-primary font-bold">PVO-ECO-01</span>
<span class="font-body-md text-on-surface font-medium mt-1">Reduce whole-life infrastructure cost</span>
</div>
</td>
<td class="py-3 px-4"><span class="font-body-md text-[13px] text-on-surface">Economy and whole-life value</span></td><td class="py-3 px-4 font-body-md text-[13px] text-on-surface-variant">Management Objective</td>
<td class="py-3 px-4 font-body-md text-[13px] text-on-surface">Category-triggered</td>
<td class="py-3 px-4 font-body-md text-[13px] text-on-surface-variant">Demand gate</td>
<td class="py-3 px-4 font-data-mono text-data-mono text-on-surface-variant">v1</td>
<td class="py-3 px-4">
<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-status-available/10 text-status-available border border-status-available/20 font-body-md text-xs font-medium">
<span class="w-1.5 h-1.5 rounded-full bg-status-available"></span>
                                            Active
                                        </span>
</td>
<td class="py-3 px-4 text-right">
<button type="button" class="text-primary hover:text-primary-container font-body-md text-sm font-medium transition-colors">View</button>
</td>
</tr>
<tr class="hover:bg-surface-container/50 transition-colors group">
<td class="py-3 px-4">
<div class="flex flex-col">
<span class="font-data-mono text-data-mono text-primary font-bold">PVO-RES-01</span>
<span class="font-body-md text-on-surface font-medium mt-1">Improve continuity of critical services</span>
</div>
</td>
<td class="py-3 px-4"><span class="font-body-md text-[13px] text-on-surface">Contract performance and resilience</span></td><td class="py-3 px-4 font-body-md text-[13px] text-on-surface-variant">Entity Strategy</td>
<td class="py-3 px-4 font-body-md text-[13px] text-on-surface">Procurement-type-triggered</td>
<td class="py-3 px-4 font-body-md text-[13px] text-on-surface-variant">Contract obligation or KPI</td>
<td class="py-3 px-4 font-data-mono text-data-mono text-on-surface-variant">v1</td>
<td class="py-3 px-4">
<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-status-available/10 text-status-available border border-status-available/20 font-body-md text-xs font-medium">
<span class="w-1.5 h-1.5 rounded-full bg-status-available"></span>
                                            Active
                                        </span>
</td>
<td class="py-3 px-4 text-right">
<button type="button" class="text-primary hover:text-primary-container font-body-md text-sm font-medium transition-colors">View</button>
</td>
</tr>
<tr class="hover:bg-surface-container/50 transition-colors group">
<td class="py-3 px-4">
<div class="flex flex-col">
<span class="font-data-mono text-data-mono text-primary font-bold">PVO-SUS-02</span>
<span class="font-body-md text-on-surface font-medium mt-1">Ensure compliant handling of replaced ICT equipment</span>
</div>
</td>
<td class="py-3 px-4"><span class="font-body-md text-[13px] text-on-surface">Sustainability and asset stewardship</span></td><td class="py-3 px-4 font-body-md text-[13px] text-on-surface-variant">Act</td>
<td class="py-3 px-4 font-body-md text-[13px] text-on-surface">Asset-triggered</td>
<td class="py-3 px-4 font-body-md text-[13px] text-on-surface-variant">Asset or disposal control</td>
<td class="py-3 px-4 font-data-mono text-data-mono text-on-surface-variant">v1</td>
<td class="py-3 px-4">
<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-status-available/10 text-status-available border border-status-available/20 font-body-md text-xs font-medium">
<span class="w-1.5 h-1.5 rounded-full bg-status-available"></span>
                                            Active
                                        </span>
</td>
<td class="py-3 px-4 text-right">
<button type="button" class="text-primary hover:text-primary-container font-body-md text-sm font-medium transition-colors">View</button>
</td>
</tr>
<tr class="hover:bg-surface-container/50 transition-colors group">
<td class="py-3 px-4">
<div class="flex flex-col">
<span class="font-data-mono text-data-mono text-primary font-bold">PVO-INT-01</span>
<span class="font-body-md text-on-surface font-medium mt-1">Minimise uncontrolled contract changes</span>
</div>
</td>
<td class="py-3 px-4"><span class="font-body-md text-[13px] text-on-surface">Integrity and accountability</span></td><td class="py-3 px-4 font-body-md text-[13px] text-on-surface-variant">Policy</td>
<td class="py-3 px-4 font-body-md text-[13px] text-on-surface">Universal consideration</td>
<td class="py-3 px-4 font-body-md text-[13px] text-on-surface-variant">Reporting only</td>
<td class="py-3 px-4 font-data-mono text-data-mono text-on-surface-variant">v1</td>
<td class="py-3 px-4">
<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-status-reserved/10 text-status-reserved border border-status-reserved/20 font-body-md text-xs font-medium">
<span class="w-1.5 h-1.5 rounded-full bg-status-reserved"></span>
                                            Submitted
                                        </span>
</td>
<td class="py-3 px-4 text-right">
<button type="button" class="text-secondary hover:text-secondary-container font-body-md text-sm font-medium transition-colors">Review</button>
</td>
</tr>
</tbody>
</table>
</div>
<div class="p-4 border-t border-outline-variant bg-surface-container-lowest flex items-center justify-between text-sm text-on-surface-variant rounded-b-xl">
<span class="">Showing 5 of 42 objectives</span>
<div class="flex items-center gap-2">
<button type="button" class="w-8 h-8 flex items-center justify-center rounded border border-outline-variant hover:bg-surface-container transition-colors disabled:opacity-50"><span class="material-symbols-outlined text-[18px]">chevron_left</span></button>
<span class="px-2">Page 1 of 9</span>
<button type="button" class="w-8 h-8 flex items-center justify-center rounded border border-outline-variant hover:bg-surface-container transition-colors"><span class="material-symbols-outlined text-[18px]">chevron_right</span></button>
</div>
</div>
</div>
<div class="mt-4 p-4 bg-surface-container-low rounded-lg border border-outline-variant flex items-start gap-3">
<span class="material-symbols-outlined text-outline mt-0.5">info</span>
<p class="font-body-md text-sm text-on-surface-variant leading-relaxed">Guidance suggests where an objective may be treated. Downstream approval is still required.</p>
</div>
</div>
</div>
</div>`;
};
