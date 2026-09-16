<!-- NDS-UI-07 withdrawal review (§12.6) — NDS-DES-12 base (blocked/
     "still-Active") + the CLEAR variant. The dependency is always the fresh
     server result, never a cached button state. -->
<template>
	<div class="kt-panel-lg" style="max-width: 700px">
		<h3 style="margin: 0">Review withdrawal request</h3>
		<div style="font-size: 16px; font-weight: 600; margin: var(--kt-space-3) 0 2px">{{ revision.title }}</div>
		<div class="kt-label" style="margin-bottom: var(--kt-space-3)">
			Need {{ need.need_reference }} · Withdrawal request {{ request.name }} · Accepted revision {{ revision.revision_number }}
		</div>
		<span class="kt-status" :class="dependency.included ? 'is-attention' : 'is-pending'">
			{{ dependency.included ? "Waiting for a Planning change" : "Awaiting review" }}
		</span>

		<div v-if="errorSummary" data-testid="nds-error-summary" class="kt-notice is-critical" style="margin-top: var(--kt-space-4)">
			<div class="kt-notice-body">{{ errorSummary }}</div>
		</div>

		<h6 class="kt-card-title" style="margin-top: var(--kt-space-6)">Withdrawal request</h6>
		<div style="display: flex; gap: var(--kt-space-6); font-size: 13px; margin: var(--kt-space-3) 0 var(--kt-space-3)">
			<div><span class="kt-label" style="display: block">Requested by</span>{{ requesterLabel }}</div>
			<div><span class="kt-label" style="display: block">Requested at</span>{{ formatInstant(requestedAt) }}</div>
		</div>
		<div style="font-size: 13px">
			<span class="kt-label" style="display: block">Reason for withdrawal</span>{{ request.reason }}
		</div>

		<!-- §11.13 second section — Planning status; blocked (STILL-ACTIVE) or
		     CLEAR (no Active inclusion). UNAVAILABLE (the check itself failing)
		     is not distinguishable from CLEAR by the current read contract —
		     see FOLLOW_UPS FU-27. -->
		<div v-if="dependency.included" class="kt-notice is-warning" style="margin: var(--kt-space-4) 0">
			<div class="kt-notice-body">
				<strong>Withdrawal cannot be approved yet.</strong> This requirement is still
				included in the current annual plan. Procurement must review the necessary plan
				change before withdrawal can proceed.
				<div v-if="dependency.active_plan_item" style="font-size: 12px; margin-top: var(--kt-space-3)">
					Item: {{ dependency.active_plan_item }}
				</div>
				<button
					v-if="dependency.active_plan_item"
					type="button"
					class="kt-action-link"
					data-testid="nds-view-plan-item"
					style="font-size: 12px; margin-top: 6px"
					@click="$emit('view-plan-item')"
				>
					View annual plan item
				</button>
			</div>
		</div>
		<div v-else class="kt-notice is-info" style="margin: var(--kt-space-4) 0">
			<div class="kt-notice-body">This requirement is not included in the current annual plan.</div>
		</div>

		<div class="kt-panel" style="margin-bottom: var(--kt-space-4)">
			<div class="kt-meta-row">
				<div><span class="kt-label">Department</span><span class="kt-meta-value" style="font-size: 14px">{{ scope.organisation_unit || "" }}</span></div>
				<div><span class="kt-label">Financial year</span><span class="kt-meta-value" style="font-size: 14px">{{ scope.financial_year || "" }}</span></div>
			</div>
		</div>

		<RequirementCard :revision="revision" />

		<p v-if="makerCheckerBlocked" class="text-muted" style="font-size: 14.5px; margin: var(--kt-space-4) 0 0">
			You requested this withdrawal, so it must be decided by another Head of User
			Department.
		</p>

		<div style="display: flex; justify-content: flex-end; gap: var(--kt-space-2); padding-top: var(--kt-space-4); border-top: 1px solid var(--kt-color-divider)">
			<button
				v-if="canDecline"
				class="kt-btn kt-btn-secondary"
				:disabled="pending"
				data-testid="nds-withdrawal-decline"
				@click="$emit('decline')"
			>
				Decline withdrawal
			</button>
			<!-- §11.13 — blocked (still-Active) never offers Approve; Close
			     replaces it as the only other footer action. -->
			<button
				v-if="dependency.included"
				class="kt-btn kt-btn-secondary"
				data-testid="nds-withdrawal-close"
				:disabled="pending"
				@click="$emit('close')"
			>
				Close
			</button>
			<button
				v-else-if="canApprove"
				class="kt-btn kt-btn-primary"
				:disabled="pending"
				data-testid="nds-withdrawal-approve"
				@click="$emit('approve')"
			>
				Approve withdrawal
			</button>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import RequirementCard from "./RequirementCard.vue";
import { formatInstant } from "../data/format.js";

const props = defineProps({
	need: { type: Object, default: () => ({}) },
	request: { type: Object, default: () => ({}) },
	revision: { type: Object, default: () => ({}) },
	scope: { type: Object, default: () => ({}) },
	dependency: { type: Object, default: () => ({}) },
	requesterLabel: { type: String, default: "" },
	requestedAt: { type: String, default: "" },
	// KT-STD-001 §3A.6 — an "oversight" reader (technical or Auditor) never
	// decides: the parent passes task.permitted_decisions, empty for them, so
	// Approve/Decline never render even while the request is open.
	permitted: { type: Array, default: () => [] },
	makerCheckerBlocked: Boolean,
	errorSummary: { type: String, default: "" },
	pending: Boolean,
});
defineEmits(["approve", "decline", "close", "view-plan-item"]);

const canDecline = computed(() => !props.makerCheckerBlocked && props.permitted.includes("decline"));
const canApprove = computed(() => !props.makerCheckerBlocked && props.permitted.includes("approve"));
</script>
