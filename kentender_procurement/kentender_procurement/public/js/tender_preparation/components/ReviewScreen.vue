<!-- TPR-DES-04 Review and readiness (§13.6): the Blocking/Warning counts,
     the fixed eight-row Check/Result table, one card per finding, and
     Preview Invitation / Preview complete Tender / Submit for approval. -->
<template>
	<div>
		<div class="tpr-masthead">
			<h1 class="kt-page-title" style="font-size: 28px">Review Tender</h1>
			<p class="kt-page-lede">Resolve Blocking findings and review the complete Tender before submission.</p>
		</div>
		<p v-if="error" class="tpr-error-banner" role="alert">{{ error }}</p>
		<div class="tpr-statuses" style="margin-bottom: 24px" data-testid="tpr-readiness-counts">
			<span class="kt-status" :class="readiness.blocking_count ? 'is-critical' : 'is-live'">{{ readiness.blocking_count || 0 }} Blocking</span>
			<span class="kt-status" :class="readiness.warning_count ? 'is-attention' : 'is-live'">{{ readiness.warning_count || 0 }} Warning</span>
		</div>
		<table class="kt-table" style="margin-bottom: 24px" data-testid="tpr-readiness-summary">
			<thead><tr><th>Check</th><th>Result</th></tr></thead>
			<tbody><tr v-for="row in summaryRows" :key="row.check"><td>{{ row.check }}</td><td>{{ row.result }}</td></tr></tbody>
		</table>
		<div v-for="finding in findings" :key="finding.finding_code + finding.field_reference + finding.message" class="kt-card kt-blueprint tpr-card-pad tpr-card-narrow" style="margin-bottom: 16px" data-testid="tpr-finding">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="tpr-card-kicker">{{ finding.severity }}</div>
			<p class="tpr-card-body">{{ finding.message }}<a v-if="finding.task_number && finding.task_number <= 5" href="#" class="tpr-inline-link" style="margin-left: 8px" @click.prevent="$emit('go-to-task', finding.task_number)">Open Task {{ finding.task_number }}</a></p>
		</div>
		<div class="tpr-actions">
			<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tpr-preview-invitation" @click="$emit('preview', 'invitation')">Preview Invitation</button>
			<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tpr-preview-tender" @click="$emit('preview', 'issued_tender')">Preview complete Tender</button>
			<button v-if="canSubmit" type="button" class="kt-btn kt-btn-primary" :disabled="pending || !readiness.ready" data-testid="tpr-submit" @click="$emit('submit')">Submit for approval</button>
		</div>
		<p class="tpr-muted" style="margin-top: 16px"><a href="#" @click.prevent="$emit('go-to-task', 5)">Back to Task 5 — Contract terms</a></p>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({ editor: { type: Object, default: () => ({}) }, pending: Boolean, error: { type: String, default: "" } });
defineEmits(["preview", "submit", "go-to-task"]);
const readiness = computed(() => props.editor.readiness || {});
const findings = computed(() => readiness.value.findings || []);
const inherited = computed(() => props.editor.inherited || {});

function blocked(codes) {
	return findings.value.some((f) => f.severity === "Blocking" && codes.includes(f.finding_code));
}
const summaryRows = computed(() => {
	const c = inherited.value.counts || {};
	const ran = !!readiness.value.run_at;
	const state = (codes, okText) => (!ran ? "Not run yet" : blocked(codes) ? "Blocking finding — see below" : okText);
	return [
		{ check: "Source handoff", result: state(["HANDOFF_INVALID", "HANDOFF_CONSUMED_ELSEWHERE", "HANDOFF_DIGEST_CHANGED"], "Complete · digest verified") },
		{ check: "Tender details", result: state(["CONTROL_MISSING", "DATE_ORDER", "VALUES_INCONSISTENT"], "Complete") },
		{ check: "Inherited requirements", result: state(["SNAPSHOT_CHANGED", "FILE_INVALID"], `Complete · ${c.items || 0} item${c.items === 1 ? "" : "s"}`) },
		{ check: "Reservation and lotting compatibility", result: state(["COMPATIBILITY_FAILED"], `Complete · ${inherited.value.reservation_category || "None"} · ${inherited.value.lotting_indicator || "Single lot"}`) },
		{ check: "Supplier-response mappings", result: state(["MAPPING_INCOMPLETE", "EVIDENCE_UNLINKED"], "Complete") },
		{ check: "Evaluation and contract mappings", result: state(["MAPPING_INCOMPLETE"], "Complete") },
		{ check: "Price schedule", result: state(["SCHEDULE_MISMATCH"], "Complete · generated") },
		{ check: "Rendered Invitation and Tender", result: state(["RENDER_FAILED", "RENDER_PROBLEM", "TEMPLATE_UNAVAILABLE", "PACKAGE_DIGEST_FAILED"], "Complete") },
	];
});
const canSubmit = computed(() => !!(props.editor.permitted_actions || {}).can_submit);
</script>
