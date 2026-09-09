<!-- TPR-DES-03 · Task 5 — Contract terms (§8.5, §13.5): read-only summaries
     from the Requisition and exactly the finite §8.5 controls; both Links
     offer Active governed records only (TPR-AC-021). -->
<template>
	<div>
		<div class="tpr-section">
			<div class="kt-card-title">Read-only summaries</div>
			<div class="tpr-grid-4">
				<div class="tpr-ro-field"><span class="kt-label">Delivery</span><span class="tpr-ro-val">{{ inherited.latest_delivery_date }} · {{ inherited.delivery_location }}</span></div>
				<div class="tpr-ro-field"><span class="kt-label">Warranty</span><span class="tpr-ro-val">{{ (inherited.warranty_support || {}).minimum_warranty_months }} months</span></div>
				<div class="tpr-ro-field"><span class="kt-label">Services</span><span class="tpr-ro-val">{{ (inherited.related_services || []).length ? (inherited.related_services || []).length + " related service(s)" : "None" }}</span></div>
				<div class="tpr-ro-field"><span class="kt-label">Acceptance</span><span class="tpr-ro-val">{{ (inherited.acceptance_requirements || []).length ? (inherited.acceptance_requirements || []).length + " acceptance requirement(s)" : "Delivery only" }}</span></div>
			</div>
		</div>
		<div class="tpr-section">
			<div class="kt-card-title">Officer controls</div>
			<div class="tpr-grid-3">
				<div class="tpr-field tpr-span-2"><label for="tpr-inspection">Inspection and acceptance location</label><select id="tpr-inspection" class="kt-input" :value="form.inspection_location || ''" :disabled="!editable" @change="set('inspection_location', $event.target.value)"><option value="">Select an Active location</option><option v-for="o in options.delivery_locations || []" :key="o.value" :value="o.value">{{ o.label }}</option></select><p v-if="errors.inspection_location" class="tpr-field-error">{{ errors.inspection_location }}</p></div>
				<div class="tpr-field"><label for="tpr-payment">Payment timing</label><select id="tpr-payment" class="kt-input" :value="form.payment_timing_days || ''" :disabled="!editable" @change="set('payment_timing_days', $event.target.value)"><option v-for="o in ['30', '45', '60']" :key="o" :value="o">{{ o }} days</option></select><p v-if="errors.payment_timing_days" class="tpr-field-error">{{ errors.payment_timing_days }}</p></div>
				<div class="tpr-field"><label>Performance security required</label><SegControl name="tpr-ps" label="Performance security required" :model-value="form.performance_security_required" :disabled="!editable" @update:model-value="set('performance_security_required', $event)" /></div>
				<div v-if="form.performance_security_required" class="tpr-field"><label for="tpr-ps-pct">Performance security</label><input id="tpr-ps-pct" type="number" min="1" max="10" step="0.5" class="kt-input" :value="form.performance_security_percent" :disabled="!editable" @input="set('performance_security_percent', $event.target.value)" /><p v-if="errors.performance_security_percent" class="tpr-field-error">{{ errors.performance_security_percent }}</p></div>
				<div class="tpr-field"><label for="tpr-dd">Delay damages per week</label><input id="tpr-dd" type="number" min="0.1" max="1" step="0.1" class="kt-input" :value="form.delay_damages_per_week_percent" :disabled="!editable" @input="set('delay_damages_per_week_percent', $event.target.value)" /><p v-if="errors.delay_damages_per_week_percent" class="tpr-field-error">{{ errors.delay_damages_per_week_percent }}</p></div>
				<div class="tpr-field"><label for="tpr-dd-max">Maximum delay damages</label><input id="tpr-dd-max" type="number" min="5" max="10" step="1" class="kt-input" :value="form.maximum_delay_damages_percent" :disabled="!editable" @input="set('maximum_delay_damages_percent', $event.target.value)" /><p v-if="errors.maximum_delay_damages_percent" class="tpr-field-error">{{ errors.maximum_delay_damages_percent }}</p></div>
				<div class="tpr-field tpr-span-2"><label for="tpr-office">Contract contact office</label><select id="tpr-office" class="kt-input" :value="form.contract_contact_office || ''" :disabled="!editable" @change="set('contract_contact_office', $event.target.value)"><option value="">Select an Active office</option><option v-for="o in options.contact_offices || []" :key="o.value" :value="o.value">{{ o.label }}</option></select><p v-if="errors.contract_contact_office" class="tpr-field-error">{{ errors.contract_contact_office }}</p></div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, watch } from "vue";
import SegControl from "./SegControl.vue";

const props = defineProps({ editor: { type: Object, default: () => ({}) }, errors: { type: Object, default: () => ({}) }, editable: { type: Boolean, default: true } });
const inherited = computed(() => props.editor.inherited || {});
const options = computed(() => props.editor.options || {});
const FIELDS = ["inspection_location", "payment_timing_days", "performance_security_required", "performance_security_percent", "delay_damages_per_week_percent", "maximum_delay_damages_percent", "contract_contact_office"];
const form = reactive({});
const dirty = new Set();
function hydrate() {
	const v = props.editor.officer_values || {};
	for (const f of FIELDS) {
		if (dirty.has(f)) continue;
		form[f] = f === "performance_security_required" ? !!v[f] : (v[f] === undefined ? null : v[f]);
	}
}
watch(() => [(props.editor.tender || {}).tender, (props.editor.tender || {}).record_version], () => { dirty.clear(); hydrate(); }, { immediate: true });
function set(field, value) { dirty.add(field); form[field] = value; }
function getPayload() {
	const out = {};
	for (const f of dirty) {
		let value = form[f];
		if (["performance_security_percent", "delay_damages_per_week_percent", "maximum_delay_damages_percent"].includes(f) && value !== "" && value !== null) value = Number(value);
		out[f] = value === "" ? null : value;
	}
	return out;
}
defineExpose({ getPayload });
</script>
