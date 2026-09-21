<!-- NDS-UI-05 review task (§12.5) — NDS-DES-06 initial review, NDS-DES-09
     review of proposed changes. Renders the exact immutable submitted
     revision identified by the task, then the decision area. -->
<template>
	<div class="kt-panel-lg" style="max-width: 880px">
		<h3 style="margin: 0; display: flex; align-items: center; gap: 10px">
			<span class="kt-icon-tile">
				<svg
					v-if="isSuccessor"
					width="18"
					height="18"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="1.5"
					stroke-linecap="round"
					stroke-linejoin="round"
				><circle cx="18" cy="18" r="3" /><circle cx="6" cy="6" r="3" /><path d="M13 6h3a2 2 0 0 1 2 2v7" /><path d="M11 18H8a2 2 0 0 1-2-2V9" /></svg>
				<svg
					v-else
					width="18"
					height="18"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="1.5"
					stroke-linecap="round"
					stroke-linejoin="round"
				><rect width="8" height="4" x="8" y="2" rx="1" /><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" /><path d="m9 14 2 2 4-4" /></svg>
			</span>{{ heading }}
		</h3>
		<div style="font-size: 16px; font-weight: 600; margin: var(--kt-space-3) 0 2px">{{ revision.title }}</div>
		<div class="kt-label" style="margin-bottom: 6px">{{ need.need_reference }}</div>
		<div style="display: flex; gap: var(--kt-space-3); margin-bottom: var(--kt-space-4)">
			<span class="text-muted" style="font-size: 12px">{{ revisionLabel }}</span>
			<span v-if="isSuccessor" class="text-muted" style="font-size: 12px">
				Previously accepted revision {{ acceptedRevision.revision_number }}
			</span>
		</div>

		<div v-if="errorSummary" data-testid="nds-error-summary" class="kt-notice is-critical">
			<div class="kt-notice-body">{{ errorSummary }}</div>
		</div>

		<div class="kt-panel" style="margin-bottom: var(--kt-space-4)">
			<div class="kt-meta-row">
				<div><span class="kt-label">Requester</span><span class="kt-meta-value" style="font-size: 14px">{{ requesterLabel }}</span></div>
				<div><span class="kt-label">Department</span><span class="kt-meta-value" style="font-size: 14px">{{ scope.organisation_unit || "" }}</span></div>
				<div><span class="kt-label">Financial year</span><span class="kt-meta-value" style="font-size: 14px">{{ scope.financial_year || "" }}</span></div>
				<div><span class="kt-label">Submitted at</span><span class="kt-meta-value" style="font-size: 14px" data-volatile="true">{{ formatInstant(openedAt) }}</span></div>
			</div>
		</div>

		<!-- NDS-DES-09 — the changed field(s) lead, before the full proposal. -->
		<template v-if="isSuccessor && changedFields.length">
			<h6 class="kt-card-title nds-section-title">
				<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="18" r="3" /><circle cx="6" cy="6" r="3" /><path d="M13 6h3a2 2 0 0 1 2 2v7" /><path d="M11 18H8a2 2 0 0 1-2-2V9" /></svg
				><span>What changed</span>
			</h6>
			<table class="kt-table" style="margin: var(--kt-space-4) 0 var(--kt-space-6)">
				<thead><tr><th>Field</th><th>Previously accepted</th><th>Proposed</th></tr></thead>
				<tbody>
					<tr v-for="row in changedFields" :key="row.label">
						<td>{{ row.label }}</td>
						<td>{{ row.before }}</td>
						<td><strong>{{ row.after }}</strong></td>
					</tr>
				</tbody>
			</table>
		</template>

		<RequirementCard :revision="revision" />

		<h6 class="kt-card-title nds-section-title">
			<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m14.5 12.5-8 8a2.119 2.119 0 1 1-3-3l8-8" /><path d="m16 16 6-6" /><path d="m8 8 6-6" /><path d="m9 7 8 8" /><path d="m21 11-8-8" /></svg
			><span>Your decision</span>
		</h6>
		<p v-if="isSuccessor" class="text-muted" style="font-size: 12px; margin: var(--kt-space-3) 0 4px">
			Accepting updates the requirement available to Planning. Existing departmental and
			annual plans do not change automatically.
		</p>
		<p v-if="isSuccessor" class="text-muted" style="font-size: 12px; margin: 0 0 var(--kt-space-4)">
			Declining the changes keeps the previously accepted requirement.
		</p>
		<p v-else class="text-muted" style="font-size: 12px; margin: var(--kt-space-3) 0 var(--kt-space-4)">
			Accepting makes this requirement available for departmental procurement planning. It
			does not approve spending or start procurement.
		</p>
		<p v-if="makerCheckerBlocked" class="text-muted" style="font-size: 14.5px; margin: 0 0 var(--kt-space-4)">
			You submitted this revision, so it must be decided by another Head of User
			Department.
		</p>

		<div
			v-if="!makerCheckerBlocked && permitted.length"
			style="display: flex; justify-content: flex-end; gap: var(--kt-space-2); padding-top: var(--kt-space-4); border-top: 1px solid var(--kt-color-divider)"
		>
			<button class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="nds-decision-return" @click="$emit('return')">
				<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7v6h6" /><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13" /></svg
				>Return for correction
			</button>
			<button class="kt-btn kt-btn-secondary kt-danger" :disabled="pending" data-testid="nds-decision-decline" @click="$emit('decline')">
				<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18M6 6l12 12" /></svg
				>{{ declineLabel }}
			</button>
			<button class="kt-btn kt-btn-primary" :disabled="pending" data-testid="nds-decision-accept" @click="$emit('accept')">
				<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5" /></svg
				>{{ acceptLabel }}
			</button>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import RequirementCard from "./RequirementCard.vue";
