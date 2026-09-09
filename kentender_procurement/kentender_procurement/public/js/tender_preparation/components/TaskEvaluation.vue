<!-- TPR-DES-03 · Task 4 — Submission and evaluation (§8.4, §13.5): the
     fixed evaluation sequence, the finite officer controls, the generated
     evidence table with each row's source label, and the officer's
     additional evidence rows (linked to a visible requirement). -->
<template>
	<div>
		<div class="tpr-section">
			<div class="kt-card-title">Officer controls</div>
			<div class="tpr-grid-3">
				<div class="tpr-field"><label>Manufacturer authorisation required</label><SegControl name="tpr-mfr" label="Manufacturer authorisation required" :model-value="form.manufacturer_authorisation_required" :disabled="!editable" @update:model-value="set('manufacturer_authorisation_required', $event)" /></div>
				<div class="tpr-field"><label>Product datasheets/brochures required</label><SegControl name="tpr-ds" label="Product datasheets or brochures required" :model-value="form.datasheets_required" :disabled="!editable" @update:model-value="set('datasheets_required', $event)" /></div>
				<div class="tpr-field"><label>Warranty confirmation required</label><input class="kt-input" :value="generated.warranty_confirmation_required" disabled /></div>
				<div class="tpr-field"><label>Past supply experience required</label><SegControl name="tpr-exp" label="Past supply experience required" :model-value="form.past_experience_required" :disabled="!editable" @update:model-value="set('past_experience_required', $event)" /></div>
				<template v-if="form.past_experience_required">
					<div class="tpr-field"><label for="tpr-min-contracts">Minimum comparable contracts</label><select id="tpr-min-contracts" class="kt-input" :value="form.minimum_comparable_contracts || ''" :disabled="!editable" @change="set('minimum_comparable_contracts', $event.target.value)"><option value="">Select</option><option v-for="o in ['1', '2', '3']" :key="o" :value="o">{{ o }}</option></select><p v-if="errors.minimum_comparable_contracts" class="tpr-field-error">{{ errors.minimum_comparable_contracts }}</p></div>
					<div class="tpr-field"><label for="tpr-exp-years">Experience period</label><select id="tpr-exp-years" class="kt-input" :value="form.experience_period_years || ''" :disabled="!editable" @change="set('experience_period_years', $event.target.value)"><option value="">Select</option><option value="3">3 years</option><option value="5">5 years</option></select><p v-if="errors.experience_period_years" class="tpr-field-error">{{ errors.experience_period_years }}</p></div>
				</template>
				<div class="tpr-field"><label>After-sales support evidence required</label><SegControl name="tpr-asr" label="After-sales support evidence required" :model-value="form.after_sales_evidence_required" :disabled="!editable" @update:model-value="set('after_sales_evidence_required', $event)" /></div>
				<div v-if="form.after_sales_evidence_required" class="tpr-field tpr-span-2"><label for="tpr-as-evidence">After-sales evidence</label><select id="tpr-as-evidence" class="kt-input" :value="form.after_sales_evidence || ''" :disabled="!editable" @change="set('after_sales_evidence', $event.target.value)"><option value="">Select</option><option v-for="o in afterSalesOptions" :key="o" :value="o">{{ o }}</option></select><p v-if="errors.after_sales_evidence" class="tpr-field-error">{{ errors.after_sales_evidence }}</p></div>
			</div>
		</div>
		<div class="tpr-section">
			<div class="kt-card-title">Generated evidence requirements</div>
			<table class="kt-table" data-testid="tpr-evidence">
				<thead><tr><th>Evidence</th><th>Type</th><th>Linked to</th><th>Mandatory</th><th>Source</th><th></th></tr></thead>
				<tbody>
					<tr v-for="row in evidence" :key="row.evidence_requirement_id">
						<td>{{ row.evidence_label }}</td><td>{{ row.evidence_type }}</td><td>{{ row.linked_requirement_id }}</td><td>{{ row.mandatory ? "Yes" : "No" }}</td><td class="tpr-muted">{{ row.source }}</td>
						<td class="tpr-table-action"><a v-if="row.source === 'Additional officer evidence' && editable" href="#" class="tpr-inline-link" @click.prevent="$emit('remove-evidence', row)">Remove</a></td>
					</tr>
				</tbody>
			</table>
			<div v-if="editable" class="tpr-actions" style="margin-top: 10px"><button type="button" class="kt-btn kt-btn-ghost" data-testid="tpr-add-evidence" @click="$emit('add-evidence')">Add additional evidence</button></div>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, watch } from "vue";
import SegControl from "./SegControl.vue";

const props = defineProps({ editor: { type: Object, default: () => ({}) }, errors: { type: Object, default: () => ({}) }, editable: { type: Boolean, default: true } });
defineEmits(["add-evidence", "remove-evidence"]);
const generated = computed(() => props.editor.generated || {});
const evidence = computed(() => props.editor.evidence_requirements || []);
const afterSalesOptions = computed(() => ((props.editor.controls || {}).after_sales_evidence || {}).options || []);
const FIELDS = ["manufacturer_authorisation_required", "datasheets_required", "past_experience_required", "minimum_comparable_contracts", "experience_period_years", "after_sales_evidence_required", "after_sales_evidence"];
const BOOLS = new Set(["manufacturer_authorisation_required", "datasheets_required", "past_experience_required", "after_sales_evidence_required"]);
const form = reactive({});
const dirty = new Set();
function hydrate() {
	const v = props.editor.officer_values || {};
	for (const f of FIELDS) {
		if (dirty.has(f)) continue;
		form[f] = BOOLS.has(f) ? !!v[f] : (v[f] === undefined ? null : v[f]);
	}
}
watch(() => [(props.editor.tender || {}).tender, (props.editor.tender || {}).record_version], () => { dirty.clear(); hydrate(); }, { immediate: true });
function set(field, value) { dirty.add(field); form[field] = value; }
function getPayload() {
	const out = {};
	for (const f of dirty) out[f] = form[f] === "" ? null : form[f];
	return out;
}
defineExpose({ getPayload });
</script>
