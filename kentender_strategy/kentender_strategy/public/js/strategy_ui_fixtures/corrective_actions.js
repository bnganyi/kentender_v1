// Auto-extracted Stitch canvas — strategy_corrective_actions_kentender_catalyst
frappe.provide("kentender_strategy.ui_fixtures");
kentender_strategy.ui_fixtures.corrective_actions = function () {
	return `<div class="kt-str-root" data-testid="kt-str-corrective-actions">
<!-- Page Header Section -->
<div class="px-8 pt-8 pb-6 bg-surface-container-lowest border-b border-subtle">
<!-- Breadcrumb -->
<nav aria-label="Breadcrumb" class="flex text-body-md font-body-md text-on-surface-variant mb-4">
<ol class="inline-flex items-center space-x-1 md:space-x-2">
<li class="inline-flex items-center hover:text-primary cursor-pointer">Portfolio</li>
<li><span class="material-symbols-outlined text-sm mx-1">chevron_right</span></li>
<li class="inline-flex items-center hover:text-primary cursor-pointer data-mono">MOH-SP-0001</li>
<li><span class="material-symbols-outlined text-sm mx-1">chevron_right</span></li>
<li class="inline-flex items-center text-primary font-medium">Measurement</li>
</ol>
</nav>
<div class="flex justify-between items-start gap-4">
<div>
<h1 class="text-headline-lg font-headline-lg text-on-surface mb-2 tracking-tight">Strategy corrective actions</h1>
<p class="text-body-lg font-body-lg text-on-surface-variant">Track and verify actions raised from measured strategic underperformance.</p>
</div>
<button type="button" class="bg-primary text-on-primary hover:bg-primary/90 px-5 py-2.5 rounded-lg text-body-md font-body-md font-medium transition-colors shadow-sm flex items-center gap-2 whitespace-nowrap" data-kt-str-action="create-corrective">
<span class="material-symbols-outlined text-sm">add</span>
                        Create corrective action
                    </button>
</div>
</div>
<!-- Filters Section -->
<div class="px-8 py-4 bg-surface border-b border-subtle">
<div class="flex flex-wrap items-center gap-3">
<div class="relative min-w-[240px] flex-grow max-w-md">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-sm">search</span>
<input class="w-full pl-9 pr-3 py-2 bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none h-10" placeholder="Search target or action..." type="text"/>
</div>
<select class="px-3 py-2 bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none h-10 appearance-none pr-8 relative cursor-pointer min-w-[120px]">
<option value="">Owner (All)</option>
<option>Head, ICT Infrastructure</option>
<option>Infrastructure Programme Lead</option>
<option>Facilities Director</option>
</select>
<select class="px-3 py-2 bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none h-10 appearance-none pr-8 cursor-pointer min-w-[140px]">
<option value="">Due status (All)</option>
<option>Due in &lt; 14 days</option>
<option>Overdue</option>
<option>On track</option>
</select>
<select class="px-3 py-2 bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none h-10 appearance-none pr-8 cursor-pointer min-w-[160px]">
<option value="">Action status (All)</option>
<option>Open</option>
<option>In progress</option>
<option>Submitted for verification</option>
</select>
<button type="button" class="text-primary hover:text-primary/80 text-body-md font-body-md font-medium px-2 py-2 ml-auto">Clear filters</button>
</div>
</div>
<!-- Bento/Grid Layout for Table + Panel -->
<div class="flex flex-1 overflow-hidden p-8 gap-6 max-w-[1600px] mx-auto w-full">
<!-- Main Table Section (Left Side, flexes to fill space) -->
<div class="flex-1 bg-surface-container-lowest border border-[#E2E8F0] rounded-xl flex flex-col overflow-hidden shadow-sm">
<div class="overflow-x-auto overflow-y-auto flex-1">
<table class="w-full text-left border-collapse">
<thead class="bg-surface-container-low text-label-caps font-label-caps text-on-surface-variant sticky top-0 z-10 border-b border-[#E2E8F0]">
<tr>
<th class="px-4 py-3 font-semibold w-48">Target &amp; Measurement</th>
<th class="px-4 py-3 font-semibold min-w-[200px]">Corrective action</th>
<th class="px-4 py-3 font-semibold">Owner</th>
<th class="px-4 py-3 font-semibold w-32">Due date</th>
<th class="px-4 py-3 font-semibold w-40">Status</th>
<th class="px-4 py-3 font-semibold w-48">Due state</th>
<th class="px-4 py-3 font-semibold text-right w-24">Action</th>
</tr>
</thead>
<tbody class="text-body-md font-body-md text-on-surface divide-y divide-[#E2E8F0]">
<!-- Active Row -->
<tr class="bg-primary-fixed/30 hover:bg-primary-fixed/40 transition-colors cursor-pointer border-l-2 border-l-primary group">
<td class="px-4 py-4 align-top">
<div class="font-data-mono text-primary font-medium">MOH-TGT-0001</div>
<div class="text-sm text-on-surface-variant mt-1">September 2027</div>
</td>
<td class="px-4 py-4 align-top font-medium pr-6">
                                        Resolve storage-controller instability and confirm service stability
                                    </td>
<td class="px-4 py-4 align-top text-on-surface-variant">
                                        Head, ICT Infrastructure
                                    </td>
<td class="px-4 py-4 align-top font-data-mono text-sm text-on-surface-variant">
                                        31 Oct 2027
                                    </td>
<td class="px-4 py-4 align-top">
<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-secondary-fixed text-on-secondary-fixed">
<span class="w-1.5 h-1.5 rounded-full bg-primary mr-1.5"></span>
                                            In progress
                                        </span>
</td>
<td class="px-4 py-4 align-top">
<div class="flex items-center gap-1.5 text-status-reserved font-medium text-sm">
<span class="material-symbols-outlined text-[16px]">schedule</span>
                                            Due in 8 days
                                        </div>
</td>
<td class="px-4 py-4 align-top text-right">
<button type="button" class="text-primary font-semibold hover:underline decoration-2 underline-offset-4 text-sm">Continue</button>
</td>
</tr>
<!-- Row 2 -->
<tr class="hover:bg-surface-container transition-colors cursor-pointer border-l-2 border-l-transparent">
<td class="px-4 py-4 align-top">
<div class="font-data-mono text-on-surface font-medium">MOH-TGT-04</div>
<div class="text-sm text-on-surface-variant mt-1">Q1 2027/28</div>
</td>
<td class="px-4 py-4 align-top pr-6">
                                        Validate regional network redundancy plan
                                    </td>
<td class="px-4 py-4 align-top text-on-surface-variant">
                                        Infrastructure Programme Lead
                                    </td>
<td class="px-4 py-4 align-top font-data-mono text-sm text-on-surface-variant">
                                        15 Oct 2027
                                    </td>
<td class="px-4 py-4 align-top">
<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-tertiary-fixed text-on-tertiary-fixed">
<span class="w-1.5 h-1.5 rounded-full bg-tertiary mr-1.5"></span>
                                            Submitted for verification
                                        </span>
</td>
<td class="px-4 py-4 align-top">
<div class="flex items-center gap-1.5 text-on-surface-variant text-sm">
<span class="material-symbols-outlined text-[16px]">hourglass_empty</span>
                                            Awaiting verification
                                        </div>
</td>
<td class="px-4 py-4 align-top text-right">
<button type="button" class="text-secondary font-semibold hover:underline decoration-2 underline-offset-4 text-sm">Review</button>
</td>
</tr>
<!-- Row 3 -->
<tr class="hover:bg-surface-container transition-colors cursor-pointer border-l-2 border-l-transparent">
<td class="px-4 py-4 align-top">
<div class="font-data-mono text-on-surface font-medium">MOH-TGT-05</div>
<div class="text-sm text-on-surface-variant mt-1">August 2027</div>
</td>
<td class="px-4 py-4 align-top pr-6">
                                        Complete delayed energy baseline assessment
                                    </td>
<td class="px-4 py-4 align-top text-on-surface-variant">
                                        Facilities Director
                                    </td>
<td class="px-4 py-4 align-top font-data-mono text-sm text-status-exhausted font-medium">
                                        30 Sep 2027
                                    </td>
<td class="px-4 py-4 align-top">
<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-surface-variant text-on-surface-variant">
<span class="w-1.5 h-1.5 rounded-full bg-outline mr-1.5"></span>
                                            Open
                                        </span>
</td>
<td class="px-4 py-4 align-top">
<div class="flex items-center gap-1.5 text-status-exhausted font-medium text-sm bg-error-container/30 px-2 py-0.5 rounded inline-flex">
<span class="material-symbols-outlined text-[16px]">error</span>
                                            Overdue
                                        </div>
</td>
<td class="px-4 py-4 align-top text-right">
<button type="button" class="px-3 py-1.5 border border-outline-variant rounded-md text-sm font-medium hover:bg-surface-container-highest transition-colors">Start</button>
</td>
</tr>
</tbody>
</table>
</div>
</div>
<!-- Detail Panel (Right Side, Fixed Width) -->
<aside class="w-[420px] bg-surface-container-lowest border border-[#E2E8F0] rounded-xl flex flex-col overflow-hidden shadow-sm flex-shrink-0">
<!-- Panel Header -->
<div class="p-5 border-b border-[#E2E8F0] bg-surface-container-low flex justify-between items-start">
<div>
<div class="flex items-center gap-3 mb-1">
<span class="font-data-mono font-medium text-primary text-sm">MOH-TGT-0001</span>
<span class="text-on-surface-variant text-sm">/ September 2027</span>
</div>
<h3 class="text-headline-sm font-headline-sm mt-2 line-clamp-2 pr-2">Resolve storage-controller instability and confirm service stability</h3>
</div>
<div class="flex-shrink-0">
<span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-secondary-fixed text-on-secondary-fixed border border-secondary-fixed-dim">
                                In progress
                            </span>
</div>
</div>
<!-- Panel Scrollable Content -->
<div class="flex-1 overflow-y-auto p-6 space-y-6">
<!-- Details Grid -->
<div class="grid grid-cols-2 gap-y-5 gap-x-4">
<div class="col-span-2">
<span class="block text-label-caps font-label-caps text-outline mb-1">Expected Result</span>
<p class="text-body-md font-body-md text-on-surface">System uptime restored to &gt;=99.9% availability.</p>
</div>
<div>
<span class="block text-label-caps font-label-caps text-outline mb-1">Owner</span>
<div class="flex items-center gap-2 text-body-md font-body-md">
<div class="w-6 h-6 rounded-full bg-tertiary-container text-on-tertiary flex items-center justify-center text-xs font-medium">HI</div>
<span class="truncate">Head, ICT Infrastructure</span>
</div>
</div>
<div>
<span class="block text-label-caps font-label-caps text-outline mb-1">Due Date</span>
<div class="flex items-center gap-2 text-body-md font-body-md font-data-mono text-status-reserved font-medium">
<span class="material-symbols-outlined text-[16px]">event</span>
                                    31 Oct 2027
                                </div>
</div>
</div>
<hr class="border-[#E2E8F0]"/>
<!-- Evidence Section -->
<div>
<h4 class="text-body-md font-headline-md font-semibold mb-3 flex items-center gap-2">
<span class="material-symbols-outlined text-[20px] text-primary">description</span>
                                Completion Evidence
                            </h4>
<div class="border border-dashed border-outline-variant rounded-lg p-6 bg-surface-container-low text-center flex flex-col items-center justify-center cursor-pointer hover:bg-surface-container transition-colors group">
<div class="w-10 h-10 rounded-full bg-surface-container-highest flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
<span class="material-symbols-outlined text-outline">upload_file</span>
</div>
<p class="text-body-md font-body-md font-medium text-on-surface mb-1">Upload verifying documentation</p>
<p class="text-sm text-on-surface-variant">PDF, DOCX, or XLSX (Max 10MB)</p>
</div>
</div>
<hr class="border-[#E2E8F0]"/>
<!-- Timeline -->
<div>
<h4 class="text-body-md font-headline-md font-semibold mb-4">Status Timeline</h4>
<div class="relative border-l-2 border-surface-variant ml-3 space-y-6 pb-2">
<div class="relative pl-6">
<div class="absolute w-3 h-3 bg-secondary rounded-full -left-[7px] top-1.5 ring-4 ring-surface-container-lowest"></div>
<div class="text-sm font-medium text-on-surface">In progress</div>
<div class="text-xs text-on-surface-variant mt-0.5 font-data-mono">24 Oct 2027, 09:41 AM</div>
</div>
<div class="relative pl-6">
<div class="absolute w-3 h-3 bg-outline-variant rounded-full -left-[7px] top-1.5 ring-4 ring-surface-container-lowest"></div>
<div class="text-sm text-on-surface-variant">Open</div>
<div class="text-xs text-outline mt-0.5 font-data-mono">18 Oct 2027, 14:22 PM</div>
</div>
</div>
</div>
</div>
<!-- Panel Footer Action -->
<div class="p-5 border-t border-[#E2E8F0] bg-surface-container-lowest mt-auto">
<button type="button" class="w-full bg-primary text-on-primary hover:bg-primary/90 py-2.5 rounded-lg text-body-md font-body-md font-medium transition-colors shadow-sm flex items-center justify-center gap-2">
                            Submit for verification
                            <span class="material-symbols-outlined text-sm">arrow_forward</span>
</button>
</div>
</aside>
</div>
</div>
</div>`;
};
