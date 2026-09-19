<!-- TPR-DES-11 Respond to addendum inquiry (760px), ported class-for-class:
     candidate shown as "Verified supplier account" (identity only for
     oversight readers, from the server), the question, the response, the
     Yes/No effect choice with its consequence text, Cancel / Send response.
     Answered and Late inquiries render read-only with their outcome. -->
<template>
	<div class="tnd-page tnd-page--tight" data-screen-label="TPR-DES-11 Respond to addendum inquiry">
		<BlueprintCard>
			<div class="tnd-head">
				<h1 class="tnd-h1" style="margin-bottom: 6px" data-testid="tnd-record-title">Respond to addendum inquiry</h1>
				<p class="tnd-refs">Addendum {{ inquiry.addendum_reference }} · {{ data.tender.tender_reference }}</p>
				<p class="tnd-lede">Answer the question and state whether the response changes any Tender requirement.</p>
			</div>
			<div class="tnd-section tnd-grid-2">
				<div class="tnd-fact"><div class="kt-label">Candidate</div><div class="tnd-fact-value" data-testid="tnd-inq-candidate">{{ inquiry.candidate_label }}<span v-if="inquiry.candidate_identity" class="tnd-sub">Identity (oversight only): {{ inquiry.candidate_identity }}</span></div></div>
				<div class="tnd-fact"><div class="kt-label">Received</div><div class="tnd-fact-value">{{ inquiry.received_at_label }}</div></div>
			</div>
			<div class="tnd-section">
				<div class="kt-label" style="margin-bottom: 6px">Question</div>
				<p class="tnd-card-body" data-testid="tnd-inq-question">{{ inquiry.question }}</p>
			</div>
			<div v-if="inquiry.status === 'Late'" class="tnd-section">
				<div class="kt-notice is-critical" data-testid="tnd-inq-late"><div class="kt-notice-body"><strong>{{ data.late_text || "The inquiry deadline has passed." }}</strong> The inquiry is preserved and cannot be answered.</div></div>
			</div>
			<template v-else-if="inquiry.status === 'Answered'">
				<div class="tnd-section"><div class="kt-label" style="margin-bottom: 6px">Response</div><p class="tnd-card-body" data-testid="tnd-inq-response-text">{{ inquiry.response }}</p></div>
				<div class="tnd-section tnd-section--last tnd-grid-2">
					<div class="tnd-fact"><div class="kt-label">Responded by</div><div class="tnd-fact-value">{{ inquiry.responded_by_name }}<span class="tnd-sub">{{ inquiry.responded_at_label }}</span></div></div>
					<div class="tnd-fact"><div class="kt-label">Effect</div><div class="tnd-fact-value">{{ inquiry.affects_requirements ? "Affects a Tender requirement — broadcast to every registered candidate" : "No requirement affected — sent to the candidate" }}<span class="tnd-sub">{{ inquiry.broadcast_status }}</span></div></div>
				</div>
			</template>
			<template v-else>
				<div class="tnd-section">
					<div class="kt-field" style="margin: 0"><label for="tnd-inq-response">Response</label><textarea id="tnd-inq-response" class="kt-input" rows="4" v-model="response" :disabled="!canRespond" data-testid="tnd-inq-response"></textarea><p v-if="fieldError" class="tnd-field-error" data-testid="tnd-inq-error">{{ fieldError }}</p></div>
				</div>
				<div class="tnd-section tnd-section--last">
					<div class="kt-label" style="margin-bottom: 8px">Does this response affect a Tender requirement?</div>
					<div style="display: flex; gap: 16px">
						<label class="tnd-radio"><input type="radio" name="tnd-affects" :checked="!affects" :disabled="!canRespond" data-testid="tnd-inq-affects-no" @change="affects = false" /><span class="dot"></span>No</label>
						<label class="tnd-radio"><input type="radio" name="tnd-affects" :checked="affects" :disabled="!canRespond" data-testid="tnd-inq-affects-yes" @change="affects = true" /><span class="dot"></span>Yes</label>
					</div>
					<p class="tnd-small tnd-muted-700" style="margin: 12px 0 0" data-testid="tnd-inq-effect">{{ affects ? effects.yes : effects.no }}</p>
				</div>
			</template>
		</BlueprintCard>
		<div class="tnd-footer tnd-footer--end">
			<button type="button" class="kt-btn kt-btn-secondary" data-testid="tnd-inq-cancel" @click="$emit('back')">{{ canRespond ? "Cancel" : "Back" }}</button>
			<button v-if="canRespond" type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="tnd-inq-send" @click="send">Send response</button>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import BlueprintCard from "./BlueprintCard.vue";

const props = defineProps({
	data: { type: Object, default: () => ({ tender: {}, inquiry: {} }) },
	pending: Boolean,
	error: { type: String, default: "" },
});
const emit = defineEmits(["back", "send"]);

const inquiry = computed(() => props.data.inquiry || {});
const effects = computed(() => props.data.effect_texts || { no: "The response will be sent to the candidate and recorded.", yes: "The response will be sent to every registered candidate without identifying who asked." });
const canRespond = computed(() => (props.data.allowed_actions || []).includes("send_response"));
const response = ref("");
const affects = ref(false);
const fieldError = computed(() => props.error || "");
function send() {
	emit("send", { response: response.value.trim(), affects_requirements: affects.value });
}
</script>
