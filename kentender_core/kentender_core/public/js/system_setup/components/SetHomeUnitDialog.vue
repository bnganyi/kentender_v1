<script setup>
// AUTH-ADR-001 v1.12 AUTH-DES-11 — set, change or clear one person's home
// organisation unit. A focused dialog: the person (read-only), the unit, and
// the sentence that says what this records and what it does not. Built in-Vue
// (AGENTS.md §6.3), not with frappe.ui.Dialog.
import { nextTick, onMounted, ref } from "vue";

const props = defineProps({
	row: { type: Object, required: true },
	units: { type: Array, default: () => [] },
	busy: { type: Boolean, default: false },
	error: { type: String, default: "" },
});
const emit = defineEmits(["save", "clear", "cancel"]);

const chosen = ref(props.row.organisation_unit || "");
const field = ref(null);
const recorded = !!props.row.organisation_unit;

onMounted(async () => {
	await nextTick();
	field.value?.focus();
});
</script>

<template>
	<div class="dialog-backdrop">
		<div class="dialog kt-narrow" role="dialog" aria-modal="true" aria-labelledby="kt-home-unit-title" data-testid="kt-home-unit-dialog" @keydown.esc.stop="emit('cancel')">
			<h2 id="kt-home-unit-title" class="dialog-title">{{ recorded ? __("Change home unit") : __("Set home unit") }}</h2>
			<div class="dialog-body" style="display:flex;flex-direction:column;gap:14px">
				<div class="field">
					<span class="kt-label">{{ __("Staff member") }}</span>
					<div data-testid="kt-home-unit-person">{{ row.full_name }} · {{ row.user }}</div>
				</div>
				<div class="field">
					<label for="kt-home-unit-select">{{ __("Home organisation unit") }}</label>
					<select id="kt-home-unit-select" ref="field" v-model="chosen" class="input" data-testid="kt-home-unit-select">
						<option value="" disabled>{{ __("Choose an organisation unit") }}</option>
						<option v-for="unit in units" :key="unit.value" :value="unit.value">{{ unit.label }}</option>
					</select>
					<p class="text-muted" style="margin:6px 0 0;font-size:13px">{{ __("This records where the person works. It does not grant any responsibility or access.") }}</p>
				</div>
				<div v-if="error" class="kt-notice is-critical" role="alert" data-testid="kt-home-unit-error">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
					<div class="kt-notice-body">{{ error }}</div>
				</div>
			</div>
			<div class="dialog-actions" style="display:flex;gap:10px;align-items:center">
				<button v-if="recorded" type="button" class="btn btn-ghost" style="margin-right:auto" :disabled="busy" data-testid="kt-home-unit-clear" @click="emit('clear')">{{ __("Clear home unit") }}</button>
				<button type="button" class="btn btn-secondary" :disabled="busy" data-testid="kt-home-unit-cancel" @click="emit('cancel')">{{ __("Cancel") }}</button>
				<button type="button" class="btn btn-primary" :disabled="busy || !chosen" data-testid="kt-home-unit-save" @click="emit('save', chosen)">{{ __("Save home unit") }}</button>
			</div>
		</div>
	</div>
</template>
