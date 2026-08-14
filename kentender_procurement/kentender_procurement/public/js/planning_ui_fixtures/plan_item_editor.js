// PLN-UI-06 — literal structural port of docs/mvp-1/04_planning/ui_design/PLN-UI-06.html <main> + footer.
// Stitch utility classes retained. Only kt-stitch-canvas / testids / bind hooks added.
// In-canvas breadcrumbs omitted — Desk owns Home > … . Footer is canvas-scoped (not over Desk nav).
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_plan_item_editor = function () {
	return `<div class="kt-pln-root kt-stitch-canvas" data-testid="kt-pln-ui06-root" data-kt-pln-live="0">
<main class="flex-1 flex flex-col h-full min-h-0 overflow-hidden relative">
<div class="flex-1 min-h-0 overflow-y-auto w-full max-w-[1440px] mx-auto px-container-padding pt-8 pb-32 space-y-section-gap" data-kt-pln-editor-scroll>
<div class="space-y-4">
<div class="flex flex-col md:flex-row md:items-start justify-between gap-4">
<div>
<h1 class="font-headline-lg text-headline-lg text-on-surface mb-2" data-kt-pln-editor-title data-testid="kt-pln-ui06-title">National digital health infrastructure upgrade</h1>
<div class="flex flex-wrap items-center gap-3 text-on-surface-variant font-body-md">
<span data-kt-pln-editor-ou>Directorate of Digital Health and Policy</span>
<span class="w-1 h-1 rounded-full bg-outline-variant" data-kt-pln-editor-meta-sep aria-hidden="true"></span>
<span class="font-data-md text-data-md text-on-surface" data-kt-pln-editor-amount>KES 455,000,000</span>
</div>
<div class="mt-2 text-on-surface-variant font-body-sm" data-kt-pln-editor-version>Draft Plan Version 1</div>
<div class="mt-2 text-on-surface-variant font-body-sm hidden" data-kt-pln-editor-draft-banner hidden></div>
</div>
<div>
<span class="inline-flex items-center px-3 py-1 rounded-full bg-surface-container-high text-on-surface text-sm font-medium border border-border-subtle" data-kt-pln-editor-lifecycle data-testid="kt-pln-ui06-lifecycle">Proposed</span>
</div>
</div>
</div>
<div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
<div class="lg:col-span-8 space-y-section-gap">
<section class="bg-surface-container-lowest border border-border-subtle rounded-lg p-6 space-y-6">
<h2 class="font-headline-sm text-headline-sm text-on-surface border-b border-border-subtle pb-4">Procurement approach</h2>
<div class="space-y-6">
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase mb-2" for="kt-pln-ui06-description">Plan Item description</label>
<textarea class="w-full border-border-subtle rounded-md shadow-sm focus:border-secondary focus:ring focus:ring-secondary focus:ring-opacity-50 font-body-md p-3" id="kt-pln-ui06-description" name="requirement_description" data-kt-pln-field="requirement_description" data-kt-field="requirement_description" data-testid="kt-pln-ui06-description" rows="3">Comprehensive upgrade of national digital health network infrastructure, including secure data centers and regional health management systems.</textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="requirement_description" hidden></div>
</div>
<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase mb-2" for="kt-pln-ui06-category">Category <span class="text-error">*</span></label>
<div class="relative">
<select class="w-full border-border-subtle rounded-md shadow-sm focus:border-secondary focus:ring focus:ring-secondary focus:ring-opacity-50 font-body-md h-10 px-3 appearance-none pr-10" id="kt-pln-ui06-category" name="procurement_category" data-kt-pln-field="procurement_category" data-kt-field="procurement_category" data-testid="kt-pln-ui06-category">
<option value="ICT infrastructure and services" selected>ICT infrastructure and services</option>
<option value="Goods">Goods</option>
<option value="Works">Works</option>
<option value="Consulting Services">Consulting Services</option>
<option value="Training and professional services">Training and professional services</option>
</select>
<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-on-surface-variant">
<span class="material-symbols-outlined">expand_more</span>
</div>
</div>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="procurement_category" hidden></div>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase mb-2">Governing regime</label>
<div class="w-full bg-surface-container border border-border-subtle rounded-md shadow-sm font-body-md h-10 px-3 flex items-center text-on-surface-variant" data-kt-pln-editor-regime>PPADA</div>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase mb-2">Recommended method</label>
<div class="w-full bg-surface-container border border-border-subtle rounded-md shadow-sm font-body-md h-10 px-3 flex items-center text-on-surface-variant" data-kt-pln-editor-recommended-method>Open tender</div>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase mb-2" for="kt-pln-ui06-method">Confirmed method <span class="text-error">*</span></label>
<div class="relative">
<select class="w-full border-border-subtle rounded-md shadow-sm focus:border-secondary focus:ring focus:ring-secondary focus:ring-opacity-50 font-body-md h-10 px-3 appearance-none pr-10" id="kt-pln-ui06-method" name="procurement_method" data-kt-pln-field="procurement_method" data-kt-field="procurement_method" data-testid="kt-pln-ui06-method">
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
<div class="md:col-span-2">
<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase mb-2">Method basis</label>
<div class="w-full bg-surface-container border border-border-subtle rounded-md shadow-sm font-body-md p-3 text-on-surface-variant" data-kt-pln-editor-method-basis>Preferred competitive method under the applicable regime.</div>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase mb-2" for="kt-pln-ui06-arrangement">Arrangement <span class="text-error">*</span></label>
<div class="relative">
<select class="w-full border-border-subtle rounded-md shadow-sm focus:border-secondary focus:ring focus:ring-secondary focus:ring-opacity-50 font-body-md h-10 px-3 appearance-none pr-10" id="kt-pln-ui06-arrangement" name="arrangement" data-kt-pln-field="arrangement" data-kt-field="arrangement" data-testid="kt-pln-ui06-arrangement">
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
<div class="space-y-4 hidden" data-kt-pln-method-override hidden>
<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase mb-2" for="kt-pln-ui06-override-grounds">Override grounds</label>
<input id="kt-pln-ui06-override-grounds" class="w-full border-border-subtle rounded-md shadow-sm focus:border-secondary focus:ring focus:ring-secondary focus:ring-opacity-50 font-body-md h-10 px-3" type="text" name="method_override_grounds" data-kt-pln-field="method_override_grounds" data-kt-field="method_override_grounds"/>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="method_override_grounds" hidden></div>
<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase mb-2" for="kt-pln-ui06-override-reason">Override reason</label>
<textarea id="kt-pln-ui06-override-reason" class="w-full border-border-subtle rounded-md shadow-sm focus:border-secondary focus:ring focus:ring-secondary focus:ring-opacity-50 font-body-md p-3" rows="2" name="method_override_reason" data-kt-pln-field="method_override_reason" data-kt-field="method_override_reason"></textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="method_override_reason" hidden></div>
<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase mb-2" for="kt-pln-ui06-override-evidence">Override evidence</label>
<textarea id="kt-pln-ui06-override-evidence" class="w-full border-border-subtle rounded-md shadow-sm focus:border-secondary focus:ring focus:ring-secondary focus:ring-opacity-50 font-body-md p-3" rows="2" name="method_override_evidence" data-kt-pln-field="method_override_evidence" data-kt-field="method_override_evidence"></textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="method_override_evidence" hidden></div>
</div>
</div>
</section>
<section class="bg-surface-container-lowest border border-border-subtle rounded-lg p-6 space-y-6">
<div class="border-b border-border-subtle pb-4">
<h2 class="font-headline-sm text-headline-sm text-on-surface">Indicative lotting</h2>
<p class="font-body-sm text-on-surface-variant mt-1">Indicate whether the eventual Tender may contain lots. Detailed lots are configured during Tender preparation.</p>
</div>
<div class="space-y-6">
<div class="flex flex-col sm:flex-row gap-6">
<label class="flex items-center gap-2 cursor-pointer">
<input class="text-primary focus:ring-primary h-5 w-5 border-border-subtle" name="lotting_decision" type="radio" value="Single lot" data-kt-pln-field="lotting_decision" data-kt-field="lotting_decision" data-testid="kt-pln-ui06-lotting-single"/>
<span class="font-body-md text-on-surface">No lots expected</span>
</label>
<label class="flex items-center gap-2 cursor-pointer">
<input checked class="text-primary focus:ring-primary h-5 w-5 border-border-subtle" name="lotting_decision" type="radio" value="Multiple lots" data-kt-pln-field="lotting_decision" data-kt-field="lotting_decision" data-testid="kt-pln-ui06-lotting-multiple"/>
<span class="font-body-md text-on-surface">Indicative lots expected</span>
</label>
</div>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="lotting_decision" hidden></div>
<div class="grid grid-cols-1 md:grid-cols-2 gap-6 p-4 border border-border-subtle rounded-md bg-surface-bright" data-kt-pln-lotting-details data-testid="kt-pln-ui06-lotting-details">
<div>
<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase mb-2" for="kt-pln-ui06-lot-count">Expected lot count</label>
<input class="w-full border-border-subtle rounded-md shadow-sm focus:border-secondary focus:ring focus:ring-secondary focus:ring-opacity-50 font-body-md h-10 px-3 max-w-[150px]" id="kt-pln-ui06-lot-count" name="expected_lot_count" data-kt-pln-field="expected_lot_count" data-kt-field="expected_lot_count" data-testid="kt-pln-ui06-lot-count" type="number" min="2"/>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="expected_lot_count" hidden></div>
</div>
<div class="md:col-span-2">
<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase mb-2" for="kt-pln-ui06-lot-basis">Indicative lot basis</label>
<textarea class="w-full border-border-subtle rounded-md shadow-sm focus:border-secondary focus:ring focus:ring-secondary focus:ring-opacity-50 font-body-md p-3" id="kt-pln-ui06-lot-basis" name="lot_basis" data-kt-pln-field="lot_basis" data-kt-field="lot_basis" data-testid="kt-pln-ui06-lot-basis" rows="2"></textarea>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="lot_basis" hidden></div>
</div>
</div>
</div>
</section>
<section class="bg-surface-container-lowest border border-border-subtle rounded-lg overflow-hidden">
<div class="p-6 border-b border-border-subtle">
<h2 class="font-headline-sm text-headline-sm text-on-surface">Planned schedule</h2>
</div>
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse">
<thead>
<tr class="bg-surface-container-low border-b border-border-subtle">
<th class="py-3 px-6 font-label-caps text-label-caps text-on-surface-variant uppercase font-semibold w-1/2">Milestone</th>
<th class="py-3 px-6 font-label-caps text-label-caps text-on-surface-variant uppercase font-semibold w-1/2">Planned date</th>
</tr>
</thead>
<tbody class="divide-y divide-border-subtle bg-surface-container-lowest font-body-sm text-on-surface">
<tr class="hover:bg-surface-bright transition-colors">
<td class="py-3 px-6 flex items-center gap-3">
<span class="material-symbols-outlined text-on-surface-variant">campaign</span>
                                        Invitation published
                                    </td>
<td class="py-3 px-6">
<input class="border-border-subtle rounded-md shadow-sm focus:border-secondary focus:ring focus:ring-secondary focus:ring-opacity-50 h-9 px-3 w-40 text-sm" type="date" name="ms_invitation_published" data-kt-pln-field="ms_invitation_published" data-kt-field="ms_invitation_published" data-testid="kt-pln-ui06-ms_invitation_published"/>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="ms_invitation_published" hidden></div>
</td>
</tr>
<tr class="hover:bg-surface-bright transition-colors">
<td class="py-3 px-6 flex items-center gap-3">
<span class="material-symbols-outlined text-on-surface-variant">lock_open</span>
                                        Tender opening
                                    </td>
<td class="py-3 px-6">
<input class="border-border-subtle rounded-md shadow-sm focus:border-secondary focus:ring focus:ring-secondary focus:ring-opacity-50 h-9 px-3 w-40 text-sm" type="date" name="ms_tender_opening" data-kt-pln-field="ms_tender_opening" data-kt-field="ms_tender_opening" data-testid="kt-pln-ui06-ms_tender_opening"/>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="ms_tender_opening" hidden></div>
</td>
</tr>
<tr class="hover:bg-surface-bright transition-colors">
<td class="py-3 px-6 flex items-center gap-3">
<span class="material-symbols-outlined text-on-surface-variant">fact_check</span>
                                        Evaluation completed
                                    </td>
<td class="py-3 px-6">
<input class="border-border-subtle rounded-md shadow-sm focus:border-secondary focus:ring focus:ring-secondary focus:ring-opacity-50 h-9 px-3 w-40 text-sm" type="date" name="ms_evaluation_completed" data-kt-pln-field="ms_evaluation_completed" data-kt-field="ms_evaluation_completed" data-testid="kt-pln-ui06-ms_evaluation_completed"/>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="ms_evaluation_completed" hidden></div>
</td>
</tr>
<tr class="hover:bg-surface-bright transition-colors">
<td class="py-3 px-6 flex items-center gap-3">
<span class="material-symbols-outlined text-on-surface-variant">gavel</span>
                                        Award approval
                                    </td>
<td class="py-3 px-6">
<input class="border-border-subtle rounded-md shadow-sm focus:border-secondary focus:ring focus:ring-secondary focus:ring-opacity-50 h-9 px-3 w-40 text-sm" type="date" name="ms_award_approval" data-kt-pln-field="ms_award_approval" data-kt-field="ms_award_approval" data-testid="kt-pln-ui06-ms_award_approval"/>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="ms_award_approval" hidden></div>
</td>
</tr>
<tr class="hover:bg-surface-bright transition-colors">
<td class="py-3 px-6 flex items-center gap-3">
<span class="material-symbols-outlined text-on-surface-variant">edit_document</span>
                                        Contract signature
                                    </td>
<td class="py-3 px-6">
<input class="border-border-subtle rounded-md shadow-sm focus:border-secondary focus:ring focus:ring-secondary focus:ring-opacity-50 h-9 px-3 w-40 text-sm" type="date" name="ms_contract_signature" data-kt-pln-field="ms_contract_signature" data-kt-field="ms_contract_signature" data-testid="kt-pln-ui06-ms_contract_signature"/>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="ms_contract_signature" hidden></div>
</td>
</tr>
<tr class="hover:bg-surface-bright transition-colors">
<td class="py-3 px-6 flex items-center gap-3">
<span class="material-symbols-outlined text-on-surface-variant">check_circle</span>
                                        Delivery and completion
                                    </td>
<td class="py-3 px-6">
<input class="border-border-subtle rounded-md shadow-sm focus:border-secondary focus:ring focus:ring-secondary focus:ring-opacity-50 h-9 px-3 w-40 text-sm" type="date" name="ms_delivery_completion" data-kt-pln-field="ms_delivery_completion" data-kt-field="ms_delivery_completion" data-testid="kt-pln-ui06-ms_delivery_completion"/>
<div class="font-body-sm text-body-sm text-status-exhausted mt-1" data-kt-field-error="ms_delivery_completion" hidden></div>
</td>
</tr>
</tbody>
</table>
</div>
</section>
<div class="bg-error-container/20 border-l-4 border-error p-4 rounded-r-md flex gap-3 items-start hidden" data-kt-pln-editor-issue data-testid="kt-pln-ui06-issue" hidden>
<span class="material-symbols-outlined text-error shrink-0">error</span>
<div>
<h4 class="font-headline-sm text-[16px] font-semibold text-error mb-1">Needs attention</h4>
<p class="font-body-sm text-body-sm text-on-surface-variant" data-kt-pln-editor-issue-copy data-kt-field-error="form">Confirm all milestone dates before requesting Finance confirmation.</p>
</div>
</div>
</div>
<div class="lg:col-span-4">
<section class="bg-surface-container-lowest border border-border-subtle rounded-lg p-6 space-y-6 sticky top-20 self-start" data-kt-pln-source-sidebar data-testid="kt-pln-ui06-source-sidebar">
<div class="flex flex-col gap-4 border-b border-border-subtle pb-4" data-kt-pln-single-source>
<div class="flex flex-col gap-4">
<h2 class="font-headline-sm text-headline-sm text-on-surface" data-kt-pln-source-heading>Approved source</h2>
<div class="flex flex-col xl:flex-row gap-2 xl:gap-4">
<a class="text-primary font-body-sm hover:underline flex items-center gap-1" href="#" data-kt-pln-action="view-demand" data-testid="kt-pln-ui06-view-demand">
<span class="material-symbols-outlined text-sm">visibility</span> View Approved Demand
                            </a>
<button type="button" class="text-primary font-body-sm hover:underline flex items-center gap-1 bg-transparent border-0 p-0 cursor-pointer" data-kt-pln-action="view-source" data-testid="kt-pln-ui06-view-source">
<span class="material-symbols-outlined text-sm">account_tree</span> View source breakdown
                            </button>
</div>
</div>
<div class="flex flex-col gap-y-6">
<div>
<div class="font-label-caps text-label-caps text-on-surface-variant uppercase mb-1">Demand</div>
<div class="font-body-md text-on-surface" data-kt-pln-source-demand data-testid="kt-pln-ui06-source-demand">National digital health infrastructure upgrade</div>
</div>
<div>
<div class="font-label-caps text-label-caps text-on-surface-variant uppercase mb-1">Need Items</div>
<div class="font-body-md text-on-surface" data-kt-pln-source-need-count>2</div>
</div>
<div>
<div class="font-label-caps text-label-caps text-on-surface-variant uppercase mb-1">Approved value</div>
<div class="font-data-md text-data-md text-on-surface" data-kt-pln-source-approved-value>KES 455,000,000</div>
</div>
<div>
<div class="font-label-caps text-label-caps text-on-surface-variant uppercase mb-1">Owner</div>
<div class="font-body-md text-on-surface" data-kt-pln-source-owner>Directorate of Digital Health and Policy</div>
</div>
<div>
<div class="font-label-caps text-label-caps text-on-surface-variant uppercase mb-1">Proposed Budget Line</div>
<div class="font-body-md text-on-surface flex items-center gap-2">
<span class="w-1 h-6 bg-primary rounded-full block"></span>
<span data-kt-pln-source-funding-line>Digital clinical systems infrastructure</span>
</div>
</div>
<div>
<div class="font-label-caps text-label-caps text-on-surface-variant uppercase mb-1">Finance confirmation</div>
<div class="font-body-md text-on-surface text-status-reserved" data-kt-pln-source-finance>Not requested</div>
</div>
<div>
<div class="font-label-caps text-label-caps text-on-surface-variant uppercase mb-1">Strategy target</div>
<div class="font-body-md text-on-surface bg-surface-bright p-3 border border-border-subtle rounded-md" data-kt-pln-source-strategy data-testid="kt-pln-ui06-strategy-context">At least 99.9% annual availability by 30 June 2028</div>
</div>
</div>
</div>
<div class="flex flex-col gap-4 hidden" data-kt-pln-combined-sources hidden>
<h2 class="font-headline-sm text-headline-sm text-on-surface">Approved sources</h2>
<div class="flex flex-col gap-y-6" data-kt-pln-combined-rows></div>
<div>
<div class="font-label-caps text-label-caps text-on-surface-variant uppercase mb-1">Combined total</div>
<div class="font-data-md text-data-md text-on-surface" data-kt-pln-combined-total></div>
</div>
<div>
<div class="font-label-caps text-label-caps text-on-surface-variant uppercase mb-1">Reason for combining</div>
<div class="font-body-md text-on-surface" data-kt-pln-formation-reason></div>
</div>
<div>
<div class="font-label-caps text-label-caps text-on-surface-variant uppercase mb-1">Finance confirmation</div>
<div class="font-body-md text-on-surface text-status-reserved" data-kt-pln-source-finance-combined>Not requested</div>
</div>
</div>
<div class="bg-surface-container-low p-4 rounded-md border-l-4 border-outline flex gap-3 mt-4">
<span class="material-symbols-outlined text-on-surface-variant">info</span>
<p class="font-body-sm text-body-sm text-on-surface-variant">Business scope, quantity, owner, delivery requirement and approved value come from the Approved Demand source(s) and cannot be changed here. Amend those facts on the Demand in Demands (HoD reapproval).</p>
</div>
</section>
</div>
</div>
</div>
<div class="absolute bottom-0 left-0 right-0 bg-surface-container-lowest border-t border-border-subtle p-4 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-40" data-testid="kt-pln-ui06-footer">
<div class="max-w-[1440px] mx-auto flex flex-row justify-between items-center gap-4 px-container-padding">
<button class="px-6 py-2.5 border border-border-subtle text-primary font-headline-sm text-sm rounded-md hover:bg-surface-container-low transition-colors bg-surface-container-lowest shadow-sm text-center whitespace-nowrap" type="button" data-kt-pln-action="cancel" data-testid="kt-pln-ui06-cancel">
                Cancel
            </button>
<div class="flex flex-row gap-3">
<button class="px-6 py-2.5 border border-border-subtle text-primary font-headline-sm text-sm rounded-md hover:bg-surface-container-low transition-colors bg-surface-container-lowest shadow-sm text-center whitespace-nowrap" type="button" data-kt-pln-action="save-draft" data-testid="kt-pln-ui06-save-draft">
                    Save draft
                </button>
<button class="px-6 py-2.5 bg-primary text-on-primary font-headline-sm text-sm rounded-md hover:bg-primary-container hover:text-on-primary-container transition-colors shadow-sm text-center flex justify-center items-center gap-2 whitespace-nowrap" type="button" data-kt-pln-action="request-finance" data-testid="kt-pln-ui06-request-finance">
<span class="material-symbols-outlined text-sm">send</span> Save and request Finance confirmation
                </button>
</div>
</div>
</div>
</main>
</div>`;
};
