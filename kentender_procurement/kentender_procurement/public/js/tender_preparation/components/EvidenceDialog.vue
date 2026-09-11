<!-- §8.4 additional evidence row: label (3–160), type, linked requirement
     type, linked requirement (a visible inherited ID only), mandatory. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="tpr-evidence-dialog" @keydown.esc="$emit('cancel')">
		<div class="kt-dialog tpr-dialog kt-blueprint" role="dialog" aria-modal="true" ref="dialogEl" tabindex="-1">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-dialog-title">Add additional evidence</div>
			<div class="tpr-dialog-body">
				<div class="tpr-field"><label for="tpr-ev-label">Evidence label</label><input id="tpr-ev-label" class="kt-input" maxlength="160" :value="form.evidence_label" @input="form.evidence_label = $event.target.value" /><p v-if="errors.evidence_label" class="tpr-field-error">{{ errors.evidence_label }}</p></div>
				<div class="tpr-field"><label for="tpr-ev-type">Evidence type</label><select id="tpr-ev-type" class="kt-input" :value="form.evidence_type" @change="form.evidence_type = $event.target.value"><option v-for="o in TYPES" :key="o" :value="o">{{ o }}</option></select></div>
				<div class="tpr-field"><label for="tpr-ev-link-type">Linked requirement type</label><select id="tpr-ev-link-type" class="kt-input" :value="form.linked_requirement_type" @change="form.linked_requirement_type = $event.target.value; form.linked_requirement_id = ''"><option v-for="o in LINK_TYPES" :key="o" :value="o">{{ o }}</option></select></div>
				<div class="tpr-field"><label for="tpr-ev-link">Linked requirement</label><select id="tpr-ev-link" class="kt-input" :value="form.linked_requirement_id" @change="form.linked_requirement_id = $event.target.value"><option value="">Select a visible requirement</option><option v-for="o in linkOptions" :key="o.value" :value="o.value">{{ o.label }}</option></select><p v-if="errors.linked_requirement_id" class="tpr-field-error">{{ errors.linked_requirement_id }}</p></div>
				<div class="tpr-field"><label>Mandatory</label><SegControl name="tpr-ev-mandatory" label="Mandatory" :model-value="form.mandatory" @update:model-value="form.mandatory = $event" /></div>
				<p v-if="error" class="tpr-field-error" role="alert">{{ error }}</p>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="tpr-evidence-confirm" @click="$emit('confirm', { ...form })">Add evidence</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from "vue";
import SegControl from "./SegControl.vue";

const props = defineProps({ editor: { type: Object, default: () => ({}) }, pending: Boolean, error: { type: String, default: "" }, errors: { type: Object, default: () => ({}) } });
defineEmits(["confirm", "cancel"]);
const TYPES = ["Declaration", "Certificate", "Datasheet or brochure", "Schedule or form", "Other document"];
const LINK_TYPES = ["Equipment item", "Technical requirement", "Related service", "Acceptance requirement"];
const form = reactive({ evidence_label: "", evidence_type: "Certificate", linked_requirement_type: "Technical requirement", linked_requirement_id: "", mandatory: true });
const dialogEl = ref(null);
const linkOptions = computed(() => {
	const i = props.editor.inherited || {};
	switch (form.linked_requirement_type) {
		case "Equipment item":
			return (i.goods || []).flatMap((g) => (g.source_items || []).map((s) => ({ value: s.requisition_item_id, label: `${s.requisition_item_id} — ${g.description}` })));
		case "Technical requirement":
			return (i.technical_requirements || []).map((r) => ({ value: r.technical_requirement_id, label: `${r.technical_requirement_id} — ${r.label}` }));
		case "Related service":
			return (i.related_services || []).map((s) => ({ value: s.service_requirement_id, label: `${s.service_requirement_id} — ${s.service_type}` }));
		default:
			return (i.acceptance_requirements || []).map((a) => ({ value: a.acceptance_requirement_id, label: `${a.acceptance_requirement_id} — ${a.check_type}` }));
	}
});
onMounted(() => nextTick(() => dialogEl.value && dialogEl.value.focus()));
</script>
