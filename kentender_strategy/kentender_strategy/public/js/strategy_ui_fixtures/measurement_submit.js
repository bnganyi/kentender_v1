// Ported from submit_measurement_moh_tgt_01/code.html (STR-UI-09).
// Stitch focused header + max-w-5xl canvas; form fields are live-bound hosts.
frappe.provide("kentender_strategy.ui_fixtures");
kentender_strategy.ui_fixtures.measurement_submit = function () {
	return `<div class="kt-str-root kt-str-meas-submit-root" data-testid="kt-str-measurement-submit">
<header class="bg-surface-container-lowest border-b border-outline-variant h-16 flex items-center px-section-gap sticky top-0 z-50" data-testid="kt-str-meas-submit-header">
<div class="flex items-center gap-4">
<button type="button" class="text-on-surface-variant hover:bg-surface-container p-2 rounded-full transition-colors flex items-center justify-center" data-kt-str-action="cancel" aria-label="Back">
<span class="material-symbols-outlined">arrow_back</span>
</button>
<div>
<h1 class="font-headline-sm text-headline-sm text-primary">Submit performance measurement</h1>
</div>
</div>
</header>
<main class="flex-grow p-section-gap max-w-5xl mx-auto w-full flex flex-col gap-section-gap" data-testid="kt-str-meas-submit-canvas">
<!-- Context Header (path crumbs omitted — Desk breadcrumbs already cover navigation) -->
<section>
<h2 class="font-headline-lg text-headline-lg text-on-surface" data-kt-str-target-code>MOH-TGT-0001</h2>
<p class="font-body-lg text-body-lg text-on-surface-variant mt-2" data-kt-str-target-title>At least 99.9% annual availability by 30 June 2028</p>
</section>
<!-- Read-only Reference Data Block -->
<section class="data-block bg-surface-container-lowest">
<h3 class="font-headline-sm text-headline-sm text-primary mb-4 flex items-center gap-2 border-b border-surface-variant pb-2">
<span class="material-symbols-outlined">info</span> Target Reference
</h3>
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-gutter">
<div class="p-3 bg-surface-container-low rounded">
<span class="font-label-caps text-label-caps text-on-surface-variant block mb-1">Indicator</span>
<span class="font-body-md text-body-md text-on-surface" data-kt-str-meas-indicator>Availability of core clinical information systems</span>
</div>
<div class="p-3 bg-surface-container-low rounded">
<span class="font-label-caps text-label-caps text-on-surface-variant block mb-1">Target</span>
<span class="font-data-mono text-data-mono text-status-available" data-kt-str-meas-target-value>≥ 99.9%</span>
</div>
<div class="p-3 bg-surface-container-low rounded">
<span class="font-label-caps text-label-caps text-on-surface-variant block mb-1">Tolerance</span>
<span class="font-data-mono text-data-mono text-status-reserved" data-kt-str-meas-tolerance>99.8%</span>
</div>
<div class="p-3 bg-surface-container-low rounded">
<span class="font-label-caps text-label-caps text-on-surface-variant block mb-1">Baseline</span>
<span class="font-data-mono text-data-mono text-on-surface" data-kt-str-meas-baseline>97.8% (30 Jun 2026)</span>
</div>
<div class="p-3 bg-surface-container-low rounded">
<span class="font-label-caps text-label-caps text-on-surface-variant block mb-1">Frequency</span>
<span class="font-body-md text-body-md text-on-surface" data-kt-str-meas-frequency>Monthly</span>
</div>
<div class="p-3 bg-surface-container-low rounded">
<span class="font-label-caps text-label-caps text-on-surface-variant block mb-1">Data Source</span>
<span class="font-body-md text-body-md text-on-surface" data-kt-str-meas-data-source>Approved infrastructure-monitoring report</span>
</div>
</div>
</section>
<!-- Measurement Form -->
<section class="data-block bg-surface-container-lowest">
<h3 class="font-headline-sm text-headline-sm text-primary mb-6 border-b border-surface-variant pb-2">Record Measurement</h3>
<div class="bg-surface-container p-3 rounded mb-6 flex items-start gap-3 border border-outline-variant" data-kt-str-meas-guidance>
<span class="material-symbols-outlined text-primary mt-0.5">lightbulb</span>
<div class="flex flex-col gap-1">
<p class="font-body-md text-body-md text-on-surface">Ensure measurements are not duplicated for the same target and period. Only one official measurement is permitted per period unless superseding a prior record.</p>
<p class="font-body-md text-body-md text-on-surface" data-kt-str-meas-period-hint>Measurement period must fall within the target period unless an authorised final measurement is recorded.</p>
</div>
</div>
<form class="grid grid-cols-1 md:grid-cols-2 gap-section-gap" data-kt-str-meas-form>
<div>
<label class="block font-label-caps text-label-caps text-on-surface mb-1">Period start <span class="text-error">*</span></label>
<input class="w-full bg-surface border border-outline-variant rounded p-2 font-body-md text-body-md text-on-surface outline-none" type="date" data-kt-str-meas-period-start value="2027-09-01"/>
</div>
<div>
<label class="block font-label-caps text-label-caps text-on-surface mb-1">Period end <span class="text-error">*</span></label>
<input class="w-full bg-surface border border-outline-variant rounded p-2 font-body-md text-body-md text-on-surface outline-none" type="date" data-kt-str-meas-period-end value="2027-09-30"/>
</div>
<div class="md:col-span-2">
<label class="block font-label-caps text-label-caps text-on-surface mb-1">Measurement date <span class="text-error">*</span></label>
<input class="w-full max-w-md bg-surface border border-outline-variant rounded p-2 font-body-md text-body-md text-on-surface outline-none" type="date" data-kt-str-meas-date value="2027-10-03"/>
</div>
<div class="md:col-span-2 grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
<div class="lg:col-span-1">
<label class="block font-label-caps text-label-caps text-on-surface mb-1">Actual Value <span class="text-error">*</span></label>
<div class="relative flex items-center">
<input class="w-full bg-surface border border-outline-variant rounded-l p-2 font-data-mono text-data-mono text-on-surface outline-none" step="0.01" type="number" data-kt-str-actual value="99.82"/>
<span class="bg-surface-container-high border border-l-0 border-outline-variant rounded-r p-2 font-data-mono text-data-mono text-on-surface-variant flex items-center justify-center min-w-[40px]" data-kt-str-meas-unit>%</span>
</div>
</div>
<div class="lg:col-span-2 kt-str-meas-derived relative overflow-hidden p-4 rounded" data-kt-str-meas-derived data-kt-str-meas-tone="at-risk">
<div class="kt-str-meas-derived-accent absolute left-0 top-0 bottom-0" aria-hidden="true"></div>
<div class="flex items-center gap-3 mb-2 pl-2">
<span class="font-label-caps text-label-caps text-on-surface-variant">Derived Result</span>
<span class="kt-str-meas-derived-badge px-2 py-0.5 rounded-full font-label-caps text-[10px] tracking-wider" data-kt-str-result>AT RISK</span>
</div>
<div class="flex items-baseline gap-4 mb-2 pl-2">
<div class="kt-str-meas-derived-variance font-data-mono text-data-mono flex items-center gap-1" data-kt-str-meas-variance>
<span class="material-symbols-outlined text-sm">trending_down</span>
<span data-kt-str-meas-variance-text>−0.08 pp</span>
</div>
</div>
<p class="font-body-md text-body-md text-on-surface-variant italic text-sm pl-2" data-kt-str-meas-result-explain>Actual is below the 99.9% target but remains within the 99.8% tolerance.</p>
</div>
</div>
<div class="md:col-span-2">
<label class="block font-label-caps text-label-caps text-on-surface mb-1">Evidence Source</label>
<input class="w-full bg-surface border border-outline-variant rounded p-2 font-body-md text-body-md text-on-surface outline-none" type="text" data-kt-str-meas-evidence-source value="Infrastructure monitoring platform"/>
</div>
<div class="md:col-span-2">
<label class="block font-label-caps text-label-caps text-on-surface mb-1">Evidence Reference</label>
<div class="border-2 border-dashed border-outline-variant rounded-lg p-6 flex flex-col items-center justify-center bg-surface-container-low hover:bg-surface-container transition-colors cursor-pointer group">
<span class="material-symbols-outlined text-outline group-hover:text-primary mb-2 text-3xl">upload_file</span>
<p class="font-body-md text-body-md text-on-surface mb-1">Drag and drop file here or click to browse</p>
<p class="font-label-caps text-label-caps text-on-surface-variant">Select or attach existing authorised evidence</p>
<input type="text" class="mt-3 w-full max-w-md bg-surface border border-outline-variant rounded p-2 font-body-md text-body-md outline-none" placeholder="Evidence reference code" data-kt-str-meas-evidence-ref value="INFRA-MON-2027-09"/>
</div>
</div>
<div class="md:col-span-2">
<label class="block font-label-caps text-label-caps text-on-surface mb-1">Commentary <span class="text-on-surface-variant font-normal normal-case">(Optional)</span></label>
<textarea class="w-full bg-surface border border-outline-variant rounded p-2 font-body-md text-body-md text-on-surface outline-none resize-y" placeholder="Add any contextual notes regarding this measurement..." rows="3" data-kt-str-meas-commentary></textarea>
</div>
</form>
</section>
<footer class="flex items-center justify-end gap-4 mt-4 pt-4 border-t border-outline-variant mb-8" data-testid="kt-str-meas-submit-footer">
<button type="button" class="font-body-md font-semibold text-on-surface-variant hover:text-primary px-4 py-2 rounded transition-colors" data-kt-str-action="cancel">
Cancel
</button>
<button type="button" class="font-body-md font-semibold text-primary border border-primary px-4 py-2 rounded-lg hover:bg-surface-container transition-colors" data-kt-str-action="save-draft">
Save draft
</button>
<button type="button" class="font-body-md font-semibold bg-primary text-on-primary px-6 py-2 rounded-lg hover:opacity-90 transition-opacity shadow-sm flex items-center gap-2" data-kt-str-action="submit-measurement">
Submit measurement
</button>
</footer>
</main>
</div>`;
};
