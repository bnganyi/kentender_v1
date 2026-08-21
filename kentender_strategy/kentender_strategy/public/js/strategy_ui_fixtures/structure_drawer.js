// Extracted drawer overlay from plan_structure_add_performance_target_drawer/code.html
// Live bind replaces [data-kt-str-drawer-form] per node type (STR-UI-04).
frappe.provide("kentender_strategy.ui_fixtures");
kentender_strategy.ui_fixtures.structure_drawer = function () {
	return `<div class="kt-str-root" data-testid="kt-str-structure-drawer">
<div class="fixed inset-0 z-[100] flex justify-end" data-testid="kt-str-structure-drawer-overlay" data-dismiss="explicit-only">
<div class="absolute inset-0 bg-on-surface/40 transition-opacity" aria-hidden="true"></div>
<div class="relative w-[500px] h-full bg-surface-container-lowest shadow-xl flex flex-col overflow-hidden" data-testid="kt-str-structure-drawer-panel">
<div class="p-section-gap border-b border-outline-variant">
<div class="flex justify-between items-start mb-2">
<h2 class="font-headline-sm text-headline-sm text-primary" data-kt-str-drawer-title>Add performance target</h2>
<button type="button" class="p-1 hover:bg-surface-container rounded-full transition-colors" data-kt-str-action="close-drawer" aria-label="Close">
<span class="material-symbols-outlined text-on-surface-variant">close</span>
</button>
</div>
<p class="text-xs text-on-surface-variant font-medium leading-relaxed" data-kt-str-drawer-path></p>
</div>
<div class="flex-1 overflow-y-auto p-section-gap space-y-6" data-kt-str-drawer-form>
<div class="space-y-1">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase">Target code</label>
<div class="font-data-mono text-data-mono bg-surface-container px-3 py-2 rounded border border-outline-variant text-on-surface-variant">—</div>
</div>
<div class="space-y-1">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase">Target title</label>
<textarea class="w-full border border-outline-variant rounded-lg p-3 text-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none min-h-[80px]"></textarea>
</div>
<div class="grid grid-cols-2 gap-4">
<div class="space-y-1">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase">Comparison direction</label>
<select class="w-full border border-outline-variant rounded-lg p-2 text-body-md focus:border-primary outline-none">
<option>At least</option>
<option>At most</option>
<option>Equal to</option>
</select>
</div>
<div class="space-y-1">
<label class="font-label-caps text-label-caps text-on-surface-variant uppercase">Target value</label>
<div class="flex">
<input class="flex-1 border border-outline-variant rounded-l-lg p-2 text-body-md font-data-mono focus:border-primary outline-none" type="text"/>
<span class="bg-surface-container border border-l-0 border-outline-variant rounded-r-lg px-3 flex items-center text-on-surface-variant font-medium">%</span>
</div>
</div>
</div>
</div>
<div class="p-section-gap border-t border-outline-variant bg-surface-container-low flex flex-row-reverse gap-3">
<button type="button" class="bg-primary text-on-primary px-6 py-2 rounded-lg font-medium hover:bg-primary-container transition-colors" data-kt-str-action="save-structure-node" data-kt-str-drawer-save>Save target</button>
<button type="button" class="text-on-surface-variant px-6 py-2 rounded-lg font-medium hover:bg-surface-container-high transition-colors" data-kt-str-action="close-drawer">Cancel</button>
</div>
</div>
</div>
</div>`;
};
