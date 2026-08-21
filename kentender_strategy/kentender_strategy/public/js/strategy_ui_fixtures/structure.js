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
<!-- Plan chrome injected by strategy_alignment_shell.planChromeHtml -->
<!-- Main Content Area: Two-Region Layout (matched card panes) -->
<div class="flex-1 flex overflow-hidden kt-str-structure-split p-section-gap gap-4 items-stretch" data-testid="kt-str-structure-split">
<!-- Left Region: Hierarchy Tree (40%) — card chrome aligned with detail -->
<div class="w-2/5 bg-surface-container-lowest border border-outline-variant rounded-xl shadow-sm flex flex-col min-h-0 overflow-hidden" data-testid="kt-str-structure-tree">
<div class="p-4 border-b border-outline-variant flex justify-between items-center bg-surface-container-low rounded-t-xl">
<h2 class="font-headline-sm text-headline-sm text-primary">Structure Hierarchy</h2>
<button type="button" class="text-primary hover:bg-primary-fixed p-1 rounded transition-colors" title="Expand All" data-kt-str-action="expand-all">
<span class="material-symbols-outlined text-xl">unfold_more</span>
</button>
</div>
<div class="flex-1 overflow-y-auto p-4 space-y-1 min-h-0" data-kt-str-structure-tree-host>
</div>
<!-- Bottom Action: Add Menu -->
<div class="p-4 border-t border-outline-variant bg-surface-container-low rounded-b-xl" data-kt-str-structure-add-bar>
<button type="button" class="w-full border border-dashed border-outline text-on-surface-variant hover:text-primary hover:border-primary hover:bg-surface-container py-2 rounded-lg flex items-center justify-center gap-2 transition-all text-sm font-medium" data-kt-str-action="add-structure-item">
<span class="material-symbols-outlined text-sm">add</span>
Add Structure Item
</button>
</div>
</div>
<!-- Right Region: Detail Panel (60%) -->
<div class="w-3/5 min-h-0 overflow-y-auto" data-testid="kt-str-structure-detail">
<div class="max-w-3xl mx-auto" data-kt-str-structure-detail-host>
<div class="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-sm p-card-padding text-on-surface-variant text-sm">
Select a structure item to view details.
</div>
</div>
</div>
</div>
</div>`;
};
