<!-- PLN-CHG-001 v1.23 §10.12 — publication evidence and recovery (U13),
     ported from U13.dc.html.

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
		<div class="pln-masthead pln-masthead-split">
			<div>
				<h1 class="kt-page-title" data-testid="pub-title">Complete publication of the annual plan</h1>
				<p class="kt-page-lede">
					Record when the approved plan was sent to the National Treasury and attach the submission evidence.
				</p>
			</div>
			<div class="pln-header-actions">
				<button type="button" class="kt-btn kt-btn-secondary" data-testid="pub-view-plan" @click="$emit('navigate', ['annual-procurement-plan', task.plan_reference])">
					View approved plan
				</button>
			</div>
		</div>

		<div class="kt-meta-row pln-context-row" data-testid="pub-context">
			<div>
				<span class="kt-label">Plan</span>
				<span class="kt-meta-value">{{ task.plan_reference }}</span>
			</div>
			<div>
				<span class="kt-label">Version</span>
				<span class="kt-meta-value">{{ task.version?.number }}</span>
			</div>
			<div>
				<span class="kt-label">State</span>
				<span class="kt-meta-value">
					<span class="kt-status" :class="`is-${task.header?.badge_kind}`">{{ stateLabel }}</span>
				</span>
			</div>
		</div>

		<!-- The four facts, each with its own label and state. -->
		<div class="kt-timeline" data-testid="pub-status">
			<div v-for="(row, index) in statusRows" :key="row.label" class="kt-timeline-row" data-testid="pub-status-row">
				<div class="kt-timeline-dot-col">
					<i class="kt-timeline-dot" :class="`is-${row.kind}`"></i>
					<i v-if="index < statusRows.length - 1" class="kt-timeline-line"></i>
				</div>
				<div class="kt-timeline-item">
					<div class="kt-timeline-item-title">{{ row.label }}</div>
					<div class="kt-timeline-item-meta">{{ row.state }}</div>
				</div>
			</div>
		</div>

		<!-- Recorded Treasury evidence, in full, once it exists. -->
		<div v-if="treasury" class="kt-meta-row" data-testid="pub-treasury-evidence">
			<div>
				<span class="kt-label">Date and time sent</span>
				<span class="kt-meta-value">{{ treasury.submitted_display }}</span>
			</div>
			<div>
				<span class="kt-label">Channel</span>
				<span class="kt-meta-value">{{ treasury.channel }}</span>
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
		<div v-if="task.publication_state === 'Indeterminate'" class="kt-notice is-attention" data-testid="pub-unknown">
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
					class="kt-btn kt-btn-primary"
					data-testid="pub-record-treasury"
					:disabled="pending"
					@click="$emit('record-treasury')"
				>
					Record Treasury submission
				</button>
				<button
					v-else-if="task.can_record_treasury && treasury"
					type="button"
					class="kt-btn kt-btn-secondary"
					data-testid="pub-correct-treasury"
					:disabled="pending"
					@click="$emit('correct-treasury')"
				>
					Correct submission details
				</button>
				<!-- The technical operator's, and only after a confirmed
				     failure. An unknown result gets reconciliation instead. -->
				<button
					v-if="task.can_retry"
					type="button"
					class="kt-btn kt-btn-secondary"
					data-testid="pub-retry"
					:disabled="pending"
					@click="$emit('retry')"
				>
					Retry publication
				</button>
				<button
					v-if="task.can_reconcile"
					type="button"
					class="kt-btn kt-btn-secondary"
					data-testid="pub-reconcile"
					:disabled="pending"
					@click="$emit('reconcile')"
				>
					Check publication result
				</button>
			</div>
		</div>

		<!-- When neither action belongs to this reader, name who it belongs
		     to rather than showing a disabled control (§10.12). -->
		<p v-if="responsibleRole" class="kt-muted" data-testid="pub-responsible">
			Responsible role: {{ responsibleRole }}
		</p>

		<details v-if="attempts.length" class="kt-disclosure" data-testid="pub-attempts">
			<summary class="kt-disclosure-head"><span class="kt-disclosure-title">Publication attempts</span></summary>
			<div class="kt-disclosure-body">
				<table class="kt-table">
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
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	task: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
});

defineEmits(["record-treasury", "correct-treasury", "retry", "reconcile", "navigate", "back"]);

const statusRows = computed(() => props.task.status_rows || []);
const attempts = computed(() => props.task.attempts || []);
const treasury = computed(() => props.task.treasury_evidence);

const stateLabel = computed(() => {
	if (props.task.publication_state === "Acknowledged" && props.task.version?.status === "Active") return "Published";
	if (!treasury.value) return "Approved — Treasury submission details needed";
	return props.task.header?.badge || "";
});

// §10.12 — a reader who holds neither action is told whose it is.
const responsibleRole = computed(() => {
	if (props.task.can_retry || props.task.can_reconcile || props.task.can_record_treasury) return "";
	if (props.task.publication_state === "Failed" || props.task.publication_state === "Indeterminate") {
		return "Authorised technical operator";
	}
	if (!treasury.value) return "Accounting Officer";
	return "";
});
</script>
