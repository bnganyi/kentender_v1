<script setup>
import { reactive, computed, ref } from "vue";
import { referenceDataApi as api } from "../../data/referenceDataApi.js";

const emit = defineEmits(["created", "cancel"]);

const form = reactive({ startYear: new Date().getFullYear() + 1 });
const busy = ref(false);

// Client-side preview only — the server (Financial Year.autoname/validate) is the
// sole source of truth and regenerates these itself; this mirrors that rule just
// for the read-only preview fields, never sent as input.
const startYearInt = computed(() => parseInt(form.startYear, 10) || 0);
const preview = computed(() => {
	const y = startYearInt.value;
	if (!y) return null;
	const endY = y + 1;
	return {
		label: `${y}/${String(endY).slice(-2)}`,
		startDate: `1 Jul ${y}`,
		endDate: `30 Jun ${endY}`,
	};
});
const canSave = computed(() => startYearInt.value > 2000 && startYearInt.value < 2200);

async function saveDraft() {
	if (!canSave.value || busy.value) return;
	busy.value = true;
	try {
		const result = await api.createFinancialYear(startYearInt.value);
		emit("created", result.financial_year);
	} finally {
		busy.value = false;
	}
}

async function submitForApproval() {
	if (!canSave.value || busy.value) return;
	busy.value = true;
	try {
		const result = await api.createFinancialYear(startYearInt.value);
		await api.submitFinancialYear(result.financial_year);
		emit("created", result.financial_year);
	} finally {
		busy.value = false;
	}
}
</script>

<template>
	<div style="padding:36px 48px 0;display:flex;flex-direction:column;gap:12px">
		<h1 style="margin:0;font-size:38px;line-height:1.05;letter-spacing:.005em">{{ __("New financial year") }}</h1>
		<div><span class="kt-status is-draft">{{ __("Draft") }}</span></div>
	</div>

	<div style="margin:36px 48px 0;flex:1">
		<div class="kt-card kt-blueprint" style="max-width:920px">
			<h2 class="kt-card-title">{{ __("Financial year") }}</h2>
			<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px 28px">
				<div class="kt-field">
					<label>{{ __("Start year") }}</label>
					<input class="kt-input" type="number" v-model="form.startYear" />
				</div>
				<div class="kt-field">
					<label>{{ __("Financial year") }}</label>
					<div class="kt-ro">{{ preview?.label || "—" }}</div>
				</div>
				<div class="kt-field">
					<label>{{ __("Start date") }}</label>
					<div class="kt-ro">{{ preview?.startDate || "—" }}</div>
				</div>
				<div class="kt-field">
					<label>{{ __("End date") }}</label>
					<div class="kt-ro">{{ preview?.endDate || "—" }}</div>
				</div>
				<div class="kt-field">
					<label>{{ __("Timezone") }}</label>
					<div class="kt-ro">Africa/Nairobi</div>
				</div>
			</div>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
		</div>
	</div>

	<div style="border-top:1px solid var(--kt-color-divider);padding:20px 48px;display:flex;justify-content:flex-end;gap:14px">
		<button type="button" class="kt-btn kt-btn-ghost" :disabled="busy" @click="emit('cancel')">{{ __("Cancel") }}</button>
		<button type="button" class="kt-btn kt-btn-secondary" :disabled="!canSave || busy" @click="saveDraft">{{ __("Save draft") }}</button>
		<button type="button" class="kt-btn kt-btn-primary" :disabled="!canSave || busy" @click="submitForApproval">{{ __("Submit for approval") }}</button>
	</div>
</template>
