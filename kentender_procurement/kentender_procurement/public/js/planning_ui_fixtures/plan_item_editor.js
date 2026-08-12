// PLN-UI-06 — literal structural port of docs/mvp-1/04_planning/ui_design/PLN-UI-06.html <main> + sticky footer.
// Stitch utility classes retained. Only kt-stitch-canvas / testids / bind hooks / Pack v1.3 conditional slots added.
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_plan_item_editor = function () {
	return `<div class="kt-pln-root kt-stitch-canvas" data-testid="kt-pln-ui06-root" data-kt-pln-live="0">
<div class="flex-1 flex w-full max-w-7xl mx-auto">
<main class="flex-1 w-full px-container-padding md:px-section-gap py-section-gap pb-32">
<!-- Page Header (Stitch: status chip above title) -->
<div class="mb-section-gap">
<div class="flex flex-col md:flex-row md:items-start justify-between gap-4">
<div>
<div class="mb-2">
<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-status-reserved/10 text-status-reserved border border-status-reserved/20" data-kt-pln-editor-lifecycle data-testid="kt-pln-ui06-lifecycle">Proposed</span>
</div>
<h1 class="font-headline-lg text-headline-lg text-on-surface mb-2" data-kt-pln-editor-title data-testid="kt-pln-ui06-title">Digital health technical staff certification programme</h1>
<div class="flex items-center gap-3 text-body-md font-body-md text-on-surface-variant">
<span class="" data-kt-pln-editor-ou>Human Resources Management and Development</span>
<span class="inline-block w-1 h-1 rounded-full bg-outline-variant shrink-0" data-kt-pln-editor-meta-sep aria-hidden="true"></span>
<span class="font-data-md text-data-md text-on-surface" data-kt-pln-editor-amount>KES 80,000,000</span>
</div>
<div class="mt-stack-sm flex items-center gap-2 bg-surface-container-low px-4 py-2 border-l-4 border-outline rounded-r-lg">
<span class="material-symbols-outlined text-outline text-sm" aria-hidden="true">info</span>
<span class="font-body-sm text-body-sm text-on-surface-variant italic" data-kt-pln-editor-draft-banner>Draft Plan update · The current Approved Plan remains active.</span>
</div>
</div>
</div>
</div>
<div class="grid grid-cols-1 lg:grid-cols-12 gap-section-gap">
<!-- Left Column (Wider for main form) -->
<div class="lg:col-span-8 flex flex-col gap-section-gap">
<!-- Planning Approach Block -->
<div class="bg-surface-container-lowest border border-subtle rounded-lg p-container-padding flex flex-col gap-section-gap">
<div class="border-b border-subtle pb-stack-sm mb-stack-xs">
<h2 class="font-headline-md text-headline-md text-on-surface">Planning approach</h2>
</div>
<div class="flex flex-col gap-stack-sm">
<label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-ui06-description">Plan Item description</label>
<textarea class="w-full border-subtle rounded focus:border-secondary focus:ring-1 focus:ring-secondary font-body-md text-body-md text-on-surface bg-surface-container-lowest resize-y" id="kt-pln-ui06-description" name="requirement_description" data-kt-pln-field="requirement_description" data-kt-field="requirement_description" data-testid="kt-pln-ui06-description" rows="3">Comprehensive certification programme for national digital health technical staff covering system administration, data security, and specialized health informatics tools. Requires accredited providers.</textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="requirement_description" hidden></div>
</div>
<div class="grid grid-cols-1 md:grid-cols-2 gap-section-gap">
<div class="flex flex-col gap-stack-sm">
<label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-ui06-category">Category</label>
<div class="relative">
<select class="w-full border-subtle rounded focus:border-secondary focus:ring-1 focus:ring-secondary font-body-md text-body-md text-on-surface bg-surface-container-lowest appearance-none pr-10" id="kt-pln-ui06-category" name="procurement_category" data-kt-pln-field="procurement_category" data-kt-field="procurement_category" data-testid="kt-pln-ui06-category">
<option value="ICT infrastructure and services">ICT infrastructure and services</option>
<option value="Goods">Goods</option>
<option value="Works">Works</option>
<option value="Consulting Services">Consulting Services</option>
<option value="Training and professional services" selected>Training and professional services</option>
</select>
<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-on-surface-variant">
<span class="material-symbols-outlined">expand_more</span>
</div>
</div>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="procurement_category" hidden></div>

</div>
<div class="flex flex-col gap-stack-sm">
<label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-ui06-arrangement">Arrangement</label>
<div class="relative">
<select id="kt-pln-ui06-arrangement" class="w-full border-subtle rounded focus:border-secondary focus:ring-1 focus:ring-secondary font-body-md text-body-md text-on-surface bg-surface-container-lowest appearance-none pr-10" name="arrangement" data-kt-pln-field="arrangement" data-kt-field="arrangement" data-testid="kt-pln-ui06-arrangement">
<option value="Single year" selected>Single year</option>
<option value="Multi-year">Multi-year</option>
</select>
<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-on-surface-variant">
<span class="material-symbols-outlined">expand_more</span>
</div>
</div>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="arrangement" hidden></div>

</div>
</div>
<div class="flex flex-col gap-stack-sm hidden" data-kt-pln-multi-year hidden>
<label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-ui06-multi-year-justification">Multi-year justification</label>
<textarea id="kt-pln-ui06-multi-year-justification" class="w-full border-subtle rounded focus:border-secondary focus:ring-1 focus:ring-secondary font-body-md text-body-md text-on-surface bg-surface-container-lowest resize-y" rows="2" name="multi_year_justification" data-kt-pln-field="multi_year_justification" data-kt-field="multi_year_justification"></textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="multi_year_justification" hidden></div>
<label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-ui06-annual-funding">Annual funding schedule</label>
<textarea id="kt-pln-ui06-annual-funding" class="w-full border-subtle rounded focus:border-secondary focus:ring-1 focus:ring-secondary font-body-md text-body-md text-on-surface bg-surface-container-lowest resize-y" rows="2" name="annual_funding_schedule" data-kt-pln-field="annual_funding_schedule" data-kt-field="annual_funding_schedule"></textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="annual_funding_schedule" hidden></div>
</div>
<div class="p-container-padding bg-surface-container-low rounded-lg border border-subtle flex flex-col gap-section-gap">
<div class="grid grid-cols-1 md:grid-cols-2 gap-section-gap">
<div class="flex flex-col gap-stack-sm">
<span class="font-label-caps text-label-caps text-on-surface-variant flex items-center gap-1">
                                        Governing regime
                                        <span class="material-symbols-outlined text-[14px] text-outline cursor-help" title="Derived from the applicable legal and funding context.">help</span>
</span>
<div class="font-body-md text-body-md text-on-surface bg-surface-container-highest px-3 py-2 rounded border border-transparent cursor-not-allowed text-on-surface-variant" data-kt-pln-editor-regime>PPADA</div>
<span class="font-body-sm text-body-sm text-outline">Derived from the applicable legal and funding context.</span>
</div>
<div class="flex flex-col gap-stack-sm">
<span class="font-label-caps text-label-caps text-on-surface-variant">Recommended method</span>
<div class="font-body-md text-body-md text-on-surface bg-surface-container-highest px-3 py-2 rounded border border-transparent cursor-not-allowed text-on-surface-variant" data-kt-pln-editor-recommended-method>Open tender</div>
</div>
</div>
<div class="grid grid-cols-1 md:grid-cols-2 gap-section-gap items-start">
<div class="flex flex-col gap-stack-sm">
<label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-ui06-method">Confirmed method</label>
<div class="relative">
<select id="kt-pln-ui06-method" class="w-full border-subtle rounded focus:border-secondary focus:ring-1 focus:ring-secondary font-body-md text-body-md text-on-surface bg-surface-container-lowest appearance-none pr-10" name="procurement_method" data-kt-pln-field="procurement_method" data-kt-field="procurement_method" data-testid="kt-pln-ui06-method">
<option value="Open tender" selected>Open tender</option>
<option value="Restricted tender">Restricted tender</option>
<option value="Request for quotations">Request for quotations</option>
<option value="Direct procurement">Direct procurement</option>
</select>
<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-on-surface-variant">
<span class="material-symbols-outlined">expand_more</span>
</div>
</div>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="procurement_method" hidden></div>

</div>
<div class="flex flex-col gap-stack-sm pt-8">
<div class="flex items-start gap-2">
<span class="material-symbols-outlined text-primary text-sm mt-0.5">check_circle</span>
<span class="font-body-sm text-body-sm text-on-surface-variant" data-kt-pln-editor-method-basis>Preferred competitive method under the applicable regime.</span>
</div>
</div>
</div>

<div class="flex flex-col gap-stack-sm hidden" data-kt-pln-method-override hidden>
<label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-ui06-override-grounds">Override grounds</label>
<input id="kt-pln-ui06-override-grounds" class="w-full border-subtle rounded focus:border-secondary focus:ring-1 focus:ring-secondary font-body-md text-body-md text-on-surface bg-surface-container-lowest" type="text" name="method_override_grounds" data-kt-pln-field="method_override_grounds" data-kt-field="method_override_grounds"/>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="method_override_grounds" hidden></div>
<label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-ui06-override-reason">Override reason</label>
<textarea id="kt-pln-ui06-override-reason" class="w-full border-subtle rounded focus:border-secondary focus:ring-1 focus:ring-secondary font-body-md text-body-md text-on-surface bg-surface-container-lowest resize-y" rows="2" name="method_override_reason" data-kt-pln-field="method_override_reason" data-kt-field="method_override_reason"></textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="method_override_reason" hidden></div>
<label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-ui06-override-evidence">Override evidence</label>
<textarea id="kt-pln-ui06-override-evidence" class="w-full border-subtle rounded focus:border-secondary focus:ring-1 focus:ring-secondary font-body-md text-body-md text-on-surface bg-surface-container-lowest resize-y" rows="2" name="method_override_evidence" data-kt-pln-field="method_override_evidence" data-kt-field="method_override_evidence"></textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="method_override_evidence" hidden></div>
</div>
</div>
<div class="flex flex-col gap-stack-sm border-t border-subtle pt-section-gap">
<span class="font-label-caps text-label-caps text-on-surface-variant">Indicative lotting</span>
<div class="flex flex-col md:flex-row gap-gutter-md mt-stack-xs">
<label class="flex items-center gap-2 cursor-pointer group">
<input checked class="text-secondary focus:ring-secondary border-outline" name="lotting_decision" type="radio" value="Single lot" data-kt-pln-field="lotting_decision" data-kt-field="lotting_decision" data-testid="kt-pln-ui06-lotting-single"/>
<span class="font-body-md text-body-md text-on-surface group-hover:text-primary transition-colors">No lots expected</span>
</label>
<label class="flex items-center gap-2 cursor-pointer group">
<input class="text-secondary focus:ring-secondary border-outline" name="lotting_decision" type="radio" value="Multiple lots" data-kt-pln-field="lotting_decision" data-kt-field="lotting_decision" data-testid="kt-pln-ui06-lotting-multiple"/>
<span class="font-body-md text-body-md text-on-surface group-hover:text-primary transition-colors">Expected to be lotted</span>
</label>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="lotting_decision" hidden></div>
</div>
<div class="flex flex-col gap-stack-sm mt-stack-sm hidden" data-kt-pln-lotting-details data-testid="kt-pln-ui06-lotting-details" hidden>
<div class="flex flex-col gap-stack-sm max-w-48">
    <label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-ui06-lot-count">Expected lot count (optional)</label>
    <input type="number" id="kt-pln-ui06-lot-count" name="expected_lot_count" data-kt-pln-field="expected_lot_count" data-kt-field="expected_lot_count" data-testid="kt-pln-ui06-lot-count" placeholder="e.g. 5" class="w-full border-subtle rounded focus:border-secondary focus:ring-1 focus:ring-secondary font-body-md text-body-md text-on-surface bg-surface-container-lowest" min="1">
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="expected_lot_count" hidden></div>
</div>
<div class="flex flex-col gap-stack-sm">
    <label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-ui06-lot-basis">Indicative lot basis</label>
    <textarea class="w-full border-subtle rounded focus:border-secondary focus:ring-1 focus:ring-secondary font-body-md text-body-md text-on-surface bg-surface-container-lowest resize-y" id="kt-pln-ui06-lot-basis" name="lot_basis" data-kt-pln-field="lot_basis" data-kt-field="lot_basis" data-testid="kt-pln-ui06-lot-basis" rows="2" placeholder="Describe the basis for lotting (e.g. by region, by technical domain)"></textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="lot_basis" hidden></div>
</div>
<p class="font-body-sm text-body-sm text-outline mt-1 max-w-2xl">This indicates whether the eventual tender may contain lots. Detailed lots are configured during tender preparation.</p>
</div>
</div>
</div>
<!-- Planned Schedule Block -->
<div class="bg-surface-container-lowest border border-subtle rounded-lg p-container-padding flex flex-col gap-section-gap">
<div class="border-b border-subtle pb-stack-sm mb-stack-xs flex justify-between items-end">
<h2 class="font-headline-md text-headline-md text-on-surface">Planned schedule</h2>
</div>
<div class="bg-primary-fixed-dim/20 px-4 py-3 rounded border border-primary-fixed-dim/30 flex items-start gap-3">
<span class="material-symbols-outlined text-primary mt-0.5">lightbulb</span>
<p class="font-body-sm text-body-sm text-on-surface-variant">Dates were proposed from the confirmed method and target completion. Changed dates require a planning reason.</p>
</div>
<div class="flex flex-col gap-stack-sm hidden" data-kt-pln-schedule-reason hidden>
<label class="font-label-caps text-label-caps text-on-surface-variant" for="kt-pln-ui06-schedule-reason">Schedule change reason</label>
<textarea id="kt-pln-ui06-schedule-reason" class="w-full border-subtle rounded focus:border-secondary focus:ring-1 focus:ring-secondary font-body-md text-body-md text-on-surface bg-surface-container-lowest resize-y" rows="2" name="schedule_change_reason" data-kt-pln-field="schedule_change_reason" data-kt-field="schedule_change_reason"></textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="schedule_change_reason" hidden></div>
</div>
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse">
<thead>
<tr class="border-b-2 border-subtle text-on-surface-variant font-label-caps text-label-caps">
<th class="py-2 pl-2">Milestone</th>
<th class="py-2 pr-2 w-48">Planned date</th>
</tr>
</thead>
<tbody class="font-body-md text-body-md">
<tr class="border-b border-surface-variant table-row-hover transition-colors">
<td class="py-3 pl-2 flex items-center gap-2">
<div class="w-2 h-2 rounded-full bg-outline"></div>
                                            Invitation
                                        </td>
<td class="py-2 pr-2">
<input class="w-full border-subtle rounded py-1 px-2 text-sm focus:border-secondary focus:ring-1 focus:ring-secondary" type="date" value="2027-12-01" name="ms_invitation_published" data-kt-pln-field="ms_invitation_published" data-kt-field="ms_invitation_published" data-testid="kt-pln-ui06-ms_invitation_published">
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="ms_invitation_published" hidden></div>
</td>
</tr>
<tr class="border-b border-surface-variant table-row-hover transition-colors">
<td class="py-3 pl-2 flex items-center gap-2">
<div class="w-2 h-2 rounded-full bg-outline"></div>
                                            Tender opening
                                        </td>
<td class="py-2 pr-2">
<input class="w-full border-subtle rounded py-1 px-2 text-sm focus:border-secondary focus:ring-1 focus:ring-secondary" type="date" value="2028-01-12" name="ms_tender_opening" data-kt-pln-field="ms_tender_opening" data-kt-field="ms_tender_opening" data-testid="kt-pln-ui06-ms_tender_opening">
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="ms_tender_opening" hidden></div>
</td>
</tr>
<tr class="border-b border-surface-variant table-row-hover transition-colors">
<td class="py-3 pl-2 flex items-center gap-2">
<div class="w-2 h-2 rounded-full bg-outline"></div>
                                            Evaluation
                                        </td>
<td class="py-2 pr-2">
<input class="w-full border-subtle rounded py-1 px-2 text-sm focus:border-secondary focus:ring-1 focus:ring-secondary" type="date" value="2028-01-31" name="ms_evaluation_completed" data-kt-pln-field="ms_evaluation_completed" data-kt-field="ms_evaluation_completed" data-testid="kt-pln-ui06-ms_evaluation_completed">
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="ms_evaluation_completed" hidden></div>
</td>
</tr>
<tr class="border-b border-surface-variant table-row-hover transition-colors">
<td class="py-3 pl-2 flex items-center gap-2">
<div class="w-2 h-2 rounded-full bg-outline"></div>
                                            Award
                                        </td>
<td class="py-2 pr-2">
<input class="w-full border-subtle rounded py-1 px-2 text-sm focus:border-secondary focus:ring-1 focus:ring-secondary" type="date" value="2028-02-15" name="ms_award_approval" data-kt-pln-field="ms_award_approval" data-kt-field="ms_award_approval" data-testid="kt-pln-ui06-ms_award_approval">
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="ms_award_approval" hidden></div>
</td>
</tr>
<tr class="border-b border-surface-variant table-row-hover transition-colors">
<td class="py-3 pl-2 flex items-center gap-2">
<div class="w-2 h-2 rounded-full bg-outline"></div>
                                            Contract
                                        </td>
<td class="py-2 pr-2">
<input class="w-full border-subtle rounded py-1 px-2 text-sm focus:border-secondary focus:ring-1 focus:ring-secondary" type="date" value="2028-03-01" name="ms_contract_signature" data-kt-pln-field="ms_contract_signature" data-kt-field="ms_contract_signature" data-testid="kt-pln-ui06-ms_contract_signature">
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="ms_contract_signature" hidden></div>
</td>
</tr>
<tr class="table-row-hover transition-colors">
<td class="py-3 pl-2 flex items-center gap-2">
<div class="w-2 h-2 rounded-full bg-status-available"></div>
<span class="font-medium text-on-surface">Delivery / Completion</span>
</td>
<td class="py-2 pr-2">
<input class="w-full border-subtle rounded py-1 px-2 text-sm focus:border-secondary focus:ring-1 focus:ring-secondary" type="date" value="2028-03-31" name="ms_delivery_completion" data-kt-pln-field="ms_delivery_completion" data-kt-field="ms_delivery_completion" data-testid="kt-pln-ui06-ms_delivery_completion">
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="ms_delivery_completion" hidden></div>
</td>
</tr>
</tbody>
</table>
</div>
</div>
<div class="bg-error-container/20 border-l-4 border-error p-4 rounded-r-md flex gap-3 items-start hidden" data-kt-pln-editor-issue data-testid="kt-pln-ui06-issue" hidden>
<span class="material-symbols-outlined text-error shrink-0">error</span>
<div>
<h4 class="font-headline-sm text-[16px] font-semibold text-error mb-1">Needs attention</h4>
<p class="font-body-sm text-body-sm text-on-surface-variant" data-kt-pln-editor-issue-copy>Confirm all milestone dates before submit for review.</p>
</div>
</div></div>
<!-- Right Column (Context & Metadata) -->
<div class="lg:col-span-4 flex flex-col gap-section-gap lg:sticky lg:top-8 self-start" data-kt-pln-source-sidebar data-testid="kt-pln-ui06-source-sidebar">
<!-- Source Demand Panel (Compact Read-Only) -->
<div class="bg-surface-bright border border-subtle rounded-lg overflow-hidden flex flex-col shadow-sm">
<div class="bg-surface-container-low px-container-padding py-3 border-b border-subtle flex items-center justify-between">
<h3 class="font-headline-sm text-headline-sm text-on-surface">Source Demand</h3>
<span class="material-symbols-outlined text-outline">source</span>
</div>
<div class="p-container-padding flex flex-col gap-4 font-body-sm">
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant block mb-1">Demand</span>
<span class="text-on-surface font-medium block leading-tight" data-kt-pln-source-demand data-testid="kt-pln-ui06-source-demand">Digital health technical staff certification programme</span>
<span class="font-data-md text-[13px] text-on-surface-variant tracking-tight block mt-1" data-kt-pln-source-demand-code></span>
</div>
<div class="grid grid-cols-2 gap-4">
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant block mb-1">Need Items</span>
<span class="font-data-md text-on-surface block" data-kt-pln-source-need-count>2</span>
</div>
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant block mb-1">Owner</span>
<span class="text-on-surface block" data-kt-pln-source-owner>Human Resources Mgt &amp; Dev</span>
</div>
</div>
<div class="p-3 bg-tertiary-fixed/30 rounded border border-tertiary-fixed-dim/50">
<span class="font-label-caps text-label-caps text-tertiary block mb-1">Approved &amp; reserved value</span>
<span class="font-data-lg text-data-lg text-on-surface block" data-kt-pln-source-reserved-value>KES 80,000,000</span>
</div>
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant block mb-1">Funding</span>
<div class="flex items-center gap-2" data-kt-pln-source-funding-row>
<span class="text-on-surface" data-kt-pln-source-funding-line>Digital health workforce dev</span>
<span class="w-1.5 h-1.5 rounded-full bg-status-reserved" data-kt-pln-source-funding-dot></span>
<span class="text-status-reserved font-medium text-xs" data-kt-pln-source-funding>Reserved</span>
</div>
<p class="font-body-sm text-body-sm text-on-surface-variant mt-2" data-kt-pln-editor-source-allocation data-testid="kt-pln-ui06-source-allocation">1 Approved Demand · 2 Need Items · KES 80,000,000</p>
</div>
<div>
<span class="block text-on-surface-variant font-label-caps text-label-caps mb-1">Strategy Context</span>
<span class="text-on-surface italic text-on-surface-variant" data-kt-pln-source-strategy data-testid="kt-pln-ui06-strategy-context">Strengthen capability to operate and support national digital health services</span>
</div>
<div class="border-t border-subtle pt-4 mt-2 flex flex-col gap-2">
<a class="text-secondary hover:text-primary transition-colors flex items-center gap-1 font-medium" href="#" data-kt-pln-action="view-demand" data-testid="kt-pln-ui06-view-demand">
<span class="material-symbols-outlined text-[16px]" aria-hidden="true">visibility</span>
                                    View approved Demand
                                </a>
<button type="button" class="text-secondary hover:text-primary transition-colors flex items-center gap-1 font-medium bg-transparent border-0 p-0 text-left cursor-pointer" data-kt-pln-action="view-source" data-testid="kt-pln-ui06-view-source">
<span class="material-symbols-outlined text-[16px]" aria-hidden="true">account_tree</span>
                                    View source breakdown
                                </button>
<button type="button" class="text-secondary hover:text-primary transition-colors flex items-center gap-1 font-medium bg-transparent border-0 p-0 text-left cursor-pointer" data-kt-pln-action="add-another-demand" data-testid="kt-pln-ui06-add-another">
<span class="material-symbols-outlined text-[16px]" aria-hidden="true">add_link</span>
                                    Add another approved Demand to this Plan Item
                                </button>
</div>
</div>
</div>
<!-- Bottom Issue -->
<div class="bg-error-container/20 border-l-4 border-error rounded-r-lg p-4 flex gap-3 items-start hidden" data-kt-pln-editor-issue-aside hidden>
<span class="material-symbols-outlined text-error mt-0.5" aria-hidden="true">warning</span>
<div>
<span class="font-label-caps text-label-caps text-error block mb-1">Needs attention</span>
<span class="font-body-sm text-body-sm text-on-surface" data-kt-pln-editor-issue-copy>Confirm all milestone dates before submit for review.</span>
</div>
</div>
</div>
</div>
</main>
<!-- Sticky Footer Actions -->
<div class="fixed bottom-0 left-0 right-0 bg-surface-container-lowest border-t border-subtle px-section-gap py-4 flex justify-between items-center z-40 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]" data-testid="kt-pln-ui06-footer">
<button type="button" class="px-4 py-2 font-body-md font-medium text-status-exhausted hover:bg-error-container/20 rounded transition-colors bg-transparent border-0 cursor-pointer" data-kt-pln-action="cancel" data-testid="kt-pln-ui06-cancel">
            Cancel
        </button>
<div class="flex gap-gutter-md">
<button type="button" class="px-6 py-2 border border-subtle font-body-md font-medium text-primary hover:bg-surface-container-low rounded transition-colors bg-surface-container-lowest cursor-pointer" data-kt-pln-action="save-draft" data-testid="kt-pln-ui06-save-draft">
                Save draft
            </button>
<button type="button" class="px-6 py-2 bg-primary font-body-md font-medium text-on-primary hover:opacity-90 rounded transition-opacity shadow-sm border-0 cursor-pointer" data-kt-pln-action="save-return" data-testid="kt-pln-ui06-save-return">
                Save and return to Plan update
            </button>
</div>
</div>
</div>
<div data-kt-pln-dialog-host></div>
</div>`;
};
