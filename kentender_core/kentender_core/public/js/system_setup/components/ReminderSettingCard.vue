<script setup>
// CFG-CHG-002 v0.14 §10.10 (Reminders #unchanged/#edited/#zero/#invalid;
// tracker CFG14-5G) — ported from the board, flat in the Procurement settings
// view like the other sections. The board's "Unchanged / Edited / Zero /
// Invalid range" tags label its specimens and are not drawn.
//
// The approaching-milestone
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
const dirty = computed(() => String(props.days) !== String(value.value).trim());
// §10.10 — a whole number of calendar days, 0–365; the server refuses the
// same range, this only states it before the round trip.
const valid = computed(() => {
	const text = String(value.value).trim();
	return /^\d+$/.test(text) && Number(text) <= 365;
});
const canSave = computed(() => !busy.value && dirty.value && valid.value);
const rangeError = computed(() => (dirty.value && !valid.value ? __("Enter a whole number from 0 to 365.") : ""));

function save() {
	return run(async () => {
		await procurementSettingsApi.setReminderThresholdDays(Number(String(value.value).trim()));
		notice.value = __("Changes saved.");
		emit("saved");
	});
}
</script>

<template>
	<div class="kt-reminders" data-testid="kt-procset-reminder">
		<h3>{{ __("Reminders") }}</h3>
		<div class="kt-field">
			<label for="kt-reminder-days">{{ __("Remind users this many days before a milestone") }}</label>
			<input
				id="kt-reminder-days"
				v-model="value"
				class="kt-input"
				type="number"
				min="0"
				max="365"
				inputmode="numeric"
				:aria-invalid="rangeError ? 'true' : 'false'"
				data-testid="kt-reminder-days"
			>
		</div>
		<p class="text-muted" style="font-size:12px">{{ __("Unit: Calendar days") }}</p>
		<p class="text-muted" style="font-size:12px">{{ __("This changes reminder timing, not procurement deadlines.") }}</p>
		<p class="text-muted" style="font-size:12px">{{ __("Use 0 to begin reminders on the milestone date; overdue reminders still apply.") }}</p>
		<div v-if="rangeError || error" class="kt-notice is-critical" role="alert" :data-testid="rangeError ? 'kt-reminder-range-error' : 'kt-reminder-error'">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
			<div class="kt-notice-body">{{ rangeError || error }}</div>
		</div>
		<!-- After a save only (a later state than the board's specimens). -->
		<div v-else-if="notice" class="kt-notice is-live" role="status" data-testid="kt-reminder-success">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M5 12l5 5L20 7" /></svg>
			<div class="kt-notice-body">{{ notice }}</div>
		</div>
		<div style="display:flex;justify-content:flex-end;margin-top:12px">
			<button type="button" class="kt-btn kt-btn-primary" :disabled="!canSave" data-testid="kt-reminder-save" @click="save">{{ __("Save changes") }}</button>
		</div>
	</div>
</template>
