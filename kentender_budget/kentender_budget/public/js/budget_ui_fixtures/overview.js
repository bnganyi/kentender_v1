// BUD-UI-03 — Stitch main canvas from overview_ministry_of_health_budget_fy_2027_28/code.html
// Fake sidenav/top chrome discarded; workspace chrome injected by budget_workspace_shell.
frappe.provide("kentender_budget.ui_fixtures");

kentender_budget.ui_fixtures.overview = function () {
	return `<div class="kt-bud-root kt-stitch-canvas" data-testid="kt-bud-overview">
<!-- Workspace chrome injected by budget_workspace_shell -->
<div class="flex-1 p-container-padding max-w-7xl mx-auto w-full" data-testid="kt-bud-overview-canvas">
<div class="grid grid-cols-1 lg:grid-cols-3 gap-section-gap">
<div class="lg:col-span-2 flex flex-col gap-section-gap">
<div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-card-padding" data-testid="kt-bud-overview-identity">
<div class="grid grid-cols-2 md:grid-cols-3 gap-4">
<div class="flex flex-col gap-1">
<span class="font-body-md text-on-surface-variant text-sm">Entity</span>
<span class="font-body-md text-on-surface font-medium" data-kt-bud-ov="entity">—</span>
</div>
<div class="flex flex-col gap-1">
<span class="font-body-md text-on-surface-variant text-sm">Fiscal Period</span>
<span class="font-body-md text-on-surface font-medium" data-kt-bud-ov="fiscal_period">—</span>
</div>
<div class="flex flex-col gap-1">
<span class="font-body-md text-on-surface-variant text-sm">Currency</span>
<span class="font-data-mono text-on-surface bg-surface-container w-fit px-2 py-0.5 rounded text-sm" data-kt-bud-ov="currency">—</span>
</div>
<div class="flex flex-col gap-1">
<span class="font-body-md text-on-surface-variant text-sm">Source</span>
<span class="font-body-md text-on-surface font-medium" data-kt-bud-ov="source">—</span>
</div>
<div class="flex flex-col gap-1">
<span class="font-body-md text-on-surface-variant text-sm">External Reference</span>
<span class="font-data-mono text-on-surface text-sm" data-kt-bud-ov="external_ref">—</span>
</div>
<div class="flex flex-col gap-1">
<span class="font-body-md text-on-surface-variant text-sm">Last Synchronised</span>
<span class="font-body-md text-on-surface text-sm flex items-center gap-1" data-kt-bud-ov="last_sync">
<span class="material-symbols-outlined text-[14px]">sync</span>
<span data-kt-bud-ov="last_sync_text">—</span>
</span>
</div>
</div>
</div>
<div class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden flex flex-col" data-testid="kt-bud-overview-funding">
<div class="bg-surface-container-low px-card-padding py-3 border-b border-outline-variant flex justify-between items-center">
<h2 class="font-headline-sm text-on-surface">Funding Guardrails</h2>
<span class="material-symbols-outlined text-on-surface-variant">info</span>
</div>
<div class="p-card-padding grid grid-cols-3 gap-4 items-stretch" data-testid="kt-bud-overview-kpis">
<div class="flex flex-col gap-1 border-l-2 border-outline-variant pl-3 py-2">
<span class="font-label-caps text-on-surface-variant text-xs uppercase">Approved</span>
<span class="font-data-mono text-xl text-on-surface" data-kt-bud-ov="approved">—</span>
</div>
<div class="flex flex-col gap-1 border-l-2 border-status-reserved pl-3 bg-status-reserved/5 rounded-r py-2">
<span class="font-label-caps text-status-reserved text-xs flex items-center gap-1 uppercase">
<span class="material-symbols-outlined text-[14px]">pending_actions</span> Reserved
</span>
<span class="font-data-mono text-xl text-on-surface" data-kt-bud-ov="reserved">—</span>
</div>
<div class="flex flex-col gap-1 border-l-2 border-status-committed pl-3 bg-status-committed/5 rounded-r py-2">
<span class="font-label-caps text-status-committed text-xs flex items-center gap-1 uppercase">
<span class="material-symbols-outlined text-[14px]">lock</span> Committed
</span>
<span class="font-data-mono text-xl text-on-surface" data-kt-bud-ov="committed">—</span>
</div>
<div class="flex flex-col gap-1 border-l-2 border-status-available pl-3 bg-status-available/5 rounded-r py-2">
<span class="font-label-caps text-status-available text-xs flex items-center gap-1 uppercase">
<span class="material-symbols-outlined text-[14px]">check_circle</span> Available
</span>
<span class="font-data-mono text-xl text-on-surface" data-kt-bud-ov="available">—</span>
</div>
<div class="flex flex-col gap-1 border-l-2 border-outline-variant pl-3 py-2">
<span class="font-label-caps text-on-surface-variant text-xs uppercase">Actual expenditure</span>
<span class="font-data-mono text-xl text-on-surface" data-kt-bud-ov="actual">—</span>
</div>
<div class="flex flex-col gap-1 border-l-2 border-outline-variant pl-3 py-2">
<span class="font-label-caps text-on-surface-variant text-xs uppercase">Outstanding commitment</span>
<span class="font-data-mono text-xl text-on-surface" data-kt-bud-ov="outstanding">—</span>
</div>
</div>
<div class="px-card-padding pb-6" data-testid="kt-bud-overview-bar">
<div class="flex justify-between font-label-caps text-on-surface-variant mb-2">
<span>Utilization</span>
<span class="font-data-mono" data-kt-bud-ov="bar_total">—</span>
</div>
<div class="h-4 w-full rounded-full flex overflow-hidden bg-surface-container-highest">
<div class="h-full bg-status-reserved" data-kt-bud-ov-bar="reserved" style="width: 0%" title="Reserved"></div>
<div class="h-full bg-status-committed border-l border-surface-container-lowest" data-kt-bud-ov-bar="committed" style="width: 0%" title="Committed"></div>
<div class="h-full bg-status-available border-l border-surface-container-lowest" data-kt-bud-ov-bar="available" style="width: 0%" title="Available"></div>
</div>
<div class="flex gap-4 mt-2 font-body-md text-xs text-on-surface-variant">
<div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-status-reserved"></span> Reserved</div>
<div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-status-committed"></span> Committed</div>
<div class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-status-available"></span> Available</div>
</div>
</div>
</div>
</div>
<div class="flex flex-col gap-section-gap">
<div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-card-padding" data-testid="kt-bud-overview-strategy">
<div class="flex items-start gap-3">
<div class="w-8 h-8 rounded bg-primary/10 text-primary flex items-center justify-center shrink-0">
<span class="material-symbols-outlined">account_tree</span>
</div>
<div>
<h3 class="font-headline-sm text-on-surface mb-2">Strategy Alignment</h3>
<ul class="font-body-md text-on-surface-variant space-y-2 mb-4">
<li class="flex items-start gap-2">
<span class="material-symbols-outlined text-[16px] mt-0.5 text-primary">adjust</span>
<span data-kt-bud-ov="strategy_lines">—</span>
</li>
</ul>
<button type="button" class="text-primary font-body-md font-medium flex items-center gap-1 hover:underline" data-kt-bud-action="open-lines" data-testid="kt-bud-overview-view-lines">
View budget lines <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
</button>
</div>
</div>
</div>
<div class="bg-surface-container-lowest border border-status-reserved rounded-xl p-card-padding relative overflow-hidden" data-testid="kt-bud-overview-attention" hidden>
<div class="absolute top-0 left-0 w-1 h-full bg-status-reserved"></div>
<div class="flex items-start gap-3">
<div class="text-status-reserved shrink-0 mt-0.5">
<span class="material-symbols-outlined">warning</span>
</div>
<div>
<h3 class="font-headline-sm text-on-surface mb-1">Attention Required</h3>
<p class="font-body-md text-on-surface-variant mb-3" data-kt-bud-ov="attention_text">—</p>
<button type="button" class="px-3 py-1.5 rounded-lg border border-outline-variant text-on-surface font-body-md text-sm hover:bg-surface-container-low transition-colors" data-kt-bud-action="open-activity" data-testid="kt-bud-overview-review-activity">
Review funding activity
</button>
</div>
</div>
</div>
<div class="bg-surface-container border border-outline-variant rounded-xl p-4 text-sm font-body-md text-on-surface-variant" data-testid="kt-bud-overview-definition">
<div class="flex items-center gap-2 mb-2 font-medium text-on-surface">
<span class="material-symbols-outlined text-[18px]">lightbulb</span>
Definitional Note
</div>
<p class="leading-relaxed" data-kt-bud-ov="definition">Available equals approved funding less active reservations and contract commitments. Actual expenditure is shown separately because it is already included within commitments.</p>
</div>
</div>
</div>
</div>
</div>`;
};
