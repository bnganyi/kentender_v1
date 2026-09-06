<!-- PLN-UI-10 Plan funding confirmation task (§12.9), rendering PLN-DES-10
     v1.12 class-for-class: one task per Plan Version — the four-field plan
     summary card, the Affordability table with its As-at line, the green
     within-approved notice (or the critical over-approved one, which omits
     Confirm), the quiet "reserves no funds" line and the decision footer.
     No per-item list, editable amount, note, reservation or "available after
     confirmation" column (§11.12). -->
<template>
	<div>
		<p class="kt-page-kicker">{{ task.header?.eyebrow }}</p>
		<h1 class="kt-page-title">{{ task.header?.title }}</h1>
		<p class="pln-quiet-ref">{{ task.header?.reference_line }}</p>
		<span class="kt-status" :class="badgeClass" data-testid="fnt-badge">
			{{ task.header?.badge }}
		</span>

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
				<div class="pln-ro-field"><label>Plan value</label><div class="pln-val">{{ task.summary?.value_display }}</div></div>
				<div class="pln-ro-field"><label>Procurement Budget Lines used</label><div class="pln-val">{{ task.summary?.lines_used }}</div></div>
				<div class="pln-ro-field"><label>Reserved share</label><div class="pln-val">{{ task.summary?.reserved_share_display }}</div></div>
			</div>
		</div>

		<!-- Affordability -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="fnt-affordability">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Affordability</div>
			<p class="pln-as-at" data-testid="fnt-as-at">Position as at {{ task.as_at_display }}</p>
			<table class="pln-table">
				<thead>
					<tr>
						<th>Procurement Budget Line</th><th>Funding source</th>
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

const props = defineProps({
	task: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
});

defineEmits(["confirm", "open-return-dialog"]);

const badgeClass = computed(() =>
	props.task.header?.badge === "Awaiting Finance" ? "is-pending" : "is-live"
);
</script>
