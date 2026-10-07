<!-- PLN-CHG-001 v1.24 §10.12 — publication evidence and recovery (U13),
     ported from Artboards-U12-U13.dc.html.

     Four facts, four rows, and none of them proves another: the plan was
     approved; the approved document was sent to Treasury; the website
     publication succeeded, failed, or could not be confirmed; and the plan is
     or is not available for procurement.

     Two rules shape the actions. An unknown external result is never shown as
     a failure and never offers a blind retry — it offers reconciliation
     first. And the AO's business action (recording external dispatch) is not
     the technical operator's (retrying or reconciling a transmission); read
     access alone grants neither. -->
<template>
	<div>
		<div class="kt-page">
			<div class="kt-page-head">
				<div>
					<h1 class="kt-page-title" data-testid="pub-title">Complete publication of the annual plan</h1>
					<p class="kt-page-desc">
						Record when the approved plan was sent to the National Treasury and attach the submission evidence.
					</p>
					<!-- The board identifies the record with one scope line inside the
					     head, not a labelled fact row below it (found live 24 Sep 2026). -->
					<div class="kt-page-scope" data-testid="pub-context">
						<span>{{ task.plan_reference }}</span>
						<span>· Version {{ task.version?.number }}</span>
					</div>
					<!-- PLN v1.27 §10.12 — the next-step line replaces the header
					     state badge. -->
					<div ref="headEl" class="kt-guidance-mount" data-testid="pub-next-step-line"></div>
				</div>
				<div class="kt-page-actions">
					<button type="button" class="btn btn-ghost" data-testid="pub-view-plan" @click="$emit('navigate', ['annual-procurement-plan', task.plan_reference])">
						View approved plan
					</button>
					<!-- §10.12 header — enabled alongside View approved plan; the
					     export itself is a separate concern from this screen. -->
					<button type="button" class="btn btn-ghost" data-testid="pub-download-plan" @click="$emit('download-plan')">
						Download approved plan
					</button>
					<button type="button" class="btn btn-ghost" data-testid="pub-download-plan-data" @click="$emit('download-plan-data')">
						Download Plan data
					</button>
				</div>
			</div>

			<!-- Always the reduced tracker: the four status rows below are the
			     working detail of stage 6, not a second tracker. -->
			<div ref="journeyEl" class="kt-guidance-mount" data-testid="pub-journey"></div>
			<div ref="bodyEl" class="kt-guidance-mount" data-testid="pub-next-step-block"></div>

			<!-- The four facts, each with its own label and state. -->
			<div class="kt-region">
				<h2>Publication status</h2>
				<table class="table" data-testid="pub-status">
					<thead>
						<tr><th>Step</th><th>State</th></tr>
					</thead>
					<tbody>
						<tr v-for="row in statusRows" :key="row.label" data-testid="pub-status-row">
							<td>{{ row.label }}</td>
							<td><span class="kt-status" :class="`is-${row.kind}`">{{ row.state }}</span></td>
						</tr>
					</tbody>
				</table>
			</div>

			<!-- Recorded Treasury evidence, in full, once it exists. §10.12
			     U13-EVIDENCE-RECORDED — every recorded field, separately
			     labelled, Destination included. -->
			<div v-if="treasury">
				<!-- The board binds the recorded evidence in a group rule. -->
				<div class="kt-group">
					<div class="kt-meta-row" data-testid="pub-treasury-evidence">
						<div>
							<span class="kt-label">Date and time sent</span>
							<span class="kt-meta-value">{{ treasury.submitted_display }}</span>
						</div>
						<div>
							<span class="kt-label">Channel</span>
							<span class="kt-meta-value">{{ treasury.channel }}</span>
						</div>
						<div>
							<span class="kt-label">Destination</span>
							<span class="kt-meta-value">{{ treasury.destination }}</span>
						</div>
						<div>
							<span class="kt-label">Dispatch reference</span>
							<span class="kt-meta-value">{{ treasury.dispatch_reference }}</span>
						</div>
						<div>
							<span class="kt-label">Recorded by</span>
							<span class="kt-meta-value">{{ treasury.recorded_by_name }}</span>
						</div>
					</div>
				</div>
				<!-- §10.12 — enabled once evidence is recorded; no Record
				     button remains once there is something to view. -->
				<a
					v-if="treasury.supporting_attachment"
					href="#"
					class="btn btn-ghost"
					data-testid="pub-view-evidence"
					@click.prevent="$emit('view-evidence', treasury)"
				>View submission evidence</a>
			</div>

			<!-- U13-WITHDRAWAL-REQUEST — a request that is open is its own state,
			     and the person who asked is named in it. -->
			<div v-if="task.withdrawal_request" class="kt-notice is-warning" data-testid="pub-withdrawal-state">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<circle cx="12" cy="12" r="9"></circle><path d="M12 8h.01M11 12h1v5h1"></path>
				</svg>
				<div class="kt-notice-body">
					<strong>Withdrawal requested — awaiting {{ task.withdrawal_request.capacity || "the approving authority" }}</strong>
					<p>{{ task.withdrawal_request.reason }}</p>
					<p class="kt-muted">
						Requested by {{ task.withdrawal_request.requested_by_name }} · {{ task.withdrawal_request.requested_display }}
					</p>
				</div>
			</div>

			<!-- A hold is a recorded control over transmission, not a withdrawal
			     of the approval (§5.5.2.3). -->
			<div v-if="task.hold?.active" class="kt-notice is-warning" data-testid="pub-hold">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
				</svg>
				<div class="kt-notice-body">
					<strong>Publication is on hold</strong>
					<p>{{ task.hold.reason }}</p>
				</div>
			</div>

			<!-- U13-UNKNOWN — said as uncertainty, with reconciliation first. -->
			<div v-if="task.publication_state === 'Indeterminate'" class="kt-notice is-warning" data-testid="pub-unknown">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<circle cx="12" cy="12" r="9"></circle><path d="M12 8h.01M11 12h1v5h1"></path>
				</svg>
				<div class="kt-notice-body">Check the existing attempt before trying again.</div>
			</div>

			<p v-if="errorSummary" class="pln-error-summary" data-testid="pub-error">{{ errorSummary }}</p>

			<div class="pln-footer" data-testid="pub-footer">
				<span></span>
				<div class="pln-footer-right">
					<!-- The AO's business action. -->
					<button
						v-if="task.can_record_treasury && !treasury"
						type="button"
						class="btn btn-primary"
						data-testid="pub-record-treasury"
						:disabled="pending"
						@click="$emit('record-treasury')"
					>
						Record Treasury submission
					</button>
					<button
						v-else-if="task.can_record_treasury && treasury"
						type="button"
						class="btn btn-secondary"
						data-testid="pub-correct-treasury"
						:disabled="pending"
						@click="$emit('correct-treasury')"
					>
						Correct submission details
					</button>
					<!-- The Head of Procurement Function's, once Treasury
					     submission is recorded and nothing holds the plan (RG-01). -->
					<button
						v-if="task.can_publish"
						type="button"
						class="btn btn-primary"
						data-testid="pub-publish"
						:disabled="pending"
						@click="$emit('publish')"
					>
						Publish annual plan
					</button>
					<!-- The technical operator's, and only after a confirmed
					     failure. An unknown result gets reconciliation instead. -->
					<button
						v-if="task.can_retry"
						type="button"
						class="btn btn-secondary"
						data-testid="pub-retry"
						:disabled="pending"
						@click="$emit('retry')"
					>
						Retry publication
					</button>
					<button
						v-if="task.can_reconcile"
						type="button"
						class="btn btn-secondary"
						data-testid="pub-reconcile"
						:disabled="pending"
						@click="$emit('reconcile')"
					>
						Check publication result
					</button>
					<!-- §10.12 U13-WITHDRAWAL — the recovery route for an approved
					     plan whose content is defective and confirmed not published.
					     The AO asks; the statutory authority decides. Only one ever
					     appears to one person, and once a request is open the AO's is
					     gone. -->
					<button
						v-if="task.can_request_withdrawal"
						type="button"
						class="btn btn-secondary"
						data-testid="pub-request-withdrawal"
						:disabled="pending"
						@click="$emit('request-withdrawal')"
					>
						Request withdrawal for correction
					</button>
					<button
						v-if="task.can_decide_withdrawal"
						type="button"
						class="btn btn-primary"
						data-testid="pub-decide-withdrawal"
						:disabled="pending"
						@click="$emit('decide-withdrawal')"
					>
						Withdraw for correction
					</button>
				</div>
			</div>

			<!-- Whose action it is when not this reader's: the waiting line above
			     names the holder and since when (PLN v1.27 replaces the old
			     "Responsible role" sentence). -->

			<!-- §10.14 / §6.3 — the Accounting Officer's own listed action when the
			     plan only became active after the financial year began. The facts
			     are stated read-only; the explanation never moves the activation
			     instant it explains, and earlier ones are kept, not replaced. -->
			<section v-if="lateActivation.applicable" class="kt-region" data-testid="pub-late-activation">
				<h2>Late start of the annual plan</h2>
				<div class="kt-meta-row">
					<div>
						<span class="kt-label">Financial year started</span>
						<span class="kt-meta-value">{{ lateActivation.financial_year_started_display }}</span>
					</div>
					<div>
						<span class="kt-label">Plan became active</span>
						<span class="kt-meta-value">{{ lateActivation.activated_display }}</span>
					</div>
				</div>
				<LateExplanationHistory
					v-if="lateActivation.explanations.length"
					:financial-year-started="lateActivation.financial_year_started_display"
					:activated-at="lateActivation.activated_display"
					:entries="lateActivation.explanations"
				/>
				<p v-else class="kt-muted" data-testid="pub-late-activation-none">No explanation has been recorded yet.</p>
				<button
					v-if="lateActivation.can_explain"
					type="button"
					class="btn btn-secondary"
					data-testid="pub-explain-late"
					:disabled="pending"
					@click="$emit('explain-late')"
				>
					{{ lateActivation.explanations.length ? "Add to the explanation" : "Explain late start of the annual plan" }}
				</button>
			</section>

			<details v-if="attempts.length" class="kt-disclosure" data-testid="pub-attempts">
				<summary class="kt-disclosure-head">
	<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">Publication attempts</span></div>
	<svg class="kt-disclosure-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 9l6 6 6-6"></path></svg>
