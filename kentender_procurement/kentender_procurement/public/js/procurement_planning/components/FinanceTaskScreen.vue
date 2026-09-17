<!-- PLN-CHG-001 v1.23 §10.9 — Finance review and reassessment (U10), ported
     from U10.dc.html.

     Finance answers one question: is each planned amount within its approved
     budget line? So the first view is Budget line, Line name, Approved,
     Planned, Difference and Result, and nothing else competes with it.

     Current balances are advisory and live in a collapsed section. That
     distinction is the whole point of the screen: low availability does not
     block confirmation, an approved-amount excess does. Confirming records
     affordability — it reserves nothing and approves nothing. -->
<template>
	<div>
		<div class="pln-masthead">
			<div>
				<h1 class="kt-page-title" data-testid="fnt-title">{{ title }}</h1>
				<p class="kt-page-lede">{{ description }}</p>
			</div>
		</div>

		<div class="kt-meta-row pln-context-row" data-testid="fnt-context">
			<div>
				<span class="kt-label">Plan</span>
				<span class="kt-meta-value">{{ task.header?.title }}</span>
			</div>
			<div>
				<span class="kt-label">Reference</span>
				<span class="kt-meta-value">{{ planReference }}</span>
			</div>
			<div>
				<span class="kt-label">Version</span>
				<span class="kt-meta-value">{{ versionNumber }}</span>
			</div>
			<div>
				<span class="kt-label">Review status</span>
				<span class="kt-meta-value">
					<span class="kt-status" :class="badgeClass" data-testid="fnt-badge">{{ reviewStatus }}</span>
				</span>
			</div>
		</div>

		<!-- The statement this decision is being made on. Budget version and
		     request time are provenance, not the decision. -->
		<div class="kt-meta-row" data-testid="fnt-statement">
			<div>
				<span class="kt-label">Budget</span>
				<span class="kt-meta-value">{{ task.budget_reference || "—" }}</span>
			</div>
			<div>
				<span class="kt-label">Amounts as at</span>
				<span class="kt-meta-value" data-testid="fnt-as-at">{{ task.as_at_display }}</span>
			</div>
		</div>

		<!-- U10-REASSESS — an Active plan being checked against a revised
		     budget, not re-approved. -->
		<div v-if="task.is_reassessment" class="kt-notice is-info" data-testid="fnt-reassessment-notice">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
				<circle cx="12" cy="12" r="9"></circle><path d="M12 8h.01M11 12h1v5h1"></path>
			</svg>
			<div class="kt-notice-body">
				This records new funding evidence for the current plan. It does not change or re-approve the plan.
			</div>
		</div>

		<!-- U10-CHANGED — the statement this review was made on has moved. -->
		<div v-if="task.stale" class="kt-notice is-warning" data-testid="fnt-changed">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
				<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
			</svg>
			<div class="kt-notice-body pln-notice-split">
				<span>The amounts for this review have changed.</span>
				<a
					v-if="task.replacement_route"
					href="#"
					data-testid="fnt-open-replacement"
					@click.prevent="$emit('navigate', task.replacement_route)"
				>Open updated funding review</a>
				<span v-else class="kt-muted">Responsible role: Procurement Planner</span>
			</div>
		</div>

		<div v-if="task.segregated" class="kt-notice is-critical" data-testid="fnt-segregated">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
				<circle cx="12" cy="12" r="9"></circle><path d="M12 8v5M12 16h.01"></path>
			</svg>
			<div class="kt-notice-body">
				You cannot decide funding for a plan you prepared. An authorised, independent decision-maker is required.
			</div>
		</div>

		<p v-if="errorSummary" class="pln-error-summary" data-testid="fnt-error">{{ errorSummary }}</p>

		<!-- The comparison. Approved versus planned, per line. -->
		<table class="kt-table" data-testid="fnt-comparison">
			<thead>
				<tr>
					<th>Budget line</th><th>Line name</th>
					<th class="is-num">Approved amount</th><th class="is-num">Planned amount</th>
					<th class="is-num">Difference</th><th>Result</th><th>Action</th>
				</tr>
			</thead>
			<tbody>
				<template v-for="(row, index) in lines" :key="row.budget_line">
					<tr :data-testid="`fnt-line-${index}`">
						<td>{{ row.budget_line_reference }}</td>
						<td>{{ row.line_name }}</td>
						<td class="is-num">{{ row.approved_display }}</td>
						<td class="is-num">{{ row.planned_display }}</td>
						<td class="is-num">{{ row.difference_display }}</td>
						<td><span class="kt-status" :class="`is-${row.result_kind}`">{{ row.result }}</span></td>
						<td>
							<a href="#" data-testid="fnt-line-details" @click.prevent="openLine = openLine === index ? null : index">View details</a>
						</td>
					</tr>
					<!-- U10-LOW-AVAILABILITY — advisory, said beside the line it
					     is about, and explicitly not a reason to withhold
					     confirmation. -->
					<tr v-if="!row.within_available && row.within_approved" class="pln-row-detail" :data-testid="`fnt-low-availability-${index}`">
						<td colspan="7" class="kt-muted">
							Current availability is lower than the planned amount. The plan is still within the approved
							budget, so funding confirmation is permitted.
						</td>
					</tr>
					<tr v-if="!row.within_approved" class="pln-row-detail" :data-testid="`fnt-excess-${index}`">
						<td colspan="7" class="pln-error-summary">
							{{ row.line_name || row.budget_line_reference }} exceeds its approved budget by {{ row.excess_display }}.
						</td>
					</tr>
					<tr v-if="openLine === index" class="pln-row-detail" :data-testid="`fnt-line-detail-${index}`">
						<td colspan="7">
							<div class="kt-meta-row">
								<div>
									<span class="kt-label">Funding source</span>
									<span class="kt-meta-value">{{ row.funding_source }}</span>
								</div>
								<div>
									<span class="kt-label">Reserved</span>
									<span class="kt-meta-value">{{ row.reserved_display }}</span>
								</div>
								<div>
									<span class="kt-label">Committed</span>
									<span class="kt-meta-value">{{ row.committed_display }}</span>
								</div>
								<div>
									<span class="kt-label">Currently available</span>
									<span class="kt-meta-value">{{ row.available_display }}</span>
								</div>
							</div>
						</td>
					</tr>
				</template>
			</tbody>
		</table>

		<!-- Current balances: advisory, collapsed, visually separated from the
		     approved-versus-planned decision. -->
		<details class="kt-disclosure" data-testid="fnt-balances">
			<summary class="kt-disclosure-head">
				<span class="kt-disclosure-title">Current balances</span>
			</summary>
			<div class="kt-disclosure-body">
				<table class="kt-table">
					<thead>
						<tr>
							<th>Budget line</th><th>Funding source</th>
							<th class="is-num">Reserved</th><th class="is-num">Committed</th><th class="is-num">Currently available</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="row in lines" :key="`balance-${row.budget_line}`">
							<td>{{ row.budget_line_reference }}</td>
							<td>{{ row.funding_source }}</td>
							<td class="is-num">{{ row.reserved_display }}</td>
							<td class="is-num">{{ row.committed_display }}</td>
							<td class="is-num">{{ row.available_display }}</td>
						</tr>
					</tbody>
				</table>
				<p class="kt-muted">Balances as at {{ task.as_at_display }}. These are advisory and do not affect the affordability decision.</p>
			</div>
		</details>

		<!-- U10-HISTORY — funding checked at approval versus the latest check,
		     never merged into one claim. -->
		<FinanceHistory v-if="history.length" :rows="history" />

		<p class="kt-muted" data-testid="fnt-consequence">
			Confirming records affordability. It does not reserve funds or approve the plan.
		</p>

		<div v-if="task.status === 'Open'" class="pln-footer" data-testid="fnt-footer">
			<button
				type="button"
				class="kt-btn kt-btn-secondary"
				data-testid="fnt-return"
				:disabled="pending || !task.can_decide"
				@click="$emit('open-return-dialog')"
			>
				Return to planner
			</button>
			<div class="pln-footer-right">
				<!-- Absent when the plan exceeds an approved amount: the
				     decision is not available, and Return is how it gets
				     fixed (§6.3). -->
				<button
					v-if="task.can_confirm"
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="fnt-confirm"
					:disabled="pending"
					@click="$emit('confirm')"
				>
					Confirm plan funding
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import FinanceHistory from "./FinanceHistory.vue";

const props = defineProps({
	task: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
});

defineEmits(["confirm", "open-return-dialog", "navigate"]);

const openLine = ref(null);

const lines = computed(() => props.task.lines || []);
const history = computed(() => props.task.history || []);

const title = computed(() =>
	props.task.is_reassessment ? "Check funding again for the current plan" : "Check funding for the annual plan",
);
const description = computed(() =>
	props.task.is_reassessment
		? "The approved budget has changed. Check the existing plan against the revised budget."
		: "Confirm whether each planned amount is within its approved budget line.",
);

const referenceLine = computed(() => props.task.header?.reference_line || "");
const planReference = computed(() => referenceLine.value.split(" · ")[1] || "");
const versionNumber = computed(() => {
	const match = /Version (\d+)/.exec(referenceLine.value);
	return match ? match[1] : "";
});

const reviewStatus = computed(() => {
	if (props.task.status !== "Open") return props.task.status;
	return props.task.can_decide ? "Your decision required" : "Awaiting Finance";
});
const badgeClass = computed(() => (props.task.status === "Open" ? "is-attention" : "is-live"));
</script>
