<!-- PLN-CHG-001 v1.18 §12.9 Plan funding confirmation task, rendering U10 /
     U10-scenarios / U10-reassess-return: one task per Plan Version — the
     plan summary card, the Affordability table with its As-at line, the
     green within-approved notice (or the critical over-approved one, which
     omits Confirm), the quiet "reserves no funds" line, the funding
     evidence history (U10-history) and the decision footer. No per-item
     list, editable amount, note, reservation or "available after
     confirmation" column (§11.12). Reassessment (an Active Version whose
     funding evidence is Stale/Returned, reached from the Annual Plan
     record's own open-task button, FU-14) is the same route and screen —
     §9's own route table names one U10 Finance route, not a separate one —
     just a different header and an explanatory read-only-content line. -->
<template>
	<div>
		<p class="kt-page-kicker">{{ task.header?.eyebrow }}</p>
		<h1 class="kt-page-title">{{ reassessmentTitle || task.header?.title }}</h1>
		<p class="pln-quiet-ref">{{ task.header?.reference_line }}</p>
		<span class="kt-status" :class="badgeClass" data-testid="fnt-badge">
			{{ task.header?.badge }}
		</span>

		<p v-if="task.is_reassessment" class="pln-card-subhead" data-testid="fnt-reassessment-notice">
			Plan content is read-only. There is no reapproval action here — this records current financial evidence for unchanged approved content.
		</p>

		<div v-if="errorSummary" class="pln-notice is-critical" role="alert" data-testid="fnt-error">
			<p class="pln-notice-title">This decision could not be completed</p>
			<p>{{ errorSummary }}</p>
		</div>

		<!-- §6.1 — the requesting Planner sees the task read-only -->
		<div v-if="task.status === 'Open' && !task.can_decide && task.segregated" class="pln-notice" data-testid="fnt-segregated">
			<p class="pln-notice-title">You requested this confirmation</p>
			<p>Another Finance Confirmation Officer must decide it.</p>
		</div>

		<!-- plan summary card -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="fnt-summary">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="pln-field-grid pln-field-grid-4">
				<div class="pln-ro-field"><label>Plan Items</label><div class="pln-val">{{ task.summary?.plan_items }}</div></div>
				<div class="pln-ro-field"><label>Planned value</label><div class="pln-val">{{ task.summary?.value_display }}</div></div>
				<div class="pln-ro-field"><label>Budget Lines</label><div class="pln-val">{{ task.summary?.lines_used }}</div></div>
				<div class="pln-ro-field"><label>Reserved share</label><div class="pln-val">{{ task.summary?.reserved_share_display }}</div></div>
			</div>
		</div>

		<!-- Affordability -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="fnt-affordability">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Affordability</div>
			<table class="pln-table">
				<thead>
					<tr>
						<th>Budget Line</th><th>Funding source</th>
						<th class="pln-num">Approved</th><th class="pln-num">Planned in this Plan</th>
						<th>Within approved</th><th class="pln-num">Reserved</th>
						<th class="pln-num">Committed</th><th class="pln-num">Currently available</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="(row, idx) in task.lines" :key="idx" :data-testid="`fnt-line-${idx}`">
						<td>{{ row.budget_line_label }}</td>
						<td>{{ row.funding_source }}</td>
						<td class="pln-num">{{ row.approved_display }}</td>
						<td class="pln-num">{{ row.planned_display }}</td>
						<td>
							{{ row.within_approved_display }}
							<span v-if="!row.within_approved && row.excess_display" class="pln-excess"> · exceeds by {{ row.excess_display }}</span>
						</td>
						<td class="pln-num">{{ row.reserved_display }}</td>
						<td class="pln-num">{{ row.committed_display }}</td>
						<td class="pln-num">{{ row.available_display }}</td>
					</tr>
				</tbody>
			</table>
			<div class="pln-fact" style="margin: 8px 0">
				<span class="kt-label">Statement as at</span>
				<span class="pln-fact-val" data-testid="fnt-as-at">{{ task.as_at_display }}</span>
			</div>
			<div
				v-if="task.notice"
				class="pln-notice pln-notice-inline"
				:class="task.notice.kind === 'live' ? 'is-live' : 'is-critical'"
				:data-testid="task.notice.kind === 'live' ? 'fnt-within-approved' : 'fnt-over-approved'"
			>
				{{ task.notice.text }}
			</div>
			<!-- advisory only: below currently available blocks nothing (§12.9) -->
			<p v-if="task.advisory" class="pln-helper-text" data-testid="fnt-advisory">{{ task.advisory.text }}</p>
			<p class="pln-quiet-line" data-testid="fnt-quiet-line">{{ task.quiet_line }}</p>
		</div>

		<FinanceHistory :history="task.history" :funding-evidence="task.funding_evidence" />

		<div v-if="task.can_decide" class="pln-footer-bar">
			<button
				type="button"
				class="kt-btn kt-btn-secondary" data-testid="fnt-return"
				:disabled="pending" @click="$emit('open-return-dialog')"
			>
				Return to planner
			</button>
			<button
				v-if="task.can_confirm"
				type="button"
				class="kt-btn kt-btn-primary" data-testid="fnt-confirm"
				:disabled="pending" @click="$emit('confirm')"
			>
				Confirm plan funding
			</button>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import FinanceHistory from "./FinanceHistory.vue";

const props = defineProps({
	task: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
});

defineEmits(["confirm", "open-return-dialog"]);

const badgeClass = computed(() =>
	props.task.header?.badge === "Awaiting Finance" ? "is-pending" : "is-live"
);

// U10-reassess-return — the Active-Version state gets its own header text;
// the plan's own title stays otherwise (§9's own single U10 route).
const reassessmentTitle = computed(() =>
	props.task.is_reassessment ? `Reassess funding for Active Plan Version ${props.task.version_number}` : ""
);
</script>
