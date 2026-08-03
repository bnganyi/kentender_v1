// Auto-extracted Stitch canvas — review_ready_for_submission
frappe.provide("kentender_strategy.ui_fixtures");
kentender_strategy.ui_fixtures.review_ready = function () {
	return `<div class="kt-str-root" data-testid="kt-str-review-ready">
<div class="max-w-3xl w-full mx-auto">
<div class="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-sm overflow-hidden text-center p-8 md:p-12" data-testid="kt-str-review-ready-card">
<div class="w-24 h-24 mx-auto mb-6 rounded-full bg-status-available/10 flex items-center justify-center">
<span class="material-symbols-outlined text-[64px] text-status-available icon-fill">check_circle</span>
</div>
<h3 class="text-headline-lg font-headline-lg text-on-surface mb-4">Ready for submission</h3>
<p class="text-body-lg font-body-lg text-on-surface-variant mb-8 max-w-lg mx-auto leading-relaxed">
                        All readiness checks have passed. This version of the strategic plan can now be submitted for official review.
                    </p>
<div class="flex justify-center gap-4 mb-10">
<div class="flex items-center gap-2 bg-surface-container px-4 py-2 rounded-full border border-outline-variant">
<span class="material-symbols-outlined text-on-surface-variant text-sm">block</span>
<span class="text-body-md font-body-md text-on-surface-variant">0 Blockers</span>
</div>
<div class="flex items-center gap-2 bg-surface-container px-4 py-2 rounded-full border border-outline-variant">
<span class="material-symbols-outlined text-on-surface-variant text-sm">warning</span>
<span class="text-body-md font-body-md text-on-surface-variant">0 Warnings</span>
</div>
</div>
<div class="flex flex-col sm:flex-row items-center justify-center gap-4 border-t border-outline-variant pt-8">
<button type="button" class="w-full sm:w-auto px-6 py-3 rounded-lg bg-surface-container-lowest text-primary border border-primary font-body-md font-semibold hover:bg-surface-container-low transition-colors" data-kt-str-action="return-overview">
                            Return to overview
                        </button>
<button type="button" class="w-full sm:w-auto px-6 py-3 rounded-lg bg-primary text-on-primary font-body-md font-semibold hover:bg-primary-container hover:text-on-primary-container transition-colors shadow-sm flex items-center justify-center gap-2" data-kt-str-action="submit-for-review">
<span>Submit for review</span>
<span class="material-symbols-outlined text-sm">arrow_forward</span>
</button>
</div>
</div>
</div>
</div>`;
};
