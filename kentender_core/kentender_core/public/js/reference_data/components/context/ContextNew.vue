<script setup>
import { reactive, computed, ref } from "vue";
import { referenceDataApi as api } from "../../data/referenceDataApi.js";

const props = defineProps({
	peOptions: { type: Array, default: () => [] }, // active PEs only: [{pe_id, code, legal_name}]
	fyOptions: { type: Array, default: () => [] }, // available FYs only: [{financial_year_id, label}]
});
const emit = defineEmits(["created", "cancel"]);

const form = reactive({ pe: "", fy: "", activeFrom: "", activeTo: "" });
const busy = ref(false);

const CORE_READINESS_UNASSESSED = [
	{ label: "Procuring Entity active", status: "Not assessed" },
	{ label: "Financial Year available", status: "Not assessed" },
	{ label: "PE type configured", status: "Not assessed" },
	{ label: "Timezone configured", status: "Not assessed" },
];

const canSave = computed(() => form.pe && form.fy && form.activeFrom && form.activeTo);

function toApiDatetime(localValue) {
	// <input type="datetime-local"> gives "YYYY-MM-DDTHH:mm" — the server (Datetime
	// fieldtype) expects "YYYY-MM-DD HH:mm:ss".
	return localValue ? `${localValue.replace("T", " ")}:00` : null;
}

async function saveDraft() {
	if (!canSave.value || busy.value) return;
	busy.value = true;
	try {
		const result = await api.createPeFyContext(form.pe, form.fy, toApiDatetime(form.activeFrom), toApiDatetime(form.activeTo));
		emit("created", result.context);
	} finally {
		busy.value = false;
	}
}

async function submitForReview() {
	if (!canSave.value || busy.value) return;
	busy.value = true;
	try {
		const result = await api.createPeFyContext(form.pe, form.fy, toApiDatetime(form.activeFrom), toApiDatetime(form.activeTo));
		await api.decidePeFyContext(result.context, "submit");
		emit("created", result.context);
	} finally {
		busy.value = false;
	}
}
</script>

<template>
	<div style="padding:36px 48px 0;display:flex;flex-direction:column;gap:10px">
		<h1 style="margin:0;font-size:38px;line-height:1.05;letter-spacing:.005em">{{ __("New PE/FY context") }}</h1>
		<p style="margin:0;font-size:15px;max-width:760px;color:color-mix(in srgb, var(--kt-color-text) 72%, transparent)">
			{{ __("Declare when a Procuring Entity and Financial Year combination is available to KenTender modules.") }}
		</p>
		<div style="margin-top:2px"><span class="kt-status is-draft">{{ __("Draft") }}</span></div>
	</div>

	<div style="margin:32px 48px 0;flex:1;display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,1fr);gap:24px;align-items:start">
		<div class="kt-card kt-blueprint">
			<h2 class="kt-card-title">{{ __("Context") }}</h2>
			<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px 28px">
				<div class="kt-field">
					<label>{{ __("Context ID") }}</label>
					<div class="kt-ro">{{ __("Not assigned") }}</div>
				</div>
				<div></div>
				<div class="kt-field">
					<label>{{ __("Procuring Entity") }}</label>
					<select class="kt-input" v-model="form.pe">
						<option value="" disabled>{{ __("Select procuring entity") }}</option>
						<option v-for="p in peOptions" :key="p.pe_id" :value="p.pe_id">{{ p.code }} — {{ p.legal_name }}</option>
					</select>
				</div>
				<div class="kt-field">
					<label>{{ __("Financial Year") }}</label>
					<select class="kt-input" v-model="form.fy">
						<option value="" disabled>{{ __("Select financial year") }}</option>
						<option v-for="f in fyOptions" :key="f.financial_year_id" :value="f.financial_year_id">{{ f.label }}</option>
					</select>
				</div>
				<div class="kt-field">
					<label>{{ __("Active from") }}</label>
					<input class="kt-input" type="datetime-local" v-model="form.activeFrom" />
				</div>
				<div class="kt-field">
					<label>{{ __("Active to") }}</label>
					<input class="kt-input" type="datetime-local" v-model="form.activeTo" />
				</div>
				<div class="kt-field">
					<label>{{ __("Timezone") }}</label>
					<div class="kt-ro">Africa/Nairobi</div>
				</div>
			</div>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
		</div>

		<div class="kt-card kt-blueprint">
			<h2 class="kt-card-title">{{ __("Core readiness") }}</h2>
			<dl style="margin:0">
				<div class="kt-row" v-for="c in CORE_READINESS_UNASSESSED" :key="c.label">
					<dt>{{ __(c.label) }}</dt>
					<dd><span class="kt-status is-pending">{{ __(c.status) }}</span></dd>
				</div>
			</dl>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
		</div>
	</div>

	<div style="border-top:1px solid var(--kt-color-divider);padding:20px 48px;display:flex;justify-content:flex-end;gap:14px;margin-top:32px">
		<button type="button" class="kt-btn kt-btn-ghost" :disabled="busy" @click="emit('cancel')">{{ __("Cancel") }}</button>
		<button type="button" class="kt-btn kt-btn-secondary" :disabled="!canSave || busy" @click="saveDraft">{{ __("Save draft") }}</button>
		<button type="button" class="kt-btn kt-btn-primary" :disabled="!canSave || busy" @click="submitForReview">{{ __("Submit for professional review") }}</button>
	</div>
</template>
