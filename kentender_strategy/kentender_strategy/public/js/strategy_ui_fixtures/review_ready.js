// STR-UI-13 Ready for submission — live-bound hosts (canvas from design port).
frappe.provide("kentender_strategy.ui_fixtures");
kentender_strategy.ui_fixtures.review_ready = function () {
	return `<div class="kt-str-root" data-testid="kt-str-review-ready">
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
<div class="max-w-3xl w-full mx-auto">
<div class="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-sm overflow-hidden text-center p-8 md:p-12" data-testid="kt-str-review-ready-card">
<div class="w-24 h-24 mx-auto mb-6 rounded-full bg-status-available/10 flex items-center justify-center">
<span class="material-symbols-outlined text-[64px] text-status-available icon-fill">check_circle</span>
</div>
<h3 class="text-headline-lg font-headline-lg text-on-surface mb-4" data-kt-str-review-ready-title>Ready for submission</h3>
<p class="text-body-lg font-body-lg text-on-surface-variant mb-8 max-w-lg mx-auto leading-relaxed" data-kt-str-review-ready-copy>
All readiness checks have passed. This version of the strategic plan can now be submitted for official review.
</p>
<div class="flex justify-center gap-4 mb-10">
<div class="flex items-center gap-2 bg-surface-container px-4 py-2 rounded-full border border-outline-variant">
<span class="material-symbols-outlined text-on-surface-variant text-sm">block</span>
<span class="text-body-md font-body-md text-on-surface-variant" data-kt-str-blocker-count-label>0 Blockers</span>
</div>
<div class="flex items-center gap-2 bg-surface-container px-4 py-2 rounded-full border border-outline-variant">
<span class="material-symbols-outlined text-on-surface-variant text-sm">warning</span>
<span class="text-body-md font-body-md text-on-surface-variant" data-kt-str-warning-count-label>0 Warnings</span>
</div>
</div>
<div class="flex flex-col sm:flex-row items-center justify-center gap-4 border-t border-outline-variant pt-8" data-kt-str-review-actions>
<button type="button" class="w-full sm:w-auto px-6 py-3 rounded-lg bg-surface-container-lowest text-primary border border-primary font-body-md font-semibold hover:bg-surface-container-low transition-colors" data-kt-str-action="return-overview">
Return to overview
</button>
<button type="button" class="hidden w-full sm:w-auto px-6 py-3 rounded-lg border border-outline-variant text-on-surface font-body-md font-semibold hover:bg-surface-container-low transition-colors" data-kt-str-action="run-readiness">
Run readiness check
</button>
<button type="button" class="hidden w-full sm:w-auto px-6 py-3 rounded-lg border border-outline-variant text-on-surface font-body-md font-semibold hover:bg-surface-container-low transition-colors" data-kt-str-action="return-for-correction">
Return for correction
</button>
<button type="button" class="hidden w-full sm:w-auto px-6 py-3 rounded-lg bg-primary text-on-primary font-body-md font-semibold shadow-sm" data-kt-str-action="approve-plan">
Approve
</button>
<button type="button" class="hidden w-full sm:w-auto px-6 py-3 rounded-lg bg-primary text-on-primary font-body-md font-semibold shadow-sm" data-kt-str-action="activate-plan">
Activate
</button>
<button type="button" class="hidden w-full sm:w-auto px-6 py-3 rounded-lg bg-primary text-on-primary font-body-md font-semibold hover:bg-primary-container transition-colors shadow-sm flex items-center justify-center gap-2" data-kt-str-action="submit-for-review" hidden>
<span data-kt-str-submit-label>Submit for review</span>
<span class="material-symbols-outlined text-sm">arrow_forward</span>
</button>
</div>
</div>
</div>
</div>
</div>`;
};
