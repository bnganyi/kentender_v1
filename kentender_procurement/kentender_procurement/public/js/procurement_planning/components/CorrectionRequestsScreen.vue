<!-- PLN-CHG-001 v1.23 §10.15 — Plan correction requests (U16), ported from
     U16.dc.html.

     The Planner reads what must change, what it is holding, and what they may
     lawfully do — in that order. Request identifiers, originating versions and
     timestamps are real and kept, but they belong in the issue's own detail,
     not in the sentence that explains the problem (PLN22-AC-011).

     Two separate facts are never merged. The hold is temporary and lifts only
     when every issue reaches a permitted outcome, so the count of what is
     still outstanding is stated rather than implied. The scope restriction is
     permanent and survives every outcome, so it keeps its own notice and there
     is no manual unlock and no "resume requisitions" action anywhere. -->
<template>
	<div>
		<div class="pln-masthead">
			<div>
				<h1 class="kt-page-title" data-testid="cor-title">Planning change required</h1>
			</div>
		</div>

		<div class="kt-meta-row pln-context-row" data-testid="cor-context">
			<div>
				<span class="kt-label">Purchase</span>
				<span class="kt-meta-value">{{ task.title }}</span>
			</div>
			<div>
				<span class="kt-label">Reference</span>
				<span class="kt-meta-value">{{ task.plan_item_id }}</span>
			</div>
			<div>
				<span class="kt-label">Current plan version</span>
				<span class="kt-meta-value">{{ task.version_number }}</span>
			</div>
		</div>

		<!-- The temporary hold. U16-MULTIPLE — one outcome never clears
		     another's, so the remaining count is stated. -->
		<div v-if="task.hold?.active" class="kt-notice is-warning" data-testid="cor-hold">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
				<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
			</svg>
			<div class="kt-notice-body">
				<strong>{{ task.hold.text }}</strong>
				<p data-testid="cor-hold-remaining">{{ task.hold.remaining }}</p>
			</div>
		</div>

		<!-- The permanent restriction. U16-PERMANENT-SCOPE — it stays visible
		     after every request resolves, and never gains a "restored" badge. -->
		<div v-if="task.scope_lock?.locked" class="kt-notice is-attention" data-testid="cor-scope-lock">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
				<rect x="5" y="11" width="14" height="9" rx="1"></rect><path d="M8 11V8a4 4 0 0 1 8 0v3"></path>
			</svg>
			<div class="kt-notice-body">{{ task.scope_lock.text }}</div>
		</div>

		<table v-if="requests.length" class="kt-table" data-testid="cor-issues">
			<thead>
				<tr><th>What needs to change</th><th>Status</th><th>Requested from</th><th>Action</th></tr>
			</thead>
			<tbody>
				<template v-for="row in requests" :key="row.request">
					<tr data-testid="cor-issue-row">
						<td>{{ row.change_required }}</td>
						<td><span class="kt-status" :class="`is-${row.status_kind}`">{{ row.status }}</span></td>
						<td>{{ row.requested_from }}</td>
						<td>
							<a href="#" data-testid="cor-issue-action" @click.prevent="$emit('open-issue', row.request)">{{ row.action }}</a>
						</td>
					</tr>
					<!-- U16-OPEN-DETAIL — the mechanics, under the issue they
					     belong to, opened deliberately. -->
					<tr v-if="openIssue === row.request" class="pln-row-detail" data-testid="cor-issue-detail">
						<td colspan="4">
							<div class="kt-meta-row">
								<div>
									<span class="kt-label">Full requested change</span>
									<span class="kt-meta-value">{{ row.change_required }}</span>
								</div>
								<div>
									<span class="kt-label">Affected purchase</span>
									<span class="kt-meta-value">{{ task.title }}</span>
								</div>
								<div>
									<span class="kt-label">Requested by</span>
									<span class="kt-meta-value">{{ row.detail.requested_by }}</span>
								</div>
								<div>
									<span class="kt-label">Requested at</span>
									<span class="kt-meta-value">{{ row.detail.requested_display }}</span>
								</div>
								<div>
									<span class="kt-label">Originating record</span>
									<span class="kt-meta-value">
										{{ row.detail.requisition_reference }}
										<template v-if="row.detail.requisition_version"> · Version {{ row.detail.requisition_version }}</template>
									</span>
								</div>
								<div>
									<span class="kt-label">Request</span>
									<span class="kt-meta-value">{{ row.detail.request }}</span>
								</div>
							</div>

							<!-- U16-COMPLETE — the exact plan that corrects it,
							     and its activation, before the control. -->
							<div v-if="row.can_record_completed" class="kt-meta-row" data-testid="cor-correcting-plan">
								<div>
									<span class="kt-label">Correcting plan</span>
									<span class="kt-meta-value">{{ correctingPlan.plan_reference }}</span>
								</div>
								<div>
									<span class="kt-label">Version</span>
									<span class="kt-meta-value">{{ correctingPlan.version_number }}</span>
								</div>
								<div>
									<span class="kt-label">Activation date</span>
									<span class="kt-meta-value">{{ correctingPlan.activated_display }}</span>
								</div>
							</div>

							<!-- The outcome of the request, once it has one. -->
							<div v-if="row.terminal" class="kt-meta-row" data-testid="cor-outcome">
								<div>
									<span class="kt-label">Outcome recorded</span>
									<span class="kt-meta-value">{{ row.detail.resolved_display }}</span>
								</div>
								<div>
									<span class="kt-label">Recorded by</span>
									<span class="kt-meta-value">{{ row.detail.resolved_by }}</span>
								</div>
								<div>
									<span class="kt-label">Note</span>
									<span class="kt-meta-value">{{ row.detail.resolution_note }}</span>
								</div>
							</div>

							<div v-if="canAct" class="pln-footer" data-testid="cor-issue-footer">
								<span>
									<!-- Why a control is absent, rather than a
									     disabled button that explains nothing. -->
									<span
										v-if="!row.terminal && !row.can_record_completed"
										class="kt-muted"
										data-testid="cor-completion-blocked"
									>
										{{ row.completion_blocked_reason }}
										<a
											v-if="correctingPlan.plan_reference"
											href="#"
											data-testid="cor-open-plan"
											@click.prevent="$emit('navigate', ['annual-procurement-plan', correctingPlan.plan_reference])"
										>Open the annual plan</a>
									</span>
								</span>
								<div class="pln-footer-right">
									<button
										v-if="row.can_close_without_change"
										type="button"
										class="kt-btn kt-btn-secondary"
										data-testid="cor-close-no-change"
										:disabled="pending"
										@click="$emit('close-without-change', row)"
									>
										Close without a plan change
									</button>
									<button
										v-if="row.can_start"
										type="button"
										class="kt-btn kt-btn-primary"
										data-testid="cor-prepare-correction"
										:disabled="pending"
										@click="$emit('prepare-correction', row)"
									>
										Prepare plan correction
									</button>
									<button
										v-if="row.can_record_completed"
										type="button"
										class="kt-btn kt-btn-primary"
										data-testid="cor-record-completed"
										:disabled="pending"
										@click="$emit('record-completed', row)"
									>
										Record correction completed
									</button>
								</div>
							</div>
						</td>
					</tr>
				</template>
			</tbody>
		</table>
		<p v-else class="kt-muted" data-testid="cor-no-issues">No planning change has been requested for this purchase.</p>

		<!-- U16-ADDITIONAL-REQUIREMENT — the lawful route for a requirement
		     that arrived after this purchase's scope was fixed. Naming it here
		     creates nothing; the action only opens the pending work. -->
		<template v-if="additional">
			<h3 class="kt-card-title">{{ additional.heading }}</h3>
			<div v-for="source in additional.sources" :key="source.dpp_entry" class="kt-card" data-testid="cor-additional">
				<h6 class="kt-card-title">{{ source.title }}</h6>
				<div class="kt-meta-row">
					<div>
						<span class="kt-label">Department</span>
						<span class="kt-meta-value">{{ source.department }}</span>
					</div>
					<div>
						<span class="kt-label">Quantity</span>
						<span class="kt-meta-value">{{ source.quantity_display }}</span>
					</div>
					<div>
						<span class="kt-label">Amount</span>
						<span class="kt-meta-value">{{ source.amount_display }}</span>
					</div>
					<div>
						<span class="kt-label">Accepted requirement</span>
						<span class="kt-meta-value">{{ source.entry_id }}</span>
					</div>
				</div>
				<!-- Three results, none of which implies another. -->
				<div class="kt-meta-row" data-testid="cor-additional-results">
					<div>
						<span class="kt-label">Annual plan</span>
						<span class="kt-meta-value">{{ source.annual_plan_result }}</span>
					</div>
					<div>
						<span class="kt-label">Procurement</span>
						<span class="kt-meta-value">{{ source.procurement_result }}</span>
					</div>
					<div>
						<span class="kt-label">Completion</span>
						<span class="kt-meta-value">{{ source.completion_result }}</span>
					</div>
				</div>
			</div>
			<a href="#" data-testid="cor-add-separate" @click.prevent="$emit('navigate', additional.route)">{{ additional.action }}</a>
		</template>

		<p v-if="errorSummary" class="pln-error-summary" data-testid="cor-error">{{ errorSummary }}</p>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	task: { type: Object, default: () => ({}) },
	openIssue: { type: String, default: "" },
	pending: Boolean,
	errorSummary: String,
});

defineEmits(["open-issue", "prepare-correction", "record-completed", "close-without-change", "navigate", "back"]);

const requests = computed(() => props.task.requests || []);
const correctingPlan = computed(() => props.task.correcting_plan || {});
const additional = computed(() => props.task.additional_requirement);
const canAct = computed(() => Boolean(props.task.can_act));
</script>
