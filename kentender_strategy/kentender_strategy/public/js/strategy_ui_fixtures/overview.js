// Extracted from docs/mvp-1/01_strategy/ui_design/plan_overview_ministry_of_health_strategic_plan/code.html
// <main> + successor modal. Stitch classes preserved; surgical nav/testid hooks only.
frappe.provide("kentender_strategy.ui_fixtures");
kentender_strategy.ui_fixtures.overview = function () {
	return `<div class="kt-str-root" data-testid="kt-str-overview">
<!-- Plan chrome injected by strategy_alignment_shell.planChromeHtml -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-section-gap" data-testid="kt-str-overview-bento">
<!-- Left Column: Primary Details -->
<div class="lg:col-span-8 space-y-section-gap" data-kt-str-overview-main="1">
<!-- 1. Plan Details Section -->
<section class="bg-surface-container-lowest border border-border-subtle rounded-xl p-card-padding">
<div class="flex items-center justify-between mb-6">
<h2 class="font-headline-sm text-headline-sm text-on-surface">Plan Details</h2>
<span class="material-symbols-outlined text-outline-variant">info</span>
</div>
<div class="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-6">
<div class="space-y-1">
<p class="text-label-caps font-label-caps text-outline uppercase">Plan type</p>
<p class="text-on-surface font-body-md" data-kt-str-detail="plan_type">Entity Strategic Plan</p>
</div>
<div class="space-y-1">
<p class="text-label-caps font-label-caps text-outline uppercase">Procuring entity</p>
<p class="text-on-surface font-body-md" data-kt-str-detail="procuring_entity">Ministry of Health</p>
</div>
<div class="space-y-1">
<p class="text-label-caps font-label-caps text-outline uppercase">Effective period</p>
<p class="text-on-surface font-body-md" data-kt-str-detail="effective_period">1 July 2026 – 30 June 2030</p>
</div>
<div class="space-y-1">
<p class="text-label-caps font-label-caps text-outline uppercase">Version / Status</p>
<p class="text-on-surface font-body-md" data-kt-str-detail="version_status">1 <span class="mx-2 text-outline-variant">•</span> Active</p>
</div>
<div class="md:col-span-2 space-y-1 pt-2">
<p class="text-label-caps font-label-caps text-outline uppercase">Description</p>
<p class="text-on-surface font-body-md leading-relaxed italic" data-kt-str-detail="description">"Strategic direction for accessible, resilient and cost-effective national health services."</p>
</div>
</div>
</section>
<!-- 4. Performance Attention (Compact Table) -->
<section class="bg-surface-container-lowest border border-border-subtle rounded-xl overflow-hidden" data-testid="kt-str-overview-attention">
<div class="p-card-padding border-b border-border-subtle flex justify-between items-center">
<h2 class="font-headline-sm text-headline-sm text-on-surface">Performance Attention</h2>
<span class="text-xs font-bold text-error bg-error-container/20 px-2 py-0.5 rounded" data-kt-str-attention-badge>0 Required Actions</span>
</div>
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse">
<thead>
<tr class="bg-surface-container-low">
<th class="px-6 py-3 text-label-caps font-label-caps text-outline uppercase">Target</th>
<th class="px-6 py-3 text-label-caps font-label-caps text-outline uppercase">Period</th>
<th class="px-6 py-3 text-label-caps font-label-caps text-outline uppercase">Result</th>
<th class="px-6 py-3 text-label-caps font-label-caps text-outline uppercase text-right">Next action</th>
</tr>
</thead>
<tbody class="divide-y divide-border-subtle" data-kt-str-attention-tbody>
<tr data-kt-str-attention-empty="1">
<td class="py-6 px-6 text-body-md text-on-surface-variant" colspan="4">No performance items need attention.</td>
</tr>
</tbody>
</table>
</div>
</section>
</div>
<!-- Right Column: Summaries -->
<div class="lg:col-span-4 space-y-section-gap" data-kt-str-overview-aside="1">
<!-- 2. Plan Structure Summary -->
<section class="bg-surface-container-lowest border border-border-subtle rounded-xl p-card-padding">
<h2 class="font-headline-sm text-headline-sm text-on-surface mb-4">Plan Structure</h2>
<div class="grid grid-cols-2 gap-4 mb-6">
<div class="bg-surface-container-low p-3 rounded-lg border border-border-subtle">
<p class="font-data-mono text-headline-sm text-primary" data-kt-str-count="programmes">0</p>
<p class="text-label-caps font-label-caps text-outline uppercase text-[10px]">Programmes</p>
</div>
<div class="bg-surface-container-low p-3 rounded-lg border border-border-subtle">
<p class="font-data-mono text-headline-sm text-primary" data-kt-str-count="sub_programmes">0</p>
<p class="text-label-caps font-label-caps text-outline uppercase text-[10px]">Sub-programmes</p>
</div>
<div class="bg-surface-container-low p-3 rounded-lg border border-border-subtle">
<p class="font-data-mono text-headline-sm text-primary" data-kt-str-count="outcomes">0</p>
<p class="text-label-caps font-label-caps text-outline uppercase text-[10px]">Outcomes</p>
</div>
<div class="bg-surface-container-low p-3 rounded-lg border border-border-subtle">
<p class="font-data-mono text-headline-sm text-primary" data-kt-str-count="indicators">0</p>
<p class="text-label-caps font-label-caps text-outline uppercase text-[10px]">Indicators</p>
</div>
</div>
<div class="flex items-center justify-between pt-4 border-t border-border-subtle">
<span class="font-data-mono text-on-surface-variant"><span data-kt-str-count="targets">0</span> Targets total</span>
<button type="button" class="text-primary font-bold text-body-md hover:underline" data-kt-str-action="view-structure">View structure</button>
</div>
</section>
<!-- 3. Public-value Commitments Summary -->
<section class="bg-surface-container-lowest border border-border-subtle rounded-xl p-card-padding">
<h2 class="font-headline-sm text-headline-sm text-on-surface mb-4">Public-value Commitments</h2>
<div class="space-y-4 mb-6">
<div class="flex items-center justify-between">
<span class="text-body-md text-on-surface-variant">Commitments active</span>
<span class="font-data-mono text-on-surface bg-surface-container-highest px-2 py-0.5 rounded" data-kt-str-commit-count="total">0</span>
</div>
<div class="flex items-center justify-between">
<span class="text-body-md text-on-surface-variant">Required considerations</span>
<span class="font-data-mono text-on-surface bg-surface-container-highest px-2 py-0.5 rounded" data-kt-str-commit-count="required">0</span>
</div>
<div class="flex items-center justify-between">
<span class="text-body-md text-on-surface-variant">Recommended considerations</span>
<span class="font-data-mono text-on-surface bg-surface-container-highest px-2 py-0.5 rounded" data-kt-str-commit-count="recommended">0</span>
</div>
</div>
<div class="pt-4 border-t border-border-subtle">
<button type="button" class="w-full py-2 border border-outline-variant text-primary font-bold text-body-md rounded-lg hover:bg-surface-container-low transition-colors" data-kt-str-action="view-commitments">View commitments</button>
</div>
</section>
<!-- Plan Context Note -->
<div class="bg-tertiary-container/5 border border-tertiary-container/10 p-4 rounded-xl" data-kt-str-policy-note>
<div class="flex gap-3">
<span class="material-symbols-outlined text-on-tertiary-container">policy</span>
<div>
<p class="font-body-md text-on-tertiary-fixed-variant leading-snug">
                                This plan is linked to the <strong>National Health Policy Framework 2025</strong>. Material deviations require cabinet-level justification.
                            </p>
</div>
</div>
</div>
</div>
</div>
<!-- Footer / Bottom Note -->
<footer class="mt-section-gap pt-6 border-t border-outline-variant flex flex-col md:flex-row justify-between items-center gap-4" data-kt-str-lock-footer>
<div class="flex items-center gap-2 text-on-surface-variant">
<span class="material-symbols-outlined text-[20px]" style="font-variation-settings: 'FILL' 1;">lock</span>
<p class="text-body-md" data-kt-str-lock-message>Active plan versions are locked. Create a successor version to make material changes.</p>
</div>
</footer>
<!-- Successor Version Modal (Hidden by Default) -->
<div class="fixed inset-0 bg-black/50 z-[100] hidden flex items-center justify-center backdrop-blur-sm" id="modal-backdrop" data-testid="kt-str-successor-modal" hidden>
<div class="bg-surface-container-lowest w-full max-w-md rounded-xl shadow-xl p-card-padding">
<h3 class="font-headline-sm text-headline-sm text-on-surface mb-2">Create Successor Version</h3>
<p class="text-body-md text-on-surface-variant mb-6" data-kt-str-successor-modal-copy>This will create an 'In-Progress' draft version (v2) while preserving the current active plan.</p>
<div class="flex justify-end gap-3">
<button type="button" class="px-4 py-2 text-on-surface-variant font-bold hover:bg-surface-container rounded-lg" data-kt-str-action="close-successor-modal">Cancel</button>
<button type="button" class="px-4 py-2 bg-primary text-white font-bold rounded-lg" data-kt-str-action="confirm-successor" data-testid="kt-str-confirm-successor">Confirm Creation</button>
</div>
</div>
</div>
</div>`;
};
