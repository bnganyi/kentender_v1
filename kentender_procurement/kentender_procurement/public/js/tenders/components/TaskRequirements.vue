<!-- TPR-DES-04 Draft: Supplier and contract requirements — Supplier evidence
     toggles (warranty confirmation fixed by the authorised requisition),
     Additional evidence table + Add/Edit/Remove, Contract terms, and the two
     disclosures. Same hydration and error rules as TaskDetails. -->
<template>
	<div>
		<div class="tnd-section tnd-section--tight">
			<p class="tnd-lede">The authorised requirements are already included. Choose only the additional evidence suppliers must provide and complete the contract terms below.</p>
		</div>

		<div class="tnd-section tnd-section--form">
			<h3 class="kt-card-title tnd-section-title"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="m9 15 2 2 4-4"/></svg>Supplier evidence</h3>
			<div class="tnd-toggle-list">
				<div class="tnd-toggle-row"><span>Manufacturer authorisation required</span><YesNo v-model="form.manufacturer_authorisation_required" name="mfr" testid="tnd-toggle-manufacturer" /></div>
				<p v-if="errors.manufacturer_authorisation_required" class="tnd-field-error">{{ errors.manufacturer_authorisation_required }}</p>
				<div class="tnd-toggle-row"><span>Product datasheets or brochures required</span><YesNo v-model="form.datasheets_required" name="ds" testid="tnd-toggle-datasheets" /></div>
				<div class="tnd-toggle-row"><span>Warranty confirmation required</span><span class="tnd-tag tnd-tag-neutral" data-testid="tnd-warranty-fixed">Yes — required by authorised requisition</span></div>
				<div class="tnd-toggle-row"><span>Past supply experience required</span><YesNo v-model="form.past_experience_required" name="exp" testid="tnd-toggle-experience" /></div>
				<div v-if="form.past_experience_required" class="tnd-indent">
					<div class="tnd-grid-2">
						<div class="kt-field" style="margin: 0"><label for="tnd-minimum_comparable_contracts">Minimum comparable contracts</label><input id="tnd-minimum_comparable_contracts" class="kt-input" type="number" min="1" step="1" v-model="form.minimum_comparable_contracts" data-testid="tnd-field-minimum_comparable_contracts" /><p v-if="errors.minimum_comparable_contracts" class="tnd-field-error">{{ errors.minimum_comparable_contracts }}</p></div>
						<div class="kt-field" style="margin: 0"><label for="tnd-experience_period_years">Within the last ___ years</label><input id="tnd-experience_period_years" class="kt-input" type="number" min="1" step="1" v-model="form.experience_period_years" data-testid="tnd-field-experience_period_years" /><p v-if="errors.experience_period_years" class="tnd-field-error">{{ errors.experience_period_years }}</p></div>
					</div>
					<p class="tnd-hint">Set a value that is relevant and proportionate to this purchase — narrower criteria can unfairly exclude qualified suppliers. HOPF reviews this criterion before approval.</p>
				</div>
				<div class="tnd-toggle-row"><span>After-sales support evidence required</span><YesNo v-model="form.after_sales_evidence_required" name="asr" testid="tnd-toggle-after-sales" /></div>
				<p v-if="errors.after_sales_evidence_required" class="tnd-field-error" data-testid="tnd-error-after_sales_evidence_required">{{ errors.after_sales_evidence_required }}</p>
				<div v-if="form.after_sales_evidence_required" class="kt-field tnd-indent" style="margin: 0"><label for="tnd-after_sales_evidence">After-sales evidence</label>
					<select id="tnd-after_sales_evidence" class="kt-input" v-model="form.after_sales_evidence" data-testid="tnd-field-after_sales_evidence"><option value="">Choose the evidence</option><option v-for="o in afterSalesOptions" :key="o" :value="o">{{ o }}</option></select>
					<p v-if="errors.after_sales_evidence" class="tnd-field-error">{{ errors.after_sales_evidence }}</p>
				</div>
			</div>
		</div>

		<div class="tnd-section tnd-section--form">
			<div class="tnd-section-head">
				<h3 class="kt-card-title" style="margin: 0; display: flex; align-items: center; gap: 6px"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M9 12h6"/><path d="M9 16h6"/></svg>Additional evidence</h3>
				<button type="button" class="kt-btn kt-btn-secondary tnd-inline-btn" :disabled="pending" data-testid="tnd-add-evidence" @click="$emit('add-evidence')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5 12h14"/><path d="M12 5v14"/></svg>Add evidence</button>
			</div>
			<table v-if="evidence.length" class="kt-table" data-testid="tnd-evidence-table">
				<thead><tr><th>Evidence</th><th>Type</th><th>Proves</th><th>Required</th><th></th></tr></thead>
				<tbody>
					<tr v-for="row in evidence" :key="row.evidence_requirement_id" :data-testid="`tnd-evidence-${row.evidence_requirement_id}`">
						<td>{{ row.label }}</td><td>{{ row.evidence_type }}</td><td>{{ row.proves }}</td><td>{{ row.mandatory ? "Yes" : "No" }}</td>
						<td class="tnd-cell-right"><button type="button" class="tnd-link-btn" :disabled="pending" data-testid="tnd-evidence-edit" @click="$emit('edit-evidence', row)">Edit</button> · <button type="button" class="tnd-link-btn is-critical" :disabled="pending" data-testid="tnd-evidence-remove" @click="$emit('remove-evidence', row)">Remove</button></td>
					</tr>
				</tbody>
			</table>
			<p v-else class="tnd-empty-inline" data-testid="tnd-evidence-empty">No additional evidence has been added.</p>
		</div>

		<div class="tnd-section tnd-section--form">
			<h3 class="kt-card-title tnd-section-title"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/></svg>Contract terms</h3>
			<div class="kt-field tnd-form-row"><label for="tnd-inspection_location">Inspection and acceptance location</label>
				<select id="tnd-inspection_location" class="kt-input" v-model="form.inspection_location" data-testid="tnd-field-inspection_location"><option value="">Choose a location</option><option v-for="l in options.delivery_locations || []" :key="l" :value="l">{{ l }}</option></select>
				<p v-if="errors.inspection_location" class="tnd-field-error" data-testid="tnd-error-inspection_location">{{ errors.inspection_location }}</p>
			</div>
			<div class="tnd-grid-2 tnd-form-row">
				<div class="kt-field" style="margin: 0"><label for="tnd-payment_timing_days">Payment timing</label><select id="tnd-payment_timing_days" class="kt-input" v-model="form.payment_timing_days" data-testid="tnd-field-payment_timing_days"><option value="30">30 days</option><option value="45">45 days</option><option value="60">60 days</option></select><p v-if="errors.payment_timing_days" class="tnd-field-error">{{ errors.payment_timing_days }}</p></div>
				<div class="kt-field" style="margin: 0"><label>Performance security required</label><YesNo v-model="form.performance_security_required" name="perf" testid="tnd-toggle-performance" /><p v-if="errors.performance_security_required" class="tnd-field-error">{{ errors.performance_security_required }}</p></div>
			</div>
			<div class="tnd-grid-2 tnd-form-row tnd-indent">
				<div v-if="form.performance_security_required" class="kt-field" style="margin: 0"><label for="tnd-performance_security_percent">Performance security percentage</label><input id="tnd-performance_security_percent" class="kt-input" type="number" min="1" max="10" step="0.5" v-model="form.performance_security_percent" data-testid="tnd-field-performance_security_percent" /><p v-if="errors.performance_security_percent" class="tnd-field-error">{{ errors.performance_security_percent }}</p></div>
				<div class="kt-field" style="margin: 0"><label for="tnd-delay_damages_per_week_percent">Delay damages per week (%)</label><input id="tnd-delay_damages_per_week_percent" class="kt-input" type="number" min="0.1" max="1" step="0.1" v-model="form.delay_damages_per_week_percent" data-testid="tnd-field-delay_damages_per_week_percent" /><p v-if="errors.delay_damages_per_week_percent" class="tnd-field-error">{{ errors.delay_damages_per_week_percent }}</p></div>
			</div>
			<div class="tnd-grid-2">
				<div class="kt-field" style="margin: 0"><label for="tnd-maximum_delay_damages_percent">Maximum delay damages (%)</label><input id="tnd-maximum_delay_damages_percent" class="kt-input" type="number" min="5" max="10" step="1" v-model="form.maximum_delay_damages_percent" data-testid="tnd-field-maximum_delay_damages_percent" /><p v-if="errors.maximum_delay_damages_percent" class="tnd-field-error">{{ errors.maximum_delay_damages_percent }}</p></div>
				<div class="kt-field" style="margin: 0"><label for="tnd-contract_contact_office">Contract contact office</label><select id="tnd-contract_contact_office" class="kt-input" v-model="form.contract_contact_office" data-testid="tnd-field-contract_contact_office"><option value="">Choose an office</option><option v-for="o in options.contact_offices || []" :key="o" :value="o">{{ o }}</option></select><p v-if="errors.contract_contact_office" class="tnd-field-error">{{ errors.contract_contact_office }}</p></div>
			</div>
		</div>

		<div class="tnd-section tnd-section--form tnd-section--last">
			<div class="kt-disclosure" style="margin-bottom: 12px">
				<div class="kt-disclosure-head" role="button" tabindex="0" @click="evalOpen = !evalOpen" @keydown.enter.prevent="evalOpen = !evalOpen"><div class="kt-disclosure-title-row"><span class="kt-disclosure-title">How suppliers will be evaluated</span></div><svg class="kt-disclosure-chevron" :class="{ 'is-open': evalOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 9l6 6 6-6"/></svg></div>
				<div v-if="evalOpen" class="kt-disclosure-body"><ol class="tnd-ol"><li v-for="s in stages" :key="s">{{ s }}</li></ol></div>
			</div>
			<div class="kt-disclosure">
				<div class="kt-disclosure-head" role="button" tabindex="0" @click="reqOpen = !reqOpen" @keydown.enter.prevent="reqOpen = !reqOpen"><div class="kt-disclosure-title-row"><span class="kt-disclosure-title">Requirements carried into the contract</span></div><svg class="kt-disclosure-chevron" :class="{ 'is-open': reqOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 9l6 6 6-6"/></svg></div>
				<div v-if="reqOpen" class="kt-disclosure-body">
					<p class="tnd-card-body" style="margin: 0 0 10px">{{ carriedLine }}</p>
					<button type="button" class="kt-btn kt-btn-ghost" style="padding: 4px 0" data-testid="tnd-show-full-requirements" @click="$emit('open-drawer')">Show full requirements</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, defineComponent, h, reactive, ref, watch } from "vue";

