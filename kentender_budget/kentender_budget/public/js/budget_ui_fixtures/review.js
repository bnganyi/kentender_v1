// BUD-UI-11 — Stitch Review / readiness (review_ministry_of_health_budget_fy_2027_28).
// Fake sidenav / duplicate H1 discarded; workspace chrome from shell.
frappe.provide("kentender_budget.ui_fixtures");

kentender_budget.ui_fixtures.review = function () {
	return `<div class="kt-bud-root kt-stitch-canvas" data-testid="kt-bud-review">
<!-- Workspace chrome injected by budget_workspace_shell -->
<div class="flex-1 p-container-padding max-w-[1600px] mx-auto w-full" data-testid="kt-bud-review-canvas">
<div class="kt-bud-review-header mb-section-gap" data-testid="kt-bud-review-header">
<div class="kt-bud-review-header-row">
<div>
<h2 class="font-headline-md text-headline-md text-on-surface" data-testid="kt-bud-review-title">Readiness Checklist</h2>
<p class="font-body-md text-body-md text-on-surface-variant mt-1">Pre-submission verification for procurement activation.</p>
</div>
<div class="kt-bud-review-status-chip" data-testid="kt-bud-review-status-chip" data-kt-bud-review-status-chip>
<span class="kt-bud-review-status-dot" aria-hidden="true"></span>
<span class="font-body-md text-body-md text-on-surface text-sm" data-kt-bud-review-status-label>Draft State</span>
</div>
</div>
</div>

<div class="kt-bud-review-notice hidden" data-testid="kt-bud-review-notice" data-kt-bud-review-notice hidden role="status" aria-live="polite">
<span class="material-symbols-outlined kt-bud-review-notice-icon" aria-hidden="true">info</span>
<div class="kt-bud-review-notice-body">
<p class="kt-bud-review-notice-title" data-kt-bud-review-notice-title></p>
<p class="kt-bud-review-notice-msg" data-kt-bud-review-notice-msg></p>
</div>
<button type="button" class="kt-bud-review-notice-dismiss" data-testid="kt-bud-review-notice-dismiss" data-kt-bud-review-notice-dismiss aria-label="Dismiss">
<span class="material-symbols-outlined" aria-hidden="true">close</span>
</button>
</div>

<div class="kt-bud-review-activation hidden" data-testid="kt-bud-review-activation" data-kt-bud-review-activation hidden>
<div class="kt-bud-review-activation-card">
<span class="material-symbols-outlined icon-fill text-status-available" aria-hidden="true">check_circle</span>
<div>
<p class="font-headline-sm text-headline-sm text-on-surface">Activation record</p>
<p class="font-body-md text-body-md text-on-surface-variant mt-1" data-kt-bud-review-activation-summary></p>
</div>
</div>
</div>

<div class="kt-bud-review-grid" data-testid="kt-bud-review-groups" data-kt-bud-review-groups>
<!-- Group cards rendered by bindReview -->
</div>

<div class="kt-bud-review-footer" data-testid="kt-bud-review-footer" data-kt-bud-review-footer>
<div class="kt-bud-review-footer-disclaimer">
<span class="material-symbols-outlined text-on-surface-variant mt-0.5" aria-hidden="true">info</span>
<p class="font-body-md text-body-md text-on-surface-variant" data-kt-bud-review-disclaimer>
Activation confirms that the approved financial baseline has been verified for procurement use in KenTender. It does not constitute statutory budget approval.
</p>
</div>
<p class="kt-bud-review-footer-error hidden text-error text-sm" data-testid="kt-bud-review-footer-error" data-kt-bud-review-footer-error hidden></p>
<div class="kt-bud-review-footer-actions" data-testid="kt-bud-review-actions">
<button type="button" class="kt-bud-review-btn-secondary" data-testid="kt-bud-review-run" data-kt-bud-review-action="run">Run readiness check</button>
<button type="button" class="kt-bud-review-btn-secondary" data-testid="kt-bud-review-return" data-kt-bud-review-action="return" hidden>Return for correction</button>
<button type="button" class="kt-bud-review-btn-secondary" data-testid="kt-bud-review-mark" data-kt-bud-review-action="mark" hidden>Mark reviewed</button>
<button type="button" class="kt-bud-review-btn-primary" data-testid="kt-bud-review-submit" data-kt-bud-review-action="submit" disabled>Submit for review</button>
<button type="button" class="kt-bud-review-btn-primary" data-testid="kt-bud-review-activate" data-kt-bud-review-action="activate" hidden disabled>
<span class="material-symbols-outlined kt-bud-review-activate-lock hidden" aria-hidden="true" data-kt-bud-review-activate-lock>lock</span>
Activate budget
</button>
</div>
</div>
</div>

<div class="kt-bud-rev-reason-modal hidden" data-testid="kt-bud-review-reason-modal" data-kt-bud-review-reason-modal hidden role="dialog" aria-modal="true" aria-labelledby="kt-bud-review-reason-modal-title">
<div class="kt-bud-rev-reason-modal-card">
<div class="kt-bud-rev-reason-modal-header">
<h2 class="kt-bud-rev-reason-modal-title" id="kt-bud-review-reason-modal-title" data-kt-bud-review-reason-title>Return budget for correction</h2>
<button type="button" class="kt-bud-rev-reason-modal-close" data-testid="kt-bud-review-reason-close" data-kt-bud-review-reason-close aria-label="Close">
<span class="material-symbols-outlined" aria-hidden="true">close</span>
</button>
</div>
<div class="kt-bud-rev-reason-modal-body">
<p class="kt-bud-rev-reason-modal-lead" data-kt-bud-review-reason-lead>
Provide a mandatory reason for returning this Budget. This feedback will be sent to the officer.
</p>
<label class="sr-only" for="kt-bud-review-reason-comment">Reason</label>
<textarea id="kt-bud-review-reason-comment" class="kt-bud-rev-reason-modal-textarea" rows="4" data-testid="kt-bud-review-reason-comment" data-kt-bud-review-reason-comment placeholder="e.g., Approval evidence is missing and one line lacks a primary Strategy target."></textarea>
<p class="text-xs text-error hidden" data-kt-bud-error="comment"></p>
</div>
<div class="kt-bud-rev-reason-modal-footer">
<button type="button" class="kt-bud-rev-reason-cancel" data-testid="kt-bud-review-reason-cancel" data-kt-bud-review-reason-cancel>Cancel</button>
<button type="button" class="kt-bud-rev-reason-confirm is-return" data-testid="kt-bud-review-reason-confirm" data-kt-bud-review-reason-confirm>Confirm return</button>
</div>
</div>
</div>
</div>`;
};