</summary>
				<div class="kt-disclosure-body">
					<table class="table">
						<thead><tr><th>Attempt</th><th>Result</th><th>Attempted</th><th>External reference</th></tr></thead>
						<tbody>
							<tr v-for="row in attempts" :key="row.name">
								<td>{{ row.attempt_number }}</td>
								<td>{{ row.result }}</td>
								<td>{{ row.attempted_display || row.attempted_at }}</td>
								<td>{{ row.external_reference || "—" }}</td>
							</tr>
						</tbody>
					</table>
				</div>
			</details>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useGuidance } from "../../pln_shared/composables/useGuidance.js";

import LateExplanationHistory from "./LateExplanationHistory.vue";

const props = defineProps({
	task: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
});

defineEmits([
	"record-treasury", "correct-treasury", "publish", "retry", "reconcile",
	"request-withdrawal", "decide-withdrawal", "explain-late", "navigate", "back",
	"download-plan", "download-plan-data", "view-evidence",
]);

const statusRows = computed(() => props.task.status_rows || []);
const attempts = computed(() => props.task.attempts || []);
const treasury = computed(() => props.task.treasury_evidence);

const lateActivation = computed(() => ({
	applicable: false,
	financial_year_started_display: "",
	activated_display: "",
	explanations: [],
	can_explain: false,
	...(props.task.late_activation || {}),
}));

const headEl = ref(null);
const journeyEl = ref(null);
const bodyEl = ref(null);
useGuidance({ journeyEl, headEl, bodyEl }, { answer: () => props.task.next_step, journey: () => props.task.journey, pending: () => props.pending });
</script>
