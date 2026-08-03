// Extracted from plan_structure_ministry_of_health_draft_plan_v2/code.html <main>
// Dropped Stitch fake top app bar (Desk CL chrome). Classes preserved.
// Tree/detail bodies are live-bound hosts (STR-UI-03).
frappe.provide("kentender_strategy.ui_fixtures");
kentender_strategy.ui_fixtures.structure = function () {
	return `<div class="kt-str-root kt-str-structure-root" data-testid="kt-str-structure">
<!-- Top Alert -->
<div class="bg-error-container text-on-error-container px-section-gap py-3 flex items-center justify-between hidden" data-kt-str-structure-issues hidden aria-hidden="true">
<div class="flex items-center gap-2">
<span class="material-symbols-outlined" data-weight="fill">warning</span>
<span class="font-body-md font-medium" data-kt-str-structure-issues-label></span>
</div>
<button type="button" class="bg-error text-on-error px-4 py-1.5 rounded text-sm font-medium hover:opacity-90 transition-opacity" data-kt-str-action="resolve-structure-issues">Resolve</button>
</div>
<!-- Workspace Header -->
<div class="bg-surface-container-lowest px-section-gap py-6 border-b border-outline-variant" data-testid="kt-str-plan-chrome">
<div class="flex items-start justify-between">
<div>
<div class="flex items-center gap-3 mb-1">
<span class="font-data-mono text-data-mono text-on-surface-variant bg-surface-container px-2 py-1 rounded text-xs" data-kt-str-plan-code>—</span>
<span class="bg-status-reserved text-on-surface px-2 py-0.5 rounded font-label-caps text-[10px] uppercase font-bold tracking-wide" data-kt-str-plan-status>—</span>
<span class="text-on-surface-variant text-sm" data-kt-str-plan-version></span>
</div>
<h1 class="font-headline-lg text-headline-lg text-primary mt-2" data-kt-str-plan-title>Plan Structure</h1>
<p class="text-on-surface-variant mt-1 text-sm" data-kt-str-plan-period></p>
</div>
<div data-kt-str-structure-edit-plan>
<button type="button" class="border border-primary text-primary px-4 py-2 rounded-lg font-medium hover:bg-surface-container-low transition-colors flex items-center gap-2" data-kt-str-action="edit-plan-details">
<span class="material-symbols-outlined text-sm">edit</span>
                        Edit Plan Details
                    </button>
</div>
</div>
<!-- Tabs -->
<div class="flex gap-6 mt-6 border-b border-surface-variant" data-testid="kt-str-plan-tabs">
<button type="button" class="kt-str-tab pb-3 text-on-surface-variant hover:text-primary font-medium text-sm transition-colors" data-kt-str-tab="strategy-plan-overview">Overview</button>
<button type="button" class="kt-str-tab pb-3 text-primary border-b-2 border-primary font-medium text-sm is-active" data-kt-str-tab="strategy-plan-structure">Structure</button>
<button type="button" class="kt-str-tab pb-3 text-on-surface-variant hover:text-primary font-medium text-sm transition-colors" data-kt-str-tab="strategy-plan-value-commitments">Value Commitments</button>
<button type="button" class="kt-str-tab pb-3 text-on-surface-variant hover:text-primary font-medium text-sm transition-colors" data-kt-str-tab="strategy-plan-measurements">Measurement</button>
<button type="button" class="kt-str-tab pb-3 text-on-surface-variant hover:text-primary font-medium text-sm transition-colors" data-kt-str-tab="strategy-plan-downstream-usage">Downstream Usage</button>
<button type="button" class="kt-str-tab pb-3 text-on-surface-variant hover:text-primary font-medium text-sm transition-colors" data-kt-str-tab="strategy-plan-review">Review</button>
<button type="button" class="kt-str-tab pb-3 text-on-surface-variant hover:text-primary font-medium text-sm transition-colors" data-kt-str-tab="strategy-plan-audit">Audit</button>
</div>
</div>
<!-- Main Content Area: Two-Region Layout -->
<div class="flex-1 flex overflow-hidden kt-str-structure-split" data-testid="kt-str-structure-split">
<!-- Left Region: Hierarchy Tree (40%) -->
<div class="w-2/5 border-r border-outline-variant bg-surface-container-lowest flex flex-col h-full overflow-hidden" data-testid="kt-str-structure-tree">
<div class="p-4 border-b border-outline-variant flex justify-between items-center bg-surface-container-low">
<h2 class="font-headline-sm text-headline-sm text-primary">Structure Hierarchy</h2>
<button type="button" class="text-primary hover:bg-primary-fixed p-1 rounded transition-colors" title="Expand All" data-kt-str-action="expand-all">
<span class="material-symbols-outlined text-xl">unfold_more</span>
</button>
</div>
<div class="flex-1 overflow-y-auto p-4 space-y-1" data-kt-str-structure-tree-host>
</div>
<!-- Bottom Action: Add Menu -->
<div class="p-4 border-t border-outline-variant bg-surface-container-low" data-kt-str-structure-add-bar>
<button type="button" class="w-full border border-dashed border-outline text-on-surface-variant hover:text-primary hover:border-primary hover:bg-surface-container py-2 rounded-lg flex items-center justify-center gap-2 transition-all text-sm font-medium" data-kt-str-action="add-structure-item">
<span class="material-symbols-outlined text-sm">add</span>
Add Structure Item
</button>
</div>
</div>
<!-- Right Region: Detail Panel (60%) -->
<div class="w-3/5 bg-surface p-section-gap overflow-y-auto" data-testid="kt-str-structure-detail">
<div class="max-w-3xl mx-auto" data-kt-str-structure-detail-host>
<div class="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-sm p-card-padding text-on-surface-variant text-sm">
Select a structure item to view details.
</div>
</div>
</div>
</div>
</div>`;
};