const props = defineProps({
	values: { type: Object, default: () => ({}) },
	options: { type: Object, default: () => ({}) },
	catalogue: { type: Object, default: () => ({}) },
	inherited: { type: Object, default: () => ({}) },
	evidence: { type: Array, default: () => [] },
	stages: { type: Array, default: () => [] },
	identity: { type: String, default: "" },
	errors: { type: Object, default: () => ({}) },
	pending: Boolean,
});
defineEmits(["add-evidence", "edit-evidence", "remove-evidence", "open-drawer"]);

// The board's Yes/No segmented control, once.
const YesNo = defineComponent({
	props: { modelValue: { type: Boolean, default: null }, name: String, testid: String },
	emits: ["update:modelValue"],
	setup(p, { emit }) {
		return () =>
			h("div", { class: "tnd-seg", role: "radiogroup" }, [
				h("label", { class: "tnd-seg-opt" }, [h("input", { type: "radio", name: `tnd-${p.name}`, checked: p.modelValue === true, "data-testid": `${p.testid}-yes`, onChange: () => emit("update:modelValue", true) }), "Yes"]),
				h("label", { class: "tnd-seg-opt" }, [h("input", { type: "radio", name: `tnd-${p.name}`, checked: p.modelValue === false, "data-testid": `${p.testid}-no`, onChange: () => emit("update:modelValue", false) }), "No"]),
			]);
	},
});

