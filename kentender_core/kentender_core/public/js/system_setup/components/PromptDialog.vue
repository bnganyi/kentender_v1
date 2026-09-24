<script setup>
// One in-Vue dialog for the two single-field commands: AUTH-DES-02's Add
// organisation unit (ported from C05 #auth-des-02 — context shown as a
// read-only field, the helper line under the name) and Edit name. frappe.confirm()/frappe.ui.Dialog render outside the Vue root and
// inherit neither its state nor its Industry styles (AGENTS.md §6.3), so every
// dialog on these surfaces is built here instead.
import { nextTick, onMounted, ref, watch } from "vue";

defineProps({
	title: { type: String, required: true },
	label: { type: String, required: true },
	modelValue: { type: String, default: "" },
	confirmLabel: { type: String, required: true },
	// Read-only context rows shown above the field: [{label, value}].
	context: { type: Array, default: () => [] },
	// Helper line under the field (AUTH-DES-02's "The unit code is
	// generated when you save.").
	hint: { type: String, default: "" },
	error: { type: String, default: "" },
	busy: { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue", "confirm", "cancel"]);

const field = ref(null);
onMounted(async () => {
	await nextTick();
	field.value?.focus();
	field.value?.select();
});
</script>

<template>
	<div class="kt-dialog-backdrop">
		<div
			class="kt-dialog kt-narrow"
			role="dialog"
			aria-modal="true"
			aria-labelledby="kt-prompt-title"
			data-testid="kt-ou-prompt"
			@keydown.esc.stop="emit('cancel')"
		>
			<h2 id="kt-prompt-title" class="kt-dialog-title">{{ title }}</h2>
			<div class="dialog-body" style="display:flex;flex-direction:column;gap:14px">
				<div v-for="(row, index) in context" :key="row.label" class="kt-field">
					<label :for="'kt-prompt-context-' + index">{{ row.label }}</label>
					<input :id="'kt-prompt-context-' + index" class="kt-input" type="text" readonly :value="row.value" style="background:var(--kt-color-surface-2)">
				</div>
				<div class="kt-field">
					<label for="kt-prompt-input">{{ label }}</label>
					<input
						id="kt-prompt-input"
						ref="field"
						class="kt-input"
						type="text"
						:value="modelValue"
						:aria-invalid="error ? 'true' : 'false'"
						data-testid="kt-ou-prompt-input"
						@input="emit('update:modelValue', $event.target.value)"
						@keydown.enter.prevent="emit('confirm')"
					>
					<span v-if="hint" class="text-muted" style="font-size:13px">{{ hint }}</span>
				</div>
				<div v-if="error" class="kt-notice is-critical" role="alert" data-testid="kt-ou-prompt-error">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
					<div class="kt-notice-body">{{ error }}</div>
				</div>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" @click="emit('cancel')">{{ __("Cancel") }}</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					:disabled="busy || !modelValue.trim()"
					data-testid="kt-ou-prompt-confirm"
					@click="emit('confirm')"
				>{{ confirmLabel }}</button>
			</div>
		</div>
	</div>
</template>
