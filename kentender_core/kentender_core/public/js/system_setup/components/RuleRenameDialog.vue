<script setup>
// CFG-CHG-002 v0.14 §10.6 (C03BC #rename; tracker CFG14-5D) — "Edit rule
// name": the display name only. The identifier and kind never change, and a
// rename writes no new version. Escape stops here: Frappe's window-level
// Escape handler would otherwise blur the control focus returns to (FU-25).
import { nextTick, onMounted, ref } from "vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";

const props = defineProps({
	referenceSet: { type: String, required: true },
	name: { type: String, default: "" },
	expectedVersion: { type: String, default: "" },
});
const emit = defineEmits(["saved", "cancel"]);

const value = ref(props.name);
const error = ref("");
const field = ref(null);
const { pending: busy, run } = kentender_core.desk_page.createCommandRunner(
	{ ref },
	{ onStart: () => (error.value = ""), onError: (e) => (error.value = e.message) }
);

onMounted(async () => {
	await nextTick();
	field.value?.focus();
	field.value?.select();
});

function save() {
	if (busy.value || !value.value.trim()) return;
	return run(async () => {
		await procurementSettingsApi.renameRegulatoryReference(props.referenceSet, value.value.trim(), props.expectedVersion);
		emit("saved");
	});
}
</script>

<template>
	<div class="kt-dialog-backdrop">
		<div
			class="kt-dialog kt-narrow"
			role="dialog"
			aria-modal="true"
			:aria-label="__('Edit rule name')"
			data-testid="kt-procset-rule-rename-dialog"
			@keydown.esc.stop="emit('cancel')"
		>
			<h2 class="kt-dialog-title">{{ __("Edit rule name") }}</h2>
			<div class="dialog-body">
				<div class="kt-field">
					<label for="kt-rule-rename">{{ __("Rule name") }}</label>
					<input
						id="kt-rule-rename"
						ref="field"
						v-model="value"
						class="kt-input"
						data-testid="kt-procset-rule-rename-input"
						@keydown.enter.prevent="save"
					>
				</div>
				<div v-if="error" class="kt-notice is-critical" role="alert" data-testid="kt-procset-rule-rename-error">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
					<div class="kt-notice-body">{{ error }}</div>
				</div>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" data-testid="kt-procset-rule-rename-cancel" @click="emit('cancel')">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="busy || !value.trim()" data-testid="kt-procset-rule-rename-save" @click="save">{{ __("Save changes") }}</button>
			</div>
		</div>
	</div>
</template>
