<script setup>
// §12.1.2 — Deactivate is confirmed with its impact, not performed silently.
// Reactivate reuses the same dialog with its own copy.
defineProps({
	title: { type: String, required: true },
	body: { type: String, required: true },
	confirmLabel: { type: String, required: true },
	destructive: { type: Boolean, default: false },
	error: { type: String, default: "" },
	busy: { type: Boolean, default: false },
});
const emit = defineEmits(["confirm", "cancel"]);
</script>

<template>
	<div class="kt-dialog-backdrop" @click.self="emit('cancel')">
		<div
			class="kt-dialog kt-blueprint kt-narrow"
			role="dialog"
			aria-modal="true"
			:aria-label="title"
			data-testid="kt-ou-confirm"
			@keydown.esc="emit('cancel')"
		>
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<h2 class="kt-dialog-title">{{ title }}</h2>
			<p class="kt-confirm-body">{{ body }}</p>
			<p v-if="error" class="kt-inline-error" role="alert">{{ error }}</p>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" @click="emit('cancel')">
					{{ __("Cancel") }}
				</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					:class="{ 'kt-danger': destructive }"
					:disabled="busy"
					data-testid="kt-ou-confirm-accept"
					@click="emit('confirm')"
				>{{ confirmLabel }}</button>
			</div>
		</div>
	</div>
</template>
