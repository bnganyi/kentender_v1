// BUD-UI-08 — Create Budget Revision (Stitch create_budget_revision…/code.html).
// Dedicated Desk page — not hosted inside the Revisions workspace tab.
frappe.provide("kentender_budget.ui_fixtures");

kentender_budget.ui_fixtures.revision_create = function () {
	return `<div class="kt-bud-root kt-stitch-canvas kt-bud-rev-create-page" data-testid="kt-bud-revision-create" data-kt-bud-live="0">
<div class="kt-bud-rev-create" data-testid="kt-bud-revisions-create" data-kt-bud-revisions-create>
<div class="kt-bud-rev-create-scroll">
<div class="kt-bud-rev-notice hidden" data-testid="kt-bud-rev-create-notice" data-kt-bud-rev-create-notice hidden role="alert" aria-live="assertive">
<span class="material-symbols-outlined kt-bud-rev-notice-icon" aria-hidden="true">error</span>
<div class="kt-bud-rev-notice-body">
<p class="kt-bud-rev-notice-title" data-kt-bud-rev-create-notice-title></p>
<p class="kt-bud-rev-notice-msg" data-kt-bud-rev-create-notice-msg></p>
</div>
</div>

<div class="kt-bud-rev-create-header">
<h1 class="kt-bud-rev-create-title">Create budget revision</h1>
<p class="kt-bud-rev-create-sub">Record an externally approved change to the active procurement budget.</p>
<p class="font-body-md text-on-surface-variant hidden" data-kt-bud-rev-saved-code-wrap>
<span class="font-label-caps text-label-caps uppercase text-on-surface-variant">Revision</span>
<span class="font-data-mono text-data-mono font-bold ml-2" data-kt-bud-rev-saved-code></span>
</p>
</div>

<form class="kt-bud-rev-create-form" data-testid="kt-bud-rev-create-form" data-kt-bud-rev-create-form onsubmit="return false;">
<input type="hidden" data-kt-bud-field="revision" value="">
<input type="hidden" data-kt-bud-field="approval_evidence" value="">

<div class="kt-bud-rev-main-grid">
<div class="kt-bud-rev-main-left">
<div data-testid="kt-bud-rev-details">
<h3>Revision Details</h3>
<div class="kt-bud-rev-fields">
<div class="kt-bud-rev-field">
<label for="kt-bud-rev-ext-ref">External revision reference</label>
<input id="kt-bud-rev-ext-ref" type="text" placeholder="e.g. MOF/2023/REV-01" data-kt-bud-field="external_approval_reference" autocomplete="off">
<p class="text-xs text-error hidden" data-kt-bud-error="external_approval_reference"></p>
</div>
<div class="kt-bud-rev-dates">
<div class="kt-bud-rev-field">
<label for="kt-bud-rev-approval-date">Approval date</label>
<div class="kt-bud-rev-date-wrap">
<input id="kt-bud-rev-approval-date" type="date" data-kt-bud-field="approval_date">
<span class="material-symbols-outlined" aria-hidden="true">calendar_today</span>
</div>
<p class="text-xs text-error hidden" data-kt-bud-error="approval_date"></p>
</div>
<div class="kt-bud-rev-field">
<label for="kt-bud-rev-effective-date">Effective date</label>
<div class="kt-bud-rev-date-wrap">
<input id="kt-bud-rev-effective-date" type="date" data-kt-bud-field="effective_date">
<span class="material-symbols-outlined" aria-hidden="true">event</span>
</div>
<p class="text-xs text-error hidden" data-kt-bud-error="effective_date"></p>
</div>
</div>
<div class="kt-bud-rev-field">
<label for="kt-bud-rev-reason">Reason</label>
<textarea id="kt-bud-rev-reason" rows="3" placeholder="Provide justification for the revision..." data-kt-bud-field="reason"></textarea>
<p class="text-xs text-error hidden" data-kt-bud-error="reason"></p>
</div>
<div class="kt-bud-rev-field" data-testid="kt-bud-rev-evidence">
<label>Approval evidence <span class="kt-bud-rev-optional">(optional)</span></label>
<div class="hidden" data-kt-bud-evidence-chip>
<span class="material-symbols-outlined text-primary">description</span>
<span class="font-body-md text-body-md text-on-surface flex-1" data-kt-bud-evidence-name></span>
<button class="text-error" type="button" data-kt-bud-action="clear-evidence" aria-label="Remove evidence">
<span class="material-symbols-outlined">delete</span>
</button>
</div>
<div data-kt-bud-action="pick-evidence" data-testid="kt-bud-evidence-dropzone" role="button" tabindex="0">
<span class="material-symbols-outlined" aria-hidden="true">upload_file</span>
<span class="font-body-md text-on-surface-variant">Click or drag file to upload</span>
<span class="font-label-caps text-label-caps text-outline">PDF, DOCX up to 10MB</span>
<input type="file" class="hidden" accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,application/pdf" data-kt-bud-field="approval_evidence_file">
</div>
<p class="text-xs text-error hidden" data-kt-bud-error="approval_evidence"></p>
</div>
</div>
<div class="kt-bud-rev-finance-note">
<span class="material-symbols-outlined text-on-surface-variant text-sm" aria-hidden="true">info</span>
<p>KenTender records externally approved revisions. Finance approval is not granted here.</p>
</div>
</div>
</div>

<div class="kt-bud-rev-main-right">
<div class="kt-bud-rev-impact" data-testid="kt-bud-rev-impact" data-kt-bud-rev-impact>
<div class="kt-bud-rev-impact-card">
<div class="kt-bud-rev-impact-label">Budget before</div>
<div class="kt-bud-rev-impact-value" data-kt-bud-rev-impact-before>—</div>
</div>
<div class="kt-bud-rev-impact-card kt-bud-rev-impact-change">
<div class="kt-bud-rev-impact-label">Total change</div>
<div class="kt-bud-rev-impact-value">
<span class="material-symbols-outlined text-sm" aria-hidden="true">trending_up</span>
<span data-kt-bud-rev-impact-change>—</span>
</div>
</div>
<div class="kt-bud-rev-impact-card kt-bud-rev-impact-after">
<div class="kt-bud-rev-impact-label">Budget after</div>
<div class="kt-bud-rev-impact-value" data-kt-bud-rev-impact-after>—</div>
</div>
<div class="kt-bud-rev-impact-stat">
<div class="kt-bud-rev-impact-stat-icon">
<span class="material-symbols-outlined" aria-hidden="true">assignment</span>
</div>
<div>
<div class="kt-bud-rev-impact-value" data-kt-bud-rev-impact-demands>0</div>
<div class="kt-bud-rev-impact-label">Affected Demands</div>
</div>
</div>
<div class="kt-bud-rev-impact-stat kt-bud-rev-impact-tenders">
<div class="kt-bud-rev-impact-stat-icon">
<span class="material-symbols-outlined" aria-hidden="true">contract</span>
</div>
<div>
<div class="kt-bud-rev-impact-value" data-kt-bud-rev-impact-tenders>0</div>
<div class="kt-bud-rev-impact-label">Affected Tenders / Contracts</div>
</div>
</div>
</div>

<div data-testid="kt-bud-rev-lines-card">
<div class="kt-bud-rev-lines-head">
<h3>Line Changes</h3>
<button type="button" class="kt-bud-rev-add-line" data-testid="kt-bud-rev-add-line" data-kt-bud-rev-action="add-line">
<span class="material-symbols-outlined text-sm" aria-hidden="true">add</span> Add Line
</button>
</div>
<div class="overflow-x-auto">
<table data-testid="kt-bud-rev-lines-table" data-kt-bud-rev-lines-table>
<thead>
<tr>
<th class="data-table-header">Budget line</th>
<th class="data-table-header text-right">Current Approved</th>
<th class="data-table-header text-right">Change</th>
<th class="data-table-header text-right">Revised Amount</th>
<th class="data-table-header text-right">Reserved</th>
<th class="data-table-header text-right">Committed</th>
<th class="data-table-header text-center">Impact</th>
</tr>
</thead>
<tbody data-testid="kt-bud-rev-lines-tbody" data-kt-bud-rev-lines-tbody>
<tr><td colspan="7" class="px-4 py-6 text-center text-on-surface-variant">Loading lines…</td></tr>
</tbody>
</table>
</div>
<p class="text-xs text-error hidden px-4 py-2" data-kt-bud-error="lines"></p>
<div class="kt-bud-rev-constraint">
<span class="material-symbols-outlined text-sm" aria-hidden="true">info</span>
Constraint: Revised amount cannot be below Reserved + Committed.
</div>
</div>
</div>
</div>
</form>
</div>

<div class="kt-bud-rev-footer" data-testid="kt-bud-rev-footer">
<div class="kt-bud-rev-footer-error hidden" data-testid="kt-bud-rev-footer-error" data-kt-bud-rev-footer-error hidden role="alert">
<span class="material-symbols-outlined" aria-hidden="true">error</span>
<span data-kt-bud-rev-footer-error-msg></span>
</div>
<div class="kt-bud-rev-footer-row">
<button type="button" class="kt-bud-rev-btn-cancel" data-testid="kt-bud-rev-cancel" data-kt-bud-rev-action="cancel">Cancel</button>
<div class="flex">
<button type="button" class="kt-bud-rev-btn-draft" data-testid="kt-bud-rev-save-draft" data-kt-bud-rev-action="save-draft">
<span class="material-symbols-outlined text-sm" aria-hidden="true">save</span>
Save draft
</button>
<button type="button" class="kt-bud-rev-btn-submit" data-testid="kt-bud-rev-submit" data-kt-bud-rev-action="submit">
Submit for review
<span class="material-symbols-outlined text-sm" aria-hidden="true">send</span>
</button>
</div>
</div>
</div>
</div>
</div>`;
};
