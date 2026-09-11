<!-- REQ-DES-09's "Change lead department?" dialog (§13.11/§5.1) — a Select
     restricted to the Plan Item's contributing departments, a required
     reason (20-500 characters), and Cancel/Confirm change. The only place
     `lead_org_unit_id` can change, never available after submission. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="req-change-lead-unit-dialog" @keydown.esc="$emit('cancel')">
		<div class="kt-dialog" role="dialog" aria-modal="true" ref="dialogEl" tabindex="-1">
			<div class="kt-dialog-title">Change lead department?</div>

			<div class="kt-field">
				<label for="lead-unit-select">Lead department</label>
				<select id="lead-unit-select" class="kt-input" v-model="newLeadUnit">
					<option v-for="unit in contributingUnits" :key="unit.id" :value="unit.id">{{ unit.label }}</option>
				</select>
			</div>

			<div class="kt-field">
				<label for="lead-unit-reason">Reason</label>
				<textarea id="lead-unit-reason" class="kt-input" rows="3" minlength="20" maxlength="500" :value="reason" @input="reason = $event.target.value"></textarea>
				<p v-if="fieldError" class="req-field-error">{{ fieldError }}</p>
			</div>

			<p v-if="error" class="req-field-error" role="alert">{{ error }}</p>

			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="req-change-lead-unit-dialog-confirm" @click="confirm">Confirm change</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from "vue";

const props = defineProps({
	task: { type: Object, required: true },
	pending: Boolean,
	error: { type: String, default: "" },
});

const emit = defineEmits(["confirm", "cancel"]);

const dialogEl = ref(null);
const contributingUnits = computed(() => {
	const labels = props.task.contributing_org_unit_labels || {};
	return Object.entries(labels).map(([id, label]) => ({ id, label }));
});
const currentLeadUnit = computed(() => (props.task.requisition || {}).lead_org_unit || "");
const newLeadUnit = ref(currentLeadUnit.value || (contributingUnits.value[0] || {}).id || "");
const reason = ref("");
const fieldError = ref("");

function confirm() {
	const trimmed = reason.value.trim();
	if (trimmed.length < 20 || trimmed.length > 500) {
		fieldError.value = "A reason of 20-500 characters is required.";
		return;
	}
	fieldError.value = "";
	emit("confirm", { new_lead_org_unit: newLeadUnit.value, reason: trimmed });
}

onMounted(() => {
	nextTick(() => dialogEl.value && dialogEl.value.focus());
});
</script>
