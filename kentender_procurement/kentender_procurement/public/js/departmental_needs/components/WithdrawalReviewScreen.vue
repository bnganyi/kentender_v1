<!-- NDS-UI-07 withdrawal review (§12.6) — NDS-DES-12 base (blocked/
     "still-Active"), the CLEAR variant and NDS-DES-12-UNAVAILABLE (the check
     itself failing, `dependency.unavailable`). The dependency is always the
     fresh server result, never a cached button state. -->
<template>
	<div class="kt-page">
		<div>
			<h1 class="kt-page-title">Review withdrawal request</h1>
			<div style="font-family: var(--kt-font-heading); font-weight: 600; font-size: 22px; margin-top: 10px">{{ revision.title }}</div>
			<div style="display: flex; align-items: center; gap: 12px; margin-top: 6px">
				<span class="text-muted" style="font-size: 13px">{{ need.need_reference }} · Accepted revision {{ revision.revision_number }}</span>
			</div>
			<div class="text-muted" style="font-size: 12px; margin-top: 8px">Withdrawal request {{ request.name }}</div>
		</div>

		<!-- NDS-CHG-001 v1.15 §5.5 — the guidance region replaces the status
		     badge ("Waiting for a Planning change" / "Awaiting review"): the
		     next step names the state and whose turn it is. -->
		<div ref="guidanceEl" class="kt-guidance-mount" data-testid="nds-guidance"></div>

		<div v-if="errorSummary" data-testid="nds-error-summary" class="kt-notice is-critical" style="max-width: 900px">
			<div class="kt-notice-body">{{ errorSummary }}</div>
		</div>

		<!-- §11.13 — Planning status leads the decision: blocked (STILL-ACTIVE),
		     CLEAR (no Active inclusion) or NDS-DES-12-UNAVAILABLE (the check
		     itself failed — a distinguishable provider-failure profile, separate
		     from CLEAR; closes FOLLOW_UPS FU-27's withdrawal-screen gap). -->
		<div v-if="dependency.unavailable" class="kt-notice is-critical" style="max-width: 900px">
			<div class="kt-notice-body">
				Planning information could not be checked. Withdrawal cannot be approved until
				the check succeeds.
				<div>
					<button
						type="button"
						class="kt-action-link"
						data-testid="nds-retry-dependency"
						style="font-size: 12px; margin-top: 6px"
						:disabled="dependencyChecking"
						@click="$emit('retry-dependency')"
					>
						{{ dependencyChecking ? "Checking…" : "Try again" }}
					</button>
				</div>
			</div>
		</div>
		<div v-else-if="dependency.included" class="kt-notice is-critical" style="max-width: 900px">
			<div class="kt-notice-body">
				<div style="font-weight: 600; color: var(--kt-color-text)">Withdrawal cannot be approved yet.</div>
				<p style="margin: 6px 0 0">
					This requirement is still included in the current annual plan. Procurement must
					review the necessary plan change before withdrawal can proceed.
				</p>
			</div>
		</div>
		<div v-else class="kt-notice is-info" style="max-width: 900px">
			<div class="kt-notice-body">This requirement is not included in the current annual plan.</div>
		</div>

		<!-- A titled section is a `.kt-region`: that is what puts its heading
		     in the section typeface and its content on the section rhythm.
		     Five headings in this module stood in bare divs, so they were
		     styled by nothing and drifted from the sections beside them
		     (found live 24 Sep 2026). -->
		<div class="kt-region">
			<h2>Why withdrawal was requested</h2>
			<div style="max-width: 900px">
				<p style="margin: 0; font-size: 15px; line-height: 1.55">{{ request.reason }}</p>
				<p class="text-muted" style="margin: 12px 0 0; font-size: 12px">
					Requested by {{ requesterLabel }} · <span data-volatile="true">{{ formatInstant(requestedAt) }}</span>
				</p>
			</div>
		</div>

		<div v-if="dependency.included || dependency.active_plan_item" class="kt-region is-secondary">
			<h2>Planning dependency</h2>
			<div class="kt-group" style="max-width: 900px">
				<div class="kt-meta-row">
					<div><span class="kt-label">Responsible</span><span class="kt-meta-value" style="font-size: 15px">Procurement Planner</span></div>
					<div v-if="dependency.active_plan"><span class="kt-label">Plan</span><span class="kt-meta-value" style="font-size: 15px">{{ dependency.active_plan }}</span></div>
					<div v-if="dependency.active_plan_item"><span class="kt-label">Item</span><span class="kt-meta-value" style="font-size: 15px">{{ dependency.active_plan_item }}</span></div>
				</div>
				<button
					v-if="dependency.active_plan_item"
					type="button"
					class="kt-action-link"
					data-testid="nds-view-plan-item"
					style="margin-top: 12px"
					@click="$emit('view-plan-item')"
				>
					View annual plan item
				</button>
			</div>
		</div>

		<div class="kt-region">
			<h2>Accepted requirement</h2>
			<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; font-size: 13px; color: var(--kt-color-neutral-700)">
				<span>{{ scope.organisation_unit || "" }}</span>
				<span>·</span>
				<span>{{ scope.financial_year || "" }}</span>
			</div>
			<div style="max-width: 900px">
				<RequirementCard :revision="revision" />
			</div>
		</div>

		<p v-if="makerCheckerBlocked" class="text-muted" style="font-size: 14.5px; max-width: 900px">
			You requested this withdrawal, so it must be decided by another Head of User
			Department.
		</p>

		<div style="display: flex; justify-content: flex-end; gap: 12px; padding-top: 20px; border-top: 1px solid var(--kt-color-divider); max-width: 900px">
			<!-- §11.13 — blocked (still-Active) or UNAVAILABLE never offer
			     Approve; Close replaces it as the only other footer action.
			     Decline sits between Close and Approve so the same single
			     button naturally reproduces both artboard orders: [Close,
			     Decline] when blocked (Approve absent) and [Decline, Approve]
			     when clear (Close absent) — NDS-DES-12 puts the blocked state's
			     one real decision rightmost, the reverse of NDS-DES-12-CLEAR's
			     Decline-then-Approve order, where Approve is rightmost as the
			     primary action. -->
			<button
				v-if="dependency.included || dependency.unavailable"
				class="btn btn-secondary"
				data-testid="nds-withdrawal-close"
				:disabled="pending"
				@click="$emit('close')"
			>
				Close
			</button>
			<button
				v-if="canDecline"
				class="btn btn-secondary"
				:disabled="pending"
				data-testid="nds-withdrawal-decline"
				@click="$emit('decline')"
			>
				<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18M6 6l12 12" /></svg
				>Decline withdrawal
			</button>
			<button
				v-if="!(dependency.included || dependency.unavailable) && canApprove"
				class="btn btn-primary"
				:disabled="pending"
				data-testid="nds-withdrawal-approve"
				@click="$emit('approve')"
			>
				<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5" /></svg
				>Approve withdrawal
			</button>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import RequirementCard from "./RequirementCard.vue";
import { followFix, useGuidance } from "../../nds_shared/composables/useGuidance.js";
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
	dependencyChecking: Boolean,
	nextStep: { type: Object, default: null },
	journey: { type: Object, default: null },
});
defineEmits(["approve", "decline", "close", "view-plan-item", "retry-dependency"]);

const guidanceEl = ref(null);
useGuidance(guidanceEl, { answer: () => props.nextStep, journey: () => props.journey }, { onFix: followFix });

const canDecline = computed(() => !props.makerCheckerBlocked && props.permitted.includes("decline"));
const canApprove = computed(() => !props.makerCheckerBlocked && props.permitted.includes("approve"));
</script>