const evalOpen = ref(false);
const reqOpen = ref(false);
const afterSalesOptions = computed(() => ((props.catalogue.after_sales_evidence || {}).options) || ["Kenya service-centre details and escalation contacts", "Manufacturer or authorised service-partner commitment", "Both"]);
const carriedLine = computed(() => {
	const c = props.inherited.counts || {};
	const items = (props.inherited.items || []).map((i) => `${i.quantity} ${i.unit} ${i.item_name}`).join(", ");
	const warranty = Object.keys(props.inherited.warranty_support || {}).length;
	return `${items || "Authorised items"} · ${c.technical_requirements || 0} technical requirements · ${warranty} warranty/support facts · ${c.acceptance_requirements || 0} acceptance checks.`;
});

const form = reactive({ manufacturer_authorisation_required: null, datasheets_required: null, past_experience_required: null, minimum_comparable_contracts: "", experience_period_years: "", after_sales_evidence_required: null, after_sales_evidence: "", inspection_location: "", payment_timing_days: "30", performance_security_required: null, performance_security_percent: "", delay_damages_per_week_percent: "", maximum_delay_damages_percent: "", contract_contact_office: "" });
let hydrated = "";
let dirty = false;
function asBool(v) {
	return v === null || v === undefined ? null : !!v;
}
function hydrate() {
	const v = props.values || {};
	form.manufacturer_authorisation_required = asBool(v.manufacturer_authorisation_required);
	form.datasheets_required = asBool(v.datasheets_required);
	form.past_experience_required = asBool(v.past_experience_required);
	form.minimum_comparable_contracts = v.minimum_comparable_contracts ?? "";
	form.experience_period_years = v.experience_period_years ?? "";
	form.after_sales_evidence_required = asBool(v.after_sales_evidence_required);
	form.after_sales_evidence = v.after_sales_evidence || "";
	form.inspection_location = v.inspection_location || "";
	form.payment_timing_days = v.payment_timing_days != null ? String(v.payment_timing_days) : "30";
	form.performance_security_required = asBool(v.performance_security_required);
	form.performance_security_percent = v.performance_security_percent ?? "";
	form.delay_damages_per_week_percent = v.delay_damages_per_week_percent ?? "";
	form.maximum_delay_damages_percent = v.maximum_delay_damages_percent ?? "";
	form.contract_contact_office = v.contract_contact_office || "";
	dirty = false;
}
watch(
	() => props.identity,
	(id) => {
		if (id !== hydrated) {
			hydrated = id;
			hydrate();
		}
	},
	{ immediate: true }
);
watch(form, () => {
	dirty = true;
});

