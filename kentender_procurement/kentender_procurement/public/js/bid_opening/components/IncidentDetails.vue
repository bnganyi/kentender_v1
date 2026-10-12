<!-- An incident's full details (Project Owner, 10 Oct 2026). Opening them is an explicit, audited read that names its purpose; the
     summary row above is part of the opening page and needs none. Nothing here loads on its own and a page refresh never repeats it. -->
<script setup>
import { computed, ref } from "vue";
import { getIncidentDetails } from "../data/api.js";

const props = defineProps({
	tender: { type: String, required: true },
	incident: { type: String, required: true },
	purposes: { type: Array, default: () => [] },
});
const purpose = ref("");
const details = ref(null);
const error = ref("");
const busy = ref(false);
const rows = computed(() => {
	const d = details.value;
	if (!d) return [];
	return [
		["Status", d.status],
		["Raised", d.raised_label],
		["Handled by", d.handled_by],
		["Notice", `${d.notification_state}${d.notification_attempts ? ` · ${d.notification_attempts} attempt${d.notification_attempts === 1 ? "" : "s"}` : ""}${d.last_notified_label ? ` · last ${d.last_notified_label}` : ""}`],
		...(d.envelope ? [["Envelope", d.envelope]] : []),
		...(d.resolution_note ? [["Resolution", `${d.resolution_note}${d.resolved_label ? ` · ${d.resolved_label}` : ""}${d.resolved_by ? ` · ${d.resolved_by}` : ""}`]] : []),
	].filter((r) => r[1]);
});
async function show() {
	if (!purpose.value || busy.value) return;
	busy.value = true;
	error.value = "";
	try {
		const r = await getIncidentDetails(props.tender, props.incident, purpose.value);
		if (r && r.ok) details.value = r.details;
		else error.value = (r && r.message) || "The details could not be opened.";
	} catch (e) {
		error.value = "These details are not available to you.";
	} finally {
		busy.value = false;
	}
}
</script>

<template>
	<div class="bop-incident-details" :data-testid="`bop-incident-details-${incident}`">
		<template v-if="!details">
			<label class="kt-label" :for="`bop-purpose-${incident}`">Why are you opening these details?</label>
			<select :id="`bop-purpose-${incident}`" v-model="purpose" class="input" data-testid="bop-incident-purpose">
				<option value="">Choose a purpose</option>
				<option v-for="p in purposes" :key="p" :value="p">{{ p }}</option>
			</select>
			<button type="button" class="btn btn-secondary" :disabled="!purpose || busy" data-testid="bop-incident-show" @click="show">Show full details</button>
			<p class="bds-muted" style="margin:8px 0 0">Opening these details is recorded with your name, the time and your purpose.</p>
			<p v-if="error" class="kt-field-error" data-testid="bop-incident-error">{{ error }}</p>
		</template>
		<table v-else class="table" data-testid="bop-incident-detail-table"><tbody>
			<tr v-for="r in rows" :key="r[0]"><th scope="row">{{ r[0] }}</th><td>{{ r[1] }}</td></tr>
		</tbody></table>
	</div>
</template>
