<!-- TPR-DES-04 "Add supplier evidence" dialog (and its Edit twin): label,
     evidence type, requirement type, the published requirement it proves,
     Required. §4.4: additional evidence must prove a published requirement;
     it can never add a qualification or technical condition — so "Proves"
     is a choice among the inherited rows, never free text. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="tnd-evidence-dialog" @keydown.esc="$emit('cancel')">
		<div ref="dialogEl" class="kt-dialog tnd-dialog" role="dialog" aria-modal="true" aria-labelledby="tnd-evidence-title" tabindex="-1">
			<div id="tnd-evidence-title" class="kt-dialog-title">{{ row ? "Edit supplier evidence" : "Add supplier evidence" }}</div>
			<div class="tnd-dialog-body">
				<div class="kt-field"><label for="tnd-ev-label">Evidence label</label><input id="tnd-ev-label" class="kt-input" v-model="form.label" maxlength="160" data-testid="tnd-ev-label" /><p v-if="fieldErrors.label" class="tnd-field-error" data-testid="tnd-ev-error-label">{{ fieldErrors.label }}</p></div>
				<div class="tnd-grid-2">
					<div class="kt-field" style="margin: 0"><label for="tnd-ev-type">Evidence type</label><select id="tnd-ev-type" class="kt-input" v-model="form.evidence_type" data-testid="tnd-ev-type"><option v-for="t in EVIDENCE_TYPES" :key="t" :value="t">{{ t }}</option></select><p v-if="fieldErrors.evidence_type" class="tnd-field-error">{{ fieldErrors.evidence_type }}</p></div>
					<div class="kt-field" style="margin: 0"><label for="tnd-ev-link-type">Requirement type</label><select id="tnd-ev-link-type" class="kt-input" v-model="form.linked_requirement_type" data-testid="tnd-ev-link-type" @change="form.linked_requirement_id = ''"><option v-for="t in LINK_TYPES" :key="t" :value="t">{{ t }}</option></select><p v-if="fieldErrors.linked_requirement_type" class="tnd-field-error">{{ fieldErrors.linked_requirement_type }}</p></div>
				</div>
				<div class="kt-field" style="margin-top: 12px"><label for="tnd-ev-proves">Proves</label>
					<select v-if="form.linked_requirement_type !== 'Warranty/support'" id="tnd-ev-proves" class="kt-input" v-model="form.linked_requirement_id" data-testid="tnd-ev-proves"><option value="">Choose the published requirement</option><option v-for="o in provesOptions" :key="o.id" :value="o.id">{{ o.label }}</option></select>
					<div v-else id="tnd-ev-proves" class="tnd-fact-value tnd-fact-value--muted">Warranty and support requirements carried from the authorised requisition</div>
					<p v-if="fieldErrors.linked_requirement_id" class="tnd-field-error" data-testid="tnd-ev-error-proves">{{ fieldErrors.linked_requirement_id }}</p>
				</div>
				<label class="kt-checkbox" style="margin-bottom: 10px"><input type="checkbox" v-model="form.mandatory" data-testid="tnd-ev-mandatory" /><span class="box"></span>Required</label>
				<p class="tnd-xs tnd-muted" style="margin: 0">Additional evidence must prove a published requirement. It cannot add a new qualification or technical condition.</p>
				<p v-if="error" class="tnd-field-error" role="alert" data-testid="tnd-ev-error">{{ error }}</p>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="tnd-ev-confirm" @click="confirm">{{ row ? "Save evidence" : "Add evidence" }}</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from "vue";

const props = defineProps({
	row: { type: Object, default: null },
	inherited: { type: Object, default: () => ({}) },
	pending: Boolean,
	error: { type: String, default: "" },
	serverErrors: { type: Object, default: () => ({}) },
});
const emit = defineEmits(["confirm", "cancel"]);

const EVIDENCE_TYPES = ["Certificate", "Declaration", "Datasheet or brochure", "Schedule or form", "Other document"];
const LINK_TYPES = ["Technical requirement", "Item", "Service", "Warranty/support"];

const dialogEl = ref(null);
const form = reactive({
	label: props.row ? props.row.label : "",
	evidence_type: props.row ? props.row.evidence_type : "Certificate",
	linked_requirement_type: props.row ? props.row.linked_requirement_type : "Technical requirement",
	linked_requirement_id: props.row ? props.row.linked_requirement_id : "",
	mandatory: props.row ? !!props.row.mandatory : true,
});
const localErrors = reactive({});
const fieldErrors = computed(() => ({ ...localErrors, ...(props.serverErrors || {}) }));

const provesOptions = computed(() => {
	const inh = props.inherited || {};
	if (form.linked_requirement_type === "Technical requirement") return (inh.technical_requirements || []).map((t) => ({ id: t.technical_requirement_id, label: `${t.label} — ${t.required_value}${t.unit ? " " + t.unit : ""}` }));
	if (form.linked_requirement_type === "Item") return (inh.items || []).map((i) => ({ id: i.requisition_item_id, label: `${i.item_name} — ${i.quantity} ${i.unit}` }));
	if (form.linked_requirement_type === "Service") return (inh.related_services || []).map((s) => ({ id: s.service_requirement_id, label: `${s.service_type} — ${s.required_result}` }));
	return [];
});

function confirm() {
	for (const k of Object.keys(localErrors)) delete localErrors[k];
	const label = form.label.trim();
	if (label.length < 3 || label.length > 160) localErrors.label = "Enter plain text of 3–160 characters.";
	if (form.linked_requirement_type !== "Warranty/support" && !form.linked_requirement_id) localErrors.linked_requirement_id = "Choose a published inherited requirement of that type.";
	if (Object.keys(localErrors).length) return;
	emit("confirm", { label, evidence_type: form.evidence_type, linked_requirement_type: form.linked_requirement_type, linked_requirement_id: form.linked_requirement_type === "Warranty/support" ? "" : form.linked_requirement_id, mandatory: !!form.mandatory });
}
onMounted(() => nextTick(() => dialogEl.value && dialogEl.value.focus()));
</script>
