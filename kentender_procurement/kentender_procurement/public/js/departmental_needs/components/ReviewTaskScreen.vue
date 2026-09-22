<!-- NDS-UI-05 review task (§12.5) — NDS-DES-06 initial review, NDS-DES-09
     review of proposed changes. Renders the exact immutable submitted
     revision identified by the task, then the decision area. -->
<template>
	<div class="kt-page">
		<div>
			<h1 class="kt-page-title">{{ heading }}</h1>
			<div style="font-family: var(--kt-font-heading); font-weight: 600; font-size: 22px; margin-top: 10px">{{ revision.title }}</div>
			<div class="text-muted" style="font-size: 13px; margin-top: 2px">
				{{ need.need_reference }}<template v-if="isSuccessor"> · {{ revisionLabel }} · Accepted revision {{ acceptedRevision.revision_number }}</template
				><template v-else> · {{ revisionLabel }}</template>
			</div>
		</div>

		<div v-if="errorSummary" data-testid="nds-error-summary" class="kt-notice is-critical" style="max-width: 900px">
			<div class="kt-notice-body">{{ errorSummary }}</div>
		</div>

		<!-- NDS-DES-06/09 — the decision statement leads, before any content. -->
		<div class="kt-notice" style="max-width: 900px">
			<svg class="kt-notice-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect width="8" height="4" x="8" y="2" rx="1" /><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" /><path d="m9 14 2 2 4-4" /></svg>
			<div class="kt-notice-body">
				<template v-if="isSuccessor">
					<strong>Decision required</strong> — decide whether the proposed version should replace
					the accepted requirement.
				</template>
				<template v-else>
					<div style="font-family: var(--kt-font-heading); font-weight: 600; font-size: 16px; text-transform: uppercase; letter-spacing: 0.02em">
						Decision required
					</div>
					<p style="margin: 6px 0 0">
						Decide whether this requirement should be available to departmental procurement
						planning.
					</p>
				</template>
			</div>
		</div>

		<div style="display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--kt-color-neutral-700)">
			<span>Submitted by {{ requesterLabel }}</span>
			<span>·</span>
			<span>{{ scope.organisation_unit || "" }}</span>
			<span>·</span>
			<span>{{ scope.financial_year || "" }}</span>
			<span>·</span>
			<span data-volatile="true">{{ formatInstant(openedAt) }}</span>
		</div>

		<!-- NDS-DES-09 — the changed field(s) lead, before the full proposal. -->
		<div v-if="isSuccessor && changedFields.length">
			<h2>What changed</h2>
			<table class="kt-table" style="max-width: 900px; width: 100%">
				<thead><tr><th>Field</th><th>Previously accepted</th><th>Proposed</th></tr></thead>
				<tbody>
					<tr v-for="row in changedFields" :key="row.label">
						<td>{{ row.label }}</td>
						<td>{{ row.before }}</td>
						<td><strong>{{ row.after }}</strong></td>
					</tr>
				</tbody>
			</table>
		</div>

		<div>
			<h2>{{ isSuccessor ? "Complete proposal" : "What the department needs" }}</h2>
			<div style="max-width: 900px">
				<RequirementCard :revision="revision" />
			</div>
		</div>

		<div v-if="!makerCheckerBlocked && permitted.length" class="kt-decision" style="max-width: 900px">
			<p v-if="isSuccessor" class="text-muted" style="font-size: 14px; color: var(--kt-color-neutral-800); margin: 0 0 20px; max-width: 680px">
				Accepting updates the requirement available to Planning. Existing departmental and
				annual plans do not change automatically. Declining keeps the previously accepted
				requirement.
			</p>
			<p v-else class="text-muted" style="font-size: 14px; color: var(--kt-color-neutral-800); margin: 0 0 20px; max-width: 640px">
				Accepting makes this requirement available for departmental procurement planning. It
				does not approve spending or start procurement.
			</p>
			<div style="display: flex; justify-content: flex-end; gap: 12px; flex-wrap: wrap">
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
		<p v-if="makerCheckerBlocked" class="text-muted" style="font-size: 14.5px; max-width: 900px">
			You submitted this revision, so it must be decided by another Head of User Department.
		</p>
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
