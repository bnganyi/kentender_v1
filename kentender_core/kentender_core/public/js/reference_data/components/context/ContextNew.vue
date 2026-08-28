<script setup>
import { reactive, computed, ref, watch } from "vue";
import { referenceDataApi as api } from "../../data/referenceDataApi.js";
import { classifyApiError } from "../../data/apiError.js";
import KtErrorBanner from "../KtErrorBanner.vue";

const props = defineProps({
	peOptions: { type: Array, default: () => [] }, // active PEs only: [{pe_id, code, legal_name}]
	fyOptions: { type: Array, default: () => [] }, // available FYs only: [{financial_year_id, label}]
});
const emit = defineEmits(["created", "cancel"]);

const form = reactive({ pe: "", fy: "", activeFrom: "", activeTo: "" });
const busy = ref(false);
const fieldErrors = reactive({});
const bannerError = ref("");

const FIELD_MAP = {
	PE_NOT_ACTIVE: "pe",
	FY_NOT_AVAILABLE: "fy",
	PEFY_CONTEXT_DUPLICATE: "fy",
	PEFY_DATES_INVALID: "activeTo",
};

watch(() => form.pe, () => delete fieldErrors.pe);
watch(() => form.fy, () => delete fieldErrors.fy);
watch([() => form.activeFrom, () => form.activeTo], () => delete fieldErrors.activeTo);

function clearErrors() {
	bannerError.value = "";
	Object.keys(fieldErrors).forEach((k) => delete fieldErrors[k]);
}

function showError(err) {
	const { field, message, banner } = classifyApiError(err, FIELD_MAP);
	if (field) fieldErrors[field] = message;
	else bannerError.value = banner;
}

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

async function enableContext() {
	if (!canSave.value || busy.value) return;
	busy.value = true;
	clearErrors();
	try {
		const result = await api.enablePeFyContext(form.pe, form.fy, toApiDatetime(form.activeFrom), toApiDatetime(form.activeTo));
		emit("created", result.context);
	} catch (err) {
		showError(err);
	} finally {
		busy.value = false;
	}
}
</script>

<template>
	<div style="padding:36px 48px 0;display:flex;flex-direction:column;gap:10px">
		<h1 style="margin:0;font-size:38px;line-height:1.05;letter-spacing:.005em">{{ __("Enable PE for financial year") }}</h1>
		<p style="margin:0;font-size:15px;max-width:760px;color:color-mix(in srgb, var(--kt-color-text) 72%, transparent)">
			{{ __("Declare when a Procuring Entity and Financial Year combination is available to KenTender modules.") }}
		</p>
	</div>

	<div style="margin:32px 48px 0;flex:1;display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,1fr);gap:24px;align-items:start">
		<div style="grid-column:1 / -1"><KtErrorBanner :message="bannerError" @dismiss="bannerError = ''" /></div>

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
					<select class="kt-input" v-model="form.pe" :style="fieldErrors.pe ? 'border-color:#b0143a' : ''">
						<option value="" disabled>{{ __("Select procuring entity") }}</option>
						<option v-for="p in peOptions" :key="p.pe_id" :value="p.pe_id">{{ p.code }} — {{ p.legal_name }}</option>
					</select>
					<div v-if="fieldErrors.pe" style="color:#b0143a;font-size:12px;margin-top:4px">{{ fieldErrors.pe }}</div>
				</div>
				<div class="kt-field">
					<label>{{ __("Financial Year") }}</label>
					<select class="kt-input" v-model="form.fy" :style="fieldErrors.fy ? 'border-color:#b0143a' : ''">
						<option value="" disabled>{{ __("Select financial year") }}</option>
						<option v-for="f in fyOptions" :key="f.financial_year_id" :value="f.financial_year_id">{{ f.label }}</option>
					</select>
					<div v-if="fieldErrors.fy" style="color:#b0143a;font-size:12px;margin-top:4px">{{ fieldErrors.fy }}</div>
				</div>
				<div class="kt-field">
					<label>{{ __("Active from") }}</label>
					<input class="kt-input" type="datetime-local" v-model="form.activeFrom" />
				</div>
				<div class="kt-field">
					<label>{{ __("Active to") }}</label>
					<input
						class="kt-input"
						type="datetime-local"
						v-model="form.activeTo"
						:style="fieldErrors.activeTo ? 'border-color:#b0143a' : ''"
					/>
					<div v-if="fieldErrors.activeTo" style="color:#b0143a;font-size:12px;margin-top:4px">{{ fieldErrors.activeTo }}</div>
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
		<button type="button" class="kt-btn kt-btn-primary" :disabled="!canSave || busy" @click="enableContext">{{ __("Enable context") }}</button>
	</div>
</template>
