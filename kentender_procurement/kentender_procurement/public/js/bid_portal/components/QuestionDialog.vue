<script setup>
// BDS-CHG-001 v0.8 §10.8 BDS-DES-07-QUESTION-OPEN-DIALOG (and its success
// state), ported from "Bid Board v3 - B". A registered candidate asks one
// question before the clarification deadline; `SubmitTenderClarification`
// sends it to Tenders, which owns the record (§11.2). Nothing is created
// until Send question. Invalid text is named in place and kept.
import { computed, inject, nextTick, onMounted, ref } from "vue";
import { useDialogFocus } from "../composables/useDialogFocus.js";

const METHOD = "kentender_procurement.bid_submission.api.submit_tender_clarification";
const props = defineProps({
	tender: { type: Object, required: true },
	organisation: { type: Object, default: null },
});
const emit = defineEmits(["close", "sent"]);
const portal = inject("portal");
const question = ref("");
const error = ref("");
const failure = ref("");
const sent = ref(null);
const field = ref(null);
const key = `bds-q-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value);

function send() {
	error.value = "";
	failure.value = "";
	return runner.run(async () => {
		const result = await portal.call(METHOD, { tender_reference: props.tender.reference, question: question.value, organisation: (props.organisation || {}).id || "", idempotency_key: key }, { type: "POST" });
		if (result && result.ok) {
			sent.value = result;
			emit("sent", result);
		} else if (result && result.errors) {
			error.value = result.errors.question || result.message;
		}
	}, "Send question");
}
const dialogBox = ref(null);
useDialogFocus(field, dialogBox);
</script>

<template>
	<div ref="dialogBox" class="kt-dialog-backdrop" data-testid="bds-question-dialog" @keydown.esc.stop="emit('close')">
		<div class="kt-dialog bds-dialog" role="dialog" aria-modal="true" :aria-label="__('Ask a question about this Tender')">
			<div class="kt-dialog-title">{{ __("Ask a question about this Tender") }}</div>
			<template v-if="sent">
				<div class="kt-notice is-live" role="status" data-testid="bds-question-sent">
					<svg class="kt-notice-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="m8.5 12.5 2.5 2.5 4.5-5" /></svg>
					<div class="kt-notice-body"><strong>{{ __("Question received {0}", [sent.received_at]) }}</strong></div>
				</div>
				<div class="kt-dialog-actions">
					<button type="button" class="kt-btn kt-btn-secondary" data-testid="bds-question-close" @click="emit('close')">{{ __("Close") }}</button>
				</div>
			</template>
			<template v-else>
				<div class="kt-dialog-body">{{ __("Questions must be sent before {0}. Your organisation will be known to the procurement team but will not be identified in a general answer.", [tender.clarification_deadline]) }}</div>
				<div class="bds-dialog-facts">
					<div class="bds-dialog-fact"><span class="kt-label">{{ __("Tender") }}</span><span>{{ tender.title }} · {{ tender.reference }}</span></div>
					<div v-if="organisation" class="bds-dialog-fact"><span class="kt-label">{{ __("Organisation") }}</span><span>{{ organisation.legal_name }}</span></div>
				</div>
				<div class="kt-field">
					<label for="bds-question">{{ __("Your question") }}</label>
					<textarea id="bds-question" ref="field" v-model="question" class="kt-input" rows="4" maxlength="2000" :aria-invalid="!!error" aria-describedby="bds-question-help" data-testid="bds-question-text"></textarea>
					<p v-if="error" class="kt-field-error">{{ error }}</p>
					<p v-else id="bds-question-help" class="bds-help">{{ __("10–2,000 characters.") }}</p>
				</div>
				<div v-if="failure" class="kt-notice is-critical" role="alert"><div class="kt-notice-body">{{ failure }}</div></div>
				<div class="kt-dialog-actions">
					<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="bds-question-cancel" @click="emit('close')">{{ __("Cancel") }}</button>
					<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="bds-question-send" @click="send">{{ pending ? __("Sending…") : __("Send question") }}</button>
				</div>
			</template>
		</div>
	</div>
</template>
