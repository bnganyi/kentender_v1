<!-- NDS-UI-05 review task (§12.5) — NDS-DES-06 initial review, NDS-DES-09
     review of proposed changes. Renders the exact immutable submitted
     revision identified by the task, then the decision area.
     NDS-DES-14-REVIEW-CHANGED is ported class-for-class from NDS
     Artboards.dc.html. -->
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

		<!-- NDS-CHG-001 v1.15 §5.5 — the guidance region replaces the
		     "Decision required" statement: the reviewer's next step leads,
		     before any content (KT-STD-001 v1.9 §2.9.3 rule 1). -->
		<div ref="guidanceEl" class="kt-guidance-mount" data-testid="nds-guidance"></div>

		<div v-if="errorSummary" data-testid="nds-error-summary" class="kt-notice is-critical" style="max-width: 900px">
			<div class="kt-notice-body">{{ errorSummary }}</div>
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

		<!-- NDS-DES-14-REVIEW-CHANGED — the task loaded but the server now
		     reports no decision this viewer may still make (`permitted` empty),
		     most commonly because someone else already decided it: without this,
		     the decision area simply disappears with no explanation. The
		     artboard leads with this notice, before the requirement content —
		     Refresh is the one thing this state asks the actor to do first. -->
		<div
			v-if="!makerCheckerBlocked && !permitted.length"
			class="kt-notice is-warning"
			style="max-width: 900px"
			data-testid="nds-review-changed"
		>
			<div class="kt-notice-body">
				<p style="margin: 0">This review has already changed. Refresh to see the current result.</p>
				<button type="button" class="btn btn-secondary" style="margin-top: 12px" data-testid="nds-review-refresh" @click="$emit('refresh')">
					Refresh
				</button>
			</div>
		</div>

		<!-- NDS-DES-09 — the changed field(s) lead, before the full proposal. -->
		<!-- A titled section is a `.kt-region`: that is what puts its heading
		     in the section typeface and its content on the section rhythm.
		     Five headings in this module stood in bare divs, so they were
		     styled by nothing and drifted from the sections beside them
		     (found live 24 Sep 2026). -->
		<div v-if="isSuccessor && changedFields.length" class="kt-region">
			<h2>What changed</h2>
			<table class="table" style="max-width: 900px; width: 100%">
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

		<div class="kt-region">
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
				<button class="btn btn-secondary" :disabled="pending" data-testid="nds-decision-return" @click="$emit('return')">
					<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7v6h6" /><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13" /></svg
					>Return for correction
				</button>
				<button class="btn btn-secondary kt-danger" :disabled="pending" data-testid="nds-decision-decline" @click="$emit('decline')">
					<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18M6 6l12 12" /></svg
					>{{ declineLabel }}
				</button>
				<button class="btn btn-primary" :disabled="pending" data-testid="nds-decision-accept" @click="$emit('accept')">
					<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5" /></svg
					>{{ acceptLabel }}
				</button>
			</div>
		</div>
		<!-- v1.15 — "You submitted this revision…" is the maker's next-step
		     sentence now, stated once in the guidance region. -->
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import RequirementCard from "./RequirementCard.vue";
import { followFix, useGuidance } from "../../nds_shared/composables/useGuidance.js";
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
	nextStep: { type: Object, default: null },
	journey: { type: Object, default: null },
});
defineEmits(["return", "accept", "decline", "refresh"]);

const guidanceEl = ref(null);
useGuidance(guidanceEl, { answer: () => props.nextStep, journey: () => props.journey }, { onFix: followFix });

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
