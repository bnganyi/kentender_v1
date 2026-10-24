<!-- Opening access support records a finding on an incident (BOP-CHG-001 v0.16 §5.2, §10.8; TRUST-OPS-001 v0.2 §9.2): Unresolved, Recovered or Cannot recover,
     with a reason and opaque evidence references, against the incident revision this page showed. It is a finding only: it starts nothing, resumes nothing and
     chooses no legal ground. A changed finding is added to the history; the earlier one stays. Shown to the assigned support holder only; the server decides. -->
<script setup>
import { ref } from "vue";

const props = defineProps({
	incident: { type: Object, required: true },
	pending: Boolean,
});
const emit = defineEmits(["record"]);
const finding = ref("");
const reason = ref("");
const evidence = ref("");
const error = ref("");

function submit() {
	if (!finding.value) {
		error.value = "Choose what you found.";
		return;
	}
	if (!reason.value.trim()) {
		error.value = "Record what you found.";
		return;
	}
	error.value = "";
	emit("record", {
		incident: props.incident.incident_id,
		finding: finding.value,
		reason: reason.value.trim(),
		evidence_refs: evidence.value.trim(),
		expected_revision: props.incident.incident_revision,
	});
	reason.value = "";
	evidence.value = "";
	finding.value = "";
}
</script>

<template>
	<form class="bop-finding-form" :data-testid="`bop-finding-form-${incident.incident_id}`" @submit.prevent="submit">
		<p class="kt-label" style="margin: 12px 0 4px">Current finding: <span data-testid="bop-finding-current">{{ incident.current_finding || "Unresolved" }}</span></p>
		<div class="field"><label :for="`bop-finding-${incident.incident_id}`">What did you find?</label>
			<select :id="`bop-finding-${incident.incident_id}`" v-model="finding" class="input" data-testid="bop-finding-select">
				<option value="">Choose a finding</option>
				<option value="Unresolved">Unresolved — still checking</option>
				<option value="Recovered">Recovered — the obstacle is removed</option>
				<option value="Cannot recover">Cannot recover</option>
			</select></div>
		<div class="field"><label :for="`bop-finding-reason-${incident.incident_id}`">Reason</label>
			<textarea :id="`bop-finding-reason-${incident.incident_id}`" v-model="reason" class="input" rows="3" data-testid="bop-finding-reason"></textarea></div>
		<div class="field"><label :for="`bop-finding-evidence-${incident.incident_id}`">Evidence references</label>
			<textarea :id="`bop-finding-evidence-${incident.incident_id}`" v-model="evidence" class="input" rows="2" placeholder="Log or digest-check identifiers, one per line — never bid content" data-testid="bop-finding-evidence"></textarea></div>
		<p class="bds-muted" style="margin: 4px 0 8px">Recorded with your name and the time. A finding never starts, resumes or ends the opening; the chair and the Accounting Officer act on it.</p>
		<p v-if="error" class="kt-field-error" role="alert" data-testid="bop-finding-error">{{ error }}</p>
		<button type="submit" class="btn btn-secondary" :disabled="pending" data-testid="bop-finding-submit">Record finding</button>
	</form>
</template>
