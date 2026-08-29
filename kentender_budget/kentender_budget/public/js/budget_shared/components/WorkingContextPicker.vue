<script setup>
// BUD-CHG-001 v1.2 Phase 8 — shown wherever a screen has no explicit
// Budget/Version/Line id in its own URL (BUD-UI-01's workspace, BUD-UI-02's
// pre-creation form) and the working PE/FY context is ambiguous. Reuses the
// exact <select class="kt-input"> + read-only fallback pattern already used
// for Organisation Unit / Funding Source pickers elsewhere in this bundle.
defineProps({
	loading: { type: Boolean, default: false },
	mode: { type: String, default: "none" },
	contexts: { type: Array, default: () => [] },
	selected: { type: Object, default: null },
});
const emit = defineEmits(["select"]);

function label(ctx) {
	return `${ctx.procuring_entity.name} · ${ctx.financial_year.label} (${ctx.context_status})`;
}
function onChange(e) {
	emit("select", e.target.value);
}
</script>

<template>
	<div class="kt-card kt-blueprint kt-empty" data-testid="working-context-picker">
		<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>

		<template v-if="loading">
			<div class="kt-skel" style="width: 280px; height: 20px"></div>
		</template>

		<template v-else-if="mode === 'none'">
			<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="color: var(--kt-color-accent-800)">
				<rect x="5" y="11" width="14" height="10" rx="1" /><path d="M8 11V7a4 4 0 0 1 8 0v4" />
			</svg>
			<h2>{{ __("You have no assigned Procuring Entity / Financial Year context.") }}</h2>
			<p class="kt-muted">{{ __("Ask your KenTender administrator to assign a Procuring Entity before using Budget & Funding.") }}</p>
		</template>

		<template v-else-if="mode === 'single'">
			<div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Working context") }}</div>
			<div style="font-size: 15px; font-weight: 500" data-testid="working-context-single">{{ label(contexts[0]) }}</div>
		</template>

		<template v-else>
			<div class="kt-eyebrow" style="margin-bottom: 8px">{{ __("Select a working context") }}</div>
			<select class="kt-input" style="max-width: 420px" :value="selected?.context_id || ''" @change="onChange" data-testid="working-context-select">
				<option value="" disabled>{{ __("Choose Procuring Entity / Financial Year…") }}</option>
				<option v-for="ctx in contexts" :key="ctx.context_id" :value="ctx.context_id">{{ label(ctx) }}</option>
			</select>
		</template>
	</div>
</template>
