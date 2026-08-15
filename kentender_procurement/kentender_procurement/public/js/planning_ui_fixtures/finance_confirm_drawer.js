// PLN-UI-07 / 07A — literal Stitch right-side Finance drawer (sufficient + shortfall).
// Source: docs/mvp-1/04_planning/ui_design/PLN-UI-07.html, PLN-UI-07A.html
frappe.provide("kentender_procurement.ui_fixtures");

kentender_procurement.ui_fixtures.planning_finance_confirm_drawer = function () {
	return `<div class="absolute inset-0 z-[200] hidden kt-stitch-canvas" data-testid="kt-pln-ui07-drawer" data-kt-pln-finance-drawer hidden>
<div class="relative z-50 flex justify-end w-full h-full">
<div class="flex-1 min-w-0 h-full bg-inverse-surface/40 backdrop-blur-sm" data-kt-pln-action="close-finance" data-testid="kt-pln-ui07-backdrop"></div>
<div class="w-full max-w-2xl bg-surface-container-lowest h-full shadow-2xl flex flex-col z-50 border-l border-border-subtle shrink-0" data-testid="kt-pln-ui07-panel">
<div class="flex flex-col h-full min-h-0" data-kt-pln-07-variant="sufficient" data-testid="kt-pln-ui07-sufficient">
<header class="flex items-center justify-between px-container-padding py-stack-sm border-b border-border-subtle bg-surface-container-lowest">
<h2 class="font-headline-md text-headline-md text-on-surface" data-testid="kt-pln-ui07-title">Confirm Plan Item funding</h2>
<button type="button" aria-label="Close drawer" class="p-2 rounded-full hover:bg-surface-container transition-colors text-on-surface-variant flex items-center justify-center group" data-kt-pln-action="close-finance" data-testid="kt-pln-ui07-close">
<span class="material-symbols-outlined text-[24px] group-hover:text-on-surface">close</span>
</button>
</header>
<main class="flex-1 overflow-y-auto p-container-padding space-y-section-gap">
<section class="bg-surface-container-lowest border border-border-subtle rounded p-container-padding space-y-stack-sm relative before:absolute before:left-0 before:top-0 before:bottom-0 before:w-1 before:bg-primary-container before:rounded-l">
<div class="flex justify-between items-start mb-2">
<h3 class="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider">Plan Item Context</h3>
<span class="font-data-md text-data-md text-on-surface-variant text-sm bg-surface-container px-2 py-0.5 rounded whitespace-normal" data-kt-pln-07-code>PPI-MOH-2027-021</span>
</div>
<div class="space-y-4">
<div>
<p class="font-headline-sm text-headline-sm text-on-surface mb-1 whitespace-normal" data-kt-pln-07-title>National digital health infrastructure upgrade</p>
<p class="font-body-sm text-body-sm text-on-surface-variant whitespace-normal" data-kt-pln-07-plan>Ministry of Health Annual Procurement Plan 2027/28 · Draft Version 1</p>
</div>
<div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pt-2 border-t border-border-subtle border-dashed">
<div>
<p class="font-label-caps text-label-caps text-outline mb-1 uppercase tracking-wider">Owner OU</p>
<p class="font-body-md text-body-md text-on-surface whitespace-normal" data-kt-pln-07-ou>Directorate of Digital Health and Policy</p>
</div>
<div>
<p class="font-label-caps text-label-caps text-outline mb-1 uppercase tracking-wider">Plan Item status</p>
<div class="inline-flex items-center px-2 py-1 rounded-full bg-primary-fixed text-on-primary-fixed border border-primary-fixed-dim font-body-sm text-body-sm">
<span class="w-1.5 h-1.5 rounded-full bg-primary mr-1.5"></span>
<span data-kt-pln-07-status>Proposed · Planning complete</span>
</div>
</div>
</div>
</div>
</section>
<section class="space-y-stack-sm">
<h3 class="font-headline-sm text-headline-sm text-on-surface border-b border-border-subtle pb-2 mb-4">Funding to confirm</h3>
<div class="space-y-2 mb-4" data-kt-pln-07-sources></div>
<div class="grid grid-cols-1 md:grid-cols-2 gap-container-padding">
<div class="space-y-1">
<p class="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider">Source Demand</p>
<p class="font-body-md text-body-md text-on-surface whitespace-normal" data-kt-pln-07-demand>National digital health infrastructure upgrade</p>
</div>
<div class="space-y-1">
<p class="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider">Proposed Budget Line</p>
<p class="font-body-md text-body-md text-on-surface whitespace-normal" data-kt-pln-07-line>Digital clinical systems infrastructure</p>
</div>
</div>
<div class="bg-surface-bright border border-border-subtle rounded p-container-padding mt-4 grid grid-cols-1 sm:grid-cols-3 gap-container-padding divide-y sm:divide-y-0 sm:divide-x divide-border-subtle" data-testid="kt-pln-ui07-money">
<div class="sm:pr-4 py-2 sm:py-0 flex flex-col justify-center">
<p class="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider mb-2">Amount to reserve</p>
<p class="font-data-lg text-data-lg text-primary tracking-tight whitespace-normal" data-kt-pln-07-amount>KES 455,000,000</p>
</div>
<div class="sm:px-4 py-2 sm:py-0 flex flex-col justify-center">
<p class="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider mb-2">Available allocation</p>
<p class="font-data-md text-data-md text-on-surface whitespace-normal" data-kt-pln-07-available>KES 480,000,000</p>
</div>
<div class="sm:pl-4 py-2 sm:py-0 flex flex-col justify-center">
<div class="flex items-center gap-2 mb-2">
<p class="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider">Derived balance</p>
<span class="inline-flex items-center gap-1 text-status-available font-body-sm text-[12px] bg-status-available/10 px-1.5 py-0.5 rounded">
<span class="material-symbols-outlined text-[14px]">check_circle</span> Sufficient
</span>
</div>
<p class="font-data-md text-data-md text-on-surface whitespace-normal" data-kt-pln-07-balance>KES 25,000,000</p>
</div>
</div>
<div class="flex items-start gap-3 bg-surface-container-low border border-border-subtle rounded p-3 mt-4 text-on-surface-variant">
<span class="material-symbols-outlined text-outline mt-0.5">info</span>
<p class="font-body-sm text-body-sm">Confirming funding records the Finance decision and reserves this amount for the Plan Item.</p>
</div>
</section>
<section class="space-y-2 mt-section-gap">
<label class="font-label-caps text-label-caps text-on-surface uppercase tracking-wider block" for="kt-pln-ui07-note">Decision note</label>
<textarea class="w-full bg-surface-container-lowest border border-border-subtle rounded p-3 font-body-md text-body-md text-on-surface focus:border-secondary focus:ring-1 focus:ring-secondary focus:outline-none transition-shadow resize-none" id="kt-pln-ui07-note" data-kt-field="reason" placeholder="Enter any relevant notes or conditions..." rows="3"></textarea>
<p class="hidden font-body-sm text-body-sm text-error mt-stack-xs" data-kt-field-error="reason" hidden></p>
<p class="font-body-sm text-body-sm text-outline">Decision notes are optional when confirming, but required if returning the item to the planner for revision.</p>
</section>
</main>
<footer class="border-t border-border-subtle p-container-padding bg-surface-container-lowest flex flex-col sm:flex-row items-center justify-between gap-4 mt-auto">
<button type="button" class="w-full sm:w-auto font-body-md text-body-md font-medium text-status-exhausted hover:bg-error-container/20 px-4 py-2 rounded transition-colors flex items-center justify-center gap-2" data-kt-pln-action="close-finance" data-testid="kt-pln-ui07-cancel">Cancel</button>
<div class="flex flex-col sm:flex-row items-center gap-3 w-full sm:w-auto">
<button type="button" class="w-full sm:w-auto font-body-md text-body-md font-medium text-primary border border-border-subtle hover:bg-surface-container-low px-4 py-2 rounded transition-colors bg-surface-container-lowest flex items-center justify-center gap-2" data-kt-pln-action="return-finance" data-testid="kt-pln-ui07-return">
<span class="material-symbols-outlined text-[20px]">undo</span> Return to planner
</button>
<button type="button" class="w-full sm:w-auto font-body-md text-body-md font-medium text-on-primary bg-primary hover:bg-on-primary-fixed-variant px-6 py-2 rounded transition-colors shadow-sm flex items-center justify-center gap-2" data-kt-pln-action="confirm-finance" data-testid="kt-pln-ui07-confirm">
<span class="material-symbols-outlined text-[20px]">check</span> Confirm funding
</button>
</div>
</footer>
</div>
<div class="flex flex-col h-full min-h-0 hidden" data-kt-pln-07-variant="shortfall" data-testid="kt-pln-ui07a-shortfall" hidden>
<header class="flex items-center justify-between px-container-padding py-stack-sm border-b border-border-subtle bg-surface-container-lowest">
<h2 class="font-headline-md text-headline-md text-on-surface" data-testid="kt-pln-ui07a-title">Funding shortfall</h2>
<button type="button" aria-label="Close drawer" class="p-2 rounded-full hover:bg-surface-container transition-colors text-on-surface-variant flex items-center justify-center group" data-kt-pln-action="close-finance">
<span class="material-symbols-outlined text-[24px] group-hover:text-on-surface">close</span>
</button>
</header>
<main class="flex-1 overflow-y-auto p-container-padding space-y-section-gap">
<section class="bg-surface-container-lowest border border-border-subtle rounded p-container-padding space-y-stack-sm relative before:absolute before:left-0 before:top-0 before:bottom-0 before:w-1 before:bg-primary-container before:rounded-l">
<div class="flex justify-between items-start mb-2">
<h3 class="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider">Plan Item Context</h3>
<span class="font-data-md text-data-md text-on-surface-variant text-sm bg-surface-container px-2 py-0.5 rounded whitespace-normal" data-kt-pln-07-code>PPI-MOH-2027-021</span>
</div>
<div class="space-y-4">
<div>
<p class="font-headline-sm text-headline-sm text-on-surface mb-1 whitespace-normal" data-kt-pln-07-title>National digital health infrastructure upgrade</p>
<p class="font-body-sm text-body-sm text-on-surface-variant whitespace-normal" data-kt-pln-07-plan>Ministry of Health Annual Procurement Plan 2027/28 · Draft Version 1</p>
</div>
<div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pt-2 border-t border-border-subtle border-dashed">
<div>
<p class="font-label-caps text-label-caps text-outline mb-1 uppercase tracking-wider">Owner OU</p>
<p class="font-body-md text-body-md text-on-surface whitespace-normal" data-kt-pln-07-ou>Directorate of Digital Health and Policy</p>
</div>
<div>
<p class="font-label-caps text-label-caps text-outline mb-1 uppercase tracking-wider">Plan Item status</p>
<div class="inline-flex items-center px-2 py-1 rounded-full bg-primary-fixed text-on-primary-fixed border border-primary-fixed-dim font-body-sm text-body-sm">
<span class="w-1.5 h-1.5 rounded-full bg-primary mr-1.5"></span>
<span data-kt-pln-07-status>Proposed · Planning complete</span>
</div>
</div>
</div>
</div>
</section>
<section class="space-y-stack-sm">
<h3 class="font-headline-sm text-headline-sm text-on-surface border-b border-border-subtle pb-2 mb-4">Funding required</h3>
<div class="space-y-2 mb-4" data-kt-pln-07-sources></div>
<div class="grid grid-cols-1 md:grid-cols-2 gap-container-padding">
<div class="space-y-1">
<p class="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider">Source Demand</p>
<p class="font-body-md text-body-md text-on-surface whitespace-normal" data-kt-pln-07-demand>National digital health infrastructure upgrade</p>
</div>
<div class="space-y-1">
<p class="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider">Proposed Budget Line</p>
<p class="font-body-md text-body-md text-on-surface whitespace-normal" data-kt-pln-07-line>Digital clinical systems infrastructure</p>
</div>
</div>
<div class="bg-surface-bright border border-border-subtle rounded p-container-padding mt-4 grid grid-cols-1 sm:grid-cols-3 gap-container-padding divide-y sm:divide-y-0 sm:divide-x divide-border-subtle" data-testid="kt-pln-ui07a-money">
<div class="sm:pr-4 py-2 sm:py-0 flex flex-col justify-center">
<p class="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider mb-2">Amount required</p>
<p class="font-data-lg text-data-lg text-primary tracking-tight whitespace-normal" data-kt-pln-07-amount>KES 455,000,000</p>
</div>
<div class="sm:px-4 py-2 sm:py-0 flex flex-col justify-center">
<p class="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider">Current available allocation</p>
<p class="font-data-md text-data-md text-on-surface whitespace-normal" data-kt-pln-07-available>KES 400,000,000</p>
</div>
<div class="sm:pl-4 py-2 sm:py-0 flex flex-col justify-center">
<div class="flex items-center gap-2 mb-2">
<p class="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider">Funding shortfall</p>
<span class="inline-flex items-center gap-1 text-status-exhausted font-body-sm text-[12px] bg-error-container/20 px-1.5 py-0.5 rounded">
<span class="material-symbols-outlined text-[14px]">error</span> Insufficient funding
</span>
</div>
<p class="font-data-md text-data-md text-status-exhausted whitespace-normal" data-kt-pln-07-shortfall>KES 55,000,000</p>
</div>
</div>
<div class="flex items-start gap-3 bg-error-container/10 border border-error/20 rounded p-3 mt-4 text-on-surface">
<span class="material-symbols-outlined text-error mt-0.5">warning</span>
<div class="space-y-1">
<p class="font-body-sm text-body-sm font-medium" data-kt-pln-07a-notice>This Plan Item cannot be confirmed because the Budget Line is short by KES 55,000,000.</p>
<p class="font-body-sm text-body-sm text-on-surface-variant">
<span class="block mb-2"><strong>Resolve funding</strong> — Review the Budget Line and address the shortfall in Budget &amp; Funding.</span>
<span class="block"><strong>Return to planner</strong> — Send the item back if its funding source or requirement needs correction.</span>
</p>
</div>
</div>
</section>
<section class="space-y-2 mt-section-gap">
<label class="font-label-caps text-label-caps text-on-surface uppercase tracking-wider block" for="kt-pln-ui07a-reason">Reason for returning</label>
<textarea class="w-full bg-surface-container-lowest border border-border-subtle rounded p-3 font-body-md text-body-md text-on-surface focus:border-secondary focus:ring-1 focus:ring-secondary focus:outline-none transition-shadow resize-none" id="kt-pln-ui07a-reason" data-kt-field="reason" placeholder="Enter any relevant notes or conditions..." rows="3"></textarea>
<p class="hidden font-body-sm text-body-sm text-error mt-stack-xs" data-kt-field-error="reason" hidden></p>
</section>
</main>
<footer class="border-t border-border-subtle p-container-padding bg-surface-container-lowest flex flex-col sm:flex-row items-center justify-between gap-4 mt-auto">
<button type="button" class="w-full sm:w-auto font-body-md text-body-md font-medium text-on-surface-variant hover:bg-surface-container px-4 py-2 rounded transition-colors flex items-center justify-center gap-2" data-kt-pln-action="close-finance" data-testid="kt-pln-ui07a-close">Close</button>
<div class="flex flex-col sm:flex-row items-center gap-3 w-full sm:w-auto">
<button type="button" class="w-full sm:w-auto font-body-md text-body-md font-medium text-primary border border-border-subtle hover:bg-surface-container-low px-4 py-2 rounded transition-colors bg-surface-container-lowest flex items-center justify-center gap-2" data-kt-pln-action="return-finance" data-testid="kt-pln-ui07a-return">
<span class="material-symbols-outlined text-[20px]">undo</span> Return to planner
</button>
<a class="w-full sm:w-auto font-body-md text-body-md font-medium text-on-primary bg-primary hover:bg-on-primary-fixed-variant px-6 py-2 rounded transition-colors shadow-sm flex items-center justify-center gap-2 no-underline" href="/app/budget-funding" data-testid="kt-pln-ui07a-resolve">Resolve in Budget &amp; Funding</a>
</div>
</footer>
</div>
</div>
</div>
</div>`;
};
