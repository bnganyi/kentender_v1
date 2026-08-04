// Ported from verify_measurement_moh_tgt_01 (STR-UI-10). Live-bound hosts for verify decisions.
frappe.provide("kentender_strategy.ui_fixtures");
kentender_strategy.ui_fixtures.measurement_verify = function () {
	return `<div class="kt-str-root kt-str-meas-verify-root" data-testid="kt-str-measurement-verify">
<div class="max-w-7xl mx-auto space-y-section-gap">
<!-- Page Header -->
<div class="flex flex-col md:flex-row md:items-start justify-between gap-4" data-testid="kt-str-meas-verify-header">
<div>
<div class="flex items-center gap-2 mb-2">
<button type="button" class="text-secondary hover:underline flex items-center text-sm" data-kt-str-action="cancel">
<span class="material-symbols-outlined text-sm mr-1">arrow_back</span>
                                Back to measurements
                            </button>
</div>
<h1 class="font-headline-lg text-headline-lg-mobile md:text-headline-lg text-on-surface mb-2">Verify performance measurement</h1>
<p class="text-on-surface-variant font-body-lg">
<span class="font-semibold text-on-surface">Target:</span>
<span data-kt-str-target-code>MOH-TGT-0001</span> — <span data-kt-str-target-title>At least 99.9% annual availability by 30 June 2028</span>
                        </p>
</div>
<div class="flex flex-col sm:flex-row items-start sm:items-center gap-3">
<div class="kt-str-meas-status-pill bg-secondary-container text-on-secondary-container border border-secondary-fixed" data-kt-str-meas-workflow-pill>
<span class="material-symbols-outlined kt-str-meas-status-pill-icon" data-kt-str-meas-workflow-icon aria-hidden="true">hourglass_empty</span>
<span class="font-label-caps text-label-caps uppercase kt-str-meas-status-pill-label" data-kt-str-meas-workflow-label>Submitted</span>
</div>
<div class="kt-str-meas-status-pill bg-amber-50 text-status-reserved border border-amber-200" data-kt-str-meas-result-pill data-kt-str-meas-tone="at-risk">
<span class="material-symbols-outlined kt-str-meas-status-pill-icon" data-kt-str-meas-result-icon aria-hidden="true">warning</span>
<span class="font-label-caps text-label-caps uppercase kt-str-meas-status-pill-label" data-kt-str-result>At Risk</span>
</div>
</div>
</div>
<!-- Comparison Region -->
<div class="grid grid-cols-1 lg:grid-cols-2 gap-gutter" data-testid="kt-str-meas-verify-compare">
<!-- Left Column: Approved Target -->
<div class="bg-surface-container-lowest border border-outline-variant rounded-lg flex flex-col h-full shadow-sm">
<div class="bg-surface-container-low px-card-padding py-3 border-b border-outline-variant rounded-t-lg">
<h2 class="font-headline-sm text-headline-sm text-on-surface flex items-center gap-2">
<span class="material-symbols-outlined text-primary">fact_check</span>
                                Approved Target Reference
                            </h2>
</div>
<div class="p-card-padding space-y-4 flex-1">
<div class="grid grid-cols-3 gap-4 border-b border-outline-variant pb-4">
<div class="col-span-1 text-on-surface-variant text-sm font-medium">Indicator</div>
<div class="col-span-2 text-on-surface" data-kt-str-meas-indicator>Availability of core clinical information systems</div>
</div>
<div class="grid grid-cols-3 gap-4 border-b border-outline-variant pb-4">
<div class="col-span-1 text-on-surface-variant text-sm font-medium">Target</div>
<div class="col-span-2 text-on-surface font-semibold bg-surface-container-low inline-block px-2 py-1 rounded w-max" data-kt-str-meas-target-value>≥99.9%</div>
</div>
<div class="grid grid-cols-3 gap-4 border-b border-outline-variant pb-4">
<div class="col-span-1 text-on-surface-variant text-sm font-medium">Tolerance</div>
<div class="col-span-2 text-on-surface" data-kt-str-meas-tolerance>99.8%</div>
</div>
<div class="grid grid-cols-3 gap-4 border-b border-outline-variant pb-4">
<div class="col-span-1 text-on-surface-variant text-sm font-medium">Baseline</div>
<div class="col-span-2 text-on-surface" data-kt-str-meas-baseline>97.8% as at 30 June 2026</div>
</div>
<div class="grid grid-cols-3 gap-4 border-b border-outline-variant pb-4">
<div class="col-span-1 text-on-surface-variant text-sm font-medium">Period</div>
<div class="col-span-2 text-on-surface" data-kt-str-meas-period-label>September 2027</div>
</div>
<div class="grid grid-cols-3 gap-4">
<div class="col-span-1 text-on-surface-variant text-sm font-medium">Expected Data Source</div>
<div class="col-span-2 text-on-surface" data-kt-str-meas-data-source>Approved infrastructure-monitoring report</div>
</div>
</div>
</div>
<!-- Right Column: Submitted Result -->
<div class="bg-surface-container-lowest border border-outline-variant rounded-lg flex flex-col h-full shadow-sm relative overflow-hidden" data-kt-str-meas-submitted-card>
<!-- Guardrail indicator -->
<div class="absolute top-0 left-0 w-1 h-full bg-status-reserved" data-kt-str-meas-tone-rail></div>
<div class="bg-surface-container-low px-card-padding py-3 border-b border-outline-variant rounded-t-lg ml-1">
<h2 class="font-headline-sm text-headline-sm text-on-surface flex items-center gap-2">
<span class="material-symbols-outlined text-primary">upload_file</span>
                                Submitted Result
                            </h2>
</div>
<div class="p-card-padding space-y-4 flex-1 ml-1 bg-amber-50/20" data-kt-str-meas-submitted-body>
<div class="grid grid-cols-3 gap-4 border-b border-outline-variant/60 pb-4">
<div class="col-span-1 text-on-surface-variant text-sm font-medium flex items-center">Actual</div>
<div class="col-span-2">
<span class="font-data-mono text-data-mono text-status-reserved font-bold bg-white px-2 py-1 rounded border border-amber-200 shadow-sm" data-kt-str-actual>99.82%</span>
</div>
</div>
<div class="grid grid-cols-3 gap-4 border-b border-outline-variant/60 pb-4">
<div class="col-span-1 text-on-surface-variant text-sm font-medium flex items-center">Variance</div>
<div class="col-span-2 font-data-mono text-data-mono text-status-reserved bg-white px-2 py-1 rounded inline-block border border-amber-100 shadow-sm" data-kt-str-meas-variance>
                                    −0.08 percentage points
                                </div>
</div>
<div class="grid grid-cols-3 gap-4 border-b border-outline-variant/60 pb-4">
<div class="col-span-1 text-on-surface-variant text-sm font-medium">Measurement Date</div>
<div class="col-span-2 text-on-surface" data-kt-str-meas-date-display>3 October 2027</div>
</div>
<div class="grid grid-cols-3 gap-4 border-b border-outline-variant/60 pb-4">
<div class="col-span-1 text-on-surface-variant text-sm font-medium">Evidence Source</div>
<div class="col-span-2 text-on-surface" data-kt-str-meas-evidence-source>Infrastructure monitoring platform</div>
</div>
<div class="grid grid-cols-3 gap-4 border-b border-outline-variant/60 pb-4">
<div class="col-span-1 text-on-surface-variant text-sm font-medium">Submitted By</div>
<div class="col-span-2 text-on-surface flex items-center gap-2" data-kt-str-meas-submitted-by>
                                    —
                                </div>
</div>
<div class="grid grid-cols-3 gap-4">
<div class="col-span-1 text-on-surface-variant text-sm font-medium">Commentary</div>
<div class="col-span-2 text-on-surface italic bg-white p-3 rounded border border-outline-variant/60 shadow-inner text-sm" data-kt-str-meas-commentary>
                                    —
                                </div>
</div>
</div>
</div>
</div>
<!-- Evidence Viewer Area -->
<div class="bg-surface-container-lowest border border-outline-variant rounded-lg shadow-sm" data-testid="kt-str-meas-verify-evidence">
<div class="px-card-padding py-3 border-b border-outline-variant">
<h3 class="font-headline-sm text-headline-sm text-on-surface flex items-center gap-2">
<span class="material-symbols-outlined text-on-surface-variant">attach_file</span>
                            Attached Evidence
                        </h3>
</div>
<div class="p-card-padding">
<div class="flex items-center justify-between p-4 border border-outline-variant rounded-lg bg-surface hover:bg-surface-container-low transition-colors group">
<div class="flex items-center gap-4">
<div class="w-10 h-10 bg-error/10 text-error rounded flex items-center justify-center">
<span class="material-symbols-outlined">picture_as_pdf</span>
</div>
<div>
<p class="font-medium text-on-surface text-sm" data-kt-str-meas-evidence-ref>MOH_Infra_Sept2027_Monitoring.pdf</p>
<p class="text-xs text-on-surface-variant mt-0.5" data-kt-str-meas-evidence-meta>Evidence reference</p>
</div>
</div>
<button type="button" class="text-primary hover:text-primary-container font-medium text-sm flex items-center gap-1 px-3 py-1.5 rounded hover:bg-primary/5 transition-colors" data-kt-str-action="view-evidence">
<span class="material-symbols-outlined text-sm">visibility</span>
                                View Evidence
                            </button>
</div>
</div>
</div>
<!-- Decision Area -->
<div class="bg-surface-container-lowest border border-outline-variant rounded-lg shadow-sm overflow-hidden" data-testid="kt-str-meas-verify-decision">
<div class="bg-surface-container-low px-card-padding py-3 border-b border-outline-variant">
<h3 class="font-headline-sm text-headline-sm text-on-surface flex items-center gap-2">
<span class="material-symbols-outlined text-primary">rule</span>
                            Verification Decision
                        </h3>
</div>
<div class="p-card-padding space-y-6">
<!-- Segregation of Duties Alert -->
<div class="bg-primary/5 border-l-4 border-primary p-4 rounded-r" data-kt-str-meas-sod>
<div class="flex items-start">
<span class="material-symbols-outlined text-primary mt-0.5 mr-3">info</span>
<div>
<h4 class="text-sm font-semibold text-primary-container">Segregation of Duties Enforced</h4>
<p class="text-sm text-on-surface-variant mt-1" data-kt-str-meas-sod-text>
                                        Verifiers must be independent of the submitter</p>
</div>
</div>
</div>
<!-- Comments -->
<div>
<label class="block text-sm font-medium text-on-surface mb-2" for="verification-comments">
                                Verification comments <span class="text-on-surface-variant font-normal">(required for rejections or corrections)</span>
</label>
<textarea class="w-full rounded-lg border-outline-variant focus:border-primary focus:ring focus:ring-primary/20 text-sm p-3 bg-surface text-on-surface placeholder-on-surface-variant transition-colors" id="verification-comments" data-kt-str-meas-verify-comments placeholder="Enter your findings or reasons for your decision here..." rows="3"></textarea>
</div>
<!-- Follow-up: At risk optional CA -->
<div class="flex items-start bg-amber-50/50 p-3 rounded border border-amber-100" data-kt-str-meas-ca-box>
<div class="flex items-center h-5">
<input class="w-4 h-4 text-primary bg-surface border-outline-variant rounded focus:ring-primary focus:ring-2" id="create-corrective" type="checkbox" data-kt-str-meas-create-ca checked>
</div>
<div class="ml-3 text-sm">
<label class="font-medium text-on-surface cursor-pointer" for="create-corrective">Create corrective action after verification</label>
<p class="text-on-surface-variant mt-1">Recommended because the submitted result is categorized as 'At risk'.</p>
</div>
</div>
<!-- Off track authorised exception -->
<div class="hidden flex items-start bg-error-container/40 p-3 rounded border border-error/20" data-kt-str-meas-exception-box>
<div class="flex items-center h-5">
<input class="w-4 h-4 text-primary bg-surface border-outline-variant rounded focus:ring-primary focus:ring-2" id="authorised-exception" type="checkbox" data-kt-str-meas-exception>
</div>
<div class="ml-3 text-sm flex-1">
<label class="font-medium text-on-surface cursor-pointer" for="authorised-exception">Record authorised exception (skip corrective action)</label>
<p class="text-on-surface-variant mt-1">Required for Off track verification without opening a corrective action.</p>
<textarea class="mt-2 w-full rounded-lg border-outline-variant text-sm p-2 bg-surface hidden" data-kt-str-meas-exception-reason rows="2" placeholder="Exception reason (required when exception is selected)"></textarea>
</div>
</div>
</div>
<!-- Action Bar -->
<div class="bg-surface-container px-card-padding py-4 border-t border-outline-variant flex flex-col sm:flex-row justify-between items-center gap-4" data-testid="kt-str-meas-verify-actions">
<div class="flex gap-3 w-full sm:w-auto">
<button type="button" class="flex-1 sm:flex-none justify-center px-4 py-2 border border-outline text-on-surface rounded-lg hover:bg-surface-variant transition-colors font-medium text-sm flex items-center gap-2" data-kt-str-action="reject-measurement">
<span class="material-symbols-outlined text-sm">cancel</span>
                                Reject
                            </button>
<button type="button" class="flex-1 sm:flex-none justify-center px-4 py-2 border border-outline text-on-surface rounded-lg hover:bg-surface-variant transition-colors font-medium text-sm flex items-center gap-2" data-kt-str-action="request-changes">
<span class="material-symbols-outlined text-sm">replay</span>
                                Return for correction
                            </button>
</div>
<button type="button" class="w-full sm:w-auto justify-center px-6 py-2 bg-primary text-on-primary rounded-lg hover:bg-primary-container transition-colors font-medium text-sm flex items-center gap-2 shadow-sm" data-kt-str-action="verify-measurement">
<span class="material-symbols-outlined text-sm">check_circle</span>
                            Verify Measurement
                        </button>
</div>
</div>
</div>
<!-- Bottom spacing -->
<div class="h-12"></div>
</div>
</div>`;
};
