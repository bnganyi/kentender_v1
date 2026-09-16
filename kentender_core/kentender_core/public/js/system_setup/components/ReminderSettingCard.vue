<script setup>
// CFG-CHG-002 v0.11 §10.10 (Reminders.dc.html) — the approaching-milestone
// threshold, stated as what the administrator is actually setting ("Remind
// users this many days before a milestone") with its unit and both
// consequences spelled out: this is reminder timing, expressly not a
// statutory procurement deadline (§5.5.1B).
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
// §10.10 — a whole number of calendar days, 0–365; the server refuses the
// same range, this only states it before the round trip.
const valid = computed(() => {
	const text = value.value.trim();
	return /^\d+$/.test(text) && Number(text) <= 365;
});
const canSave = computed(() => !busy.value && dirty.value && valid.value);
const rangeError = computed(() => (dirty.value && !valid.value ? __("Enter a whole number from 0 to 365.") : ""));

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
		<h3 class="kt-card-title">{{ __("Reminders") }}</h3>
		<div class="kt-field kt-procset-days">
			<label for="kt-reminder-days">{{ __("Remind users this many days before a milestone") }}</label>
			<input id="kt-reminder-days" v-model="value" class="kt-input" inputmode="numeric" data-testid="kt-reminder-days">
		</div>
		<p class="kt-hint">{{ __("Unit: Calendar days") }}</p>
		<p class="kt-hint">{{ __("This changes reminder timing, not procurement deadlines.") }}</p>
		<p class="kt-hint">{{ __("Use 0 to begin reminders on the milestone date; overdue reminders still apply.") }}</p>
		<p v-if="rangeError" class="kt-inline-error" role="alert" data-testid="kt-reminder-range-error">{{ rangeError }}</p>
		<p v-else-if="error" class="kt-inline-error" role="alert" data-testid="kt-reminder-error">{{ error }}</p>
		<p v-else-if="notice" class="kt-setup-success" data-testid="kt-reminder-success">{{ notice }}</p>
		<div class="kt-procset-card-actions">
			<button type="button" class="kt-btn kt-btn-primary" :disabled="!canSave" data-testid="kt-reminder-save" @click="save">{{ __("Save changes") }}</button>
		</div>
	</div>
</template>
