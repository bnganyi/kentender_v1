<script setup>
// C03-source-editor — one funding source: name and enabled. Rename is refused
// server-side while a Budget line version references the entry
// (`CFG_CATALOGUE_IN_USE`); no approval, no draft.
import { computed, nextTick, onMounted, ref } from "vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";

const props = defineProps({
	source: { type: Object, default: null },
	creating: { type: Boolean, default: false },
});
const emit = defineEmits(["saved", "cancel"]);

const label = ref(props.source?.label || "");
const enabled = ref(props.source ? !!props.source.enabled : true);
const error = ref("");
const field = ref(null);
const { pending: busy, run } = kentender_core.desk_page.createCommandRunner(
	{ ref },
	{ onStart: () => (error.value = ""), onError: (e) => (error.value = e.message) }
);

const title = computed(() => (props.creating ? __("Add funding source") : __("Edit funding source")));
const canSave = computed(() => !busy.value && label.value.trim().length >= 2);

onMounted(async () => {
	await nextTick();
	field.value?.focus();
});

function save() {
	return run(async () => {
		if (props.creating) {
			await procurementSettingsApi.addFundingSource(label.value.trim());
		} else {
			await procurementSettingsApi.updateFundingSource(
				props.source.name,
				{ label: label.value.trim(), enabled: enabled.value },
				props.source.expected_version
			);
		}
		emit("saved");
	});
}
</script>

<template>
	<div class="kt-procset-view" data-testid="kt-procset-source-editor">
		<div class="kt-section-head">
			<div>
				<span class="kt-eyebrow">{{ __("Procurement settings") }}</span>
				<h2 class="kt-section-title">{{ title }}</h2>
			</div>
		</div>
		<div class="kt-card kt-blueprint kt-procset-narrow">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<div class="kt-field">
				<label for="kt-fs-name">{{ __("Funding source name") }}</label>
				<input id="kt-fs-name" ref="field" v-model="label" class="kt-input" data-testid="kt-fs-name">
				<p v-if="source && source.referenced" class="kt-hint">{{ __("This source is referenced by a Budget line and cannot be renamed.") }}</p>
			</div>
			<label class="kt-setup-check">
				<input v-model="enabled" type="checkbox" :disabled="creating" data-testid="kt-fs-enabled">
				{{ __("Enabled") }}
			</label>
			<p v-if="error" class="kt-inline-error" role="alert" data-testid="kt-fs-error">{{ error }}</p>
		</div>
		<div class="kt-procset-footer kt-procset-narrow">
			<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" data-testid="kt-fs-cancel" @click="emit('cancel')">{{ __("Cancel") }}</button>
			<button type="button" class="kt-btn kt-btn-primary" :disabled="!canSave" data-testid="kt-fs-save" @click="save">{{ __("Save changes") }}</button>
		</div>
	</div>
</template>
