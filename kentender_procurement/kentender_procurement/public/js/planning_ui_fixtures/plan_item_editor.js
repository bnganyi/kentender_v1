// PLN-UI-06 — literal Stitch <main> + sticky footer from docs/mvp-1/04_planning/ui_design/PLN-UI-06.html
// Fake top/side nav discarded; kt-stitch-canvas + testids/bind hooks only.
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_plan_item_editor = function () {
	return `<div class="kt-pln-root kt-stitch-canvas" data-testid="kt-pln-ui06-root">
<main class="flex-1 overflow-y-auto relative pb-24">
<div class="max-w-5xl mx-auto px-container-padding py-section-gap">
<header class="mb-section-gap">
<nav aria-label="Breadcrumb" class="flex text-body-sm text-on-surface-variant mb-4">
<ol class="inline-flex items-center space-x-1 md:space-x-2">
<li class="inline-flex items-center">
<a class="hover:text-primary transition-colors" href="/app/planning-workspace">Procurement Planning</a>
</li>
<li>
<div class="flex items-center">
<span class="material-symbols-outlined text-sm mx-1" aria-hidden="true">chevron_right</span>
<a class="hover:text-primary transition-colors" href="#" data-kt-pln-editor-plan-crumb>2027/28 Plan</a>
</div>
</li>
<li aria-current="page">
<div class="flex items-center">
<span class="material-symbols-outlined text-sm mx-1" aria-hidden="true">chevron_right</span>
<span class="text-on-surface font-medium truncate max-w-xs" data-kt-pln-editor-title-crumb>National digital health infrastructure upgrade</span>
</div>
</li>
</ol>
</nav>
<div class="flex flex-col md:items-start gap-4">
<div>
<div class="flex items-center gap-2 mb-3">
<span class="inline-flex items-center px-2.5 py-1 rounded-full font-label-caps text-[11px] font-bold tracking-wider bg-surface-variant text-on-surface-variant border border-outline-variant/30 shadow-sm" data-kt-pln-editor-lifecycle>
DRAFT
</span>
<span class="inline-flex items-center px-2.5 py-1 rounded-full font-label-caps text-[11px] font-bold tracking-wider bg-status-reserved/10 text-status-reserved border border-status-reserved/20 shadow-sm" data-kt-pln-editor-validation-chip>
<span class="material-symbols-outlined text-[14px] mr-1" aria-hidden="true">warning</span>
NEEDS ATTENTION
</span>
</div>
<h1 class="font-headline-lg text-[24px] md:text-[30px] font-bold text-on-surface leading-tight tracking-tight mb-2" data-kt-pln-editor-title>
National digital health infrastructure upgrade
</h1>
<div class="flex flex-wrap items-center gap-x-2 gap-y-1 font-body-md text-on-surface-variant">
<span data-kt-pln-editor-ou>Directorate of Digital Health and Policy</span>
<span class="text-subtle">·</span>
<span class="font-data-md font-medium text-on-surface" data-kt-pln-editor-amount>KES 455,000,000</span>
</div>
</div>
</div>
</header>
<div class="bg-status-reserved/10 border border-status-reserved/20 rounded-lg p-4 flex gap-3 items-start shadow-sm mb-6" data-kt-pln-editor-issue>
<span class="material-symbols-outlined text-status-reserved filled mt-0.5" aria-hidden="true">warning</span>
<div>
<h4 class="font-body-sm font-bold text-on-surface mb-1">Needs attention</h4>
<p class="font-body-sm text-on-surface-variant leading-snug" data-kt-pln-editor-issue-copy>Confirm the indicative lot basis before departmental sign-off.</p>
</div>
</div>
<div class="grid grid-cols-1 lg:grid-cols-12 gap-section-gap">
<div class="lg:col-span-8 space-y-section-gap">
<section class="bg-surface-container-lowest rounded-lg border border-subtle p-container-padding md:p-6 shadow-sm">
<h2 class="font-label-caps text-on-surface-variant mb-6 pb-2 border-b border-subtle flex items-center gap-2">
<span class="material-symbols-outlined text-[18px]" aria-hidden="true">architecture</span>
Planning approach
</h2>
<div class="space-y-6">
<div>
<label class="block font-label-caps text-on-surface-variant mb-2" for="kt-pln-ui06-description">Plan Item description</label>
<textarea id="kt-pln-ui06-description" class="flat-input resize-y min-h-[100px] p-3 w-full" name="requirement_description" data-kt-pln-field="requirement_description" data-kt-field="requirement_description">Comprehensive upgrade of national digital health network infrastructure, including secure data centers, interoperable facility networks, and standardized hardware provisioning for regional health management teams.</textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="requirement_description" hidden></div>
</div>
<div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
<div>
<label class="block font-label-caps text-on-surface-variant mb-2" for="kt-pln-ui06-category">Category</label>
<div class="relative">
<select id="kt-pln-ui06-category" class="flat-input appearance-none py-2.5 pl-3 pr-10 bg-white" name="procurement_category" data-kt-pln-field="procurement_category" data-kt-field="procurement_category">
<option selected="" value="ICT infrastructure and services">ICT infrastructure and services</option>
<option value="Goods">Goods</option>
<option value="Works">Works</option>
<option value="Consulting Services">Consulting Services</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-on-surface-variant" aria-hidden="true">arrow_drop_down</span>
</div>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="procurement_category" hidden></div>
</div>
<div>
<label class="block font-label-caps text-on-surface-variant mb-1">Governing regime</label>
<div class="px-3 py-2.5 bg-surface-container-low rounded border border-transparent text-body-md text-on-surface-variant flex items-center gap-2" data-kt-pln-editor-regime>
<span class="material-symbols-outlined text-[18px]" aria-hidden="true">gavel</span>
PPADA
</div>
<p class="text-[12px] text-on-surface-variant mt-1">Derived from the applicable legal and funding context.</p>
</div>
<div>
<label class="block font-label-caps text-on-surface-variant mb-2">Recommended method</label>
<div class="px-3 py-2.5 bg-surface-container-low rounded border border-transparent text-body-md text-on-surface-variant" data-kt-pln-editor-recommended-method>
Open tender
</div>
</div>
<div>
<label class="block font-label-caps text-on-surface-variant mb-2" for="kt-pln-ui06-method">Confirmed method</label>
<div class="relative">
<select id="kt-pln-ui06-method" class="flat-input appearance-none py-2.5 pl-3 pr-10 bg-white" name="procurement_method" data-kt-pln-field="procurement_method" data-kt-field="procurement_method" required="">
<option value="Open tender">Open tender</option>
<option value="Restricted tender">Restricted tender</option>
<option value="Direct procurement">Direct procurement</option>
<option value="Request for quotations">Request for quotations</option>
<option value="Framework agreement">Framework agreement</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-on-surface-variant" aria-hidden="true">arrow_drop_down</span>
</div>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="procurement_method" hidden></div>
</div>
<div class="md:col-span-2">
<label class="block font-label-caps text-on-surface-variant mb-2">Method basis</label>
<div class="px-3 py-2.5 bg-surface-container-low rounded border border-transparent text-body-sm text-on-surface-variant leading-snug" data-kt-pln-editor-method-basis>
Preferred competitive method under the applicable regime.
</div>
</div>
<div class="md:col-span-2 hidden" data-kt-pln-method-override>
<label class="block font-label-caps text-on-surface-variant mb-2" for="kt-pln-ui06-override-grounds">Override grounds</label>
<input id="kt-pln-ui06-override-grounds" class="flat-input py-2.5 px-3 w-full" type="text" name="method_override_grounds" data-kt-pln-field="method_override_grounds" data-kt-field="method_override_grounds"/>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="method_override_grounds" hidden></div>
<label class="block font-label-caps text-on-surface-variant mb-2 mt-4" for="kt-pln-ui06-override-reason">Override reason</label>
<textarea id="kt-pln-ui06-override-reason" class="flat-input resize-y min-h-[60px] p-3 w-full" name="method_override_reason" data-kt-pln-field="method_override_reason" data-kt-field="method_override_reason"></textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="method_override_reason" hidden></div>
<label class="block font-label-caps text-on-surface-variant mb-2 mt-4" for="kt-pln-ui06-override-evidence">Override evidence</label>
<textarea id="kt-pln-ui06-override-evidence" class="flat-input resize-y min-h-[60px] p-3 w-full" name="method_override_evidence" data-kt-pln-field="method_override_evidence" data-kt-field="method_override_evidence"></textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="method_override_evidence" hidden></div>
</div>
<div>
<label class="block font-label-caps text-on-surface-variant mb-2" for="kt-pln-ui06-arrangement">Arrangement</label>
<div class="relative">
<select id="kt-pln-ui06-arrangement" class="flat-input appearance-none py-2.5 pl-3 pr-10 bg-white" name="arrangement" data-kt-pln-field="arrangement" data-kt-field="arrangement" required="">
<option selected="" value="Single year">Single year</option>
<option value="Multi-year">Multi-year</option>
<option value="Framework">Framework agreement</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-on-surface-variant" aria-hidden="true">arrow_drop_down</span>
</div>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="arrangement" hidden></div>
</div>
<div class="md:col-span-2 hidden" data-kt-pln-multi-year>
<label class="block font-label-caps text-on-surface-variant mb-2" for="kt-pln-ui06-multi-year-just">Multi-year justification</label>
<textarea id="kt-pln-ui06-multi-year-just" class="flat-input resize-y min-h-[60px] p-3 w-full" name="multi_year_justification" data-kt-pln-field="multi_year_justification" data-kt-field="multi_year_justification"></textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="multi_year_justification" hidden></div>
<label class="block font-label-caps text-on-surface-variant mb-2 mt-4" for="kt-pln-ui06-funding-schedule">Annual funding schedule</label>
<textarea id="kt-pln-ui06-funding-schedule" class="flat-input resize-y min-h-[60px] p-3 w-full" name="annual_funding_schedule" data-kt-pln-field="annual_funding_schedule" data-kt-field="annual_funding_schedule"></textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="annual_funding_schedule" hidden></div>
</div>
</div>
<div class="mt-8 pt-6 border-t border-subtle space-y-6">
<h3 class="font-label-caps text-on-surface-variant mb-4 pb-2 border-b border-subtle">Source allocation and indicative lotting</h3>
<div>
<label class="block font-label-caps text-on-surface-variant mb-2">Source allocation</label>
<div class="flex items-center gap-4 flex-wrap">
<div class="px-3 py-2.5 bg-surface-container-low rounded border border-transparent text-body-sm text-on-surface-variant leading-snug flex-1" data-kt-pln-editor-source-allocation data-testid="kt-pln-ui06-source-allocation">
1 Approved Demand · 2 Need Items · KES 455,000,000
</div>
<button type="button" class="text-primary text-body-sm font-medium hover:underline" data-kt-pln-action="view-source">View source breakdown</button>
</div>
<button type="button" class="mt-3 text-primary font-label-caps text-[11px] hover:underline hidden" data-kt-pln-action="add-another-demand" data-testid="kt-pln-ui06-add-another" hidden>
Add another approved Demand to this Plan Item
</button>
</div>
<div>
<label class="block font-label-caps text-on-surface-variant mb-2">Indicative lotting decision</label>
<div class="flex gap-4">
<label class="flex items-center gap-2 cursor-pointer">
<input checked="" class="text-primary focus:ring-primary" name="lotting_decision" type="radio" value="Multiple lots" data-kt-pln-field="lotting_decision" data-kt-field="lotting_decision"/>
<span class="text-body-md text-on-surface">Indicative lots expected</span>
</label>
<label class="flex items-center gap-2 cursor-pointer">
<input class="text-primary focus:ring-primary" name="lotting_decision" type="radio" value="Single lot" data-kt-pln-field="lotting_decision" data-kt-field="lotting_decision"/>
<span class="text-body-md text-on-surface">No lots expected</span>
</label>
</div>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="lotting_decision" hidden></div>
</div>
<div>
<label class="block font-label-caps text-on-surface-variant mb-2" for="kt-pln-ui06-lot-count">Expected lot count</label>
<input id="kt-pln-ui06-lot-count" class="flat-input py-2.5 px-3 max-w-[150px]" type="number" name="expected_lot_count" data-kt-pln-field="expected_lot_count" data-kt-field="expected_lot_count"/>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="expected_lot_count" hidden></div>
</div>
<div>
<label class="block font-label-caps text-on-surface-variant mb-2 flex items-center gap-1" for="kt-pln-ui06-lot-basis">
Indicative lot basis
<span class="material-symbols-outlined text-[14px] text-status-reserved" title="Needs attention" aria-hidden="true">warning</span>
</label>
<textarea id="kt-pln-ui06-lot-basis" class="flat-input resize-y min-h-[80px] p-3 w-full border-status-reserved/50 focus:border-status-reserved focus:ring-status-reserved bg-status-reserved/5" name="lot_basis" data-kt-pln-field="lot_basis" data-kt-field="lot_basis">Infrastructure supply, installation and support components.</textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="lot_basis" hidden></div>
</div>
</div>
</div>
</section>
<section class="bg-surface-container-lowest rounded-lg border border-subtle p-container-padding md:p-6 shadow-sm">
<h2 class="font-label-caps text-on-surface-variant mb-6 pb-2 border-b border-subtle flex items-center gap-2">
<span class="material-symbols-outlined text-[18px]" aria-hidden="true">verified_user</span>
Statutory and strategy treatment
</h2>
<div class="space-y-6">
<div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
<div class="md:col-span-2">
<label class="block font-label-caps text-on-surface-variant mb-2" for="kt-pln-ui06-statutory">Statutory allocation treatment</label>
<div class="relative">
<select id="kt-pln-ui06-statutory" class="flat-input appearance-none py-2.5 pl-3 pr-10 bg-white" name="statutory_treatment" data-kt-pln-field="statutory_treatment" data-kt-field="statutory_treatment">
<option selected="" value="Reserved">Contributes through indicative reserved lot(s)</option>
<option value="Preferential">Direct allocation</option>
<option value="Open competition">No contribution</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-on-surface-variant" aria-hidden="true">arrow_drop_down</span>
</div>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="statutory_treatment" hidden></div>
</div>
<div class="md:col-span-2">
<label class="block font-label-caps text-on-surface-variant mb-2" for="kt-pln-ui06-target-groups">Target group</label>
<div class="relative">
<select id="kt-pln-ui06-target-groups" class="flat-input appearance-none py-2.5 pl-3 pr-10 bg-white" name="statutory_target_groups" data-kt-pln-field="statutory_target_groups" data-kt-field="statutory_target_groups" multiple="" size="3" style="height: auto;">
<option selected="" value="Women">Women</option>
<option selected="" value="Youth">Youth</option>
<option selected="" value="Persons with disabilities">Persons with disabilities</option>
<option value="Local enterprises">Local enterprises</option>
</select>
<span class="material-symbols-outlined absolute right-3 top-3 pointer-events-none text-on-surface-variant" aria-hidden="true">arrow_drop_down</span>
</div>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="statutory_target_groups" hidden></div>
</div>
<div>
<label class="block font-label-caps text-on-surface-variant mb-2" for="kt-pln-ui06-treatment-value">Planned treatment value</label>
<div class="relative">
<span class="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant font-data-md">KES</span>
<input id="kt-pln-ui06-treatment-value" class="flat-input py-2.5 pl-12 pr-3 font-data-md" type="text" name="planned_treatment_value" data-kt-pln-field="planned_treatment_value" data-kt-field="planned_treatment_value" value="136,500,000"/>
</div>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="planned_treatment_value" hidden></div>
</div>
<div>
<label class="block font-label-caps text-on-surface-variant mb-1">Plan-level coverage</label>
<div class="px-3 py-2.5 bg-surface-container-low rounded border border-transparent text-body-sm text-on-surface-variant" data-kt-pln-editor-coverage>
KES 136,500,000 planned of KES 136,500,000 currently required
</div>
<p class="text-[12px] text-on-surface-variant mt-1">The required value is calculated from the current statutory rule and Plan total. Users do not enter the percentage.</p>
</div>
</div>
<div class="border-l-4 border-status-available pl-4 py-1">
<label class="block font-label-caps text-on-surface-variant mb-1">Strategy context</label>
<p class="font-body-md text-on-surface mb-2" data-kt-pln-editor-strategy-target>At least 99.9% annual availability by 30 June 2028</p>
<ul class="text-body-sm text-on-surface-variant list-disc pl-4 space-y-1" data-kt-pln-editor-strategy-commitments>
<li>Improve availability of critical health services</li>
<li>Reduce whole-life infrastructure cost</li>
<li>Improve continuity of critical services</li>
<li>Ensure compliant handling of replaced ICT equipment</li>
</ul>
</div>
<div>
<label class="block font-label-caps text-on-surface-variant mb-2" for="kt-pln-ui06-value-note">Value treatment note</label>
<textarea id="kt-pln-ui06-value-note" class="flat-input resize-none h-[80px] p-3 text-body-sm w-full" name="value_treatment_note" data-kt-pln-field="value_treatment_note" data-kt-field="value_treatment_note">Carry requirements into specifications, evaluation and contract performance measures.</textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="value_treatment_note" hidden></div>
</div>
</div>
</section>
</div>
<div class="lg:col-span-4 space-y-section-gap">
<aside class="bg-surface-container-lowest rounded-lg border border-subtle p-5 shadow-sm">
<h2 class="font-label-caps text-on-surface-variant mb-4 pb-2 border-b border-subtle flex items-center gap-2">
<span class="material-symbols-outlined text-[18px]" aria-hidden="true">source</span>
Approved source
</h2>
<ul class="space-y-4">
<li>
<span class="block font-label-caps text-on-surface-variant mb-0.5">Demand</span>
<span class="block font-body-sm text-on-surface font-medium leading-tight" data-kt-pln-editor-source-demand>National digital health infrastructure upgrade</span>
</li>
<li>
<span class="block font-label-caps text-on-surface-variant mb-0.5">Funding</span>
<div class="flex items-center gap-2 mt-1">
<span class="block font-body-sm text-on-surface" data-kt-pln-editor-source-funding>Digital clinical systems infrastructure · KES 455,000,000 reserved</span>
</div>
</li>
<li>
<span class="block font-label-caps text-on-surface-variant mb-0.5">Primary Strategy target</span>
<span class="block font-body-sm text-on-surface leading-tight" data-kt-pln-editor-source-primary>At least 99.9% annual availability by 30 June 2028</span>
</li>
<li>
<span class="block font-label-caps text-on-surface-variant mb-0.5">Supporting Strategy target</span>
<span class="block font-body-sm text-on-surface leading-tight" data-kt-pln-editor-source-supporting>Restore critical services within four hours by 30 June 2028</span>
</li>
<li>
<span class="block font-label-caps text-on-surface-variant mb-0.5">Owner</span>
<span class="block font-body-sm text-on-surface" data-kt-pln-editor-source-owner>Directorate of Digital Health and Policy</span>
</li>
</ul>
<div class="mt-5 pt-4 border-t border-subtle">
<a class="inline-flex items-center text-primary font-body-sm font-medium hover:underline group" href="#" data-kt-pln-action="view-demand">
View approved Demand
<span class="material-symbols-outlined text-[16px] ml-1 group-hover:translate-x-1 transition-transform" aria-hidden="true">arrow_forward</span>
</a>
</div>
</aside>
<aside class="bg-surface-container-lowest rounded-lg border border-subtle overflow-hidden shadow-sm">
<div class="p-5 pb-3">
<h2 class="font-label-caps text-on-surface-variant flex items-center gap-2">
<span class="material-symbols-outlined text-[18px]" aria-hidden="true">event_note</span>
Planned schedule
</h2>
<p class="text-[12px] text-on-surface-variant mt-2 leading-tight">Dates were proposed from the confirmed method and target completion. Changed dates require a planning reason.</p>
</div>
<div class="overflow-x-auto p-4 pt-0">
<table class="w-full text-left border-collapse">
<thead>
<tr class="border-y border-subtle bg-surface">
<th class="px-3 py-2 font-label-caps text-on-surface-variant font-medium">Milestone</th>
<th class="px-3 py-2 font-label-caps text-on-surface-variant font-medium text-right w-[150px]">Planned date</th>
</tr>
</thead>
<tbody class="font-body-sm text-on-surface divide-y divide-subtle/50">
<tr class="hover:bg-surface-container-low transition-colors">
<td class="px-3 py-2.5">Invitation published</td>
<td class="px-3 py-2.5"><input class="flat-input py-1 px-2 text-[13px] font-data-md" type="date" name="ms_invitation_published" data-kt-pln-field="ms_invitation_published" data-kt-field="ms_invitation_published" value="2027-09-15"/><div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="ms_invitation_published" hidden></div></td>
</tr>
<tr class="hover:bg-surface-container-low transition-colors">
<td class="px-3 py-2.5">Tender opening</td>
<td class="px-3 py-2.5"><input class="flat-input py-1 px-2 text-[13px] font-data-md" type="date" name="ms_tender_opening" data-kt-pln-field="ms_tender_opening" data-kt-field="ms_tender_opening" value="2027-10-20"/><div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="ms_tender_opening" hidden></div></td>
</tr>
<tr class="hover:bg-surface-container-low transition-colors">
<td class="px-3 py-2.5">Evaluation completed</td>
<td class="px-3 py-2.5"><input class="flat-input py-1 px-2 text-[13px] font-data-md" type="date" name="ms_evaluation_completed" data-kt-pln-field="ms_evaluation_completed" data-kt-field="ms_evaluation_completed" value="2027-11-15"/><div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="ms_evaluation_completed" hidden></div></td>
</tr>
<tr class="hover:bg-surface-container-low transition-colors">
<td class="px-3 py-2.5">Award approval</td>
<td class="px-3 py-2.5"><input class="flat-input py-1 px-2 text-[13px] font-data-md" type="date" name="ms_award_approval" data-kt-pln-field="ms_award_approval" data-kt-field="ms_award_approval" value="2027-12-15"/><div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="ms_award_approval" hidden></div></td>
</tr>
<tr class="hover:bg-surface-container-low transition-colors">
<td class="px-3 py-2.5">Contract signature</td>
<td class="px-3 py-2.5"><input class="flat-input py-1 px-2 text-[13px] font-data-md" type="date" name="ms_contract_signature" data-kt-pln-field="ms_contract_signature" data-kt-field="ms_contract_signature" value="2028-01-15"/><div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="ms_contract_signature" hidden></div></td>
</tr>
<tr class="hover:bg-surface-container-low transition-colors">
<td class="px-3 py-2.5">Delivery and completion</td>
<td class="px-3 py-2.5"><input class="flat-input py-1 px-2 text-[13px] font-data-md" type="date" name="ms_delivery_completion" data-kt-pln-field="ms_delivery_completion" data-kt-field="ms_delivery_completion" value="2028-03-31"/><div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="ms_delivery_completion" hidden></div></td>
</tr>
</tbody>
</table>
</div>
<div class="hidden" aria-hidden="true">
<textarea name="schedule_change_reason" data-kt-pln-field="schedule_change_reason" data-kt-field="schedule_change_reason"></textarea>
<div data-kt-field-error="schedule_change_reason" hidden></div>
</div>
</aside>
</div>
</div>
</div>
<div class="h-24 md:h-20 w-full"></div>
</main>
<div class="fixed bottom-0 left-0 lg:left-64 right-0 bg-surface-container-lowest border-t border-subtle shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-40 px-container-padding py-4 transition-all duration-200" data-testid="kt-pln-ui06-footer">
<div class="max-w-5xl mx-auto flex flex-col-reverse sm:flex-row justify-between items-center gap-4">
<button type="button" class="w-full sm:w-auto px-4 py-2 text-status-exhausted font-body-md font-medium rounded hover:bg-status-exhausted/10 transition-colors" data-kt-pln-action="cancel">
Cancel
</button>
<div class="flex flex-col sm:flex-row w-full sm:w-auto gap-3">
<button type="button" class="w-full sm:w-auto px-6 py-2 border border-primary text-primary font-body-md font-medium rounded hover:bg-primary/5 transition-colors" data-kt-pln-action="save-draft" data-testid="kt-pln-ui06-save-draft">
Save draft
</button>
<button type="button" class="w-full sm:w-auto px-6 py-2 bg-primary text-on-primary font-body-md font-medium rounded hover:bg-on-primary-fixed-variant transition-colors shadow-sm shadow-primary/30" data-kt-pln-action="save-return" data-testid="kt-pln-ui06-save-return">
Save and return to plan
</button>
</div>
</div>
</div>
</div>`;
};
