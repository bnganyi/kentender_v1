<!-- REQ-DES-06's "Add related service" dialog (§5.8). Not in the artboard
     file itself, same as ItemDialog.vue — built on kt_industry_tokens.css's
     shared .kt-dialog chrome. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="req-service-dialog" @keydown.esc="$emit('cancel')">
		<div class="kt-dialog" role="dialog" aria-modal="true" ref="dialogEl" tabindex="-1">
			<div class="kt-dialog-title">Add related service</div>

			<div class="kt-field">
				<label for="svc-type">Service type</label>
				<select id="svc-type" class="kt-input" v-model="fields.service_type">
					<option value="" disabled>Select a service type</option>
					<option v-for="t in serviceTypes" :key="t" :value="t">{{ t }}</option>
				</select>
				<p v-if="errors.service_type" class="req-field-error">{{ errors.service_type }}</p>
			</div>

			<div class="kt-field">
				<label for="svc-applies-to">Applies to</label>
				<select id="svc-applies-to" class="kt-input" v-model="appliesTo">
					<option value="__all__">All items</option>
					<option v-for="item in items" :key="item.requisition_item_id" :value="item.requisition_item_id">{{ item.item_name }} — {{ item.plan_item_line_id }}</option>
				</select>
			</div>

			<div class="kt-field">
				<label for="svc-result">Required result</label>
				<textarea id="svc-result" class="kt-input" rows="2" minlength="10" maxlength="500" :value="fields.required_result" @input="fields.required_result = $event.target.value"></textarea>
				<p v-if="errors.required_result" class="req-field-error">{{ errors.required_result }}</p>
			</div>

			<div class="req-field-grid">
				<div class="kt-field">
					<label for="svc-coverage">Quantity or coverage</label>
					<input id="svc-coverage" class="kt-input" maxlength="120" :value="fields.quantity_or_coverage" @input="fields.quantity_or_coverage = $event.target.value" />
					<p v-if="errors.quantity_or_coverage" class="req-field-error">{{ errors.quantity_or_coverage }}</p>
				</div>
				<div class="kt-field">
					<label for="svc-date">Completion date</label>
					<input id="svc-date" type="date" class="kt-input" :value="fields.completion_date" @input="fields.completion_date = $event.target.value" />
					<p v-if="errors.completion_date" class="req-field-error">{{ errors.completion_date }}</p>
				</div>
			</div>

			<div class="kt-field">
				<label for="svc-evidence">Acceptance evidence</label>
				<select id="svc-evidence" class="kt-input" v-model="fields.acceptance_evidence">
					<option value="" disabled>Select evidence</option>
					<option v-for="e in evidenceTypes" :key="e" :value="e">{{ e }}</option>
				</select>
				<p v-if="errors.acceptance_evidence" class="req-field-error">{{ errors.acceptance_evidence }}</p>
			</div>
			<div class="kt-field" v-if="fields.acceptance_evidence === 'Other stated record'">
				<label for="svc-other-evidence">Other evidence name</label>
				<input id="svc-other-evidence" class="kt-input" maxlength="120" :value="fields.other_evidence_name" @input="fields.other_evidence_name = $event.target.value" />
				<p v-if="errors.other_evidence_name" class="req-field-error">{{ errors.other_evidence_name }}</p>
			</div>

			<p v-if="error" class="req-field-error" role="alert">{{ error }}</p>

			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="req-service-dialog-confirm" @click="confirm">Add service</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from "vue";

const props = defineProps({
	editor: { type: Object, required: true },
	pending: Boolean,
	error: { type: String, default: "" },
});

const emit = defineEmits(["confirm", "cancel"]);

const dialogEl = ref(null);
const items = computed(() => (props.editor.package || {}).items || []);
const catalogue = computed(() => props.editor.catalogue || {});
const serviceTypes = computed(() => catalogue.value.service_types || []);
const evidenceTypes = computed(() => catalogue.value.service_acceptance_evidence || []);

const appliesTo = ref("__all__");
const fields = reactive({
	service_type: "",
	required_result: "",
	quantity_or_coverage: "",
	completion_date: "",
	acceptance_evidence: "",
	other_evidence_name: "",
});
const errors = reactive({});

function validate() {
	const next = {};
	if (!fields.service_type) next.service_type = "A service type is required.";
	if (fields.required_result.trim().length < 10) next.required_result = "10-500 characters describing the required result is required.";
	if (!fields.quantity_or_coverage.trim()) next.quantity_or_coverage = "Quantity or coverage is required.";
	if (!fields.completion_date) next.completion_date = "A completion date is required.";
	if (!fields.acceptance_evidence) next.acceptance_evidence = "Acceptance evidence is required.";
	if (fields.acceptance_evidence === "Other stated record" && !fields.other_evidence_name.trim()) next.other_evidence_name = "Other evidence name is required.";
	Object.keys(errors).forEach((k) => delete errors[k]);
	Object.assign(errors, next);
	return Object.keys(next).length === 0;
}

function confirm() {
	if (!validate()) return;
	emit("confirm", {
		...fields,
		applies_to_scope: appliesTo.value === "__all__" ? "All items" : "Item",
		applies_to_id: appliesTo.value === "__all__" ? "" : appliesTo.value,
	});
}

onMounted(() => {
	nextTick(() => dialogEl.value && dialogEl.value.focus());
});
</script>
