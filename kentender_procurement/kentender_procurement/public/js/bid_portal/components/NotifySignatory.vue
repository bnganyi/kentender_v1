<script setup>
// Hand a finished bid over (owner request, 2 Oct 2026). The person who prepared
// the bid cannot submit it, so this tells the Authorised Signatory it is ready:
// one message with a link and an optional note. The read says who is waiting,
// when they were last told and whether another message may go now; the server
// refuses a second message within ten minutes. Nothing here decides any of it.
import { computed, inject, ref } from "vue";

const METHOD = "kentender_procurement.bid_submission.api.notify_signatory";
const props = defineProps({
	handover: { type: Object, required: true }, // { signatories, can_notify, last, wait_text, max_note }
	bid: { type: Object, required: true }, // { reference }
	organisation: { type: String, default: "" },
});
const emit = defineEmits(["sent"]);
const portal = inject("portal");
const note = ref("");
const error = ref("");
const failure = ref("");
const sent = ref("");
let attempt = `bds-notify-${Date.now().toString(36)}`;
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value);
const names = computed(() => props.handover.signatories.join(", "));

function send() {
	error.value = "";
	failure.value = "";
	sent.value = "";
	return runner.run(async () => {
		const result = await portal.call(METHOD, { bid_reference: props.bid.reference, note: note.value, organisation: props.organisation, idempotency_key: attempt }, { type: "POST" });
		if (result && result.ok) {
			sent.value = `${result.recipients.join(", ")} was notified ${result.notified_at}.`;
			note.value = "";
			attempt = `bds-notify-${Date.now().toString(36)}`; // the next message is a new request
			emit("sent", result);
		} else if (result && result.errors) {
			error.value = result.errors.note || result.errors.notify || result.message;
		}
	}, "Notify");
}
</script>

<template>
	<div class="kt-region" data-testid="bds-handover">
		<h2>{{ __("Hand over to the signatory") }}</h2>
		<div class="bds-region-body">
			<p class="bds-muted">{{ __("Only an Authorised Signatory can sign and submit this bid. {0} has it waiting in My bids. You can send a message with a link to it.", [names]) }}</p>
			<p v-if="handover.last" class="bds-muted" data-testid="bds-handover-last">{{ __("Last notified {0} by {1}.", [handover.last.at_label, handover.last.by]) }}</p>
			<div v-if="sent" class="kt-notice is-live" role="status" data-testid="bds-handover-sent">
				<svg class="kt-notice-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="m8.5 12.5 2.5 2.5 4.5-5" /></svg>
				<div class="kt-notice-body">{{ sent }}</div>
			</div>
			<template v-if="handover.can_notify">
				<div class="kt-field">
					<label for="bds-handover-note">{{ __("Message (optional)") }}</label>
					<textarea id="bds-handover-note" v-model="note" class="kt-input" rows="2" :maxlength="handover.max_note" :aria-invalid="!!error" data-testid="bds-handover-note"></textarea>
					<p v-if="error" class="kt-field-error" data-testid="bds-handover-error">{{ error }}</p>
				</div>
				<div><button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="bds-handover-send" @click="send">{{ pending ? __("Sending…") : __("Notify {0}", [names]) }}</button></div>
			</template>
			<p v-else-if="handover.wait_text" class="bds-muted" data-testid="bds-handover-wait">{{ handover.wait_text }}</p>
			<div v-if="failure" class="kt-notice is-critical" role="alert"><div class="kt-notice-body">{{ failure }}</div></div>
		</div>
	</div>
</template>
