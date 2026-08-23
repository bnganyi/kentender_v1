<script setup>
import { reactive, computed, ref } from "vue";
import { referenceDataApi as api } from "../../data/referenceDataApi.js";

const props = defineProps({ peTypes: { type: Array, default: () => [] } });
const emit = defineEmits(["created", "cancel"]);

const form = reactive({
	entityCode: "",
	peType: "",
	legalName: "",
	displayName: "",
	effectiveFrom: frappe.datetime.get_today(),
});
const busy = ref(false);

const canSave = computed(() => form.entityCode.trim() && form.peType && form.legalName.trim());

async function saveDraft() {
	if (!canSave.value || busy.value) return;
	busy.value = true;
	try {
		const result = await api.createPe({
			entity_code: form.entityCode.trim().toUpperCase(),
			legal_name: form.legalName.trim(),
			display_name: (form.displayName || form.legalName).trim(),
			pe_type_code: form.peType,
			effective_from: form.effectiveFrom,
		});
		emit("created", result.pe);
	} finally {
		busy.value = false;
	}
}

async function submitForApproval() {
	if (!canSave.value || busy.value) return;
	busy.value = true;
	try {
		const result = await api.createPe({
			entity_code: form.entityCode.trim().toUpperCase(),
			legal_name: form.legalName.trim(),
			display_name: (form.displayName || form.legalName).trim(),
			pe_type_code: form.peType,
			effective_from: form.effectiveFrom,
		});
		await api.decidePeChange(result.pe, "submit");
		emit("created", result.pe);
	} finally {
		busy.value = false;
	}
}
</script>

<template>
	<div style="padding:36px 48px 0;display:flex;flex-direction:column;gap:12px">
		<h1 style="margin:0;font-size:38px;line-height:1.05;letter-spacing:.005em">{{ __("New procuring entity") }}</h1>
		<div><span class="kt-status is-draft">{{ __("Draft") }}</span></div>
	</div>

	<div style="margin:36px 48px 0;flex:1;display:flex;flex-direction:column;gap:24px">
		<div class="kt-card kt-blueprint" style="max-width:920px">
			<h2 class="kt-card-title">{{ __("Identity") }}</h2>
			<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px 28px">
				<div class="kt-field">
					<label>{{ __("PE code") }}</label>
					<input class="kt-input" type="text" v-model="form.entityCode" placeholder="PE-KEMSA" />
				</div>
				<div class="kt-field">
					<label>{{ __("PE type") }}</label>
					<select class="kt-input" v-model="form.peType">
						<option value="" disabled>{{ __("Select PE type") }}</option>
						<option v-for="t in peTypes" :key="t.type_code" :value="t.type_code">{{ t.label }}</option>
					</select>
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
		<button type="button" class="kt-btn kt-btn-secondary" :disabled="!canSave || busy" @click="saveDraft">{{ __("Save draft") }}</button>
		<button type="button" class="kt-btn kt-btn-primary" :disabled="!canSave || busy" @click="submitForApproval">{{ __("Submit for approval") }}</button>
	</div>
</template>