import { formatDate, formatInstant } from "../data/format.js";

const props = defineProps({
	need: { type: Object, default: () => ({}) },
	revision: { type: Object, default: () => ({}) },
	acceptedRevision: { type: Object, default: () => ({}) },
	scope: { type: Object, default: () => ({}) },
	requesterLabel: { type: String, default: "" },
	openedAt: { type: String, default: "" },
	taskType: { type: String, default: "Initial acceptance" },
	permitted: { type: Array, default: () => [] },
	makerCheckerBlocked: Boolean,
	errorSummary: { type: String, default: "" },
	pending: Boolean,
});
defineEmits(["return", "accept", "decline"]);

const isSuccessor = computed(() => props.taskType === "Successor acceptance");

const heading = computed(() => (isSuccessor.value ? "Review proposed changes" : "Review departmental need"));
const revisionLabel = computed(() =>
	isSuccessor.value ? `Proposed revision ${props.revision.revision_number || ""}` : `Revision ${props.revision.revision_number || ""}`
);

// §8.5 — the presented decision labels split by whether this is the
// requirement's initial submission or a proposed update to an already
// accepted one; the underlying command is the same either way.
const acceptLabel = computed(() => (isSuccessor.value ? "Accept proposed changes" : "Accept for planning"));
const declineLabel = computed(() => (isSuccessor.value ? "Decline proposed changes" : "Do not take forward"));

const DIFF_FIELDS = [
	{ key: "title", label: "Requirement title" },
	{ key: "description", label: "Description" },
	{ key: "expected_operational_result", label: "Expected result" },
	{ key: "indicative_quantity", label: "Quantity" },
	{ key: "unit_label", label: "Unit" },
	{ key: "required_by_date", label: "Required by", format: formatDate },
];

const changedFields = computed(() => {
	if (!isSuccessor.value || !props.acceptedRevision?.name) return [];
	const rows = [];
	for (const field of DIFF_FIELDS) {
		const before = props.acceptedRevision[field.key];
		const after = props.revision[field.key];
		if (String(before ?? "") === String(after ?? "")) continue;
		const fmt = field.format || ((v) => v ?? "");
		rows.push({ label: field.label, before: fmt(before), after: fmt(after) });
	}
	return rows;
});
</script>
