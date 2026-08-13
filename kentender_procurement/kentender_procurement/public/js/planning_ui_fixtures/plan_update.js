// PLN-UI-10 — literal Stitch <main> from docs/mvp-1/04_planning/ui_design/PLN-UI-10.html
// Fake top nav + in-canvas breadcrumbs discarded (Desk chrome); kt-stitch-canvas + testids/bind hooks only.
// Legal identity wraps (no ellipsis clipping). Money is live-bound with thousands separators.
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_plan_update = function () {
	return `<div class="kt-pln-root kt-stitch-canvas" data-testid="kt-pln-ui10-root">
<div class="flex-1 flex flex-col items-center w-full px-container-padding py-section-gap">
<div class="w-full max-w-[1200px] flex flex-col gap-section-gap">
<header class="flex flex-col gap-stack-sm" data-testid="kt-pln-ui10-header">
<div class="flex flex-col md:flex-row md:items-start justify-between gap-4 mt-2">
<div class="flex flex-col gap-stack-xs">
<div class="flex items-center gap-4">
<h1 class="font-headline-lg text-headline-lg text-on-background m-0">Plan update</h1>
<div class="flex gap-2">
<span class="px-2.5 py-0.5 rounded-full bg-surface-container-high text-on-surface-variant font-label-caps text-label-caps inline-flex items-center" data-kt-pln-ui10-status-chip>Draft</span>
<span class="px-2.5 py-0.5 rounded-full bg-status-reserved/10 text-status-reserved font-label-caps text-label-caps inline-flex items-center" data-kt-pln-ui10-attention-chip>Needs attention</span>
</div>
</div>
<p class="font-body-lg text-body-lg text-on-surface-variant m-0" data-kt-pln-ui10-subtitle>Annual Procurement Plan</p>
</div>
<button type="button" class="px-4 py-2 border border-border-subtle rounded text-primary font-body-md text-body-md font-medium hover:bg-surface-container-low transition-colors self-start whitespace-nowrap" data-testid="kt-pln-ui10-validate" data-kt-pln-action="validate">
                        Run validation
                    </button>
</div>
</header>
<div class="bg-primary-fixed/30 border border-primary-fixed-dim rounded-lg p-4 flex items-start gap-3" data-testid="kt-pln-ui10-banner">
<span class="material-symbols-outlined text-primary mt-0.5 filled" data-icon="info">info</span>
<p class="font-body-md text-body-md text-on-background m-0" data-kt-pln-ui10-banner-copy>Approved Version 1 remains active until this update is approved.</p>
</div>
<div class="bg-surface-container-lowest border border-border-subtle rounded-lg p-6 flex flex-col md:flex-row gap-6 md:gap-12" data-testid="kt-pln-ui10-summary">
<div class="flex flex-col gap-1">
<span class="font-label-caps text-label-caps text-on-surface-variant" data-kt-pln-ui10-approved-label>Approved Version 1</span>
<span class="font-data-md text-data-md text-on-background" data-kt-pln-ui10-approved-total>KES 0.00</span>
</div>
<div class="hidden md:block w-px bg-border-subtle self-stretch"></div>
<div class="flex flex-col gap-1">
<span class="font-label-caps text-label-caps text-on-surface-variant" data-kt-pln-ui10-draft-label>Draft Version 2</span>
<span class="font-data-md text-data-md text-on-background" data-kt-pln-ui10-draft-total>KES 0.00</span>
</div>
<div class="hidden md:block w-px bg-border-subtle self-stretch"></div>
<div class="flex flex-col gap-1">
<span class="font-label-caps text-label-caps text-on-surface-variant">Change</span>
<span class="font-data-md text-data-md text-status-available flex items-center gap-1" data-kt-pln-ui10-change>
<span class="material-symbols-outlined text-[16px]" data-icon="arrow_upward">arrow_upward</span>
<span data-kt-pln-ui10-change-copy>KES 0.00 added</span>
</span>
</div>
<div class="hidden md:block w-px bg-border-subtle self-stretch"></div>
<div class="flex flex-col gap-1">
<span class="font-label-caps text-label-caps text-on-surface-variant">Plan Items</span>
<div class="flex items-center gap-4 text-body-sm font-body-sm">
<span class="text-on-background font-medium" data-kt-pln-ui10-changed-count>0 Changed</span>
<span class="text-on-surface-variant" data-kt-pln-ui10-unchanged-count>0 Unchanged</span>
</div>
</div>
</div>
<section class="bg-surface-container-lowest border border-border-subtle rounded-lg flex flex-col" data-testid="kt-pln-ui10-context">
<div class="px-6 py-4 border-b border-border-subtle">
<h2 class="font-headline-sm text-headline-sm text-on-background m-0">Update context</h2>
</div>
<div class="p-6 flex flex-col gap-6">
<div class="flex flex-col gap-2">
<label class="font-label-caps text-label-caps text-on-surface-variant">Change Type</label>
<div class="px-3 py-2 bg-surface-container-low rounded border border-border-subtle text-on-background font-body-md text-body-md w-max" data-kt-pln-ui10-change-type>
                            Additional approved need
                        </div>
</div>
<div class="flex flex-col gap-2 max-w-3xl">
<label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-ui10-reason">Reason for adding after approval</label>
<textarea class="w-full px-3 py-2 border border-border-subtle rounded bg-surface-container-lowest text-on-background font-body-md text-body-md focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary/50 placeholder-outline" id="kt-pln-ui10-reason" data-testid="kt-pln-ui10-reason" data-kt-field="update_reason" placeholder="Briefly explain why this requirement is being added after Plan approval." rows="3"></textarea>
<div class="font-body-sm text-body-sm text-error mt-1 hidden" data-kt-field-error="update_reason" hidden></div>
</div>
<div class="flex items-center gap-6 text-body-sm font-body-sm text-on-surface-variant pt-2">
<div class="flex items-center gap-2">
<span class="material-symbols-outlined text-[18px]" data-icon="domain">domain</span>
<span data-kt-pln-ui10-initiated>Initiated by</span>
</div>
<div class="flex items-center gap-2">
<span class="material-symbols-outlined text-[18px]" data-icon="calendar_today">calendar_today</span>
<span data-kt-pln-ui10-created>Created</span>
</div>
</div>
</div>
</section>
<section class="flex flex-col gap-4" data-testid="kt-pln-ui10-changes">
<h2 class="font-headline-sm text-headline-sm text-on-background m-0">Changes in this update</h2>
<div class="bg-surface-container-lowest border border-border-subtle rounded-lg overflow-x-auto relative shadow-sm" data-testid="kt-pln-ui10-changes-table">
<table class="w-full text-left border-collapse min-w-[900px]">
<thead>
<tr class="bg-surface-container-low border-b border-border-subtle font-label-caps text-label-caps text-on-surface-variant">
<th class="py-3 px-4 font-medium w-24">Change</th>
<th class="py-3 px-4 font-medium">Plan Item</th>
<th class="py-3 px-4 font-medium">Organisation Unit</th>
<th class="py-3 px-4 font-medium text-right">Value</th>
<th class="py-3 px-4 font-medium">Finance</th>
<th class="py-3 px-4 font-medium">Validation</th>
<th class="py-3 px-4 font-medium text-right">Action</th>
</tr>
</thead>
<tbody class="font-body-md text-body-md divide-y divide-border-subtle" data-kt-pln-ui10-changes-body></tbody>
</table>
</div>
<div class="flex items-center justify-between text-body-sm font-body-sm text-on-surface-variant px-2" data-testid="kt-pln-ui10-unchanged">
<span data-kt-pln-ui10-unchanged-copy>1 existing Plan Item remains unchanged and operational.</span>
<button type="button" class="text-primary hover:underline" data-kt-pln-action="toggle-unchanged" data-testid="kt-pln-ui10-view-unchanged">View unchanged item</button>
</div>
<div class="bg-surface-container-lowest border border-border-subtle rounded-lg overflow-x-auto hidden" data-testid="kt-pln-ui10-unchanged-table" hidden>
<table class="w-full text-left border-collapse min-w-[900px]">
<thead>
<tr class="bg-surface-container-low border-b border-border-subtle font-label-caps text-label-caps text-on-surface-variant">
<th class="py-3 px-4 font-medium">Plan Item</th>
<th class="py-3 px-4 font-medium">Organisation Unit</th>
<th class="py-3 px-4 font-medium text-right">Value</th>
<th class="py-3 px-4 font-medium text-right">Action</th>
</tr>
</thead>
<tbody data-kt-pln-ui10-unchanged-body></tbody>
</table>
</div>
</section>
<div class="bg-status-reserved/10 border-l-4 border-status-reserved rounded-r-lg p-4 flex items-start gap-3 mt-4 hidden" data-testid="kt-pln-ui10-issue" hidden>
<span class="material-symbols-outlined text-status-reserved mt-0.5 filled" data-icon="warning">warning</span>
<p class="font-body-md text-body-md text-on-background m-0 font-medium" data-kt-pln-ui10-issue-copy>Finance confirmation is required for the added Plan Item before this update can be submitted for review.</p>
</div>
<div class="bg-surface-container-low border border-border-subtle rounded-lg p-4 hidden" data-testid="kt-pln-ui10-no-changes" hidden>
<p class="font-body-md text-body-md text-on-background m-0 font-medium">No changes remain in this update.</p>
</div>
<div class="flex justify-between items-center pt-6 border-t border-border-subtle mt-4 pb-12" data-testid="kt-pln-ui10-footer">
<button type="button" class="px-4 py-2 text-status-exhausted font-body-md text-body-md font-medium hover:bg-status-exhausted/10 rounded transition-colors" data-testid="kt-pln-ui10-cancel" data-kt-pln-action="cancel-update">
                    Cancel update
                </button>
<div class="flex gap-4">
<button type="button" class="px-4 py-2 text-primary font-body-md text-body-md font-medium hover:bg-primary/10 rounded transition-colors" data-testid="kt-pln-ui10-save" data-kt-pln-action="save-update">
                        Save draft
                    </button>
<button type="button" class="px-6 py-2 bg-on-surface-variant/20 text-on-surface-variant/50 font-body-md text-body-md font-medium rounded cursor-not-allowed" disabled="" data-testid="kt-pln-ui10-submit" data-kt-pln-action="submit-update">
                        Submit update for review
                    </button>
</div>
</div>
</div>
</div>
</div>
<div data-kt-pln-dialog-host></div>`;
};
