<!-- §12.1 — several eligible contexts require explicit selection before rows
     are requested. Reuses the same <select class="kt-input"> inside a
     .kt-card.kt-blueprint.kt-empty that the Budget working-context picker
     uses, so the two modules present the same control.

     Departmental Needs is scoped by PE *and* department, so the picker offers
     the PE/OU pair the §8.1 resolve_needs_contexts contract returns — not the
     PE/FY pair Budget uses. Selecting a context is a filter over an already
     authorised scope; it never grants authority (§6). -->
<template>
	<div class="kt-card kt-blueprint kt-empty" data-testid="nds-context-picker">
		<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
		<i class="kt-corner bl"></i><i class="kt-corner br"></i>
		<h2>Select a department</h2>
		<p class="kt-muted">
			You work in more than one department. Choose the one whose needs you want to see.
		</p>
		<div style="display: flex; gap: 12px; margin-top: 8px">
			<select
				class="kt-input"
				style="max-width: 420px"
				:value="contextKey"
				data-testid="nds-context-select"
				@change="$emit('select-context', $event.target.value)"
			>
				<option value="" disabled>Choose a Procuring Entity and department…</option>
				<option v-for="option in contexts" :key="key(option)" :value="key(option)">
					{{ label(option) }}
				</option>
			</select>
			<select
				v-if="financialYears.length > 1"
				class="kt-input"
				style="max-width: 220px"
				:value="financialYear"
				data-testid="nds-fy-select"
				@change="$emit('select-financial-year', $event.target.value)"
			>
				<option value="" disabled>Financial Year…</option>
				<option v-for="fy in financialYears" :key="fy.id" :value="fy.id">
					{{ fy.label || fy.id }}
				</option>
			</select>
		</div>
	</div>
</template>

<script setup>
defineProps({
	contexts: { type: Array, default: () => [] },
	financialYears: { type: Array, default: () => [] },
	contextKey: { type: String, default: "" },
	financialYear: { type: String, default: "" },
});
defineEmits(["select-context", "select-financial-year"]);

function key(option) {
	return `${option.procuring_entity}::${option.organisation_unit}`;
}

function label(option) {
	return `${option.procuring_entity_label} · ${option.organisation_unit_label}`;
}
</script>
