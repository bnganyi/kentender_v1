<!-- REQ-DES-06's "Add acceptance check" dialog (§5.9). Not in the artboard
     file itself, same as ItemDialog.vue — built on kt_industry_tokens.css's
     shared .kt-dialog chrome. §5.9: "Satisfactory"/"acceptable" wording
     without an observable condition is invalid — the server independently
     re-checks this (services/validation.py's SUBJECTIVE_ACCEPTANCE finding);
     this dialog only surfaces the server's own message if it still fails. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="req-acceptance-dialog" @keydown.esc="$emit('cancel')">
		<div class="kt-dialog" role="dialog" aria-modal="true" ref="dialogEl" tabindex="-1">
			<div class="kt-dialog-title">Add acceptance check</div>

			<div class="kt-field">
				<label for="acc-check-type">Check</label>
				<select id="acc-check-type" class="kt-input" v-model="fields.check_type">
					<option value="" disabled>Select a check</option>
					<option v-for="t in checkTypes" :key="t" :value="t">{{ t }}</option>
				</select>
				<p v-if="errors.check_type" class="req-field-error">{{ errors.check_type }}</p>
			</div>

			<div class="kt-field">
				<label for="acc-applies-to">Applies to</label>
				<select id="acc-applies-to" class="kt-input" v-model="appliesTo">
					<option value="__all__">All items</option>
					<option v-for="item in items" :key="item.requisition_item_id" :value="item.requisition_item_id">{{ item.item_name }} — {{ item.plan_item_line_id }}</option>
					<option v-for="svc in services" :key="svc.service_requirement_id" :value="svc.service_requirement_id">{{ svc.service_type }} (service)</option>
				</select>
			</div>

			<div class="kt-field">
				<label for="acc-pass-condition">Pass condition</label>
				<textarea id="acc-pass-condition" class="kt-input" rows="2" minlength="10" maxlength="500" :value="fields.pass_condition" @input="fields.pass_condition = $event.target.value"></textarea>
				<p v-if="errors.pass_condition" class="req-field-error">{{ errors.pass_condition }}</p>
			</div>

			<div class="kt-field">
				<label for="acc-evidence">Evidence</label>
				<select id="acc-evidence" class="kt-input" v-model="fields.evidence_type">
					<option value="" disabled>Select evidence</option>
					<option v-for="e in evidenceTypes" :key="e" :value="e">{{ e }}</option>
				</select>
				<p v-if="errors.evidence_type" class="req-field-error">{{ errors.evidence_type }}</p>
			</div>
			<div class="kt-field" v-if="fields.evidence_type === 'Other stated record'">
				<label for="acc-other-evidence">Other evidence name</label>
				<input id="acc-other-evidence" class="kt-input" maxlength="120" :value="fields.other_evidence_name" @input="fields.other_evidence_name = $event.target.value" />
				<p v-if="errors.other_evidence_name" class="req-field-error">{{ errors.other_evidence_name }}</p>
			</div>

			<p v-if="error" class="req-field-error" role="alert">{{ error }}</p>

			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="req-acceptance-dialog-confirm" @click="confirm">Add check</button>
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
const services = computed(() => (props.editor.package || {}).related_services || []);
const catalogue = computed(() => props.editor.catalogue || {});
const checkTypes = computed(() => catalogue.value.acceptance_check_types || []);
const evidenceTypes = computed(() => catalogue.value.acceptance_evidence_types || []);

// Subjective wording with no observable condition (§5.9) — a client-side
// hint only; services/validation.py's own SUBJECTIVE_ACCEPTANCE finding is
// the actual gate, re-checked independently on every save.
const SUBJECTIVE_PATTERN = /\b(satisfactory|acceptable)\b/i;

const appliesTo = ref("__all__");
const fields = reactive({ check_type: "", pass_condition: "", evidence_type: "", other_evidence_name: "" });
const errors = reactive({});

function validate() {
	const next = {};
	if (!fields.check_type) next.check_type = "A check is required.";
	const condition = fields.pass_condition.trim();
	if (condition.length < 10) next.pass_condition = "10-500 characters stating an observable result is required.";
	else if (SUBJECTIVE_PATTERN.test(condition) && condition.replace(SUBJECTIVE_PATTERN, "").trim().length < 10) {
		next.pass_condition = '"Satisfactory" or "acceptable" alone, without an observable condition, is invalid.';
	}
	if (!fields.evidence_type) next.evidence_type = "Evidence is required.";
	if (fields.evidence_type === "Other stated record" && !fields.other_evidence_name.trim()) next.other_evidence_name = "Other evidence name is required.";
	Object.keys(errors).forEach((k) => delete errors[k]);
	Object.assign(errors, next);
	return Object.keys(next).length === 0;
}

function confirm() {
	if (!validate()) return;
	const isService = services.value.some((s) => s.service_requirement_id === appliesTo.value);
	emit("confirm", {
		...fields,
		applies_to_scope: appliesTo.value === "__all__" ? "All items" : isService ? "Service" : "Item",
		applies_to_id: appliesTo.value === "__all__" ? "" : appliesTo.value,
	});
}

onMounted(() => {
	nextTick(() => dialogEl.value && dialogEl.value.focus());
});
</script>
