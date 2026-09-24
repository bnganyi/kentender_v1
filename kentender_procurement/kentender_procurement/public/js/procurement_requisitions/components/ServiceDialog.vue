<!-- Add or edit one related service (REQ-DES-05 "When Yes, show service
     table and Add service"). Not drawn on the board; built from the shared
     dialog and field primitives. -->
<template>
	<DialogFrame :title="row ? 'Edit related service' : 'Add related service'" :width="520" :busy="busy" testid="req-service-dialog" @close="$emit('close')">
		<div class="req-grid-2-tight">
			<div class="kt-field">
				<label :for="`${id}-type`">Service</label>
				<select :id="`${id}-type`" v-model="form.service_type" class="kt-input" :class="{ 'is-invalid': fieldError('service_type') }" data-testid="req-service-type">
					<option value="">Select a service</option>
					<option v-for="t in catalogue.service_types || []" :key="t" :value="t">{{ t }}</option>
				</select>
				<span v-if="fieldError('service_type')" class="req-field-error">{{ fieldError("service_type") }}</span>
			</div>
			<div class="kt-field">
				<label :for="`${id}-coverage`">Quantity or coverage</label>
				<input :id="`${id}-coverage`" v-model="form.quantity_or_coverage" class="kt-input" :class="{ 'is-invalid': fieldError('quantity_or_coverage') }" data-testid="req-service-coverage" />
				<span v-if="fieldError('quantity_or_coverage')" class="req-field-error">{{ fieldError("quantity_or_coverage") }}</span>
			</div>
		</div>
		<div class="kt-field">
			<label :for="`${id}-result`">Required result</label>
			<textarea :id="`${id}-result`" v-model="form.required_result" class="kt-input" rows="2" :class="{ 'is-invalid': fieldError('required_result') }" data-testid="req-service-result"></textarea>
			<span v-if="fieldError('required_result')" class="req-field-error">{{ fieldError("required_result") }}</span>
		</div>
		<div class="req-grid-2-tight">
			<div class="kt-field">
				<label :for="`${id}-date`">Completion date</label>
				<DateField :id="`${id}-date`" v-model="form.completion_date" :max="(view.request_information || {}).latest_delivery_date || ''" :invalid="!!fieldError('completion_date')" />
				<span v-if="fieldError('completion_date')" class="req-field-error">{{ fieldError("completion_date") }}</span>
			</div>
			<div class="kt-field">
				<label :for="`${id}-evidence`">Acceptance evidence</label>
				<select :id="`${id}-evidence`" v-model="form.acceptance_evidence" class="kt-input" :class="{ 'is-invalid': fieldError('acceptance_evidence') }">
					<option value="">Select the evidence</option>
					<option v-for="t in catalogue.service_evidence || []" :key="t" :value="t">{{ t }}</option>
				</select>
				<span v-if="fieldError('acceptance_evidence')" class="req-field-error">{{ fieldError("acceptance_evidence") }}</span>
			</div>
		</div>
		<div v-if="form.acceptance_evidence === 'Other stated record'" class="kt-field">
			<label :for="`${id}-other`">Name of the evidence record</label>
			<input :id="`${id}-other`" v-model="form.other_evidence_name" class="kt-input" />
		</div>
		<Notice v-if="otherError" tone="critical">{{ otherError }}</Notice>
		<template #actions>
			<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" @click="$emit('close')">Cancel</button>
			<button type="button" class="kt-btn kt-btn-primary" :disabled="busy" data-testid="req-service-confirm" @click="confirm">Save related service</button>
		</template>
	</DialogFrame>
</template>

<script setup>
import { computed, reactive } from "vue";
import { useReq } from "../data/context.js";
import DateField from "./shared/DateField.vue";
import DialogFrame from "./shared/DialogFrame.vue";
import Notice from "./shared/Notice.vue";

const props = defineProps({ view: { type: Object, required: true }, row: { type: Object, default: null } });
const emit = defineEmits(["close"]);
const ctx = useReq();
const busy = computed(() => ctx.pending.value);
const id = `req-svc-${Math.random().toString(36).slice(2, 8)}`;
const catalogue = computed(() => props.view.catalogue || {});
const r = props.row || {};
const form = reactive({
	service_type: r.service_type || "", required_result: r.required_result || "", quantity_or_coverage: r.quantity_or_coverage || "",
	completion_date: r.completion_date || "", acceptance_evidence: r.acceptance_evidence || "", other_evidence_name: r.other_evidence_name || "",
	applies_to_scope: r.applies_to_scope || "All items", applies_to_id: r.applies_to_id || "",
});
const LABEL = props.row ? "update-service" : "add-service";
const error = computed(() => (ctx.commandError.value && ctx.commandError.value.label === LABEL ? ctx.commandError.value : null));
function fieldError(field) {
	return (error.value && error.value.detail && error.value.detail.fields && error.value.detail.fields[field]) || "";
}
const otherError = computed(() => (error.value && !(error.value.detail && error.value.detail.fields) ? error.value.message : ""));

async function confirm() {
	const base = { requisition: props.view.header.requisition, values: { ...form }, expected_record_version: props.view.package_record_version };
	const done = props.row
		? await ctx.run(LABEL, (key) => ctx.api.updateService({ ...base, service_requirement_id: props.row.service_requirement_id, idempotency_key: key }))
		: await ctx.run(LABEL, (key) => ctx.api.addService({ ...base, idempotency_key: key }));
	if (done) emit("close");
}
</script>
