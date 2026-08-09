// DEM-UI-09 / 09A–D — Approved Demand detail (Stitch DEM-UI-09*.html).
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.demand_detail = function () {
	return `
<div class="kt-dem-detail kt-stitch-canvas" data-testid="kt-dem-ui09-root" data-kt-dem-detail-root data-kt-dem-live="0">
<header class="kt-dem-ui09-header" data-testid="kt-dem-ui09-header">
<div class="kt-dem-ui09-header-top">
<div class="kt-dem-ui09-title-block">
<div class="kt-dem-ui09-meta-top">
<span class="kt-dem-ui09-code font-data-mono" data-kt-dem-label="detail_code" data-testid="kt-dem-ui09-code">—</span>
<span class="kt-dem-ui09-approved-pill" data-testid="kt-dem-ui09-status">
<span class="kt-dem-ui09-approved-dot" aria-hidden="true"></span>
<span data-kt-dem-label="detail_status">APPROVED</span>
</span>
</div>
<h1 class="kt-dem-ui09-title mb-0" data-kt-dem-label="detail_title" data-testid="kt-dem-ui09-title">—</h1>
</div>
<div class="kt-dem-ui09-header-actions">
<button type="button" class="kt-dem-ui09-btn kt-dem-ui09-btn--secondary" data-kt-dem-action="detail-print" data-testid="kt-dem-ui09-print">
<span class="material-symbols-outlined text-[18px]" aria-hidden="true">print</span>
Print
</button>
<button type="button" class="kt-dem-ui09-btn kt-dem-ui09-btn--danger hidden" data-kt-dem-action="detail-cancel" data-testid="kt-dem-ui09-cancel" hidden>
Cancel remaining
</button>
</div>
</div>
<div class="kt-dem-ui09-meta-row" data-testid="kt-dem-ui09-meta">
<div class="kt-dem-ui09-meta-item">
<span class="material-symbols-outlined" aria-hidden="true">alt_route</span>
<span class="kt-dem-ui09-meta-label">Route</span>
<span class="kt-dem-ui09-meta-value" data-kt-dem-label="detail_route">Standard</span>
</div>
<div class="kt-dem-ui09-meta-divider" aria-hidden="true"></div>
<div class="kt-dem-ui09-meta-item">
<span class="material-symbols-outlined" aria-hidden="true">payments</span>
<span class="kt-dem-ui09-meta-label">Confirmed estimate:</span>
<span class="kt-dem-ui09-meta-value font-data-mono" data-kt-dem-label="detail_estimate">—</span>
</div>
<div class="kt-dem-ui09-meta-divider" aria-hidden="true"></div>
<div class="kt-dem-ui09-meta-item">
<span class="material-symbols-outlined kt-dem-ui09-planning-icon" aria-hidden="true">check_circle</span>
<span class="kt-dem-ui09-meta-label">Planning:</span>
<span class="kt-dem-ui09-meta-value" data-kt-dem-label="detail_planning_usage">—</span>
</div>
</div>
<div class="kt-dem-ui09-lock" data-testid="kt-dem-ui09-lock">
<span class="material-symbols-outlined" aria-hidden="true">lock</span>
<div>
<h4 class="kt-dem-ui09-lock-title mb-0">Baseline Locked</h4>
<p class="kt-dem-ui09-lock-text mb-0" data-kt-dem-label="detail_lock_message">The approved Demand baseline is locked. Material change requires cancellation and a linked replacement Demand.</p>
</div>
</div>
<nav class="kt-dem-ui09-tabs" data-testid="kt-dem-ui09-tabs" data-kt-dem-detail-tabs role="tablist">
<button type="button" class="kt-dem-ui09-tab is-active" data-kt-dem-detail-tab="overview" data-testid="kt-dem-ui09-tab-overview" role="tab" aria-selected="true">Overview</button>
<button type="button" class="kt-dem-ui09-tab" data-kt-dem-detail-tab="scope" data-testid="kt-dem-ui09-tab-scope" role="tab" aria-selected="false">Approved scope</button>
<button type="button" class="kt-dem-ui09-tab" data-kt-dem-detail-tab="strategy" data-testid="kt-dem-ui09-tab-strategy" role="tab" aria-selected="false">Strategy and value</button>
<button type="button" class="kt-dem-ui09-tab" data-kt-dem-detail-tab="funding" data-testid="kt-dem-ui09-tab-funding" role="tab" aria-selected="false">Funding</button>
<button type="button" class="kt-dem-ui09-tab" data-kt-dem-detail-tab="lifecycle" data-testid="kt-dem-ui09-tab-lifecycle" role="tab" aria-selected="false">Lifecycle</button>
</nav>
</header>

<div class="kt-dem-ui09-panels" data-kt-dem-detail-panels>

<section class="kt-dem-ui09-panel" data-kt-dem-detail-panel="overview" data-testid="kt-dem-ui09-overview">
<section class="kt-dem-ui09-card">
<h2 class="kt-dem-ui09-card-title">1. Demand Summary</h2>
<p class="kt-dem-ui09-body" data-kt-dem-label="ov_need">—</p>
<div class="kt-dem-ui09-def-grid">
<div>
<span class="kt-dem-ui09-def-label">Owning unit</span>
<span class="kt-dem-ui09-def-value" data-kt-dem-label="ov_owning_unit">—</span>
</div>
<div>
<span class="kt-dem-ui09-def-label">Required by</span>
<span class="kt-dem-ui09-def-value font-data-mono" data-kt-dem-label="ov_required_by">—</span>
</div>
</div>
</section>
<section class="kt-dem-ui09-card">
<div class="kt-dem-ui09-card-head"><h2 class="kt-dem-ui09-card-title mb-0">2. Approved Position</h2></div>
<div class="kt-dem-ui09-position-strip" data-testid="kt-dem-ui09-position">
<div class="kt-dem-ui09-position-cell">
<span class="kt-dem-ui09-def-label">Approved amount</span>
<span class="kt-dem-ui09-position-value font-data-mono" data-kt-dem-label="ov_amount">—</span>
</div>
<div class="kt-dem-ui09-position-cell">
<span class="kt-dem-ui09-def-label">Funding status</span>
<span class="kt-dem-ui09-position-value" data-kt-dem-label="ov_funding_status">—</span>
</div>
<div class="kt-dem-ui09-position-cell">
<span class="kt-dem-ui09-def-label">Downstream records</span>
<span class="kt-dem-ui09-position-value" data-kt-dem-label="ov_downstream">—</span>
</div>
<div class="kt-dem-ui09-position-cell">
<span class="kt-dem-ui09-def-label">Planning usage</span>
<span class="kt-dem-ui09-position-value" data-kt-dem-label="ov_planning">—</span>
</div>
</div>
</section>
<section class="kt-dem-ui09-card">
<div class="kt-dem-ui09-card-head"><h2 class="kt-dem-ui09-card-title mb-0">3. Control Summary</h2></div>
<div class="kt-dem-ui09-control-list">
<div class="kt-dem-ui09-control-row">
<div class="kt-dem-ui09-control-main">
<span class="material-symbols-outlined" aria-hidden="true">list_alt</span>
<div>
<p class="kt-dem-ui09-control-title mb-0">Approved scope</p>
<p class="kt-dem-ui09-control-detail mb-0" data-kt-dem-label="ov_ctrl_scope">—</p>
</div>
</div>
<button type="button" class="kt-dem-ui09-link" data-kt-dem-action="goto-tab" data-kt-dem-tab="scope" data-testid="kt-dem-ui09-goto-scope">View approved scope <span class="material-symbols-outlined text-[16px]" aria-hidden="true">arrow_forward</span></button>
</div>
<div class="kt-dem-ui09-control-row">
<div class="kt-dem-ui09-control-main">
<span class="material-symbols-outlined" aria-hidden="true">track_changes</span>
<div>
<p class="kt-dem-ui09-control-title mb-0">Strategy and value</p>
<p class="kt-dem-ui09-control-detail mb-0" data-kt-dem-label="ov_ctrl_strategy">—</p>
</div>
</div>
<button type="button" class="kt-dem-ui09-link" data-kt-dem-action="goto-tab" data-kt-dem-tab="strategy" data-testid="kt-dem-ui09-goto-strategy">View alignment <span class="material-symbols-outlined text-[16px]" aria-hidden="true">arrow_forward</span></button>
</div>
<div class="kt-dem-ui09-control-row">
<div class="kt-dem-ui09-control-main">
<span class="material-symbols-outlined" aria-hidden="true">fact_check</span>
<div>
<p class="kt-dem-ui09-control-title mb-0">Decisions</p>
<p class="kt-dem-ui09-control-detail mb-0" data-kt-dem-label="ov_ctrl_decisions">—</p>
</div>
</div>
<button type="button" class="kt-dem-ui09-link" data-kt-dem-action="goto-tab" data-kt-dem-tab="lifecycle" data-testid="kt-dem-ui09-goto-lifecycle">View lifecycle <span class="material-symbols-outlined text-[16px]" aria-hidden="true">arrow_forward</span></button>
</div>
</div>
</section>
</section>

<section class="kt-dem-ui09-panel hidden" data-kt-dem-detail-panel="scope" data-testid="kt-dem-ui09a-scope" hidden>
<section class="kt-dem-ui09-card">
<h2 class="kt-dem-ui09-card-title">1. Approved need</h2>
<div class="kt-dem-ui09-stack">
<div><span class="kt-dem-ui09-def-label">What is needed</span><p class="kt-dem-ui09-body mb-0" data-kt-dem-label="sc_what">—</p></div>
<div><span class="kt-dem-ui09-def-label">Why it is needed</span><p class="kt-dem-ui09-body mb-0" data-kt-dem-label="sc_why">—</p></div>
<div><span class="kt-dem-ui09-def-label">Expected outcome</span><p class="kt-dem-ui09-body mb-0" data-kt-dem-label="sc_outcome">—</p></div>
<div><span class="kt-dem-ui09-def-label">Beneficiaries</span><p class="kt-dem-ui09-body mb-0" data-kt-dem-label="sc_beneficiaries">—</p></div>
</div>
</section>
<section class="kt-dem-ui09-card">
<h2 class="kt-dem-ui09-card-title">2. Delivery and classification</h2>
<div class="kt-dem-ui09-def-grid kt-dem-ui09-def-grid--3">
<div><span class="kt-dem-ui09-def-label">Owning unit</span><span class="kt-dem-ui09-def-value" data-kt-dem-label="sc_owning_unit">—</span></div>
<div><span class="kt-dem-ui09-def-label">Required by</span><span class="kt-dem-ui09-def-value" data-kt-dem-label="sc_required_by">—</span></div>
<div><span class="kt-dem-ui09-def-label">Delivery location</span><span class="kt-dem-ui09-def-value" data-kt-dem-label="sc_delivery">—</span></div>
<div><span class="kt-dem-ui09-def-label">Route</span><span class="kt-dem-ui09-def-value" data-kt-dem-label="sc_route">—</span></div>
<div><span class="kt-dem-ui09-def-label">Procurement category</span><span class="kt-dem-ui09-def-value" data-kt-dem-label="sc_category">—</span></div>
<div><span class="kt-dem-ui09-def-label">Confirmed estimate</span><span class="kt-dem-ui09-def-value font-data-mono" data-kt-dem-label="sc_estimate">—</span></div>
<div class="kt-dem-ui09-def-span"><span class="kt-dem-ui09-def-label">Estimate basis</span><span class="kt-dem-ui09-def-value" data-kt-dem-label="sc_basis">—</span></div>
</div>
</section>
<section class="kt-dem-ui09-card">
<h2 class="kt-dem-ui09-card-title">3. Approved Need Items</h2>
<div class="kt-dem-ui09-table-wrap">
<table class="kt-dem-ui09-table" data-testid="kt-dem-ui09a-items">
<thead><tr><th>Item</th><th>Quantity</th><th>Unit</th><th>Approved estimate</th></tr></thead>
<tbody data-kt-dem-detail-items></tbody>
</table>
</div>
<p class="kt-dem-ui09-total font-data-mono mb-0">Total: <span data-kt-dem-label="sc_total">—</span></p>
</section>
</section>

<section class="kt-dem-ui09-panel hidden" data-kt-dem-detail-panel="strategy" data-testid="kt-dem-ui09b-strategy" hidden>
<section class="kt-dem-ui09-card">
<div class="kt-dem-ui09-card-head kt-dem-ui09-card-head--row">
<h2 class="kt-dem-ui09-card-title mb-0">1. Strategy alignment</h2>
<span class="kt-dem-ui09-confirmed-pill" data-kt-dem-label="st_confirmed">Confirmed at approval</span>
</div>
<div class="kt-dem-ui09-def-grid">
<div><span class="kt-dem-ui09-def-label">Plan</span><span class="kt-dem-ui09-def-value" data-kt-dem-label="st_plan">—</span></div>
<div><span class="kt-dem-ui09-def-label">Plan version</span><span class="kt-dem-ui09-def-value" data-kt-dem-label="st_version">—</span></div>
<div class="kt-dem-ui09-def-span"><span class="kt-dem-ui09-def-label">Outcome</span><span class="kt-dem-ui09-def-value" data-kt-dem-label="st_outcome">—</span></div>
<div class="kt-dem-ui09-def-span"><span class="kt-dem-ui09-def-label">Primary target</span><span class="kt-dem-ui09-def-value" data-kt-dem-label="st_primary">—</span></div>
<div class="kt-dem-ui09-def-span"><span class="kt-dem-ui09-def-label">Supporting target</span><span class="kt-dem-ui09-def-value" data-kt-dem-label="st_supporting">—</span></div>
<div class="kt-dem-ui09-def-span"><span class="kt-dem-ui09-def-label">Supporting reason</span><span class="kt-dem-ui09-def-value" data-kt-dem-label="st_reason">—</span></div>
</div>
</section>
<section class="kt-dem-ui09-card">
<h2 class="kt-dem-ui09-card-title">2. Public-value treatments</h2>
<div class="kt-dem-ui09-table-wrap">
<table class="kt-dem-ui09-table" data-testid="kt-dem-ui09b-pvc">
<thead><tr><th>Commitment</th><th>Approved treatment</th><th>Rationale</th></tr></thead>
<tbody data-kt-dem-detail-pvc></tbody>
</table>
</div>
<p class="kt-dem-ui09-note mb-0" data-kt-dem-label="st_disclaimer">Alignment records planned support for Strategy and public value. It does not prove that an outcome has been achieved.</p>
</section>
</section>

<section class="kt-dem-ui09-panel hidden" data-kt-dem-detail-panel="funding" data-testid="kt-dem-ui09c-funding" hidden>
<section class="kt-dem-ui09-card">
<h2 class="kt-dem-ui09-card-title">1. Confirmed allocation</h2>
<div class="kt-dem-ui09-def-grid">
<div class="kt-dem-ui09-def-span"><span class="kt-dem-ui09-def-label">Budget</span><span class="kt-dem-ui09-def-value" data-kt-dem-label="fu_budget">—</span></div>
<div class="kt-dem-ui09-def-span"><span class="kt-dem-ui09-def-label">Budget line</span><span class="kt-dem-ui09-def-value" data-kt-dem-label="fu_line">—</span></div>
<div><span class="kt-dem-ui09-def-label">Confirmed allocation</span><span class="kt-dem-ui09-def-value font-data-mono" data-kt-dem-label="fu_alloc">—</span></div>
<div><span class="kt-dem-ui09-def-label">Budget Officer</span><span class="kt-dem-ui09-def-value" data-kt-dem-label="fu_bo">—</span></div>
<div><span class="kt-dem-ui09-def-label">Confirmed on</span><span class="kt-dem-ui09-def-value" data-kt-dem-label="fu_date">—</span></div>
<div><span class="kt-dem-ui09-def-label">Strategy consistency</span><span class="kt-dem-ui09-def-value" data-kt-dem-label="fu_consistency">—</span></div>
</div>
</section>
<section class="kt-dem-ui09-card">
<h2 class="kt-dem-ui09-card-title">2. Reservation position</h2>
<div class="kt-dem-ui09-def-grid">
<div><span class="kt-dem-ui09-def-label">Reservation</span><span class="kt-dem-ui09-def-value font-data-mono" data-kt-dem-label="fu_rsv">—</span></div>
<div><span class="kt-dem-ui09-def-label">Condition</span><span class="kt-dem-ui09-def-value" data-kt-dem-label="fu_condition">—</span></div>
<div><span class="kt-dem-ui09-def-label">Original reservation</span><span class="kt-dem-ui09-def-value font-data-mono" data-kt-dem-label="fu_original">—</span></div>
<div><span class="kt-dem-ui09-def-label">Converted to commitment</span><span class="kt-dem-ui09-def-value font-data-mono" data-kt-dem-label="fu_converted">—</span></div>
<div><span class="kt-dem-ui09-def-label">Remaining reserved</span><span class="kt-dem-ui09-def-value font-data-mono" data-kt-dem-label="fu_remaining">—</span></div>
</div>
<p class="kt-dem-ui09-equation font-data-mono" data-kt-dem-label="fu_equation">—</p>
<p class="kt-dem-ui09-note mb-0" data-kt-dem-label="fu_note">The reservation identity carries forward through Planning and Tendering. Contract and downstream record details are shown under Lifecycle.</p>
</section>
</section>

<section class="kt-dem-ui09-panel hidden" data-kt-dem-detail-panel="lifecycle" data-testid="kt-dem-ui09d-lifecycle" hidden>
<section class="kt-dem-ui09-card">
<h2 class="kt-dem-ui09-card-title">1. Downstream usage</h2>
<div class="kt-dem-ui09-table-wrap">
<table class="kt-dem-ui09-table" data-testid="kt-dem-ui09d-downstream">
<thead><tr><th>Record</th><th>Value</th><th>Relationship</th><th>Status</th><th>Action</th></tr></thead>
<tbody data-kt-dem-detail-downstream></tbody>
</table>
</div>
<p class="kt-dem-ui09-empty hidden mb-0" data-kt-dem-detail-downstream-empty hidden>No downstream Planning records yet.</p>
</section>
<section class="kt-dem-ui09-card">
<h2 class="kt-dem-ui09-card-title">2. Decisions</h2>
<ol class="kt-dem-ui09-timeline" data-kt-dem-detail-decisions data-testid="kt-dem-ui09d-decisions"></ol>
</section>
<section class="kt-dem-ui09-card">
<div class="kt-dem-ui09-card-head kt-dem-ui09-card-head--row">
<h2 class="kt-dem-ui09-card-title mb-0">3. Audit history</h2>
<button type="button" class="kt-dem-ui09-link" data-kt-dem-action="open-audit" data-testid="kt-dem-ui09-view-audit">View full audit</button>
</div>
<div class="kt-dem-ui09-table-wrap">
<table class="kt-dem-ui09-table" data-testid="kt-dem-ui09d-audit">
<thead><tr><th>Date and time</th><th>Actor</th><th>Action</th><th>Reason or result</th></tr></thead>
<tbody data-kt-dem-detail-audit></tbody>
</table>
</div>
</section>
</section>

</div>

<div class="kt-dem-ui09-modal hidden" data-kt-dem-detail-audit-modal data-testid="kt-dem-ui09-audit-modal" hidden>
<div class="kt-dem-ui09-modal-backdrop" data-kt-dem-action="close-audit"></div>
<div class="kt-dem-ui09-modal-card" role="dialog" aria-modal="true" aria-labelledby="kt-dem-ui09-audit-title">
<div class="kt-dem-ui09-modal-head">
<h2 id="kt-dem-ui09-audit-title" class="kt-dem-ui09-card-title mb-0">Full audit</h2>
<button type="button" class="kt-dem-ui09-modal-close" data-kt-dem-action="close-audit" aria-label="Close">
<span class="material-symbols-outlined" aria-hidden="true">close</span>
</button>
</div>
<div class="kt-dem-ui09-table-wrap">
<table class="kt-dem-ui09-table">
<thead><tr><th>Date and time</th><th>Actor</th><th>Action</th><th>Reason or result</th></tr></thead>
<tbody data-kt-dem-detail-audit-full></tbody>
</table>
</div>
</div>
</div>
</div>`;
};
