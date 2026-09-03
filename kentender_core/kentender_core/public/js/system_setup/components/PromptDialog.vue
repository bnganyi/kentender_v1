<script setup>
// One in-Vue dialog for the two single-field commands (§12.1.2's add dialog and
// Edit name). frappe.confirm()/frappe.ui.Dialog render outside the Vue root and
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
	<div class="kt-dialog-backdrop" @click.self="emit('cancel')">
		<div
			class="kt-dialog kt-blueprint kt-narrow"
			role="dialog"
			aria-modal="true"
			:aria-label="title"
			data-testid="kt-ou-prompt"
			@keydown.esc="emit('cancel')"
		>
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<h2 class="kt-dialog-title">{{ title }}</h2>
			<div class="kt-dialog-fields">
				<div v-for="row in context" :key="row.label" class="kt-field">
					<label>{{ row.label }}</label>
					<div class="kt-ro">{{ row.value }}</div>
				</div>
				<div class="kt-field">
					<label :for="'kt-prompt-input'">{{ label }}</label>
					<input
						id="kt-prompt-input"
						ref="field"
						class="kt-input"
						:value="modelValue"
						:aria-invalid="!!error"
						data-testid="kt-ou-prompt-input"
						@input="emit('update:modelValue', $event.target.value)"
						@keydown.enter.prevent="emit('confirm')"
					>
					<p v-if="hint" class="kt-hint">{{ hint }}</p>
					<p v-if="error" class="kt-inline-error" role="alert">{{ error }}</p>
				</div>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" @click="emit('cancel')">
					{{ __("Cancel") }}
				</button>
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
