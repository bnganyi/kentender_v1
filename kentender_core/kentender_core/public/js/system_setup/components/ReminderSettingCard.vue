<script setup>
// C04-eligibility-reminder — the approaching-milestone threshold: an
// operational reminder period, expressly not a statutory deadline (§5.5.1B).
import { computed, ref, watch } from "vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";

const props = defineProps({ days: { type: Number, default: 7 } });
const emit = defineEmits(["saved"]);

const value = ref(String(props.days));
watch(() => props.days, (days) => (value.value = String(days)));
const error = ref("");
const notice = ref("");
const { pending: busy, run } = kentender_core.desk_page.createCommandRunner(
	{ ref },
	{ onStart: () => { error.value = ""; notice.value = ""; }, onError: (e) => (error.value = e.message) }
);
const dirty = computed(() => String(props.days) !== value.value.trim());
const canSave = computed(() => !busy.value && dirty.value && /^\d+$/.test(value.value.trim()));

function save() {
	return run(async () => {
		await procurementSettingsApi.setReminderThresholdDays(Number(value.value.trim()));
		notice.value = __("Changes saved.");
		emit("saved");
	});
}
</script>

<template>
	<div class="kt-card kt-blueprint kt-procset-narrow" data-testid="kt-procset-reminder">
		<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
		<h3 class="kt-card-title">{{ __("Approaching milestone threshold") }}</h3>
		<div class="kt-field kt-procset-days">
			<label for="kt-reminder-days">{{ __("Days") }}</label>
			<input id="kt-reminder-days" v-model="value" class="kt-input" inputmode="numeric" data-testid="kt-reminder-days">
		</div>
		<p class="kt-hint">{{ __("Operational reminder period; not a statutory procurement deadline.") }}</p>
		<p v-if="error" class="kt-inline-error" role="alert" data-testid="kt-reminder-error">{{ error }}</p>
		<p v-else-if="notice" class="kt-setup-success" data-testid="kt-reminder-success">{{ notice }}</p>
		<div class="kt-procset-card-actions">
			<button type="button" class="kt-btn kt-btn-primary" :disabled="!canSave" data-testid="kt-reminder-save" @click="save">{{ __("Save changes") }}</button>
		</div>
	</div>
</template>
