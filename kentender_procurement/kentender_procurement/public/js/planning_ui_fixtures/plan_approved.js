// PLN-UI-09 — literal Stitch <main> from docs/mvp-1/04_planning/ui_design/PLN-UI-09.html
// Fake top/side nav + in-canvas breadcrumbs discarded (Desk chrome); kt-stitch-canvas + testids/bind hooks only.
// Legal identity wraps (no ellipsis clipping). Money is live-bound with thousands separators.
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_plan_approved = function () {
	return `<div class="kt-pln-root kt-stitch-canvas" data-testid="kt-pln-ui09-root">
<div class="flex-1 overflow-y-auto p-section-gap">
<div class="max-w-7xl mx-auto space-y-section-gap">
<div class="flex flex-col md:flex-row md:items-start justify-between gap-4" data-testid="kt-pln-ui09-header">
<div>
<h1 class="font-headline-lg text-headline-lg text-on-surface mb-stack-xs" data-kt-pln-ui09-title>Approved procurement plan</h1>
<div class="flex items-center gap-3 font-body-sm text-body-sm text-on-surface-variant" data-kt-pln-ui09-secondary>
<span class="flex items-center gap-1"><span class="material-symbols-outlined text-[18px] text-status-available" data-icon="check_circle">check_circle</span> Open Plan</span>
<span class="">·</span>
<span class="font-bold" data-kt-pln-ui09-version>Approved Version 1</span>
<span class="">·</span>
<span class="">Approved baseline is read-only</span>
</div>
<p class="font-body-sm text-body-sm text-tertiary mt-stack-sm bg-surface-container p-3 rounded border border-subtle flex items-start gap-2 max-w-2xl">
<span class="material-symbols-outlined text-[18px] text-primary shrink-0 mt-0.5" data-icon="info">info</span>
<span class="">Add an Approved Demand as a new Plan Item. The current Approved Version remains active while the update is reviewed.</span>
</p>
</div>
<div class="flex flex-col gap-2 shrink-0" data-kt-pln-ui09-actions>
<button type="button" class="bg-primary text-on-primary font-label-caps text-label-caps px-4 py-2.5 rounded shadow-sm hover:bg-on-primary-fixed-variant transition-colors flex items-center justify-center gap-2" data-testid="kt-pln-ui09-add-item" data-kt-pln-action="add-demand">
<span class="material-symbols-outlined" data-icon="add_circle">add_circle</span>
                            Add Plan Item
                        </button>
<button type="button" class="bg-surface text-primary border border-subtle font-label-caps text-label-caps px-4 py-2.5 rounded hover:bg-surface-container-low transition-colors flex items-center justify-center gap-2" data-testid="kt-pln-ui09-export" data-kt-pln-action="export-approved">
<span class="material-symbols-outlined" data-icon="download">download</span>
                            Export approved plan
                        </button>
</div>
</div>
<div class="bg-tertiary-fixed border border-tertiary-fixed-dim rounded p-4 flex flex-col sm:flex-row items-center justify-between gap-4 hidden" data-testid="kt-pln-ui09-successor-notice" hidden style="display:none">
<div class="flex items-center gap-3 text-on-tertiary-fixed">
<span class="material-symbols-outlined text-primary" data-icon="edit_note">edit_note</span>
<p class="font-body-sm text-body-sm" data-kt-pln-ui09-successor-copy>
<span class="font-bold">Draft Version 2 in progress</span> · 1 new Plan Item · Approved Version 1 remains operational.
                        </p>
</div>
<div class="flex gap-2">
<button type="button" class="bg-surface text-primary border border-primary-fixed-dim font-label-caps text-label-caps px-3 py-1.5 rounded hover:bg-primary-fixed transition-colors" data-kt-pln-action="continue-update" data-testid="kt-pln-ui09-continue">
                            Continue update
                        </button>
<button type="button" class="text-primary font-label-caps text-label-caps px-3 py-1.5 rounded hover:bg-surface-container transition-colors" data-kt-pln-action="view-changes" data-testid="kt-pln-ui09-view-changes">
                            View changes
                        </button>
</div>
</div>
<div class="grid grid-cols-2 md:grid-cols-5 gap-4" data-testid="kt-pln-ui09-summary">
<div class="bg-surface border border-subtle rounded p-4 flex flex-col justify-center border-l-4 border-l-primary">
<span class="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Approved plan value</span>
<span class="font-data-lg text-data-lg text-on-surface" data-kt-pln-ui09-total>KES 0.00</span>
</div>
<div class="bg-surface border border-subtle rounded p-4 flex flex-col justify-center">
<span class="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Plan Items</span>
<span class="font-data-lg text-data-lg text-on-surface" data-kt-pln-ui09-items>0</span>
</div>
<div class="bg-surface border border-subtle rounded p-4 flex flex-col justify-center">
<span class="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Tender take-up</span>
<span class="font-data-lg text-data-lg text-on-surface" data-kt-pln-ui09-takeup>0 of 0</span>
</div>
<div class="bg-surface border border-subtle rounded p-4 flex flex-col justify-center hidden" data-kt-pln-ui09-on-schedule-kpi hidden>
<span class="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">On schedule</span>
<span class="font-data-lg text-data-lg text-on-surface" data-kt-pln-ui09-on-schedule></span>
</div>
<div class="bg-surface border border-subtle rounded p-4 flex flex-col justify-center">
<span class="font-label-caps text-label-caps text-on-surface-variant mb-1 uppercase">Publication</span>
<span class="font-body-lg text-body-lg text-on-surface font-semibold flex items-center gap-2" data-kt-pln-ui09-pub-kpi>
<span class="w-2.5 h-2.5 rounded-full bg-outline"></span> Not published
                        </span>
</div>
</div>
<div class="bg-surface border border-subtle rounded p-3 flex flex-wrap items-center gap-4" data-testid="kt-pln-ui09-filters">
<div class="flex items-center gap-2">
<span class="material-symbols-outlined text-on-surface-variant text-[20px]" data-icon="filter_list">filter_list</span>
<span class="font-label-caps text-label-caps text-on-surface-variant">Filter by:</span>
</div>
<div class="relative">
<select class="appearance-none bg-surface-container-low border-subtle rounded py-1.5 pl-3 pr-10 font-body-sm text-body-sm text-on-surface focus:border-secondary focus:ring-1 focus:ring-secondary" data-kt-pln-ui09-filter="period" aria-label="Reporting period">
<option value="">FY</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none" aria-hidden="true">expand_more</span>
</div>
<div class="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-1 bg-surface-container px-3 py-1.5 rounded border border-surface-variant cursor-not-allowed opacity-70" data-kt-pln-ui09-as-at>
<span class="material-symbols-outlined text-[16px]" data-icon="calendar_today">calendar_today</span>
                        As at:
                    </div>
<div class="relative">
<select class="appearance-none bg-surface-container-low border-subtle rounded py-1.5 pl-3 pr-10 font-body-sm text-body-sm text-on-surface focus:border-secondary focus:ring-1 focus:ring-secondary" data-kt-pln-ui09-filter="ou" aria-label="Organisation Unit">
<option value="">All permitted units</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none" aria-hidden="true">expand_more</span>
</div>
<div class="relative">
<select class="appearance-none bg-surface-container-low border-subtle rounded py-1.5 pl-3 pr-10 font-body-sm text-body-sm text-on-surface focus:border-secondary focus:ring-1 focus:ring-secondary" data-kt-pln-ui09-filter="status" aria-label="Take-up status">
<option value="">All statuses</option>
<option value="Not taken up">Not taken up</option>
<option value="Tender active">Tender active</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none" aria-hidden="true">expand_more</span>
</div>
</div>
<section class="bg-surface border border-subtle rounded overflow-hidden" data-testid="kt-pln-ui09-implementation-table">
<div class="px-5 py-4 border-b border-subtle bg-surface-container-lowest flex justify-between items-center">
<h3 class="font-headline-sm text-headline-sm text-on-surface">Plan implementation</h3>
</div>
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse">
<thead>
<tr class="border-b border-subtle bg-surface-container-lowest">
<th class="px-5 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase whitespace-nowrap">Requirement</th>
<th class="px-5 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase whitespace-nowrap">Organisation Unit</th>
<th class="px-5 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase whitespace-nowrap text-right">Planned value</th>
<th class="px-5 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase whitespace-nowrap">Tender take-up</th>
<th class="px-5 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase whitespace-nowrap">Planned milestone</th>
<th class="px-5 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase whitespace-nowrap hidden" data-kt-pln-ui09-progress-col hidden>Actual progress</th>
<th class="px-5 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase whitespace-nowrap text-center hidden" data-kt-pln-ui09-variance-col hidden>Variance</th>
<th class="px-5 py-3 font-label-caps text-label-caps text-on-surface-variant uppercase whitespace-nowrap text-right">Action</th>
</tr>
</thead>
<tbody class="divide-y divide-subtle" data-kt-pln-ui09-items-body></tbody>
</table>
</div>
</section>
<section class="bg-surface border border-subtle rounded p-5 relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-6" data-testid="kt-pln-ui09-publication">
<div class="absolute right-0 top-0 w-64 h-full bg-gradient-to-l from-surface-container-highest/30 to-transparent pointer-events-none"></div>
<div class="flex items-start gap-4 z-10">
<div class="w-12 h-12 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center shrink-0">
<span class="material-symbols-outlined text-[24px]" data-icon="public">public</span>
</div>
<div>
<h3 class="font-headline-sm text-headline-sm text-on-surface mb-1">Publication Evidence</h3>
<div class="flex flex-wrap items-center gap-x-4 gap-y-2 font-body-sm text-body-sm text-on-surface-variant" data-kt-pln-ui09-pub-meta>
<span class="">Destination: <strong class="text-on-surface" data-kt-pln-ui09-pub-dest>Tender Portal</strong></span>
<span class="hidden sm:inline">·</span>
<span class="flex items-center gap-1">Status: <span class="w-2 h-2 rounded-full bg-outline" data-kt-pln-ui09-pub-dot></span> <strong class="text-on-surface" data-kt-pln-ui09-pub-status>Not published</strong></span>
<span class="hidden sm:inline" data-kt-pln-ui09-pub-date-sep>·</span>
<span class="" data-kt-pln-ui09-pub-date-wrap>Date: <strong class="text-on-surface" data-kt-pln-ui09-pub-date>—</strong></span>
</div>
</div>
</div>
<a class="z-10 inline-flex items-center justify-center gap-2 px-4 py-2 bg-surface-container border border-subtle rounded font-label-caps text-label-caps text-on-surface hover:bg-surface-container-high transition-colors shrink-0 hidden" href="#" data-kt-pln-ui09-pub-link hidden>
<span class="material-symbols-outlined text-[18px]" data-icon="open_in_new">open_in_new</span>
                        View publication evidence
                    </a>
</section>
</div>
</div>
</div>`;
};
