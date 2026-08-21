// STR-UI-13 Readiness blockers — live-bound hosts (canvas from design port).
frappe.provide("kentender_strategy.ui_fixtures");
kentender_strategy.ui_fixtures.review_blockers = function () {
	return `<div class="kt-str-root" data-testid="kt-str-review-blockers">
<!-- Plan chrome injected by strategy_alignment_shell.planChromeHtml -->
<div class="p-container-padding md:p-8 max-w-6xl mx-auto pb-32">
<div class="mb-section-gap hidden" data-kt-str-return-reason-banner>
<div class="bg-status-reserved/10 border border-status-reserved/30 rounded-xl p-4 flex items-start gap-3">
<span class="material-symbols-outlined text-status-reserved" data-icon="reply">reply</span>
<div>
<p class="text-xs font-bold uppercase tracking-wide text-status-reserved mb-1">Returned for correction</p>
<p class="text-body-md text-on-surface" data-kt-str-return-reason></p>
</div>
</div>
</div>
<!-- Page Header -->
<div class="mb-section-gap flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
<div>
<h3 class="text-headline-md font-headline-md text-on-surface">Readiness and review</h3>
<p class="text-body-md font-body-md text-on-surface-variant mt-1">Resolve the required plan-definition and governance issues before submission.</p>
</div>
<!-- Summary Strip -->
<div class="flex bg-surface-container-low rounded-lg border border-surface-variant p-1 shadow-sm" data-kt-str-review-summary>
<div class="flex items-center gap-2 px-3 py-1.5 bg-error-container text-on-error-container rounded-md">
<span class="material-symbols-outlined text-[18px]" data-icon="cancel">cancel</span>
<span class="font-bold text-sm" data-kt-str-blocker-count-label>0 Blockers</span>
</div>
<div class="flex items-center gap-2 px-3 py-1.5 bg-[#FEF3C7] text-status-reserved rounded-md ml-1">
<span class="material-symbols-outlined text-[18px]" data-icon="warning">warning</span>
<span class="font-bold text-sm" data-kt-str-warning-count-label>0 Warnings</span>
</div>
</div>
</div>
<!-- Issue Sections -->
<div class="grid grid-cols-1 gap-6" data-kt-str-review-groups>
<div class="bg-surface-container-lowest rounded-xl border border-surface-variant shadow-sm overflow-hidden hidden" data-kt-str-review-group="Structure">
<div class="bg-surface-container-low px-card-padding py-3 border-b border-surface-variant flex justify-between items-center">
<div class="flex items-center gap-2">
<span class="material-symbols-outlined text-outline" data-icon="account_tree">account_tree</span>
<h4 class="font-bold text-on-surface text-sm uppercase tracking-wide">Structure</h4>
</div>
<span class="text-xs font-bold text-on-error-container bg-error-container px-2 py-0.5 rounded-full" data-kt-str-review-group-count>0</span>
</div>
<div class="p-0" data-kt-str-review-issues></div>
</div>
<div class="bg-surface-container-lowest rounded-xl border border-surface-variant shadow-sm overflow-hidden hidden" data-kt-str-review-group="Targets">
<div class="bg-surface-container-low px-card-padding py-3 border-b border-surface-variant flex justify-between items-center">
<div class="flex items-center gap-2">
<span class="material-symbols-outlined text-outline" data-icon="track_changes">track_changes</span>
<h4 class="font-bold text-on-surface text-sm uppercase tracking-wide">Targets</h4>
</div>
<span class="text-xs font-bold text-on-error-container bg-error-container px-2 py-0.5 rounded-full" data-kt-str-review-group-count>0</span>
</div>
<div class="p-0" data-kt-str-review-issues></div>
</div>
<div class="bg-surface-container-lowest rounded-xl border border-surface-variant shadow-sm overflow-hidden hidden" data-kt-str-review-group="Value Commitments">
<div class="bg-surface-container-low px-card-padding py-3 border-b border-surface-variant flex justify-between items-center">
<div class="flex items-center gap-2">
<span class="material-symbols-outlined text-outline" data-icon="handshake">handshake</span>
<h4 class="font-bold text-on-surface text-sm uppercase tracking-wide">Value Commitments</h4>
</div>
<span class="text-xs font-bold text-on-error-container bg-error-container px-2 py-0.5 rounded-full" data-kt-str-review-group-count>0</span>
</div>
<div class="p-0" data-kt-str-review-issues></div>
</div>
<div class="bg-surface-container-lowest rounded-xl border border-surface-variant shadow-sm overflow-hidden hidden" data-kt-str-review-group="Governance">
<div class="bg-surface-container-low px-card-padding py-3 border-b border-surface-variant flex justify-between items-center">
<div class="flex items-center gap-2">
<span class="material-symbols-outlined text-outline" data-icon="policy">policy</span>
<h4 class="font-bold text-on-surface text-sm uppercase tracking-wide">Governance</h4>
</div>
<span class="text-xs font-bold text-on-error-container bg-error-container px-2 py-0.5 rounded-full" data-kt-str-review-group-count>0</span>
</div>
<div class="p-0" data-kt-str-review-issues></div>
</div>
<div class="bg-surface-container rounded-xl p-4 flex items-center gap-3 border border-outline-variant border-opacity-30" data-kt-str-review-blocked-banner>
<span class="material-symbols-outlined text-primary" data-icon="info">info</span>
<p class="text-body-md font-medium text-on-surface-variant">
Submission is blocked until all blockers are resolved.
</p>
</div>
</div>
</div>
<!-- Sticky Bottom Action Area -->
<div class="kt-str-review-footer fixed bottom-0 right-0 bg-surface-container-lowest border-t border-surface-variant p-4 z-30 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]">
<div class="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
<div class="flex flex-col sm:flex-row w-full md:w-auto gap-3 ml-auto" data-kt-str-review-actions>
<button type="button" class="px-5 py-2 rounded-lg border border-outline-variant text-on-surface-variant hover:bg-surface-container font-semibold transition-colors order-3 sm:order-1" data-kt-str-action="return-overview">
Return to overview
</button>
<button type="button" class="px-5 py-2 rounded-lg bg-primary text-on-primary hover:bg-primary-container font-semibold shadow-sm transition-colors order-1 sm:order-2 flex items-center justify-center gap-2" data-kt-str-action="run-readiness">
<span class="material-symbols-outlined text-[18px]" data-icon="play_arrow">play_arrow</span> Run readiness check
</button>
<button type="button" class="hidden px-5 py-2 rounded-lg border border-outline-variant text-on-surface hover:bg-surface-container font-semibold transition-colors order-2" data-kt-str-action="return-for-correction">
Return for correction
</button>
<button type="button" class="hidden px-5 py-2 rounded-lg bg-primary text-on-primary font-semibold shadow-sm transition-colors order-2" data-kt-str-action="approve-plan">
Approve
</button>
<button type="button" class="hidden px-5 py-2 rounded-lg bg-primary text-on-primary font-semibold shadow-sm transition-colors order-2" data-kt-str-action="activate-plan">
Activate
</button>
<button type="button" class="px-5 py-2 rounded-lg bg-surface-variant text-outline font-semibold cursor-not-allowed order-2 sm:order-3" disabled="" title="All blockers must be resolved before submission" data-kt-str-action="submit-for-review">
Submit for review
</button>
</div>
</div>
</div>
</div>`;
};
