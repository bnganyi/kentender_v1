<!-- TPR-DES-03/04 (+ TPR-DES-13 "Returned"): the Draft editor shell — the
     returned-for-correction notice, record head, progress row, context
     strip, the active task's form and the sticky footer (Back / Save draft /
     Continue or Review Tender). Task forms expose getPayload(); the root
     owns every command. -->
<template>
	<div class="tnd-page" :data-screen-label="task === 'requirements' ? 'TPR-DES-04 Draft supplier and contract requirements' : 'TPR-DES-03 Draft Tender details'">
		<div v-if="returned" class="kt-notice is-attention" style="margin-bottom: 16px" data-testid="tnd-returned-notice">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
			<div class="kt-notice-body"><strong>Returned for correction</strong> by {{ returned.returned_by }}, {{ returned.returned_at }} — "{{ returned.comment }}"</div>
		</div>
		<BlueprintCard>
			<RecordHead :title="tender.title" :badge="versionBadge" badge-tone="is-draft" :refs="`${tender.tender_reference} · ${tender.requisition_reference}`" :lede="task === 'details' ? 'Set the dates and security suppliers must follow.' : ''" />
			<ProgressRow :current="task" :statuses="record.tasks || {}" @go="$emit('go-task', $event)" />
			<ContextStrip v-if="task === 'details'" :context="(record.inherited || {}).context || {}" @open-drawer="$emit('open-drawer')" />
			<div v-if="error" class="tnd-section tnd-section--notice" style="padding-top: 16px">
				<div class="kt-notice is-critical" role="alert" data-testid="tnd-editor-error"><div class="kt-notice-body">{{ error }}</div></div>
			</div>
			<TaskDetails v-if="task === 'details'" ref="formRef" :values="record.officer_values || {}" :options="record.options || {}" :identity="identity" :errors="fieldErrors" />
			<TaskRequirements v-else ref="formRef" :values="record.officer_values || {}" :options="record.options || {}" :catalogue="record.catalogue || {}" :inherited="record.inherited || {}" :evidence="record.evidence_requirements || []" :stages="record.evaluation_stages || []" :identity="identity" :errors="fieldErrors" :pending="pending" @add-evidence="$emit('add-evidence')" @edit-evidence="$emit('edit-evidence', $event)" @remove-evidence="$emit('remove-evidence', $event)" @open-drawer="$emit('open-drawer', true)" />
		</BlueprintCard>
		<div class="tnd-footer">
			<div class="tnd-actions" style="align-items: center">
				<a href="#" class="tnd-footer-back" data-testid="tnd-back" @click.prevent="$emit('back')">{{ task === "details" ? "Back to Tenders" : "Back" }}</a>
				<button v-if="canRequestCorrection" type="button" class="kt-btn kt-btn-ghost" :disabled="pending" data-testid="tnd-request-correction" @click="$emit('request-correction')">Request requisition correction</button>
			</div>
			<div class="tnd-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tnd-save-draft" @click="$emit('save')">Save draft</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="tnd-continue" @click="$emit('continue')">{{ task === "details" ? "Continue" : "Review Tender" }}</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import BlueprintCard from "./BlueprintCard.vue";
import RecordHead from "./RecordHead.vue";
import ProgressRow from "./ProgressRow.vue";
import ContextStrip from "./ContextStrip.vue";
import TaskDetails from "./TaskDetails.vue";
import TaskRequirements from "./TaskRequirements.vue";

const props = defineProps({
	record: { type: Object, default: () => ({ tender: {} }) },
	task: { type: String, default: "details" },
	fieldErrors: { type: Object, default: () => ({}) },
	error: { type: String, default: "" },
	pending: Boolean,
});
defineEmits(["go-task", "open-drawer", "add-evidence", "edit-evidence", "remove-evidence", "save", "continue", "back", "request-correction"]);

const formRef = ref(null);
const tender = computed(() => props.record.tender || {});
const returned = computed(() => props.record.returned || null);
const identity = computed(() => `${tender.value.name}:${tender.value.record_version}`);
const canRequestCorrection = computed(() => (props.record.allowed_actions || []).includes("request_requisition_correction"));
const versionBadge = computed(() => `Draft Version ${(props.record.version || {}).version_number || 1}`);
function getPayload() {
	return formRef.value ? formRef.value.getPayload() : {};
}
function isDirty() {
	return !!(formRef.value && formRef.value.isDirty && formRef.value.isDirty());
}
defineExpose({ getPayload, isDirty });
</script>
