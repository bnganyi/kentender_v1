<!-- Board a4: how to attend, editable before publication or to post updated
     instructions. The opening time is the Tender's deadline (not editable). -->
<template>
	<div class="kt-region"><h2>How to attend</h2>
		<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px 24px;max-width:1000px">
			<div class="field" style="grid-column:1 / -1"><label for="bop-attendance-method">Attendance method</label><input id="bop-attendance-method" v-model="method" class="input" data-testid="bop-attendance-method"></div>
			<div class="field" style="grid-column:1 / -1"><label for="bop-attendance-instructions">What attendees can do</label><textarea id="bop-attendance-instructions" v-model="instructions" class="input" rows="3" data-testid="bop-attendance-instructions"></textarea></div>
			<div><span class="kt-label">Opening time</span><div class="kt-meta-value">{{ openingLabel }}</div></div>
			<div><span class="kt-label">Published</span><div class="kt-meta-value">{{ publishedLabel || "Not yet" }}</div></div>
		</div>
		<p v-if="error" class="bop-field-error" role="alert" data-testid="bop-arrangements-error">{{ error }}</p>
	</div>
	<div class="kt-decision">
		<p style="margin:0 0 var(--space-4);font-size:15px;max-width:75ch">Publishing shows these details on the public Tender page straight away. No bid details are shown. If the online service is unavailable on the day, post updated instructions here; the opening waits until attendees can join.</p>
		<div style="display:flex;justify-content:flex-end;gap:12px">
			<button v-if="published" type="button" class="btn btn-secondary" @click="$emit('cancel')">Cancel</button>
			<button type="button" class="btn btn-primary" :disabled="pending || !method.trim()" data-testid="bop-publish" @click="$emit('publish', { attendance_method: method.trim(), access_instructions: instructions.trim() })">Publish how to attend</button>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue";

const props = defineProps({ initial: { type: Object, default: () => ({}) }, openingLabel: { type: String, default: "" }, publishedLabel: { type: String, default: "" }, published: Boolean, pending: Boolean, error: { type: String, default: "" } });
defineEmits(["publish", "cancel"]);
const method = ref(props.initial.attendance_method || "Attend the public bid opening online");
const instructions = ref(props.initial.access_instructions || "");
</script>
