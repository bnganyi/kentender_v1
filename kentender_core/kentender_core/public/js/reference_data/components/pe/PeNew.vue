<script setup>
import { reactive, computed, ref, watch, onMounted } from "vue";
import { referenceDataApi as api } from "../../data/referenceDataApi.js";
import { classifyApiError } from "../../data/apiError.js";
import { quickCreate } from "../../composables/quickCreate.js";
import KtErrorBanner from "../KtErrorBanner.vue";

const props = defineProps({
	peTypes: { type: Array, default: () => [] },
	// When set, this screen edits that still-Draft PE instead of creating a new
	// one — Create draft and Activate are separate steps (§6.1), so a draft must
	// stay editable in between rather than being a dead end.
	editCode: { type: String, default: null },
});
const emit = defineEmits(["created", "cancel", "pe-type-created"]);
const editMode = computed(() => !!props.editCode);

const form = reactive({
	entityCode: "",
	peType: "",
	legalName: "",
	displayName: "",
	effectiveFrom: frappe.datetime.get_today(),
});
const busy = ref(false);
const loading = ref(false);
const fieldErrors = reactive({});
const bannerError = ref("");

onMounted(async () => {
	if (!props.editCode) return;
	loading.value = true;
	try {
		const detail = await api.getProcuringEntity(props.editCode);
		form.entityCode = detail.pe_id;
		form.peType = detail.version?.pe_type_code || "";
		form.legalName = detail.version?.legal_name || "";
		form.displayName = detail.version?.display_name || "";
		form.effectiveFrom = detail.effective_from || form.effectiveFrom;
	} finally {
		loading.value = false;
	}
});

// Only PE_CODE_DUPLICATE is tied to a specific field today; anything else
// (e.g. AUTH_ROLE_REQUIRED) surfaces as the page-level banner instead.
const FIELD_MAP = { PE_CODE_DUPLICATE: "entityCode" };

watch(() => form.entityCode, () => delete fieldErrors.entityCode);

function clearErrors() {
	bannerError.value = "";
	Object.keys(fieldErrors).forEach((k) => delete fieldErrors[k]);
}

function showError(err) {
	const { field, message, banner } = classifyApiError(err, FIELD_MAP);
	if (field) fieldErrors[field] = message;
	else bannerError.value = banner;
}

const canSave = computed(() => form.entityCode.trim() && form.peType && form.legalName.trim());

async function createPeType() {
	const doc = await quickCreate("PE Type");
	if (!doc) return;
	form.peType = doc.type_code;
	emit("pe-type-created");
}

function payload() {
	return {
		entity_code: form.entityCode.trim().toUpperCase(),
		legal_name: form.legalName.trim(),
		display_name: (form.displayName || form.legalName).trim(),
		pe_type_code: form.peType,
		effective_from: form.effectiveFrom,
	};
}

async function saveDraft() {
	if (!canSave.value || busy.value) return;
	busy.value = true;
	clearErrors();
	try {
		if (editMode.value) {
			await api.updatePeDraft(props.editCode, payload());
			emit("created", props.editCode);
		} else {
			const result = await api.createPe(payload());
			emit("created", result.pe);
		}
	} catch (err) {
		showError(err);
	} finally {
		busy.value = false;
	}
}

async function activateProcuringEntity() {
	if (!canSave.value || busy.value) return;
	busy.value = true;
	clearErrors();
	try {
		if (editMode.value) {
			await api.updatePeDraft(props.editCode, payload());
			await api.decidePeChange(props.editCode, "activate");
			emit("created", props.editCode);
		} else {
			const result = await api.createPe(payload());
			await api.decidePeChange(result.pe, "activate");
			emit("created", result.pe);
		}
	} catch (err) {
		showError(err);
	} finally {
		busy.value = false;
	}
}
</script>

<template>
	<div style="padding:36px 48px 0;display:flex;flex-direction:column;gap:12px">
		<h1 style="margin:0;font-size:38px;line-height:1.05;letter-spacing:.005em">
			{{ editMode ? __("Edit draft procuring entity") : __("New procuring entity") }}
		</h1>
		<div><span class="kt-status is-draft">{{ __("Draft") }}</span></div>
	</div>

	<div style="margin:36px 48px 0;flex:1;display:flex;flex-direction:column;gap:24px">
		<KtErrorBanner :message="bannerError" @dismiss="bannerError = ''" style="max-width:920px" />

		<div class="kt-card kt-blueprint" style="max-width:920px">
			<h2 class="kt-card-title">{{ __("Identity") }}</h2>
			<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px 28px">
				<div class="kt-field">
					<label>{{ __("PE code") }}</label>
					<input
						class="kt-input"
						type="text"
						v-model="form.entityCode"
						:placeholder="__('e.g. PE-KEMSA')"
						:disabled="editMode"
						:style="fieldErrors.entityCode ? 'border-color:#b0143a' : ''"
					/>
					<div v-if="fieldErrors.entityCode" style="color:#b0143a;font-size:12px;margin-top:4px">{{ fieldErrors.entityCode }}</div>
				</div>
				<div class="kt-field">
					<label>{{ __("PE type") }}</label>
					<div style="display:flex;gap:8px;align-items:center">
						<select class="kt-input" v-model="form.peType" style="flex:1">
							<option value="" disabled>{{ __("Select PE type") }}</option>
							<option v-for="t in peTypes" :key="t.type_code" :value="t.type_code">{{ t.label }}</option>
						</select>
						<button
							type="button"
							class="kt-btn kt-btn-ghost"
							style="white-space:nowrap"
							@click="createPeType"
						>
							{{ __("+ New") }}
						</button>
					</div>
				</div>
				<div class="kt-field">
					<label>{{ __("Legal name") }}</label>
					<input class="kt-input" type="text" v-model="form.legalName" />
				</div>
				<div class="kt-field">
					<label>{{ __("Display name") }}</label>
					<input class="kt-input" type="text" v-model="form.displayName" :placeholder="form.legalName" />
				</div>
				<div class="kt-field">
					<label>{{ __("Effective from") }}</label>
					<input class="kt-input" type="date" v-model="form.effectiveFrom" />
				</div>
			</div>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
		</div>

		<div class="kt-card kt-blueprint" style="max-width:920px">
			<h2 class="kt-card-title">{{ __("Operational setting") }}</h2>
			<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px 28px">
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
		<button type="button" class="kt-btn kt-btn-secondary" :disabled="!canSave || busy" @click="saveDraft">
			{{ editMode ? __("Save changes") : __("Save draft") }}
		</button>
		<button type="button" class="kt-btn kt-btn-primary" :disabled="!canSave || busy" @click="activateProcuringEntity">{{ __("Activate procuring entity") }}</button>
	</div>
</template>