function getPayload() {
	const p = {};
	const put = (k, v) => {
		if (v !== "" && v !== null && v !== undefined) p[k] = v;
	};
	put("manufacturer_authorisation_required", form.manufacturer_authorisation_required);
	put("datasheets_required", form.datasheets_required);
	put("past_experience_required", form.past_experience_required);
	if (form.past_experience_required) {
		put("minimum_comparable_contracts", form.minimum_comparable_contracts === "" ? "" : Number(form.minimum_comparable_contracts));
		put("experience_period_years", form.experience_period_years === "" ? "" : Number(form.experience_period_years));
	}
	put("after_sales_evidence_required", form.after_sales_evidence_required);
	if (form.after_sales_evidence_required) put("after_sales_evidence", form.after_sales_evidence);
	put("inspection_location", form.inspection_location);
	put("payment_timing_days", form.payment_timing_days);
	put("performance_security_required", form.performance_security_required);
	if (form.performance_security_required) put("performance_security_percent", form.performance_security_percent === "" ? "" : Number(form.performance_security_percent));
	put("delay_damages_per_week_percent", form.delay_damages_per_week_percent === "" ? "" : Number(form.delay_damages_per_week_percent));
	put("maximum_delay_damages_percent", form.maximum_delay_damages_percent === "" ? "" : Number(form.maximum_delay_damages_percent));
	put("contract_contact_office", form.contract_contact_office);
	return p;
}
function isDirty() {
	return dirty;
}
defineExpose({ getPayload, isDirty });
</script>
