<script setup>
// BDS-CHG-001 v0.8 §10.15 BDS-DES-14 withdrawal dialog (`WithdrawBid`),
// ported from "Bid Board v3 - D": the Tender, bid, current receipt and
// deadline; a required reason of 10–500 characters; the consequence. The
// dialog is the confirmation. A refused reason is named in place; success
// opens the acknowledgement.
import { computed, inject, nextTick, onMounted, ref } from "vue";
import { useDialogFocus } from "../composables/useDialogFocus.js";
import CommonState from "./CommonState.vue";
import { conflictState } from "../composables/commonStates.js";

const METHOD = "kentender_procurement.bid_submission.api.withdraw_bid";
const props = defineProps({
	bid: { type: Object, required: true },
	withdrawal: { type: Object, required: true },
});
const emit = defineEmits(["close", "withdrawn", "stale"]);
const portal = inject("portal");
const reason = ref("");
const error = ref("");
const failure = ref("");
const problem = ref(null); // another person changed the bid, or a newer submission exists
const first = ref(null);
const key = `bds-withdraw-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value);

function withdraw() {
	error.value = "";
	failure.value = "";
	return runner.run(async () => {
		let result;
		try {
			result = await portal.call(
				METHOD,
				{ bid_reference: props.bid.reference, receipt_reference: props.withdrawal.receipt_reference, reason: reason.value.trim(), confirmed: 1, expected_record_version: props.bid.record_version, idempotency_key: key },
				{ type: "POST" },
			);
		} catch (e) {
			problem.value = conflictState(e, props.bid.tender_reference);
			if (!problem.value) throw e;
			return;
		}
		if (result && result.ok) emit("withdrawn", result);
		else if (result && result.errors) error.value = result.errors.reason || result.message || "";
		else if (result) failure.value = result.message || "";
	}, "Withdraw bid");
}
const dialogBox = ref(null);
useDialogFocus(first, dialogBox);
</script>

<template>
	<div ref="dialogBox" class="dialog-backdrop" data-testid="bds-withdraw-dialog" @keydown.esc.stop="!pending && emit('close')">
		<div class="dialog bds-dialog" role="dialog" aria-modal="true" aria-labelledby="bds-withdraw-title">
			<div id="bds-withdraw-title" class="dialog-title">{{ __("Withdraw this bid?") }}</div>
			<div class="bds-dialog-facts">
				<div class="bds-dialog-fact"><span class="kt-label">{{ __("Tender") }}</span><span>{{ bid.tender_reference }}</span></div>
				<div class="bds-dialog-fact"><span class="kt-label">{{ __("Bid") }}</span><span>{{ bid.reference }}</span></div>
				<div class="bds-dialog-fact"><span class="kt-label">{{ __("Current receipt") }}</span><span>{{ withdrawal.receipt_reference }}</span></div>
				<div class="bds-dialog-fact"><span class="kt-label">{{ __("Deadline") }}</span><span>{{ withdrawal.deadline }}</span></div>
			</div>
			<div class="field">
				<label for="bds-withdraw-reason">{{ __("Reason for withdrawal") }}</label>
				<textarea id="bds-withdraw-reason" ref="first" v-model="reason" class="input" rows="3" maxlength="500" :aria-invalid="!!error" aria-describedby="bds-withdraw-help" data-testid="bds-withdraw-reason"></textarea>
				<p v-if="error" class="kt-field-error" data-testid="bds-withdraw-error">{{ error }}</p>
				<p id="bds-withdraw-help" class="bds-help">{{ __("Enter 10–500 characters.") }}</p>
			</div>
			<p class="bds-dialog-text">{{ __("The bid will no longer be considered. You may submit a new replacement before the deadline. The submitted history will not be deleted.") }}</p>
			<div v-if="failure" class="kt-notice is-critical" role="alert"><div class="kt-notice-body">{{ failure }}</div></div>
			<CommonState v-if="problem" inline :state="problem.key" :figures="problem.figures" :action-href="problem.href" @action="emit('stale')" />
			<div class="dialog-actions">
				<button type="button" class="btn btn-secondary" :disabled="pending" @click="emit('close')">{{ __("Keep bid") }}</button>
				<button type="button" class="btn btn-primary kt-danger" :disabled="pending" data-testid="bds-withdraw-confirm" @click="withdraw">{{ pending ? __("Withdrawing…") : __("Withdraw bid") }}</button>
			</div>
		</div>
	</div>
</template>
