<script setup>
// §12.1.2 — Deactivate is confirmed with its impact, not performed silently.
// Reactivate reuses the same dialog with its own copy.
import { nextTick, onMounted, ref } from "vue";

const props = defineProps({
	title: { type: String, required: true },
	body: { type: String, required: true },
	confirmLabel: { type: String, required: true },
	destructive: { type: Boolean, default: false },
	error: { type: String, default: "" },
	busy: { type: Boolean, default: false },
	// Kept default-compatible with the original Organisation units caller;
	// a second caller (e.g. Procurement settings) passes its own so the two
	// screens' dialogs are independently selectable in a test.
	testid: { type: String, default: "kt-ou-confirm" },
});
const emit = defineEmits(["confirm", "cancel"]);

// The dialog takes focus when it opens, on the safe choice.
const cancelButton = ref(null);
onMounted(async () => {
	await nextTick();
	cancelButton.value?.focus();
});
</script>

<template>
	<div class="dialog-backdrop">
		<div
			class="dialog kt-narrow"
			:role="destructive ? 'alertdialog' : 'dialog'"
			aria-modal="true"
			:aria-label="title"
			:data-testid="testid"
			@keydown.esc.stop="emit('cancel')"
		>
			<h2 class="dialog-title">{{ title }}</h2>
			<div class="dialog-body" style="display:flex;flex-direction:column;gap:14px">
				<p style="margin:0">{{ body }}</p>
				<div v-if="error" class="kt-notice is-critical" role="alert">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
					<div class="kt-notice-body">{{ error }}</div>
				</div>
			</div>
			<div class="dialog-actions">
				<button ref="cancelButton" type="button" class="btn btn-secondary" :disabled="busy" @click="emit('cancel')">{{ __("Cancel") }}</button>
				<button
					type="button"
					class="btn btn-primary"
					:class="{ 'kt-danger': destructive }"
					:disabled="busy"
					data-testid="kt-ou-confirm-accept"
					@click="emit('confirm')"
				>{{ confirmLabel }}</button>
			</div>
		</div>
	</div>
</template>
