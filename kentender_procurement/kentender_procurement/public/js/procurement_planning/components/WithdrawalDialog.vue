<!-- PLN-CHG-001 v1.23 §10.12 — Withdrawal for correction
     (U13-WITHDRAWAL-REQUEST-DIALOG / U13-WITHDRAWAL-DECISION-DIALOG),
     ported from U13.dc.html.

     Two people, two dialogs, and neither can do the other's part. The
     Accounting Officer asks, stating why. The configured statutory authority
     decides, and cannot edit the reason it is deciding on — reading someone
     else's stated reason and being able to rewrite it are not compatible.

     Both say the same two things before the action, because they are what the
     person needs to know: the approved plan stays in history, and a correction
     repeats the review and approval it already passed. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="pub-withdrawal-dialog">
		<div class="kt-dialog" role="dialog" aria-modal="true" aria-labelledby="pub-withdrawal-title">
			<div id="pub-withdrawal-title" class="kt-dialog-title" data-testid="pub-withdrawal-title">
				{{ isDecision ? "Withdraw this plan for correction?" : "Request withdrawal for correction" }}
			</div>

			<div class="kt-meta-row" data-testid="pub-withdrawal-plan">
				<div>
					<span class="kt-label">Plan</span>
					<span class="kt-meta-value">{{ task.plan_title }}</span>
				</div>
				<div>
					<span class="kt-label">Reference</span>
					<span class="kt-meta-value">{{ task.plan_reference }}</span>
				</div>
				<div>
					<span class="kt-label">Version</span>
					<span class="kt-meta-value">{{ task.version?.number }}</span>
				</div>
				<!-- The fact the whole route depends on. -->
				<div>
					<span class="kt-label">Publication status</span>
					<span class="kt-meta-value" data-testid="pub-withdrawal-confirmation">{{ task.publication_confirmation }}</span>
				</div>
			</div>

			<!-- The decision reads the request; it does not author it. -->
			<div v-if="isDecision" class="kt-meta-row" data-testid="pub-withdrawal-request">
				<div>
					<span class="kt-label">Reason for withdrawal</span>
					<span class="kt-meta-value">{{ request.reason }}</span>
				</div>
				<div>
					<span class="kt-label">Requested by</span>
					<span class="kt-meta-value">{{ request.requested_by_name }}</span>
				</div>
				<div>
					<span class="kt-label">Requested at</span>
					<span class="kt-meta-value">{{ request.requested_display }}</span>
				</div>
			</div>
			<div v-else class="kt-field">
				<label for="pub-withdrawal-reason" class="kt-label">Reason for withdrawal</label>
				<textarea id="pub-withdrawal-reason" class="kt-input" rows="3" data-testid="pub-withdrawal-reason" v-model="reason"></textarea>
			</div>

			<p class="pln-dialog-lede" data-testid="pub-withdrawal-consequence">
				The approved plan will remain in history.
				{{
					isDecision
						? "A correction draft will be prepared and will repeat the required review and approval."
						: "If the request is approved, a correction draft will repeat the required review and approval."
				}}
			</p>

			<p v-if="error" class="pln-dialog-error" role="alert" data-testid="pub-withdrawal-error">{{ error }}</p>

			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">Cancel</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="pub-withdrawal-confirm"
					:disabled="pending || !ready"
					@click="$emit('confirm', reason.trim())"
				>
					{{ isDecision ? "Withdraw for correction" : "Request withdrawal for correction" }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";

const props = defineProps({
	task: { type: Object, default: () => ({}) },
	// "request" is the Accounting Officer's; "decision" is the statutory
	// authority's. The component never infers which from a role.
	mode: { type: String, default: "request" },
	pending: Boolean,
	error: String,
});

defineEmits(["confirm", "cancel"]);

const isDecision = computed(() => props.mode === "decision");
const request = computed(() => props.task.withdrawal_request || {});
const reason = ref("");

// The request needs a reason someone can act on; the decision is on a reason
// already given, so it is ready as soon as it is opened.
const ready = computed(() => (isDecision.value ? true : reason.value.trim().length >= 10));
</script>
