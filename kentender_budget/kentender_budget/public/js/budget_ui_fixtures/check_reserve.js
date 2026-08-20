// BUD-UI-06 — Stitch Check and Reserve modal (refined available + insufficient).
frappe.provide("kentender_budget.ui_fixtures");

kentender_budget.ui_fixtures.check_reserve = function () {
	return `<div class="kt-bud-check-reserve-host" data-testid="kt-bud-check-reserve-host" hidden>
<div class="kt-bud-check-reserve-scrim" data-testid="kt-bud-check-reserve-scrim" data-kt-bud-cr-scrim></div>
<div class="kt-bud-root kt-stitch-canvas kt-bud-check-reserve" data-testid="kt-bud-check-reserve" data-kt-bud-live="0" role="dialog" aria-modal="true" aria-labelledby="kt-bud-cr-title">
<div class="kt-bud-cr-header" data-testid="kt-bud-check-reserve-header">
<div class="kt-bud-cr-header-main">
<h1 class="font-headline-lg text-headline-lg" id="kt-bud-cr-title" data-testid="kt-bud-check-reserve-title">Check and reserve funding</h1>
<p class="text-body-md text-on-surface-variant" data-testid="kt-bud-check-reserve-subtitle">Confirm that approved procurement funding is available before this requirement proceeds.</p>
</div>
<button type="button" class="kt-bud-cr-close" data-testid="kt-bud-check-reserve-close" data-kt-bud-cr-close aria-label="Close">
<span class="material-symbols-outlined" aria-hidden="true">close</span>
</button>
</div>

<div class="kt-bud-cr-body">
<div class="kt-bud-cr-notice hidden" data-testid="kt-bud-check-reserve-notice" data-kt-bud-cr-notice hidden role="status" aria-live="polite">
<span class="material-symbols-outlined" aria-hidden="true">info</span>
<div class="kt-bud-cr-notice-body">
<p class="kt-bud-cr-notice-title" data-kt-bud-cr-notice-title></p>
<p class="kt-bud-cr-notice-msg" data-kt-bud-cr-notice-msg></p>
</div>
<button type="button" class="kt-bud-cr-notice-dismiss" data-testid="kt-bud-check-reserve-notice-dismiss" data-kt-bud-cr-notice-dismiss aria-label="Dismiss">
<span class="material-symbols-outlined" aria-hidden="true">close</span>
</button>
</div>

<div class="kt-bud-cr-context" data-testid="kt-bud-check-reserve-context">
<h2 class="font-label-caps text-label-caps text-on-surface-variant uppercase">Procurement Context</h2>
<div class="kt-bud-cr-context-grid">
<div>
<p class="text-body-md text-on-surface-variant">Demand</p>
<p class="text-body-lg font-medium" data-kt-bud-cr-demand-title>—</p>
<p class="kt-bud-cr-muted" data-kt-bud-cr-demand-code></p>
</div>
<div>
<p class="text-body-md text-on-surface-variant">Requesting department</p>
<p class="text-body-lg" data-kt-bud-cr-department>—</p>
</div>
<div>
<p class="text-body-md text-on-surface-variant">Requested amount</p>
<p class="kt-bud-cr-mono kt-bud-cr-requested" data-kt-bud-cr-requested>—</p>
</div>
<div>
<p class="text-body-md text-on-surface-variant">Primary strategic target</p>
<p class="text-body-lg" data-kt-bud-cr-target-name>—</p>
<p class="kt-bud-cr-muted" data-kt-bud-cr-target-code></p>
</div>
</div>
</div>

<div class="kt-bud-cr-allocation" data-testid="kt-bud-check-reserve-allocation">
<h2 class="font-label-caps text-label-caps text-on-surface-variant uppercase">Budget Line Selection</h2>
<div class="kt-bud-cr-select-wrap" data-testid="kt-bud-check-reserve-line-wrap">
<select aria-label="Budget line" data-testid="kt-bud-check-reserve-line" data-kt-bud-cr-line data-kt-bud-cr-filter="budget_line">
<option value="">Select a budget line</option>
</select>
<span class="material-symbols-outlined" aria-hidden="true">expand_more</span>
</div>
<p class="kt-bud-cr-line-hint text-body-md text-on-surface-variant">
Available before: <span class="kt-bud-cr-mono" data-kt-bud-cr-line-available>—</span>
</p>
</div>

<div class="kt-bud-cr-decision kt-bud-cr-decision--available hidden" data-testid="kt-bud-check-reserve-decision-available" data-kt-bud-cr-decision="available" hidden>
<div class="kt-bud-cr-decision-head">
<span class="material-symbols-outlined icon-fill" aria-hidden="true">check_circle</span>
<h3 class="font-headline-sm" data-testid="kt-bud-check-reserve-decision-title-available">Funding available</h3>
</div>
<div class="kt-bud-cr-decision-body">
<div class="kt-bud-cr-amounts">
<div class="kt-bud-cr-amount-row"><span>Available before</span><span class="kt-bud-cr-mono" data-kt-bud-cr-available-before>—</span></div>
<div class="kt-bud-cr-amount-row"><span>Requested</span><span class="kt-bud-cr-mono kt-bud-cr-amount-neg" data-kt-bud-cr-requested-row>—</span></div>
<div class="kt-bud-cr-amount-row kt-bud-cr-amount-row--strong"><span>Available after</span><span class="kt-bud-cr-mono kt-bud-cr-amount-ok" data-kt-bud-cr-available-after>—</span></div>
</div>
<div class="kt-bud-cr-bar" data-kt-bud-cr-bar-available aria-hidden="true"><div class="kt-bud-cr-bar-used"></div><div class="kt-bud-cr-bar-free"></div></div>
<div class="kt-bud-cr-lineage">
<span class="material-symbols-outlined" aria-hidden="true">info</span>
<p data-kt-bud-cr-lineage>This reservation follows the same requirement through Planning and Tendering. Those stages will not create additional funding holds.</p>
</div>
<div class="kt-bud-cr-actions">
<button type="button" class="kt-bud-cr-btn kt-bud-cr-btn--secondary" data-testid="kt-bud-check-reserve-cancel" data-kt-bud-cr-cancel>Cancel</button>
<button type="button" class="kt-bud-cr-btn kt-bud-cr-btn--primary" data-testid="kt-bud-check-reserve-reserve" data-kt-bud-cr-reserve>
<span class="material-symbols-outlined" aria-hidden="true">lock</span>
Reserve funding
</button>
</div>
</div>
</div>

<div class="kt-bud-cr-decision kt-bud-cr-decision--insufficient hidden" data-testid="kt-bud-check-reserve-decision-insufficient" data-kt-bud-cr-decision="insufficient" hidden>
<div class="kt-bud-cr-decision-head kt-bud-cr-decision-head--error">
<span class="material-symbols-outlined icon-fill" aria-hidden="true">error</span>
<h3 class="font-headline-sm" data-testid="kt-bud-check-reserve-decision-title-insufficient">Insufficient funding</h3>
</div>
<div class="kt-bud-cr-decision-body">
<div class="kt-bud-cr-amounts">
<div class="kt-bud-cr-amount-row"><span>Requested</span><span class="kt-bud-cr-mono" data-kt-bud-cr-insuff-requested>—</span></div>
<div class="kt-bud-cr-amount-row"><span>Available before</span><span class="kt-bud-cr-mono kt-bud-cr-amount-ok" data-kt-bud-cr-insuff-before>—</span></div>
<div class="kt-bud-cr-amount-row kt-bud-cr-amount-row--strong"><span>Shortfall</span><span class="kt-bud-cr-mono kt-bud-cr-amount-err" data-kt-bud-cr-shortfall>—</span></div>
</div>
<div class="kt-bud-cr-bar kt-bud-cr-bar--insuff" data-kt-bud-cr-bar-insufficient aria-hidden="true"><div class="kt-bud-cr-bar-used"></div><div class="kt-bud-cr-bar-short"></div></div>
<div class="kt-bud-cr-warn">
<span class="material-symbols-outlined" aria-hidden="true">warning</span>
<p>The selected budget line does not have sufficient unreserved funds to cover this request. Please reallocate funds or select a different budget line.</p>
</div>
<div class="kt-bud-cr-actions">
<button type="button" class="kt-bud-cr-btn kt-bud-cr-btn--secondary" data-testid="kt-bud-check-reserve-return" data-kt-bud-cr-return>Return to demand</button>
<button type="button" class="kt-bud-cr-btn kt-bud-cr-btn--outline" data-testid="kt-bud-check-reserve-select-line" data-kt-bud-cr-select-line>Select another budget line</button>
<button type="button" class="kt-bud-cr-btn kt-bud-cr-btn--disabled" data-testid="kt-bud-check-reserve-reserve-disabled" data-kt-bud-cr-reserve-disabled disabled>
<span class="material-symbols-outlined" aria-hidden="true">lock</span>
Reserve funding
</button>
</div>
</div>
</div>
</div>
</div>
</div>`;
};
