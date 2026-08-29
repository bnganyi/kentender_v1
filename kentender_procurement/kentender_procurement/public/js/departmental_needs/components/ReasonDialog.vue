<!-- NDS-DES-11 / 13a / 13b — the reason dialogs. One component: the three
     artboards differ only in title, lede, button label and tone, and §11.13
     forbids any extra control in all of them.

     §12.8 requires focus to be trapped and restored. -->
<template>
	<div class="kt-dialog-backdrop" @mousedown.self="$emit('cancel')">
		<div
			ref="dialogEl"
			class="kt-dialog"
			role="dialog"
			aria-modal="true"
			:aria-labelledby="titleId"
			@keydown.esc.prevent="$emit('cancel')"
			@keydown.tab="trapFocus"
		>
			<div :id="titleId" class="kt-dialog-title">{{ title }}</div>
			<div class="kt-dialog-body">
				<p style="margin: 0 0 16px; font-size: 14.5px; color: var(--color-neutral-700)">
					{{ lede }}
				</p>
				<div class="kt-field">
					<label :for="fieldId">Reason</label>
					<textarea
						:id="fieldId"
						ref="reasonEl"
						class="kt-input"
						rows="4"
						:value="modelValue"
						@input="$emit('update:modelValue', $event.target.value)"
					></textarea>
					<div v-if="error" class="kt-field-error">{{ error }}</div>
					<div v-else style="font-size: 12.5px; color: var(--color-neutral-600); margin-top: 6px">
						{{ minLength }}–{{ maxLength }} characters.
					</div>
				</div>
			</div>
			<div class="kt-dialog-actions">
				<button class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">
					Cancel
				</button>
				<button
					:class="destructive ? 'kt-btn-destructive' : 'kt-btn kt-btn-primary'"
					:disabled="pending"
					@click="$emit('confirm')"
				>
					{{ confirmLabel }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from "vue";

defineProps({
	title: { type: String, required: true },
	lede: { type: String, required: true },
	confirmLabel: { type: String, required: true },
	modelValue: { type: String, default: "" },
	error: { type: String, default: "" },
	pending: Boolean,
	destructive: Boolean,
	minLength: { type: Number, default: 20 },
	maxLength: { type: Number, default: 1000 },
});
defineEmits(["update:modelValue", "confirm", "cancel"]);

const dialogEl = ref(null);
const reasonEl = ref(null);
const titleId = `nds-dialog-title-${Math.random().toString(16).slice(2)}`;
const fieldId = `nds-dialog-reason-${Math.random().toString(16).slice(2)}`;
let restoreTo = null;

onMounted(() => {
	restoreTo = document.activeElement;
	reasonEl.value?.focus();
});
onBeforeUnmount(() => {
	// §12.8 — focus returns to whatever opened the dialog.
	if (restoreTo && typeof restoreTo.focus === "function") restoreTo.focus();
});

function trapFocus(event) {
	const focusable = dialogEl.value?.querySelectorAll(
		'button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
	);
	if (!focusable || !focusable.length) return;
	const first = focusable[0];
	const last = focusable[focusable.length - 1];
	if (event.shiftKey && document.activeElement === first) {
		event.preventDefault();
		last.focus();
	} else if (!event.shiftKey && document.activeElement === last) {
		event.preventDefault();
		first.focus();
	}
}
</script>
