// BUD-UI-09 — Review Budget Revision (Stitch review_revision_br_2027_042/code.html).
// Reason modal: Stitch budget_revision_rejection_reason/code.html (no footer textarea).
// Dedicated Desk page — not hosted inside the Revisions workspace tab.
frappe.provide("kentender_budget.ui_fixtures");

kentender_budget.ui_fixtures.revision_review = function () {
	return `<div class="kt-bud-root kt-stitch-canvas kt-bud-rev-review-page" data-testid="kt-bud-revision-review" data-kt-bud-live="0">
<div class="kt-bud-rev-review" data-testid="kt-bud-rev-review">
<div class="kt-bud-rev-review-scroll">
<button type="button" class="kt-bud-rev-review-back" data-testid="kt-bud-rev-review-back" data-kt-bud-rev-review-back>
<span class="material-symbols-outlined" aria-hidden="true">arrow_back</span>
Back to Revisions
</button>

<div class="kt-bud-rev-review-header">
<div class="kt-bud-rev-review-title-row">
<h1 class="kt-bud-rev-review-title">Review budget revision</h1>
<span class="kt-bud-rev-review-status" data-testid="kt-bud-rev-review-status" data-kt-bud-rev-review-status>
<span class="material-symbols-outlined" aria-hidden="true">pending</span>
<span data-kt-bud-rev-review-status-label>Pending Review</span>
</span>
</div>
<p class="kt-bud-rev-review-ref font-data-mono">Ref: <span data-kt-bud-rev-review-code>—</span></p>
</div>

<div class="kt-bud-rev-review-details" data-testid="kt-bud-rev-review-details">
<div class="kt-bud-rev-review-detail">
<span class="kt-bud-rev-review-label">Initiated by</span>
<span class="kt-bud-rev-review-value" data-kt-bud-rev-review-submitted-by>—</span>
</div>
<div class="kt-bud-rev-review-detail">
<span class="kt-bud-rev-review-label">Date submitted</span>
<span class="kt-bud-rev-review-value font-data-mono" data-kt-bud-rev-review-submitted-at>—</span>
</div>
<div class="kt-bud-rev-review-detail">
<span class="kt-bud-rev-review-label">Fiscal period</span>
<span class="kt-bud-rev-review-value" data-kt-bud-rev-review-fiscal>—</span>
</div>
<div class="kt-bud-rev-review-detail">
<span class="kt-bud-rev-review-label">External revision reference</span>
<span class="kt-bud-rev-review-value font-data-mono" data-kt-bud-rev-review-ext-ref>—</span>
</div>
<div class="kt-bud-rev-review-detail">
<span class="kt-bud-rev-review-label">Approval date</span>
<span class="kt-bud-rev-review-value font-data-mono" data-kt-bud-rev-review-approval-date>—</span>
</div>
<div class="kt-bud-rev-review-detail">
<span class="kt-bud-rev-review-label">Effective date</span>
<span class="kt-bud-rev-review-value font-data-mono" data-kt-bud-rev-review-effective-date>—</span>
</div>
<div class="kt-bud-rev-review-detail kt-bud-rev-review-detail-wide">
<span class="kt-bud-rev-review-label">Justification</span>
<p class="kt-bud-rev-review-value" data-kt-bud-rev-review-reason>—</p>
</div>
<div class="kt-bud-rev-review-detail kt-bud-rev-review-detail-wide">
<span class="kt-bud-rev-review-label">Approval evidence</span>
<span class="kt-bud-rev-review-value font-data-mono" data-kt-bud-rev-review-evidence>—</span>
</div>
</div>

<div class="kt-bud-rev-review-blocker hidden" data-testid="kt-bud-rev-review-blocker" data-kt-bud-rev-review-blocker hidden>
<span class="material-symbols-outlined kt-bud-rev-review-blocker-icon" aria-hidden="true">block</span>
<div class="kt-bud-rev-review-blocker-body">
<h3 class="kt-bud-rev-review-blocker-title">Critical blocker detected</h3>
<p class="kt-bud-rev-review-blocker-msg" data-kt-bud-rev-review-blocker-msg></p>
<button type="button" class="kt-bud-rev-review-blocker-link" data-testid="kt-bud-rev-review-view-line" data-kt-bud-rev-review-view-line>
View affected line item
<span class="material-symbols-outlined" aria-hidden="true">arrow_forward</span>
</button>
</div>
</div>

<div class="kt-bud-rev-review-notice hidden" data-testid="kt-bud-rev-review-notice" data-kt-bud-rev-review-notice hidden role="status" aria-live="polite">
<p class="kt-bud-rev-notice-title" data-kt-bud-rev-review-notice-title></p>
<p class="kt-bud-rev-notice-msg" data-kt-bud-rev-review-notice-msg></p>
</div>

<div class="kt-bud-rev-review-groups" data-testid="kt-bud-rev-review-groups">
<section class="kt-bud-rev-review-group" data-testid="kt-bud-rev-review-financial">
<header>
<span class="material-symbols-outlined" aria-hidden="true">account_balance</span>
<h2>Financial impact</h2>
</header>
<div class="kt-bud-rev-review-group-body">
<div>
<span class="kt-bud-rev-review-label">Net portfolio change</span>
<div class="kt-bud-rev-review-net">
<span class="font-data-mono" data-kt-bud-rev-review-net>—</span>
<span class="kt-bud-rev-review-pill" data-kt-bud-rev-review-balance-label>BALANCED</span>
</div>
</div>
<div class="kt-bud-rev-review-fin-split">
<div>
<span class="kt-bud-rev-review-label">Total deductions</span>
<div class="kt-bud-rev-review-deduct font-data-mono">
<span class="material-symbols-outlined" aria-hidden="true">arrow_downward</span>
<span data-kt-bud-rev-review-deductions>—</span>
</div>
</div>
<div>
<span class="kt-bud-rev-review-label">Total additions</span>
<div class="kt-bud-rev-review-add font-data-mono">
<span class="material-symbols-outlined" aria-hidden="true">arrow_upward</span>
<span data-kt-bud-rev-review-additions>—</span>
</div>
</div>
</div>
</div>
</section>

<section class="kt-bud-rev-review-group" data-testid="kt-bud-rev-review-strategy">
<header>
<span class="material-symbols-outlined" aria-hidden="true">flag</span>
<h2>Strategy and value-treatment impact</h2>
</header>
<div class="kt-bud-rev-review-group-body" data-kt-bud-rev-review-strategy-items></div>
</section>

<section class="kt-bud-rev-review-group" data-testid="kt-bud-rev-review-downstream">
<header>
<span class="material-symbols-outlined" aria-hidden="true">hub</span>
<h2>Downstream impact</h2>
</header>
<div class="kt-bud-rev-review-group-body" data-kt-bud-rev-review-downstream-cards>
<p class="kt-bud-rev-review-empty" data-kt-bud-rev-review-downstream-empty></p>
</div>
</section>
</div>
</div>

<footer class="kt-bud-rev-review-footer" data-testid="kt-bud-rev-review-footer">
<div class="kt-bud-rev-review-actions">
<button type="button" class="kt-bud-rev-review-reject" data-testid="kt-bud-rev-review-reject" data-kt-bud-rev-review-action="reject">Reject revision</button>
<button type="button" class="kt-bud-rev-review-return" data-testid="kt-bud-rev-review-return" data-kt-bud-rev-review-action="return">Return for correction</button>
<button type="button" class="kt-bud-rev-review-apply" data-testid="kt-bud-rev-review-apply" data-kt-bud-rev-review-action="apply">
<span class="material-symbols-outlined kt-bud-rev-review-apply-lock hidden" aria-hidden="true" data-kt-bud-rev-review-apply-lock>lock</span>
Apply revision
</button>
</div>
</footer>

<div class="kt-bud-rev-reason-modal hidden" data-testid="kt-bud-rev-reason-modal" data-kt-bud-rev-reason-modal hidden role="dialog" aria-modal="true" aria-labelledby="kt-bud-rev-reason-modal-title">
<div class="kt-bud-rev-reason-modal-card">
<div class="kt-bud-rev-reason-modal-header">
<h2 class="kt-bud-rev-reason-modal-title" id="kt-bud-rev-reason-modal-title" data-kt-bud-rev-reason-title>Reject budget revision</h2>
<button type="button" class="kt-bud-rev-reason-modal-close" data-testid="kt-bud-rev-reason-close" data-kt-bud-rev-reason-close aria-label="Close">
<span class="material-symbols-outlined" aria-hidden="true">close</span>
</button>
</div>
<div class="kt-bud-rev-reason-modal-body">
<p class="kt-bud-rev-reason-modal-lead" data-kt-bud-rev-reason-lead>
Provide a mandatory reason for rejection. This feedback will be sent to the initiator.
</p>
<label class="sr-only" for="kt-bud-rev-reason-comment">Reason</label>
<textarea id="kt-bud-rev-reason-comment" class="kt-bud-rev-reason-modal-textarea" rows="4" data-testid="kt-bud-rev-reason-comment" data-kt-bud-rev-reason-comment placeholder="e.g., The proposed reduction is not permitted at this stage."></textarea>
<p class="text-xs text-error hidden" data-kt-bud-error="comment"></p>
</div>
<div class="kt-bud-rev-reason-modal-footer">
<button type="button" class="kt-bud-rev-reason-cancel" data-testid="kt-bud-rev-reason-cancel" data-kt-bud-rev-reason-cancel>Cancel</button>
<button type="button" class="kt-bud-rev-reason-confirm" data-testid="kt-bud-rev-reason-confirm" data-kt-bud-rev-reason-confirm>Confirm rejection</button>
</div>
</div>
</div>
</div>
</div>`;
};
