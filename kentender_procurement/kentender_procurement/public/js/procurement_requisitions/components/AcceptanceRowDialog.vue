<!-- Add or edit one acceptance check (REQ-DES-05). The board draws the rows,
     not this dialog; built from the shared dialog and field primitives. -->
<template>
	<DialogFrame :title="row ? 'Edit acceptance check' : 'Add acceptance check'" :width="480" :busy="busy" testid="req-acceptance-dialog" @close="$emit('close')">
		<div class="field">
			<label :for="`${id}-type`">Check</label>
			<select :id="`${id}-type`" v-model="form.check_type" class="input">
				<option v-for="t in catalogue.check_types || []" :key="t" :value="t">{{ t }}</option>
			</select>
		</div>
		<div class="field">
			<label :for="`${id}-condition`">Pass condition</label>
			<textarea :id="`${id}-condition`" v-model="form.pass_condition" class="input" rows="2" :class="{ 'is-invalid': fieldError('pass_condition') }" data-testid="req-acceptance-condition"></textarea>
			<div class="kt-field-hint">State what an inspector can observe, in 10–500 characters.</div>
			<span v-if="fieldError('pass_condition')" class="req-field-error">{{ fieldError("pass_condition") }}</span>
		</div>
		<div class="field">
			<label :for="`${id}-evidence`">Evidence</label>
			<select :id="`${id}-evidence`" v-model="form.evidence_type" class="input">
				<option v-for="t in catalogue.evidence_types || []" :key="t" :value="t">{{ t }}</option>
			</select>
		</div>
		<div v-if="form.evidence_type === 'Other stated record'" class="field">
			<label :for="`${id}-other`">Name of the evidence record</label>
			<input :id="`${id}-other`" v-model="form.other_evidence_name" class="input" />
		</div>
		<Notice v-if="otherError" tone="critical">{{ otherError }}</Notice>
		<template #actions>
			<button type="button" class="btn btn-secondary" :disabled="busy" @click="$emit('close')">Cancel</button>
			<button type="button" class="btn btn-primary" :disabled="busy" data-testid="req-acceptance-confirm" @click="confirm">{{ local ? "Use this check" : "Save acceptance check" }}</button>
		</template>
	</DialogFrame>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { useReq } from "../data/context.js";
import DialogFrame from "./shared/DialogFrame.vue";
import Notice from "./shared/Notice.vue";

const props = defineProps({ view: { type: Object, required: true }, row: { type: Object, default: null }, local: { type: Boolean, default: false } });
const emit = defineEmits(["close", "local"]);
const ctx = useReq();
const busy = computed(() => ctx.pending.value);
const id = `req-acc-${Math.random().toString(36).slice(2, 8)}`;
const catalogue = computed(() => props.view.catalogue || {});
const form = reactive({
	check_type: (props.row && props.row.check_type) || "Quantity",
	pass_condition: (props.row && props.row.pass_condition) || "",
	evidence_type: (props.row && props.row.evidence_type) || "Inspection record",
	other_evidence_name: (props.row && props.row.other_evidence_name) || "",
	applies_to_scope: (props.row && props.row.applies_to_scope) || "All items",
	applies_to_id: (props.row && props.row.applies_to_id) || "",
});
const LABEL = props.row ? "update-acceptance" : "add-acceptance";
const error = computed(() => (ctx.commandError.value && ctx.commandError.value.label === LABEL ? ctx.commandError.value : null));
const localError = ref("");
function fieldError(field) {
	if (field === "pass_condition" && localError.value) return localError.value;
	return (error.value && error.value.detail && error.value.detail.fields && error.value.detail.fields[field]) || "";
}
const otherError = computed(() => (error.value && !(error.value.detail && error.value.detail.fields) ? error.value.message : ""));

async function confirm() {
	localError.value = "";
	if (props.local) {
		const length = form.pass_condition.trim().length;
		if (length < 10 || length > 500) {
			localError.value = "State an observable pass condition of 10–500 characters.";
			return;
		}
		emit("local", { ...form });
		emit("close");
		return;
	}
	const base = { requisition: props.view.header.requisition, values: { ...form }, expected_record_version: props.view.package_record_version };
	const done = props.row
		? await ctx.run(LABEL, (key) => ctx.api.updateAcceptance({ ...base, acceptance_requirement_id: props.row.acceptance_requirement_id, idempotency_key: key }))
		: await ctx.run(LABEL, (key) => ctx.api.addAcceptance({ ...base, idempotency_key: key }));
	if (done) emit("close");
}
</script>
